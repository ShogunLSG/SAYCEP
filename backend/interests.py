"""Interest matching -- slice 4, ADR-0011.

Ranks jobs by how closely the *shape* of a user's interests matches the shape
of a job's O*NET RIASEC profile, using Pearson correlation over the six areas.
Correlation, not distance, because the quiz and O*NET use different scales
(0-4 against 1-7); only the pattern -- which areas are high, which are low --
is comparable.

The quiz questions are ours, not O*NET's. O*NET's own Interest Profiler has 60
items; twelve is a simplification and the screen says so. The job profiles
are O*NET's.
"""

from math import sqrt

AREAS = "RIASEC"

# Plain names for the six areas, shown instead of the RIASEC jargon.
AREA_NAMES = {
    "R": "Hands-on", "I": "Figuring things out", "A": "Creating",
    "S": "Helping people", "E": "Leading and persuading", "C": "Organising",
}

# Two short statements per area. Our wording; each answer scores 0-2.
QUESTIONS = [
    ("R", "Fix a broken bike, appliance or engine"),
    ("I", "Work out why something happens by testing ideas"),
    ("A", "Design a poster, an outfit or a room"),
    ("S", "Teach or coach someone a new skill"),
    ("E", "Convince people to buy something or join a cause"),
    ("C", "Keep records or files neat and up to date"),
    ("R", "Build or install something with tools"),
    ("I", "Solve a tricky maths or science problem"),
    ("A", "Write, draw, act or make music"),
    ("S", "Look after people who are sick or going through a hard time"),
    ("E", "Lead a team or run a small business"),
    ("C", "Check numbers or forms carefully for mistakes"),
]


def _pearson(a, b):
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    da, db = [x - ma for x in a], [y - mb for y in b]
    na, nb = sqrt(sum(x * x for x in da)), sqrt(sum(y * y for y in db))
    if na == 0 or nb == 0:
        return None
    return sum(x * y for x, y in zip(da, db)) / (na * nb)


def match(profiles, user_scores, limit=10):
    """profiles: repository.interest_profiles(); user_scores: {area: 0-4}.
    Returns [(soc, job, r)] best first, or None when the answers don't lean
    anywhere (all equal), because then any ranking would be noise."""
    u = [user_scores.get(a, 0) for a in AREAS]
    if max(u) == min(u):
        return None
    ranked = []
    for soc, job in profiles.items():
        r = _pearson(u, [job["scores"].get(a, 0) for a in AREAS])
        if r is not None:
            ranked.append((soc, job, r))
    ranked.sort(key=lambda t: (-t[2], t[1]["title"]))
    return ranked[:limit]


def top_areas(scores, n=2):
    return [a for a, _ in sorted(scores.items(), key=lambda kv: -kv[1])[:n]]
