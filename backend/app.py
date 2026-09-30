"""SAYCEP API -- the seven endpoints specified in the proposal, plus four.

Run from the repo root:
    python -m uvicorn app:app --app-dir backend --port 8000
Then open http://127.0.0.1:8000 for the app, /docs for the API.

The eighth endpoint, PUT /profiles/{id}/target, exists because FR-03 requires
the system to record a target and replace any previous one, and none of the
seven specified endpoints can do that without a GET that writes.

The other three serve the "My plan" dashboard (docs/plans/ux-and-dashboard.md):
GET /profiles/{id} rebuilds it after a reload, and PUT/DELETE on
/profiles/{id}/skills/{element_id} record progress (ADR-0005).

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
import plain
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


class SkillStatusIn(BaseModel):
    status: str = Field(..., pattern="^(held|learning)$")


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


# Plain-language labels ride alongside the figures, never instead of them: the
# screen leads with the words and presenter mode still shows the numbers.

def _with_preparation(occ):
    return {**occ, "preparation": plain.preparation(occ["job_zone"])}


def _with_level(skill):
    return {**skill, "level": plain.importance_level(skill["importance"])}


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
        if zone_info:
            zone_info["preparation"] = plain.preparation(zone)
    return {
        "total": total,
        "returned": len(rows),
        "job_zone": zone_info,
        "occupations": [_with_preparation(dict(r)) for r in rows],
        "message": None if rows else "No occupations match that search.",
    }


@app.get("/occupations/{soc_code}", tags=["catalogue"])
def get_occupation(soc_code: str, profile_id: str | None = None, con=Depends(db)):
    """FR-09: provenance travels with the record.

    With a profile_id, each required skill says whether that profile holds it,
    so the role sheet can show "you have 4 of 7 must-haves" before the user
    commits to a target. Without one it is a plain catalogue read.
    """
    occ = _require_occupation(con, soc_code)
    held = (set(repository.profile_skill_ids(con, _require_profile(con, profile_id)["profile_id"]))
            if profile_id else None)
    skills = [
        {"element_id": s["element_id"], "name": s["name"],
         "description": s["description"],
         "level": plain.importance_level(s["importance"]),
         "importance": round(s["importance"], 2),
         "importance_scale_max": s["importance_scale_max"],
         "classification": ("essential" if s["importance"] >= ESSENTIAL_THRESHOLD
                            else "desirable"),
         "source_date": s["source_date"],
         "held": None if held is None else s["element_id"] in held}
        for s in repository.required_skills(con, soc_code)
    ]
    essential = [s for s in skills if s["classification"] == "essential"]
    return {
        **_with_preparation(dict(occ)),
        "required_skills": skills,
        "essential_count": len(essential),
        "essential_held": None if held is None else sum(s["held"] for s in essential),
        "held_count": None if held is None else sum(s["held"] for s in skills),
    }


@app.get("/skills", tags=["catalogue"])
def list_skills(con=Depends(db)):
    """FR-02: all 35, for the capture screen."""
    rows = repository.list_skills(con)
    return {
        "total": len(rows),
        "groups": list(dict.fromkeys(name for _, name in plain.SKILL_GROUPS)),
        "skills": [{**dict(r), "group": plain.skill_group(r["element_id"])} for r in rows],
    }


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


@app.get("/profiles/{profile_id}", tags=["profile"])
def get_profile(profile_id: str, con=Depends(db)):
    """The dashboard's read: who the user is, what they hold, how close they are.

    Readiness is counted, not scored: "4 of 7 must-haves", never a weighted
    percentage the user would have to take on trust. For an occupation with no
    essential skills it counts the five most important instead (ready_basis).
    """
    profile = _require_profile(con, profile_id)
    skills = [dict(r) for r in repository.profile_skills(con, profile_id)]
    target, readiness = None, None
    if profile["target_soc_code"]:
        soc = profile["target_soc_code"]
        target = _with_preparation(dict(_require_occupation(con, soc)))
        held = set(repository.profile_skill_ids(con, profile_id))
        step = pathway_service.step_readiness(con, soc, held)
        gap = gap_analyser.compute_gap(con, profile_id, soc)
        readiness = {
            "basis": step["ready_basis"],
            "have": step["ready_total"] - len(step["ready_missing"]),
            "total": step["ready_total"],
            "missing": step["ready_missing"],
            "ready": step["ready"],
            "overall_have": gap["already_held_count"],
            "overall_total": gap["required_total"],
        }
    return {
        "profile_id": profile_id,
        "profile_type": profile["profile_type"],
        "created_at": profile["created_at"],
        "target": target,
        "skills": skills,
        "held_count": sum(s["status"] == "held" for s in skills),
        "learning_count": sum(s["status"] == "learning" for s in skills),
        "readiness": readiness,
    }


@app.put("/profiles/{profile_id}/skills/{element_id}", tags=["profile"])
def set_skill_status(profile_id: str, element_id: str, body: SkillStatusIn, con=Depends(db)):
    """Progress: mark a skill 'learning' (working on it) or 'held' (can do it now).

    Only 'held' changes the gap, the pathway and the recommendations.
    """
    _require_profile(con, profile_id)
    if element_id not in repository.valid_skill_ids(con):
        raise HTTPException(404, f"No skill {element_id}")
    repository.set_skill_status(con, profile_id, element_id, body.status)
    return {"profile_id": profile_id, "element_id": element_id, "status": body.status}


@app.delete("/profiles/{profile_id}/skills/{element_id}", tags=["profile"])
def remove_skill(profile_id: str, element_id: str, con=Depends(db)):
    """Undo: the skill goes back to neither held nor being learned."""
    _require_profile(con, profile_id)
    repository.remove_skill(con, profile_id, element_id)
    return {"profile_id": profile_id, "element_id": element_id, "status": None}


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
    result = gap_analyser.compute_gap(con, profile_id, target)
    result["target"] = _with_preparation(result["target"])
    result["missing"] = [_with_level(m) for m in result["missing"]]
    return result


@app.get("/profiles/{profile_id}/pathway", tags=["profile"])
def get_pathway(profile_id: str, soc_code: str | None = None, con=Depends(db)):
    """FR-08: ordered steps, each naming the skills to acquire."""
    profile = _require_profile(con, profile_id)
    target = _resolve_target(profile, soc_code)
    _require_occupation(con, target)
    result = pathway_service.generate_pathway(con, profile_id, target)
    result["target"] = _with_preparation(result["target"])
    result["steps"] = [{**_with_preparation(st),
                        "focus": [_with_level(f) for f in st["focus"]]}
                       for st in result["steps"]]
    return result


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
             "match": plain.match_level(score), "job_zone": zones.get(soc),
             "preparation": plain.preparation(zones.get(soc))}
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
