"""Pathway Service -- FR-08.

Builds an ordered route from where a user is now to their target occupation,
with no fewer than three intermediate steps, each naming the skills to work on.

How the ordering is decided, because this is the question FR-08 invites:

  1. Candidates are the target's *primary* related occupations. That list is
     ordered by O*NET's own expert review, so the neighbourhood is not our
     invention -- only the sequencing within it is.
  2. Candidates are sequenced by similarity to the user's current skill profile,
     most similar first, so the most achievable step comes first and the route
     moves progressively toward the target.

How the skills at each step are chosen, which is the harder question:

  Measured on the loaded catalogue, consecutive steps on a real pathway have
  cosine similarity of 0.987 to 0.996 -- related occupations require very nearly
  the *same* skills. So "which new skills does this step need" is the wrong
  question: the honest answer is almost none, and steps named nothing.

  What actually separates them is *how much* of each skill is required. Moving
  from Boilermaker to Electrician does not add Troubleshooting; it raises the
  importance of Troubleshooting from 3.25 to 4.00.

  So a step does not report "new skills" -- it reports the skills that matter
  most *in that role*, ranked by O*NET importance, each badged with how it
  relates to where the user is:

    new    -- the user does not hold this skill at all
    deeper -- the role demands more of it than the previous step did,
              with O*NET's before and after figures
    (none) -- already held and already at this level

  A single ranked list rather than two filtered ones, because splitting by
  "new" and "rising" leaves steps naming nothing whenever a user already holds
  what an occupation needs -- which happens often, given how alike related
  occupations are. Ranked by importance, a step always has something to say.
"""

from config import ESSENTIAL_THRESHOLD, PATHWAY_INTERMEDIATE_STEPS
import recommend
import repository

# A rise smaller than this is noise on a 1-5 survey scale, not a development goal.
MIN_MEANINGFUL_RISE = 0.25

# 166 of the 879 occupations have no skill at or above the essential threshold.
# For those, "ready" means holding this many of the role's most important skills.
READY_FALLBACK_TOP_N = 5


def generate_pathway(con, profile_id, soc_code):
    held = set(repository.profile_skill_ids(con, profile_id))
    target = repository.get_occupation(con, soc_code)

    candidates = [r for r in repository.related_occupations(con, soc_code)
                  if r["related_soc_code"] != soc_code]
    ordered, closeness = _rank_by_closeness(con, held, candidates + [{"related_soc_code": soc_code}])
    ordered = [r for r in ordered if r["related_soc_code"] != soc_code]
    route = [r["related_soc_code"] for r in ordered[:PATHWAY_INTERMEDIATE_STEPS]]

    steps, acquired, previous = [], set(held), None
    for position, step_soc in enumerate(route + [soc_code], start=1):
        is_target = step_soc == soc_code
        row = target if is_target else next(
            r for r in ordered if r["related_soc_code"] == step_soc)

        focus = _step_focus(con, step_soc, held, previous)
        readiness = step_readiness(con, step_soc, held)
        required = repository.required_skills(con, step_soc)

        steps.append({
            "step": position,
            "soc_code": step_soc,
            "title": row["title"],
            "job_zone": row["job_zone"],
            "relatedness_tier": None if is_target else row["tier"],
            "expert_review_index": None if is_target else row["sort_index"],
            "focus": focus,
            "is_target": is_target,
            # FR-08, why this step: how much of it the user already has, and
            # the same similarity score the steps are ordered by.
            "held_count": sum(r["element_id"] in held for r in required),
            "required_count": len(required),
            "closeness": closeness.get(step_soc),
            **readiness,
        })
        previous = step_soc

    return {
        "profile_id": profile_id,
        "target": dict(target),
        "intermediate_steps": len(steps) - 1,
        "steps": steps,
        "source_dataset": target["source_dataset"],
        "ordering_basis": (
            "Candidates are the target's primary related occupations, ordered by "
            "O*NET expert review; among them, steps are sequenced by similarity "
            "to the user's current skill profile, most achievable first."
        ),
        "skills_basis": (
            "Consecutive occupations on a pathway require very nearly the same "
            "skills (measured cosine 0.987-0.996), so each step lists the skills "
            "that matter most in that role by O*NET importance, badged as new to "
            "the user or as demanding more depth than the previous step."
        ),
    }


def step_readiness(con, soc_code, held_ids):
    """Has the user got what this role depends on? Drives the dashboard's
    "your next step": the first step on the route that is not yet ready.

    Ready means every essential skill is held. For an occupation with no
    essential skills that would be trivially true, so it falls back to the
    role's READY_FALLBACK_TOP_N most important skills instead.
    """
    required = repository.required_skills(con, soc_code)  # most important first
    essential = [r for r in required if r["importance"] >= ESSENTIAL_THRESHOLD]
    basis = essential or required[:READY_FALLBACK_TOP_N]
    missing = [r for r in basis if r["element_id"] not in held_ids]
    return {
        "ready": not missing,
        "ready_basis": "essential" if essential else f"top_{READY_FALLBACK_TOP_N}",
        "ready_total": len(basis),
        "ready_missing": [{"element_id": r["element_id"], "name": r["name"]} for r in missing],
    }


def ready_jobs(con, held_ids):
    """Every job in the catalogue the user is ready for, by the same rule as
    step_readiness -- used to say what a new skill unlocked."""
    basis = repository.readiness_basis_map(con, ESSENTIAL_THRESHOLD, READY_FALLBACK_TOP_N)
    return {soc for soc, needed in basis.items() if needed <= held_ids}


def _importance_map(con, soc_code):
    return {r["element_id"]: (r["name"], r["importance"])
            for r in repository.required_skills(con, soc_code)}


def _step_focus(con, soc_code, held_ids, previous_soc, top_n=6):
    """The skills that matter most in this role, badged against the user."""
    current = _importance_map(con, soc_code)
    prior = _importance_map(con, previous_soc) if previous_soc else {}

    out = []
    for element_id, (name, importance) in current.items():
        before = prior.get(element_id, (name, None))[1]
        rises = before is not None and importance - before >= MIN_MEANINGFUL_RISE
        out.append({
            "element_id": element_id,
            "name": name,
            "importance": round(importance, 2),
            "essential": importance >= ESSENTIAL_THRESHOLD,
            # A skill the user lacks is "new" outright; from/to describes a
            # rising demand between roles and only makes sense for one they hold.
            "badge": "new" if element_id not in held_ids else ("deeper" if rises else None),
            "from": round(before, 2) if rises and element_id in held_ids else None,
            "to": round(importance, 2) if rises and element_id in held_ids else None,
        })

    # Most important first; among equals, surface what the user still lacks.
    out.sort(key=lambda s: (-s["importance"], s["badge"] != "new"))
    return out[:top_n]


def _rank_by_closeness(con, held_ids, candidates):
    """Most similar to the user's current profile first. Returns the ordered
    candidates and {soc: score}, so each step can say how close it is."""
    if not candidates:
        return [], {}
    if not held_ids:
        return list(candidates), {}

    model = recommend.Model.load(con)          # the same model as For you (ADR-0027)
    prof = model.profile(held_ids)

    def score(row):
        soc = row["related_soc_code"]
        return model.score(prof, soc) if soc in model.centred else -1.0

    scores = {row["related_soc_code"]: score(row) for row in candidates}
    return sorted(candidates, key=lambda row: scores[row["related_soc_code"]], reverse=True), scores
