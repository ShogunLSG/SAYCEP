"""The skill-matching model: occupation recommendation from 35 O*NET skills.

The emerging-technology component (FR-06). Since 19 November (ADR-0027) a person
is matched to a job by two views of the job, averaged:

  1. its ratings: the 35 O*NET importance ratings, mean-centred (below), and
  2. its must-have list: the skills rated 3.5+ (its top 5 where none are),
     as yes/no, mean-centred the same way,

each compared with the person's ticks by cosine similarity. The ticks are
yes/no, so the second view compares like with like; the first keeps how much
each skill matters. Measured: 67.6% against 58.5% for the ratings alone
(PT-01b), and ahead with realistic, messy profiles too
(backend/tests/experiment_model_upgrades.py). Job to job, where both sides
have ratings, the ratings view alone is better (PT-05), so similar() keeps it.

The rest of this note is about the ratings view (the model until 19 November).

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


def tick_vectors(vectors, threshold=ESSENTIAL_THRESHOLD, fallback=5):
    """Each job's must-have list as yes/no: skills rated at or above the
    threshold, or, for a job with none, its `fallback` most important skills
    (the same rule as pathway.step_readiness)."""
    out = {}
    for soc, v in vectors.items():
        t = [1.0 if x >= threshold else 0.0 for x in v]
        if not any(t):
            top = set(sorted(range(len(v)), key=lambda i: (-v[i], i))[:fallback])
            t = [1.0 if i in top else 0.0 for i in range(len(v))]
        out[soc] = t
    return out


class Model:
    """The skill-matching model (ADR-0027): two views of every job, averaged.

    profile() turns held skills into the two centred views of a person;
    score() is the average of the two cosines; contributions() splits that
    score into one number per skill, which add up to it exactly (the "How we
    matched you" panel and the reasons both come from it)."""

    def __init__(self, skill_ids, vectors):
        self.ids = skill_ids
        self.vectors = vectors
        self.means = skill_means(vectors, len(skill_ids))
        self.centred = centre_occupations(vectors, self.means)
        self.ticks = tick_vectors(vectors)
        self.tick_means = skill_means(self.ticks, len(skill_ids))
        self.tick_centred = centre_occupations(self.ticks, self.tick_means)

    @classmethod
    def load(cls, con):
        return cls(*load_vectors(con))

    def profile(self, held_skill_ids):
        held = set(held_skill_ids)
        ratings = centre_profile(self.ids, held, self.means)
        ticks = [(1.0 if e in held else 0.0) - self.tick_means[i] for i, e in enumerate(self.ids)]
        return ratings, ticks

    def parts(self, prof, soc):
        """(score from the ratings view, score from the must-have view)."""
        return cosine(prof[0], self.centred[soc]), cosine(prof[1], self.tick_centred[soc])

    def score(self, prof, soc):
        a, b = self.parts(prof, soc)
        return (a + b) / 2

    def rank(self, prof, limit=5, restrict_to=None):
        scored = [(soc, self.score(prof, soc)) for soc in self.centred
                  if restrict_to is None or soc in restrict_to]
        scored.sort(key=lambda p: (-p[1], p[0]))
        return scored[:limit] if limit else scored

    def contributions(self, prof, soc):
        """Per skill: (ratings part, must-have part, the two averaged). Each
        part is the skill's product over the cosine's denominator, so a part's
        sum is that view's score, and the averaged column sums to score()."""
        out = []
        for view, job in ((prof[0], self.centred[soc]), (prof[1], self.tick_centred[soc])):
            dot = sum(x * y for x, y in zip(view, job))
            den = math.sqrt(sum(x * x for x in view)) * math.sqrt(sum(y * y for y in job))
            out.append([x * y / den if den and dot else 0.0 for x, y in zip(view, job)])
        return [(a, b, (a + b) / 2) for a, b in zip(*out)]

    def reasons(self, prof, held_skill_ids, soc, top_n=3):
        """The held skills that lifted this job's score most (FR-06): positive
        contributions, largest first. A skill every job needs adds little."""
        held = set(held_skill_ids)
        c = self.contributions(prof, soc)
        parts = [(c[i][2], e) for i, e in enumerate(self.ids) if e in held]
        return [e for v, e in sorted(parts, key=lambda p: (-p[0], p[1])) if v > 1e-9][:top_n]

    def explain(self, held_skill_ids, soc):
        """Every number behind one job's score for one person (ADR-0025,
        ADR-0027), from the same methods as rank(), so it cannot disagree with
        the list. Also the score with no centring (ratings against ticks, raw),
        and how both spread across every job: what centring is for."""
        held = set(held_skill_ids)
        prof = self.profile(held)
        job = self.vectors[soc]
        c = self.contributions(prof, soc)
        rows = [{"element_id": e, "importance": job[i], "average": self.means[i],
                 "job_centred": self.centred[soc][i], "must_have": bool(self.ticks[soc][i]),
                 "must_have_share": self.tick_means[i], "typical": self.means[i] >= ESSENTIAL_THRESHOLD,
                 "held": e in held, "you_centred": prof[0][i],
                 "part_ratings": c[i][0], "part_must_haves": c[i][1], "contribution": c[i][2]}
                for i, e in enumerate(self.ids)]
        you_raw = [1.0 if e in held else 0.0 for e in self.ids]
        raw_all = sorted(cosine(you_raw, v) for v in self.vectors.values())
        model_all = sorted(self.score(prof, s) for s in self.vectors)
        span = lambda v: {"low": v[0], "high": v[-1], "median": v[len(v) // 2]}
        a, b = self.parts(prof, soc)
        return {"rows": rows, "score": (a + b) / 2, "score_ratings": a, "score_must_haves": b,
                "score_uncentred": cosine(you_raw, job),
                "spread": {"uncentred": span(raw_all), "centred": span(model_all), "jobs": len(self.vectors)},
                "reasons": self.reasons(prof, held, soc)}


def recommend(con, held_skill_ids, limit=5, max_job_zone=None, model=None):
    """Public entry point. Returns [(soc_code, title, score), ...].

    An empty profile returns an empty list rather than an arbitrary ranking --
    see TR-03. With nothing to compare, any ordering would be noise presented
    as a recommendation.
    """
    if not held_skill_ids:
        return []

    model = model or Model.load(con)

    restrict = None
    if max_job_zone is not None:
        restrict = {r[0] for r in con.execute(
            "SELECT soc_code FROM occupations WHERE job_zone <= ?",
            (max_job_zone,))}

    ranked = model.rank(model.profile(held_skill_ids), limit, restrict)
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
