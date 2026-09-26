"""SAYCEP API -- the seven endpoints specified in the proposal, plus one.

Run from the repo root:
    python -m uvicorn app:app --app-dir backend --port 8000
Then open http://127.0.0.1:8000 for the app, /docs for the API.

The eighth endpoint, PUT /profiles/{id}/target, exists because FR-03 requires
the system to record a target and replace any previous one, and none of the
seven specified endpoints can do that without a GET that writes.

Named to match the component in the sequence diagram. Routes only: the gap,
pathway and recommendation logic live in their own modules so the ML component
can be lifted into its own service later without touching the request layer.
"""

import sys
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
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

FRONTEND = Path(__file__).resolve().parent.parent / "frontend"

# NFR-03: refuse to serve rather than serve partial data.
_boot = repository.connect()
if not repository.reference_data_present(_boot):
    sys.exit("saycep.db is missing or empty. Run: python backend/load_onet.py")
repository.ensure_profile_tables(_boot)
_boot.close()


def db():
    """One connection per request.

    FastAPI runs these endpoints on a thread pool. A single shared SQLite
    connection survives a scripted test that asks one thing at a time and
    fails when a browser asks two things at once -- which the explore screen
    does. SQLite connections are cheap; open one per request.
    """
    con = repository.connect()
    try:
        yield con
    finally:
        con.close()


class ProfileIn(BaseModel):
    profile_type: str = Field(..., pattern="^(student|school_leaver)$")
    skills: list[str] = Field(default_factory=list)
    target_soc_code: str | None = None


class TargetIn(BaseModel):
    soc_code: str


def _resolve_target(profile, soc_code):
    target = soc_code or profile["target_soc_code"]
    if not target:
        raise HTTPException(400, "No target occupation. Pass soc_code, or set "
                                 "target_soc_code when creating the profile.")
    return target


def _require_profile(con, profile_id):
    profile = repository.get_profile(con, profile_id)
    if profile is None:
        raise HTTPException(404, f"No profile {profile_id}")
    return profile


def _require_occupation(con, soc_code):
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
    con=Depends(db),
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
def get_occupation(soc_code: str, con=Depends(db)):
    """FR-09: provenance travels with the record."""
    occ = _require_occupation(con, soc_code)
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
def list_skills(con=Depends(db)):
    """FR-02: all 35, for the capture screen."""
    rows = repository.list_skills(con)
    return {"total": len(rows), "skills": [dict(r) for r in rows]}


# ---------- profiles ----------

@app.post("/profiles", status_code=201, tags=["profile"])
def create_profile(body: ProfileIn, con=Depends(db)):
    """FR-01 create profile, FR-02 capture skills, FR-03 record target."""
    valid = repository.valid_skill_ids(con)
    unknown = [s for s in body.skills if s not in valid]
    if unknown:
        raise HTTPException(422, f"Unknown skill identifiers: {unknown}")
    if body.target_soc_code:
        _require_occupation(con, body.target_soc_code)

    profile_id = repository.create_profile(
        con, body.profile_type, body.skills, body.target_soc_code)
    return {
        "profile_id": profile_id,
        "profile_type": body.profile_type,
        "skills_captured": len(set(body.skills)),
        "target_soc_code": body.target_soc_code,
    }


@app.put("/profiles/{profile_id}/target", tags=["profile"])
def set_target(profile_id: str, body: TargetIn, con=Depends(db)):
    """FR-03: record the target, replacing any previously set."""
    _require_profile(con, profile_id)
    _require_occupation(con, body.soc_code)
    repository.set_target(con, profile_id, body.soc_code)
    return {"profile_id": profile_id, "target_soc_code": body.soc_code}


@app.get("/profiles/{profile_id}/gap", tags=["profile"])
def get_gap(profile_id: str, soc_code: str | None = None, con=Depends(db)):
    """FR-07: missing skills, classified, ordered by importance."""
    profile = _require_profile(con, profile_id)
    target = _resolve_target(profile, soc_code)
    _require_occupation(con, target)
    return gap_analyser.compute_gap(con, profile_id, target)


@app.get("/profiles/{profile_id}/pathway", tags=["profile"])
def get_pathway(profile_id: str, soc_code: str | None = None, con=Depends(db)):
    """FR-08: ordered steps, each naming the skills to acquire."""
    profile = _require_profile(con, profile_id)
    target = _resolve_target(profile, soc_code)
    _require_occupation(con, target)
    return pathway_service.generate_pathway(con, profile_id, target)


# ---------- recommendation ----------

@app.get("/recommendations", tags=["recommendation"])
def get_recommendations(
    profile_id: str,
    limit: int = Query(5, ge=1, le=20),
    max_job_zone: int | None = Query(None, ge=1, le=5),
    con=Depends(db),
):
    """FR-06 and TR-01 to TR-03: the emerging-technology component.

    An empty profile returns an empty list with an explanation rather than an
    arbitrary ranking -- see TR-03. With nothing to compare against, any
    ordering would be noise presented as a recommendation.
    """
    _require_profile(con, profile_id)
    held = repository.profile_skill_ids(con, profile_id)
    results = recommendation_engine.recommend(con, held, limit, max_job_zone)
    zones = repository.occupation_zones(con)
    return {
        "profile_id": profile_id,
        "method": "mean-centred cosine similarity over 35-dimensional "
                  "O*NET skill-importance vectors",
        "max_job_zone": max_job_zone,
        "recommendations": [
            {"soc_code": soc, "title": title, "score": round(score, 3),
             "job_zone": zones.get(soc)}
            for soc, title, score in results
        ],
        "message": None if results else
                   "Select at least one skill to receive recommendations.",
    }


# ---------- the app ----------

if FRONTEND.is_dir():
    app.mount("/static", StaticFiles(directory=FRONTEND), name="static")

    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(FRONTEND / "index.html")
