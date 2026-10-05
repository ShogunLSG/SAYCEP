"""SAYCEP API -- the seven endpoints specified in the proposal, plus six.

Run from the repo root:
    python -m uvicorn app:app --app-dir backend --port 8000
Then open http://127.0.0.1:8000 for the app, /docs for the API.

The eighth endpoint, PUT /profiles/{id}/target, exists because FR-03 requires
the system to record a target and replace any previous one, and none of the
seven specified endpoints can do that without a GET that writes.

The other three serve the "My plan" dashboard (docs/plans/ux-and-dashboard.md):
GET /profiles/{id} rebuilds it after a reload, and PUT/DELETE on
/profiles/{id}/skills/{element_id} record progress (ADR-0005).
POST /plans/resume and PUT /profiles/{id}/name are the welcome screen's
sign-in by plan code (ADR-0008).

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
import cvscan
import gap as gap_analyser
import interview as interview_practice
import interests as interest_matcher
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
    # Optional, and the only personal detail SAYCEP ever holds (ADR-0008).
    display_name: str | None = Field(None, max_length=40)


class CvIn(BaseModel):
    # Never stored or logged (ADR-0014). The cap keeps one request cheap.
    text: str = Field(..., min_length=20, max_length=15000)
    soc_code: str | None = None
    profile_id: str | None = None


class AnswerIn(BaseModel):
    # Never stored (ADR-0015).
    answer: str = Field(..., max_length=5000)
    skill_element_id: str | None = None


class NameIn(BaseModel):
    display_name: str | None = Field(None, max_length=40)


class PlanCodeIn(BaseModel):
    plan_code: str = Field(..., min_length=6, max_length=12)


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


def _clean_name(name):
    name = (name or "").strip()
    return name or None


def _format_code(code):
    return f"{code[:3]}-{code[3:]}" if code else None


def _dates(values):
    """FR-09: the distinct O*NET collection dates behind what a screen shows,
    oldest first. O*NET writes them MM/YYYY."""
    def key(d):
        m, _, y = d.partition("/")
        return (y, m)
    return sorted({v for v in values if v}, key=key)


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
    saved = soc_code in repository.saved_socs(con, profile_id) if profile_id else None
    tasks, task_total = repository.occupation_tasks(con, soc_code)
    tool_groups, tool_total = repository.occupation_tool_groups(con, soc_code)
    related = [
        {"soc_code": r["related_soc_code"], "title": r["title"], "job_zone": r["job_zone"],
         "preparation": plain.preparation(r["job_zone"])}
        for r in repository.related_occupations(con, soc_code)
    ]
    return {
        **_with_preparation(dict(occ)),
        # "A day in this job" -- ADR-0007.
        "tasks": [dict(t) for t in tasks],
        "task_total": task_total,
        # Job page (ADR-0009): O*NET's expert-reviewed related occupations, in
        # review order; software (hot technologies first); tools by category.
        "related": related,
        # FR-09: the publication dates behind this page's skills and tasks.
        "provenance": {"dataset": occ["source_dataset"],
                       "skill_rating_dates": _dates(s["source_date"] for s in skills),
                       "task_dates": _dates(t["source_date"] for t in tasks)},
        "technology": [dict(t) for t in repository.occupation_technology(con, soc_code)],
        "tool_groups": tool_groups,
        "tool_total": tool_total,
        "required_skills": skills,
        "saved": saved,
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
        con, body.profile_type, body.skills, body.target_soc_code, _clean_name(body.display_name))
    _log(con, profile_id, "started", skill_count=len(set(body.skills)),
         soc_code=body.target_soc_code)
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
        "display_name": profile["display_name"],
        "plan_code": _format_code(profile["plan_code"]),
        "target": target,
        "skills": skills,
        "held_count": sum(s["status"] == "held" for s in skills),
        "learning_count": sum(s["status"] == "learning" for s in skills),
        "readiness": readiness,
    }


@app.post("/plans/resume", tags=["profile"])
def resume_plan(body: PlanCodeIn, con=Depends(db)):
    """Sign in with a plan code (ADR-0008): reopen a saved plan on any device.

    The code is not a password -- anyone holding it can open the plan -- which
    is acceptable only because a plan holds nothing personal beyond an
    optional first name. The error does not say whether a code is close.
    """
    profile = repository.profile_by_plan_code(con, body.plan_code)
    if profile is None:
        raise HTTPException(404, "No plan matches that code. Check it and try again.")
    return {"profile_id": profile["profile_id"], "display_name": profile["display_name"],
            "has_target": profile["target_soc_code"] is not None}


@app.put("/profiles/{profile_id}/name", tags=["profile"])
def set_name(profile_id: str, body: NameIn, con=Depends(db)):
    """Change or clear the optional first name."""
    _require_profile(con, profile_id)
    repository.set_display_name(con, profile_id, _clean_name(body.display_name))
    return {"profile_id": profile_id, "display_name": _clean_name(body.display_name)}


def _goal_snapshot(con, profile_id):
    """(have, total) for the profile's goal right now, or (None, None)."""
    soc = repository.get_profile(con, profile_id)["target_soc_code"]
    if not soc:
        return None, None
    r = pathway_service.step_readiness(con, soc, set(repository.profile_skill_ids(con, profile_id)))
    return r["ready_total"] - len(r["ready_missing"]), r["ready_total"]


def _log(con, profile_id, kind, **kw):
    have, total = _goal_snapshot(con, profile_id)
    repository.log_event(con, profile_id, kind, goal_have=have, goal_total=total, **kw)


def _changes(con, profile, before, after):
    """What a skill change did, computed rather than claimed (slice 2's
    "unlock" moment): the goal's readiness before and after, which of the
    goal's related jobs (the pool the route is drawn from) became ready, and
    how many jobs in the whole catalogue the user is now ready for."""
    if before == after:
        return None
    out = {"goal": None, "newly_ready_steps": [], "ready_jobs_before": 0, "ready_jobs_after": 0}
    soc = profile["target_soc_code"]
    if soc:
        b = pathway_service.step_readiness(con, soc, before)
        a = pathway_service.step_readiness(con, soc, after)
        out["goal"] = {"title": repository.get_occupation(con, soc)["title"], "basis": a["ready_basis"],
                       "before": b["ready_total"] - len(b["ready_missing"]),
                       "after": a["ready_total"] - len(a["ready_missing"]),
                       "total": a["ready_total"], "ready": a["ready"]}
        steps = [r["related_soc_code"] for r in repository.related_occupations(con, soc)]
        for step_soc in steps:
            if (not pathway_service.step_readiness(con, step_soc, before)["ready"]
                    and pathway_service.step_readiness(con, step_soc, after)["ready"]):
                out["newly_ready_steps"].append(
                    {"soc_code": step_soc, "title": repository.get_occupation(con, step_soc)["title"]})
    ready_b, ready_a = pathway_service.ready_jobs(con, before), pathway_service.ready_jobs(con, after)
    out["ready_jobs_before"], out["ready_jobs_after"] = len(ready_b), len(ready_a)
    return out


@app.put("/profiles/{profile_id}/skills/{element_id}", tags=["profile"])
def set_skill_status(profile_id: str, element_id: str, body: SkillStatusIn, con=Depends(db)):
    """Progress: mark a skill 'learning' (working on it) or 'held' (can do it now).

    Only 'held' changes the gap, the pathway and the recommendations. The
    response says what the change did (`changes`), for the unlock moment.
    """
    profile = _require_profile(con, profile_id)
    if element_id not in repository.valid_skill_ids(con):
        raise HTTPException(404, f"No skill {element_id}")
    before = set(repository.profile_skill_ids(con, profile_id))
    repository.set_skill_status(con, profile_id, element_id, body.status)
    after = set(repository.profile_skill_ids(con, profile_id))
    _log(con, profile_id, "skill", element_id=element_id, status=body.status)
    return {"profile_id": profile_id, "element_id": element_id, "status": body.status,
            "changes": _changes(con, profile, before, after)}


@app.delete("/profiles/{profile_id}/skills/{element_id}", tags=["profile"])
def remove_skill(profile_id: str, element_id: str, con=Depends(db)):
    """Undo: the skill goes back to neither held nor being learned."""
    profile = _require_profile(con, profile_id)
    before = set(repository.profile_skill_ids(con, profile_id))
    repository.remove_skill(con, profile_id, element_id)
    after = set(repository.profile_skill_ids(con, profile_id))
    _log(con, profile_id, "skill", element_id=element_id, status=None)
    return {"profile_id": profile_id, "element_id": element_id, "status": None,
            "changes": _changes(con, profile, before, after)}


# ---------- saved jobs and comparison (slice 3, ADR-0010) ----------

def _job_summary(con, soc, held):
    """One job, measured against the user: the shape both the saved list and
    the comparison use."""
    occ = repository.get_occupation(con, soc)
    required = repository.required_skills(con, soc)
    ready = pathway_service.step_readiness(con, soc, held)
    return {
        "soc_code": soc, "title": occ["title"], "job_zone": occ["job_zone"],
        "preparation": plain.preparation(occ["job_zone"]),
        "readiness": {"basis": ready["ready_basis"], "total": ready["ready_total"],
                      "have": ready["ready_total"] - len(ready["ready_missing"]),
                      "ready": ready["ready"]},
        "overall_have": sum(r["element_id"] in held for r in required),
        "overall_total": len(required),
        # What stands between the user and "ready", by the same rule as the
        # count above -- so a job with no essential skills never reads as
        # "4 of 5" and "nothing left to learn" at once.
        "to_learn": [{"element_id": m["element_id"], "name": m["name"]} for m in ready["ready_missing"]],
        "rating_dates": _dates(r["source_date"] for r in required),
        "must_haves": [{"element_id": r["element_id"], "name": r["name"],
                        "held": r["element_id"] in held}
                       for r in required if r["importance"] >= ESSENTIAL_THRESHOLD],
    }


@app.get("/profiles/{profile_id}/saved", tags=["profile"])
def list_saved(profile_id: str, con=Depends(db)):
    """Saved jobs, oldest first, each with the user's readiness for it."""
    _require_profile(con, profile_id)
    held = set(repository.profile_skill_ids(con, profile_id))
    return {"profile_id": profile_id,
            "saved": [_job_summary(con, soc, held) for soc in repository.saved_socs(con, profile_id)]}


@app.put("/profiles/{profile_id}/saved/{soc_code}", tags=["profile"])
def save_job(profile_id: str, soc_code: str, con=Depends(db)):
    _require_profile(con, profile_id)
    _require_occupation(con, soc_code)
    repository.save_occupation(con, profile_id, soc_code)
    return {"profile_id": profile_id, "soc_code": soc_code, "saved": True}


@app.delete("/profiles/{profile_id}/saved/{soc_code}", tags=["profile"])
def unsave_job(profile_id: str, soc_code: str, con=Depends(db)):
    _require_profile(con, profile_id)
    repository.unsave_occupation(con, profile_id, soc_code)
    return {"profile_id": profile_id, "soc_code": soc_code, "saved": False}


@app.get("/profiles/{profile_id}/compare", tags=["profile"])
def compare_jobs(profile_id: str, soc: list[str] = Query(..., min_length=2, max_length=3),
                 con=Depends(db)):
    """Two or three jobs side by side, measured against the user: training,
    must-haves held, and which must-have skills they share."""
    _require_profile(con, profile_id)
    for code in soc:
        _require_occupation(con, code)
    held = set(repository.profile_skill_ids(con, profile_id))
    jobs = [_job_summary(con, code, held) for code in dict.fromkeys(soc)]
    sets = [{m["element_id"] for m in j["must_haves"]} for j in jobs]
    shared = set.intersection(*sets) if sets else set()
    names = {m["element_id"]: m["name"] for j in jobs for m in j["must_haves"]}
    return {"profile_id": profile_id, "jobs": jobs, "dataset": repository.get_occupation(con, soc[0])["source_dataset"],
            "shared_must_haves": sorted(({"element_id": e, "name": names[e], "held": e in held}
                                         for e in shared), key=lambda m: m["name"])}


# ---------- CV scanner (module 3, ADR-0014) ----------

_cv_index = {"mtime": None, "index": None}

# Filled in from backend/tests/benchmark_cv.py's latest run (ADR-0014).
BENCHMARK_NOTE = ("Measured on 172 held-out CVs: the goal score tracks human match scores "
                  "better than naive word overlap. See ADR-0014.")


def _cv(con):
    """The scanner's index, rebuilt only when the database file changes."""
    from config import DB_PATH
    mtime = DB_PATH.stat().st_mtime
    if _cv_index["mtime"] != mtime:
        _cv_index.update(index=cvscan.Index(con), mtime=mtime)
    return _cv_index["index"]


@app.post("/cv/scan", tags=["cv"])
def scan_cv(body: CvIn, con=Depends(db)):
    """Read a pasted CV: suggest skills it shows evidence of, and check it
    against a goal occupation. **The text is processed and discarded -- never
    stored.** Suggestions are suggestions: the user confirms each one through
    the ordinary skill endpoints (FR-02's self-report rule)."""
    index = _cv(con)
    held = {}
    soc = body.soc_code
    if body.profile_id:
        profile = _require_profile(con, body.profile_id)
        held = {r["element_id"]: r["status"] for r in repository.profile_skills(con, body.profile_id)}
        soc = soc or profile["target_soc_code"]
    if soc:
        _require_occupation(con, soc)

    evidence = cvscan.skill_evidence(index, body.text)
    software = cvscan.named(index.software, body.text, common=index.common)
    tools = cvscan.named(index.tools, body.text)
    out = {
        "suggestions": [{**sg, "status": held.get(sg["element_id"])} for sg in cvscan.suggestions(index, evidence)],
        "software_named": sorted(software), "tools_named": sorted(tools),
        "checks": cvscan.checks(body.text),
        "goal": None,
        "stored": False,
    }
    if soc:
        occ = repository.get_occupation(con, soc)
        sc = cvscan.goal_score(index, evidence, software, tools, soc)
        req = {r["element_id"]: r for r in repository.required_skills(con, soc)}
        essential = [e for e in sc["top_skills"] if req[e]["importance"] >= ESSENTIAL_THRESHOLD] or sc["top_skills"][:5]
        mention = [t["example"] for t in repository.occupation_technology(con, soc, limit=12)
                   if t["example"] not in software][:6]
        out["goal"] = {
            "soc_code": soc, "title": occ["title"],
            "score": sc["value"], "overlap": sc["overlap"], "coverage": sc["coverage"],
            "named_for_this_job": sc["named"],
            "key_skills": [{"element_id": e, "name": index.skills[e][0],
                            "evidence": evidence[e][0] if e in evidence else None,
                            "held": held.get(e) == "held"} for e in essential],
            "worth_mentioning": mention,
            "basis": BENCHMARK_NOTE,
        }
    return out


# ---------- interview practice (module 5, ADR-0015) ----------

@app.get("/interview/questions", tags=["interview"])
def interview_questions(soc_code: str | None = None, profile_id: str | None = None, con=Depends(db)):
    """Practice questions for a job: an opener, one per key skill, one from
    its most important O*NET task. With a profile and no soc_code, its goal."""
    if not soc_code and profile_id:
        soc_code = _require_profile(con, profile_id)["target_soc_code"]
    if not soc_code:
        raise HTTPException(400, "Pass soc_code, or a profile_id with a goal.")
    occ = _require_occupation(con, soc_code)
    return {"soc_code": soc_code, "title": occ["title"],
            "questions": interview_practice.questions(con, soc_code, _cv(con)),
            "note": "Practice with guidance, not a scored test. Your answers are not saved."}


@app.post("/interview/feedback", tags=["interview"])
def interview_feedback(body: AnswerIn, con=Depends(db)):
    """A checklist for one answer: the skill shown, situation -> action ->
    result, your own part, a specific detail, length. Never stored."""
    index = _cv(con)
    if body.skill_element_id and body.skill_element_id not in index.skills:
        raise HTTPException(404, f"No skill {body.skill_element_id}")
    return {**interview_practice.feedback(index, body.answer, body.skill_element_id), "stored": False}


# ---------- interests (slice 4, ADR-0011) ----------

@app.get("/interests/quiz", tags=["interests"])
def interest_quiz():
    """The twelve statements, in order. Our wording, a simplified version of
    O*NET's 60-item Interest Profiler -- the note says so on screen."""
    return {
        "questions": [{"id": i, "area": a, "text": t} for i, (a, t) in enumerate(interest_matcher.QUESTIONS)],
        "areas": interest_matcher.AREA_NAMES,
        "answers": [{"value": 0, "label": "Not for me"}, {"value": 1, "label": "Maybe"},
                    {"value": 2, "label": "I'd enjoy it"}],
        "note": "A short, simplified version of O*NET's Interest Profiler. "
                "Your answers are compared with O*NET's interest profile for every job.",
    }


@app.get("/interests/match", tags=["interests"])
def interest_match(
    r: int = Query(0, ge=0, le=4), i: int = Query(0, ge=0, le=4), a: int = Query(0, ge=0, le=4),
    s: int = Query(0, ge=0, le=4), e: int = Query(0, ge=0, le=4), c: int = Query(0, ge=0, le=4),
    max_job_zone: int | None = Query(None, ge=1, le=5),
    profile_id: str | None = None, limit: int = Query(10, ge=1, le=30), con=Depends(db),
):
    """Jobs whose O*NET interest profile has the same shape as the answers.
    Area scores are the sum of the two answers for that area (0-4). With a
    profile, each result also says how well the user's skills match it."""
    scores = {"R": r, "I": i, "A": a, "S": s, "E": e, "C": c}
    ranked = interest_matcher.match(repository.interest_profiles(con, max_job_zone), scores, limit)
    if ranked is None:
        return {"your_areas": [], "results": [], "message":
                "Your answers don't lean towards anything yet. Pick “I'd enjoy it” for a few."}
    skill_score = None
    if profile_id:
        _require_profile(con, profile_id)
        held = repository.profile_skill_ids(con, profile_id)
        if held:
            ids, vectors = recommendation_engine.load_vectors(con)
            means = recommendation_engine.skill_means(vectors, len(ids))
            centred = recommendation_engine.centre_occupations(vectors, means)
            pv = recommendation_engine.centre_profile(ids, held, means)
            skill_score = lambda soc: recommendation_engine.cosine(pv, centred[soc])
    return {
        "your_areas": [{"area": x, "name": interest_matcher.AREA_NAMES[x]}
                       for x in interest_matcher.top_areas(scores) if scores[x] > 0],
        "results": [
            {"soc_code": soc, "title": job["title"], "job_zone": job["job_zone"],
             "preparation": plain.preparation(job["job_zone"]),
             "fit": plain.interest_fit(corr), "correlation": round(corr, 3),
             "areas": [interest_matcher.AREA_NAMES[x] for x in interest_matcher.top_areas(job["scores"])],
             "skill_match": plain.match_level(skill_score(soc)) if skill_score else None,
             "source_date": job["source_date"]}
            for soc, job, corr in ranked
        ],
        "dataset": repository.get_occupation(con, ranked[0][0])["source_dataset"] if ranked else None,
        "message": None,
    }


@app.get("/profiles/{profile_id}/history", tags=["profile"])
def get_history(profile_id: str, con=Depends(db)):
    """Progress history (slice 5, ADR-0012): newest first, each event with the
    goal's readiness as it stood at that moment."""
    _require_profile(con, profile_id)
    return {"profile_id": profile_id, "events": [dict(e) for e in repository.events(con, profile_id)]}


@app.get("/skills/{element_id}", tags=["catalogue"])
def get_skill(element_id: str, profile_id: str | None = None, con=Depends(db)):
    """A skill page: what it is, where it matters most, and -- with a profile --
    where the user stands on it."""
    skill = repository.get_skill(con, element_id)
    if skill is None:
        raise HTTPException(404, f"No skill {element_id}")
    top = repository.jobs_for_skill(con, element_id)
    status = None
    if profile_id:
        _require_profile(con, profile_id)
        status = next((r["status"] for r in repository.profile_skills(con, profile_id)
                       if r["element_id"] == element_id), None)
    return {
        **dict(skill),
        "group": plain.skill_group(element_id),
        "status": status,
        "must_have_in": repository.count_jobs_needing(con, element_id, ESSENTIAL_THRESHOLD),
        "top_jobs": [
            {"soc_code": r["soc_code"], "title": r["title"], "job_zone": r["job_zone"],
             "importance": round(r["importance"], 2), "level": plain.importance_level(r["importance"]),
             "preparation": plain.preparation(r["job_zone"]), "source_date": r["source_date"]}
            for r in top
        ],
        "rating_dates": _dates(r["source_date"] for r in top),
    }


@app.put("/profiles/{profile_id}/target", tags=["profile"])
def set_target(profile_id: str, body: TargetIn, con=Depends(db)):
    """FR-03: record the target, replacing any previously set."""
    _require_profile(con, profile_id)
    _require_occupation(con, body.soc_code)
    previous = repository.get_profile(con, profile_id)["target_soc_code"]
    repository.set_target(con, profile_id, body.soc_code)
    if previous != body.soc_code:
        _log(con, profile_id, "goal", soc_code=body.soc_code)
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
                        "focus": [_with_level(f) for f in st["focus"]],
                        "closeness_label": (plain.match_level(st["closeness"])
                                            if st["closeness"] is not None else None)}
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
    why = {}
    if results:
        ids, vectors = recommendation_engine.load_vectors(con)
        means = recommendation_engine.skill_means(vectors, len(ids))
        centred = recommendation_engine.centre_occupations(vectors, means)
        pv = recommendation_engine.centre_profile(ids, held, means)
        names = {r["element_id"]: r["name"] for r in repository.list_skills(con)}
        why = {soc: [names[e] for e in recommendation_engine.reasons(ids, centred[soc], pv, held)]
               for soc, _, _ in results}
    return {
        "profile_id": profile_id,
        "method": "mean-centred cosine similarity over 35-dimensional "
                  "O*NET skill-importance vectors",
        "max_job_zone": max_job_zone,
        "recommendations": [
            {"soc_code": soc, "title": title, "score": round(score, 3),
             "match": plain.match_level(score), "job_zone": zones.get(soc),
             # FR-06: the held skills that lifted this job most (recommend.reasons).
             "because": why.get(soc, []),
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
