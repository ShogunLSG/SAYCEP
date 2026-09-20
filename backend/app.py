"""SAYCEP API -- the seven endpoints specified in the proposal.

Run:  python -m uvicorn app:app --reload --port 8000   (from the backend/ dir)
Docs: http://127.0.0.1:8000/docs

Named to match the component in the sequence diagram. Routes only: the gap,
pathway and recommendation logic live in their own modules so the ML component
can be lifted into its own service later without touching the request layer.
"""

import sqlite3
import sys

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from config import ESSENTIAL_THRESHOLD
import gap as gap_analyser
import pathway as pathway_service
import recommend as recommendation_engine
import repository

app = FastAPI(
    title="SAYCEP API",
    description="South African Youth Career and Employment Platform",
    version="0.1.0",
)

# The frontend is served separately during development.
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

con = repository.connect()

# NFR-03: refuse to serve rather than serve partial data.
if not repository.reference_data_present(con):
    sys.exit("saycep.db is missing or empty. Run: python backend/load_onet.py")
repository.ensure_profile_tables(con)


class ProfileIn(BaseModel):
    profile_type: str = Field(..., pattern="^(student|school_leaver)$")
    skills: list[str] = Field(default_factory=list)
    target_soc_code: str | None = None


def _resolve_target(profile, soc_code):
    target = soc_code or profile["target_soc_code"]
    if not target:
        raise HTTPException(400, "No target occupation. Pass soc_code, or set "
                                 "target_soc_code when creating the profile.")
    return target


def _require_profile(profile_id):
    profile = repository.get_profile(con, profile_id)
    if profile is None:
        raise HTTPException(404, f"No profile {profile_id}")
    return profile


def _require_occupation(soc_code):
    occ = repository.get_occupation(con, soc_code)
    if occ is None:
        raise HTTPException(404, f"No occupation {soc_code} in the catalogue")
    return occ


# ---------- catalogue ----------

@app.get("/occupations", tags=["catalogue"])
def list_occupations(
    zone: int | None = Query(None, ge=1, le=5, description="O*NET Job Zone"),
    q: str | None = Query(None, min_length=2, description="title search"),
    limit: int = Query(100, ge=1, le=1000),
):
    """FR-04 search, FR-05 browse by preparation level.

    When filtered by zone the response carries that zone's description, so the
    screen can show what the preparation level actually means without a second
    request.
    """
    rows = repository.list_occupations(con, zone, q, limit)
    total = repository.count_occupations(con, zone, q)
    zone_info = None
    if zone is not None:
        zone_info = next((dict(z) for z in repository.job_zones(con)
                          if z["zone"] == zone), None)
    return {
        "total": total,
        "returned": len(rows),
        "job_zone": zone_info,
        "occupations": [dict(r) for r in rows],
        "message": None if rows else "No occupations match that search.",
    }


@app.get("/occupations/{soc_code}", tags=["catalogue"])
def get_occupation(soc_code: str):
    """FR-09: provenance travels with the record."""
    occ = _require_occupation(soc_code)
    skills = repository.required_skills(con, soc_code)
    return {
        **dict(occ),
        "required_skills": [
            {"element_id": s["element_id"], "name": s["name"],
             "importance": round(s["importance"], 2),
             "importance_scale_max": s["importance_scale_max"],
             "classification": ("essential" if s["importance"] >= ESSENTIAL_THRESHOLD
                                else "desirable"),
             "source_date": s["source_date"]}
            for s in skills
        ],
    }


@app.get("/skills", tags=["catalogue"])
def list_skills():
    """FR-02: all 35, for the capture screen."""
    rows = repository.list_skills(con)
    return {"total": len(rows), "skills": [dict(r) for r in rows]}


# ---------- profiles ----------

@app.post("/profiles", status_code=201, tags=["profile"])
def create_profile(body: ProfileIn):
    """FR-01 create profile, FR-02 capture skills, FR-03 record target."""
    valid = repository.valid_skill_ids(con)
    unknown = [s for s in body.skills if s not in valid]
    if unknown:
        raise HTTPException(422, f"Unknown skill identifiers: {unknown}")
    if body.target_soc_code:
        _require_occupation(body.target_soc_code)

    profile_id = repository.create_profile(
        con, body.profile_type, body.skills, body.target_soc_code)
    return {
        "profile_id": profile_id,
        "profile_type": body.profile_type,
        "skills_captured": len(set(body.skills)),
        "target_soc_code": body.target_soc_code,
    }


@app.get("/profiles/{profile_id}/gap", tags=["profile"])
def get_gap(profile_id: str, soc_code: str | None = None):
    """FR-07: missing skills, classified, ordered by importance."""
    profile = _require_profile(profile_id)
    target = _resolve_target(profile, soc_code)
    _require_occupation(target)
    return gap_analyser.compute_gap(con, profile_id, target)


@app.get("/profiles/{profile_id}/pathway", tags=["profile"])
def get_pathway(profile_id: str, soc_code: str | None = None):
    """FR-08: ordered steps, each naming the skills to acquire."""
    profile = _require_profile(profile_id)
    target = _resolve_target(profile, soc_code)
    _require_occupation(target)
    return pathway_service.generate_pathway(con, profile_id, target)


# ---------- recommendation ----------

@app.get("/recommendations", tags=["recommendation"])
def get_recommendations(
    profile_id: str,
    limit: int = Query(5, ge=1, le=20),
    max_job_zone: int | None = Query(None, ge=1, le=5),
):
    """FR-06 and TR-01 to TR-03: the emerging-technology component.

    An empty profile returns an empty list with an explanation rather than an
    arbitrary ranking -- see TR-03. With nothing to compare against, any
    ordering would be noise presented as a recommendation.
    """
    _require_profile(profile_id)
    held = repository.profile_skill_ids(con, profile_id)
    results = recommendation_engine.recommend(con, held, limit, max_job_zone)
    return {
        "profile_id": profile_id,
        "method": "mean-centred cosine similarity over 35-dimensional "
                  "O*NET skill-importance vectors",
        "max_job_zone": max_job_zone,
        "recommendations": [
            {"soc_code": soc, "title": title, "score": round(score, 3)}
            for soc, title, score in results
        ],
        "message": None if results else
                   "Select at least one skill to receive recommendations.",
    }
