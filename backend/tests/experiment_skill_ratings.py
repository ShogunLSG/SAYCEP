"""Experiment, not a test: would letting users rate each skill ("a bit" or
"well") instead of ticking it make the skill-matching model more accurate?
Asked on 18 November 2026, as evidence for the "next step" claim (ADR-0013
found richer USER input is the lever). The app is unchanged.

Same method as PT-01b: for every job with must-have skills (importance 3.5+),
a test profile is built from them, the job itself is removed, and a hit is any
of the five closest jobs in the same occupational family (first two SOC digits).

The catch, said up front (ADR-0013): every profile here is built from the
target job's own ratings, so any variant that copies MORE of that job's data
into the profile will match its own family partly by construction. So the
variants are designed to separate two things:

  V0  ticks, as shipped: each must-have skill = 1
  V1  the same skills, graded: "well" (1.0) where the job rates it 4.0+,
      "a bit" (0.5) for 3.5-3.9. Same skills as V0; only the grading is new.
  V2  V1, but a third of the grades are wrong (people misjudge themselves):
      each grade is flipped with probability 1/3, fixed seed.
  V3  more skills, graded: V1 plus "a bit" (0.5) for skills rated 3.0-3.4.
      More copied information, so an UPPER BOUND, not an estimate.
  V1b V1's grades, but centred so an everyday skill (one the average job
      rates 3.5+) counts as ordinary at either grade, as a tick does now.
      Tests whether V1's result is the idea or how the grades are fed in.

The engine's centring is unchanged: a graded skill's centred value is its
grade minus the typical worker's (1 where the average job rates it 3.5+).

Run: python backend/tests/experiment_skill_ratings.py
"""

import math
import random
import statistics
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

import recommend
import repository

con = repository.connect()
skill_ids, vectors = recommend.load_vectors(con)
means = recommend.skill_means(vectors, len(skill_ids))
centred = recommend.centre_occupations(vectors, means)
socs = list(vectors)
idx = {e: i for i, e in enumerate(skill_ids)}
typical = [1.0 if m >= 3.5 else 0.0 for m in means]

ratings = {}
for soc, e, imp in con.execute("SELECT soc_code, element_id, importance FROM occupation_skills"):
    ratings.setdefault(soc, {})[e] = imp
targets = sorted(s for s in socs if any(v >= 3.5 for v in ratings.get(s, {}).values()))


def profile(grades):
    """grades: {element_id: 0..1}. Centred exactly as the engine centres ticks."""
    return [grades.get(e, 0.0) - typical[i] for i, e in enumerate(skill_ids)]


def v0(soc, rng):
    return {e: 1.0 for e, v in ratings[soc].items() if v >= 3.5}


def v1(soc, rng):
    return {e: (1.0 if v >= 4.0 else 0.5) for e, v in ratings[soc].items() if v >= 3.5}


def v2(soc, rng):
    g = v1(soc, rng)
    return {e: (1.5 - x if rng.random() < 1 / 3 else x) for e, x in g.items()}   # 1.0 <-> 0.5


def v3(soc, rng):
    g = v1(soc, rng)
    g.update({e: 0.5 for e, v in ratings[soc].items() if 3.0 <= v < 3.5})
    return g


def profile_b(grades):
    """V1b: an everyday skill held at any grade is ordinary (0), as a tick is."""
    return [(0.0 if grades.get(e) else -1.0) if typical[i] else grades.get(e, 0.0)
            for i, e in enumerate(skill_ids)]


def hits(make, seed=7, centre=profile):
    rng = random.Random(seed)
    out = []
    for soc in targets:
        pv = centre(make(soc, rng))
        top = [s for s, _ in recommend.rank(pv, centred, 0) if s != soc][:5]
        out.append(any(s[:2] == soc[:2] for s in top))
    return out


def interval(h):
    boot = random.Random(3)
    m = sorted(statistics.mean(boot.choices(h, k=len(h))) * 100 for _ in range(1000))
    return m[25], m[974]


family = {}
for s in socs:
    family[s[:2]] = family.get(s[:2], 0) + 1
n_other = len(socs) - 1
chance = statistics.mean(1 - math.comb(n_other - (family[s[:2]] - 1), 5) / math.comb(n_other, 5) for s in targets) * 100

print(f"Experiment: graded skill ratings vs ticks. {len(targets)} jobs with must-haves, target removed (as PT-01b).")
print(f"Random baseline: {chance:.1f}%\n")
base = hits(v0)
print(f"{'variant':58}{'same family in top 5':>22}{'95% interval':>16}{'vs V0':>12}")
for name, make, centre in [("V0 ticks, as shipped", v0, profile), ("V1 same skills, graded a bit / well", v1, profile),
                           ("V1b V1, everyday skills ordinary at any grade", v1, profile_b),
                           ("V2 V1 with a third of grades wrong", v2, profile), ("V3 more skills, graded (upper bound)", v3, profile)]:
    h = base if make is v0 else hits(make, centre=centre)
    lo, hi = interval(h)
    both = sum(a and b for a, b in zip(h, base))
    gained, lost = sum(a and not b for a, b in zip(h, base)), sum(b and not a for a, b in zip(h, base))
    print(f"{name:58}{statistics.mean(h) * 100:>21.1f}%{f'{lo:.1f}-{hi:.1f}':>16}{f'+{gained}/-{lost}':>12}")
