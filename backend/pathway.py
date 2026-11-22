"""Pathway Service -- FR-08.

Builds a route from where a user is now to their target occupation: a short
ladder of jobs at lower preparation levels (Job Zones), then the target, each
step naming the skills to work on.

How the route is decided, because this is the question FR-08 invites (ADR-0034):

  1. The ladder is built backwards from the target. For the step below it, look
     at the jobs O*NET's experts list as related to it (in either direction)
     that sit in a lower Job Zone, nearest zone first. Take the one in the same
     field of work (same SOC major group) if there is one, else the most similar;
     it must clear MIN_LINK_SIMILARITY, the model's job-to-job similarity, so a
     step is never just "a lower job". Then repeat from that step.
  2. At most PATHWAY_MAX_STEPS steps come before the target. If no related lower
     job is similar enough there are none, and the response says the target can
     be aimed for directly (the skills gap is then the plan). A Zone 1 target
     never has a ladder: nothing sits below it.
  3. Other related jobs at the same level as a step are shown beside it as
     alternatives (also_at_level), never as extra steps (ADR-0033).

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

from config import ESSENTIAL_THRESHOLD, PATHWAY_MAX_STEPS, MIN_LINK_SIMILARITY
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
    field = repository.profile_field(con, profile_id)
    model = recommend.Model.load(con)          # the same model as For you (ADR-0027)

    ladder = _ladder(con, model, soc_code, target["job_zone"])
    route = [r["soc_code"] for r in ladder]

    siblings_pool = [r for r in repository.related_occupations(con, soc_code)
                     if r["related_soc_code"] != soc_code]
    pool = set(route) | {r["related_soc_code"] for r in siblings_pool} | {soc_code}
    closeness = _closeness(model, held, field, pool)

    steps, previous = [], None
    branches_shown = set()
    rows = {r["soc_code"]: r for r in ladder}
    for position, step_soc in enumerate(route + [soc_code], start=1):
        is_target = step_soc == soc_code
        row = target if is_target else rows[step_soc]

        focus = _step_focus(con, step_soc, held, previous)
        readiness = step_readiness(con, step_soc, held)
        required = repository.required_skills(con, step_soc)

        # Other related jobs at the same preparation level (ADR-0033): alternatives
        # beside the step, never part of the ordered climb.
        on_route = set(route) | {soc_code, step_soc}
        siblings = [r for r in siblings_pool
                    if r["related_soc_code"] not in on_route
                    and r["related_soc_code"] not in branches_shown
                    and r["job_zone"] == row["job_zone"]]
        siblings.sort(key=lambda r: closeness.get(r["related_soc_code"], -1.0), reverse=True)
        also = [{"soc_code": r["related_soc_code"], "title": r["title"],
                 "job_zone": r["job_zone"]} for r in siblings[:5]]
        branches_shown.update(b["soc_code"] for b in also)

        steps.append({
            "step": position,
            "soc_code": step_soc,
            "title": row["title"],
            "job_zone": row["job_zone"],
            "relatedness_tier": None if is_target else row["tier"],
            "expert_review_index": None if is_target else row["sort_index"],
            "focus": focus,
            "is_target": is_target,
            # FR-08, why this step: how much of it the user already has, scored
            # by the same model as For you.
            "held_count": sum(r["element_id"] in held for r in required),
            "required_count": len(required),
            "closeness": closeness.get(step_soc) if held else None,
            # How like the NEXT job on the route this step is: the link that put
            # it on the ladder.
            "link_similarity": None if is_target else row["link_similarity"],
            "same_field_as_next": None if is_target else row["same_field"],
            "also_at_level": also,
            **readiness,
        })
        previous = step_soc

    direct = len(ladder) == 0
    return {
        "profile_id": profile_id,
        "target": dict(target),
        "intermediate_steps": len(steps) - 1,
        "steps": steps,
        "aim_directly": direct,
        "source_dataset": target["source_dataset"],
        "ordering_basis": (
            "Steps are built backwards from your goal: at each level down, the job "
            "O*NET's experts list as related that is most like the one above it, "
            "preferring the same field of work. A job is only a step if its skills "
            "are similar enough to the next one."
            + (" None was close enough here, so the plan for this goal is its "
               "skills gap." if direct else "")),
        "skills_basis": (
            "Consecutive occupations on a pathway require very nearly the same "
            "skills (measured cosine 0.987-0.996), so each step lists the skills "
            "that matter most in that role by O*NET importance, badged as new to "
            "the user or as demanding more depth than the previous step."
        ),
    }


def _ladder(con, model, soc_code, zone):
    """The steps below the target, lowest first. Each is a dict with soc_code,
    title, job_zone, tier, sort_index, link_similarity, same_field."""
    chain, current, current_zone, used = [], soc_code, zone, {soc_code}
    while len(chain) < PATHWAY_MAX_STEPS and current_zone > 1 and current in model.centred:
        best = None
        for z in range(current_zone - 1, 0, -1):          # nearest lower zone first
            options = []
            for r in repository.lower_zone_links(con, current, z):
                if r["soc_code"] in used or r["soc_code"] not in model.centred:
                    continue
                sim = recommend.cosine(model.centred[current], model.centred[r["soc_code"]])
                if sim >= MIN_LINK_SIMILARITY:
                    options.append((r["soc_code"][:2] == current[:2], sim, r))
            if options:
                same, sim, r = max(options, key=lambda o: (o[0], -o[2]["sort_index"], o[1]))
                best = {"soc_code": r["soc_code"], "title": r["title"], "job_zone": r["job_zone"],
                        "tier": r["tier"], "sort_index": r["sort_index"],
                        "link_similarity": round(sim, 3), "same_field": same}
                break
        if best is None:
            break
        chain.append(best)
        used.add(best["soc_code"])
        current, current_zone = best["soc_code"], best["job_zone"]
    return list(reversed(chain))


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


def _closeness(model, held_ids, field, socs):
    """{soc: how close the user's current skills are to that job}, by the same
    model as For you. Empty when the user has ticked nothing."""
    if not held_ids:
        return {}
    prof = model.profile(held_ids, field)      # with the field of study, if given (ADR-0029)
    return {soc: model.score(prof, soc) for soc in socs if soc in model.centred}
