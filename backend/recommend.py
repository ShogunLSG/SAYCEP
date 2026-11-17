"""Occupation recommendation by mean-centred skill-vector cosine similarity.

The emerging-technology component (FR-06). Each occupation is a 35-dimensional
vector of O*NET importance ratings; a user profile is a binary vector over the
same 35 skills.

Why mean-centred rather than plain cosine. O*NET's 35 skills are generic --
Reading Comprehension, Active Listening, Critical Thinking -- and almost every
occupation needs most of them to some degree. Measured on the loaded catalogue,
the mean cosine between an occupation and its nearest neighbour is 0.994: the raw
vectors nearly all point the same way, so plain cosine barely discriminates.

Subtracting the per-skill mean across all occupations re-expresses each occupation
as how it *deviates* from the average occupation, which is where the signal is.
The profile is centred against the same reference: the "typical worker" is taken
to hold those skills the average occupation rates at or above the essential
threshold. Measured effect on top-5 occupational-family agreement: 19.4% -> 32.4%,
against a 6.9% random baseline.

Content-based rather than a learned model, because O*NET supplies curated survey
ratings and no outcome labels to train on, and because this stays explainable --
when a user asks why an occupation was suggested, the overlap itself is the answer.

Standard library only.
"""

import math
import sqlite3
import statistics

from config import DB_PATH as DB, ESSENTIAL_THRESHOLD


def load_vectors(con):
    """Return (skill_ids, {soc: raw vector}) over the full catalogue."""
    skill_ids = [r[0] for r in con.execute(
        "SELECT element_id FROM skills ORDER BY element_id")]
    index = {eid: i for i, eid in enumerate(skill_ids)}

    vectors = {}
    for soc, eid, imp in con.execute(
            "SELECT soc_code, element_id, importance FROM occupation_skills"):
        vectors.setdefault(soc, [0.0] * len(skill_ids))[index[eid]] = imp
    return skill_ids, vectors


def skill_means(vectors, width):
    """Mean importance of each skill across every occupation."""
    return [statistics.mean(v[i] for v in vectors.values()) for i in range(width)]


def centre_occupations(vectors, means):
    return {soc: [v[i] - means[i] for i in range(len(means))]
            for soc, v in vectors.items()}


def centre_profile(skill_ids, held_skill_ids, means):
    """Binary profile, centred against the skills a typical occupation demands."""
    held = set(held_skill_ids)
    return [(1.0 if eid in held else 0.0)
            - (1.0 if means[i] >= ESSENTIAL_THRESHOLD else 0.0)
            for i, eid in enumerate(skill_ids)]


def reasons(skill_ids, occupation_vec, profile_vec, held_skill_ids, top_n=3):
    """Why a job ranked where it did (FR-06), taken from the score itself.

    The cosine numerator is a sum of per-skill products, centred job value x
    centred profile value. The held skills with the largest positive products
    are the ones that actually lifted this job -- skills the user has that the
    job needs *more than most jobs do*. A generic skill every job needs
    contributes nothing after centring, so it is never offered as a reason.
    """
    held = set(held_skill_ids)
    parts = [(occupation_vec[i] * profile_vec[i], eid)
             for i, eid in enumerate(skill_ids) if eid in held]
    return [eid for c, eid in sorted(parts, reverse=True) if c > 0][:top_n]


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    if dot == 0.0:
        return 0.0
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def explain(skill_ids, vectors, means, held_skill_ids, soc):
    """Every number behind one job's score for one person: the "How we matched
    you" page (ADR-0025). Built from the same functions as recommend(), so it
    cannot disagree with the list.

    Per skill: the job's importance, the average job's, the job's centred
    value, whether the person holds it, their centred value, and the product
    (its contribution to the score's numerator). Also the score, the score
    with no centring, and the spread of both across every job, which is what
    centring is for."""
    held = set(held_skill_ids)
    job = vectors[soc]
    job_c = [job[i] - means[i] for i in range(len(means))]
    you_c = centre_profile(skill_ids, held, means)
    you_raw = [1.0 if e in held else 0.0 for e in skill_ids]
    rows = [{"element_id": e, "importance": job[i], "average": means[i], "job_centred": job_c[i],
             "typical": means[i] >= ESSENTIAL_THRESHOLD, "held": e in held,
             "you_centred": you_c[i], "contribution": job_c[i] * you_c[i]}
            for i, e in enumerate(skill_ids)]
    centred = centre_occupations(vectors, means)
    raw_all = sorted(cosine(you_raw, v) for v in vectors.values())
    cen_all = sorted(cosine(you_c, v) for v in centred.values())
    span = lambda v: {"low": v[0], "high": v[-1], "median": v[len(v) // 2]}
    return {"rows": rows, "score": cosine(you_c, job_c), "score_uncentred": cosine(you_raw, job),
            "spread": {"uncentred": span(raw_all), "centred": span(cen_all), "jobs": len(vectors)},
            "reasons": reasons(skill_ids, job_c, you_c, held)}


def similar(centred, soc, limit=5):
    """The jobs whose centred skill vectors point most nearly the same way as
    this job's: job-to-job similarity (ADR-0025, PT-05). [(soc, score)]."""
    if soc not in centred:
        return []
    me = centred[soc]
    scored = [(o, cosine(me, v)) for o, v in centred.items() if o != soc]
    scored.sort(key=lambda p: (-p[1], p[0]))
    return scored[:limit]


def rank(profile_vec, centred, limit=5, restrict_to=None):
    scored = [(soc, cosine(profile_vec, vec)) for soc, vec in centred.items()
              if restrict_to is None or soc in restrict_to]
    scored.sort(key=lambda p: p[1], reverse=True)
    return scored[:limit] if limit else scored


def recommend(con, held_skill_ids, limit=5, max_job_zone=None):
    """Public entry point. Returns [(soc_code, title, score), ...].

    An empty profile returns an empty list rather than an arbitrary ranking --
    see TR-03. With nothing to compare, any ordering would be noise presented
    as a recommendation.
    """
    if not held_skill_ids:
        return []

    skill_ids, vectors = load_vectors(con)
    means = skill_means(vectors, len(skill_ids))
    centred = centre_occupations(vectors, means)

    restrict = None
    if max_job_zone is not None:
        restrict = {r[0] for r in con.execute(
            "SELECT soc_code FROM occupations WHERE job_zone <= ?",
            (max_job_zone,))}

    ranked = rank(centre_profile(skill_ids, held_skill_ids, means),
                  centred, limit, restrict)
    titles = dict(con.execute("SELECT soc_code, title FROM occupations"))
    return [(soc, titles.get(soc, "?"), score) for soc, score in ranked]


if __name__ == "__main__":
    con = sqlite3.connect(DB)
    held = [r[0] for r in con.execute(
        "SELECT element_id FROM skills WHERE name IN "
        "('Troubleshooting','Repairing','Equipment Maintenance','Operation and Control')")]
    print("Hands-on diagnostic profile, no degree required (Job Zone 1-3):")
    for soc, title, score in recommend(con, held, limit=5, max_job_zone=3):
        print(f"  {score:.3f}  {title}  ({soc})")
