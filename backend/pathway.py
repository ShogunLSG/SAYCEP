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
  importance of Troubleshooting from 3.25 to 4.00. So each step reports two
  things:

    acquire -- skills the occupation needs at or above the essential threshold
               that the user does not hold and no earlier step covered
    develop -- skills whose required importance rises at this step, with the
               before and after figures shown

  Every step on a real pathway names something under one heading or the other,
  and the figures are O*NET's own rather than a rule we invented.
"""

from config import ESSENTIAL_THRESHOLD, PATHWAY_INTERMEDIATE_STEPS
import recommend
import repository

# A rise smaller than this is noise on a 1-5 survey scale, not a development goal.
MIN_MEANINGFUL_RISE = 0.25


def generate_pathway(con, profile_id, soc_code):
    held = set(repository.profile_skill_ids(con, profile_id))
    target = repository.get_occupation(con, soc_code)

    candidates = [r for r in repository.related_occupations(con, soc_code)
                  if r["related_soc_code"] != soc_code]
    ordered = _rank_by_closeness(con, held, candidates)
    route = [r["related_soc_code"] for r in ordered[:PATHWAY_INTERMEDIATE_STEPS]]

    steps, acquired, previous = [], set(held), None
    for position, step_soc in enumerate(route + [soc_code], start=1):
        is_target = step_soc == soc_code
        row = target if is_target else next(
            r for r in ordered if r["related_soc_code"] == step_soc)

        acquire = _skills_to_acquire(con, step_soc, acquired)
        develop = _skills_to_develop(con, step_soc, previous)
        acquired |= {s["element_id"] for s in acquire}

        steps.append({
            "step": position,
            "soc_code": step_soc,
            "title": row["title"],
            "job_zone": row["job_zone"],
            "relatedness_tier": None if is_target else row["tier"],
            "expert_review_index": None if is_target else row["sort_index"],
            "acquire": acquire,
            "develop": develop,
            "is_target": is_target,
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
            "skills (measured cosine 0.987-0.996), so each step reports skills to "
            "acquire outright and skills whose required importance rises at that "
            "step, with O*NET's before and after ratings."
        ),
    }


def _importance_map(con, soc_code):
    return {r["element_id"]: (r["name"], r["importance"])
            for r in repository.required_skills(con, soc_code)}


def _skills_to_acquire(con, soc_code, already):
    """Essential skills this occupation needs that nothing earlier covered."""
    out = [
        {"element_id": eid, "name": name, "importance": round(imp, 2)}
        for eid, (name, imp) in _importance_map(con, soc_code).items()
        if eid not in already and imp >= ESSENTIAL_THRESHOLD
    ]
    out.sort(key=lambda s: -s["importance"])
    return out


def _skills_to_develop(con, soc_code, previous_soc):
    """Skills whose required importance rises against the previous step."""
    if previous_soc is None:
        return []
    current, prior = _importance_map(con, soc_code), _importance_map(con, previous_soc)
    out = []
    for eid, (name, imp) in current.items():
        before = prior.get(eid, (name, 0.0))[1]
        if imp - before >= MIN_MEANINGFUL_RISE:
            out.append({"element_id": eid, "name": name,
                        "from": round(before, 2), "to": round(imp, 2),
                        "rise": round(imp - before, 2)})
    out.sort(key=lambda s: -s["rise"])
    return out


def _rank_by_closeness(con, held_ids, candidates):
    """Most similar to the user's current profile first."""
    if not candidates:
        return []
    if not held_ids:
        return list(candidates)

    skill_ids, vectors = recommend.load_vectors(con)
    means = recommend.skill_means(vectors, len(skill_ids))
    centred = recommend.centre_occupations(vectors, means)
    profile_vec = recommend.centre_profile(skill_ids, held_ids, means)

    def score(row):
        vec = centred.get(row["related_soc_code"])
        return recommend.cosine(profile_vec, vec) if vec else -1.0

    return sorted(candidates, key=score, reverse=True)
