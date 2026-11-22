"""Plain-language labels -- what a figure means, in words a school leaver reads.

The screens lead with a sentence and keep the figure for presenter mode, so a
marker can still check FR-07 against the number while a user never has to
learn what "3.62 / 5" or "Job Zone 3" means.

These cut-points are a presentation choice, not a finding from the data. They
are set here, next to nothing else, so the frontend never decides what a number
means -- it only shows the label it is given.
"""

from config import ESSENTIAL_THRESHOLD

# O*NET importance, 1-5. The "very important" line is the essential threshold,
# so a "must-have" is never described as merely "important". Share of all
# loaded ratings at or above each line: 4.0 -> 6.4%, 3.5 -> 18.9%, 3.0 -> 45.6%.
IMPORTANCE_LEVELS = [
    (4.0, "Critical for this job"),
    (ESSENTIAL_THRESHOLD, "Very important"),
    (3.0, "Important"),
    (0.0, "Useful"),
]

# Mean-centred cosine. Measured over 300 random 3-12 skill profiles, the top
# recommendation's score has a median of 0.44 and a 90th percentile of 0.56; a
# coherent real profile (the demo script's) scores 0.64. So 0.55 and above is
# genuinely strong, and anything under 0.40 is worth saying less about.
MATCH_LEVELS = [
    (0.55, "Strong match"),
    (0.40, "Good match"),
    (float("-inf"), "Some overlap"),
]

# Pearson correlation between quiz answers and a job's RIASEC profile, -1..1.
# A single-area answer set correlates about 0.9 with that area's purest jobs,
# so 0.8 and above is a close fit. A presentation choice, like the others.
INTEREST_FIT_LEVELS = [
    (0.8, "Close fit"),
    (0.6, "Good fit"),
    (float("-inf"), "Some fit"),
]

# O*NET's Job Zones, in words. The education notes are U.S. ("high school
# diploma", "associate's degree"); "matric" is our translation of the first and
# the dev guide says so. The originals still travel in the API response.
ZONES = {
    1: ("Start with little or no training",
        "Most people learn these on the job. School-level education is usually enough."),
    2: ("Some preparation — usually matric",
        "Usually needs matric and a little work experience, often learned on the job."),
    3: ("Vocational training or an apprenticeship",
        "Usually needs a trade qualification, an apprenticeship or a college "
        "course, plus some related experience."),
    4: ("Usually a degree",
        "Most of these need a bachelor's degree and several years of related experience."),
    5: ("Postgraduate study",
        "Most of these need a master's degree or higher and many years of experience."),
}

# O*NET groups its 35 skills by element ID. These headings replace the content
# model's own names ("Basic Skills: Content", "Resource Management Skills").
#
# The ORDER is a presentation choice with a measured basis (20 November): the
# groups whose skills the fewest jobs list as must-haves come first, so what
# tells jobs apart leads and the everyday skills nearly every job needs come
# last. Share of the 879 jobs listing a group's skills as must-haves, on
# average: hands-on and technical 4%, managing 6%, people 15%, judgement 16%,
# thinking 32%, reading and speaking 38%. Nothing is hidden and no score
# depends on this order; it sets the order of the tick screen and of the
# "nice to have" list in the gap (see skill_group_rank).
SKILL_GROUPS = [
    ("2.B.3", "Hands-on and technical"),
    ("2.B.5", "Managing time, money and people"),
    ("2.B.1", "Working with people"),
    ("2.B.4", "Judgement and decisions"),
    # 2.B.2 holds one skill, Complex Problem Solving; it sits with its neighbours.
    ("2.A.2", "Thinking and problem solving"),
    ("2.B.2", "Thinking and problem solving"),
    ("2.A.1", "Reading, writing, speaking and maths"),
]


def importance_level(importance):
    return next(label for cut, label in IMPORTANCE_LEVELS if importance >= cut)


def match_level(score):
    return next(label for cut, label in MATCH_LEVELS if score >= cut)


def interest_fit(r):
    return next(label for cut, label in INTEREST_FIT_LEVELS if r >= cut)


def preparation(zone):
    short, detail = ZONES.get(zone, ("", ""))
    return {"label": short, "detail": detail}


def skill_group(element_id):
    return next((name for prefix, name in SKILL_GROUPS
                 if element_id.startswith(prefix)), "Other skills")


def skill_group_rank(element_id):
    """Where this skill's group sits in SKILL_GROUPS: 0 for the most
    distinctive group, last for the everyday skills. A skill in no group sorts
    after all of them."""
    order = list(dict.fromkeys(name for _, name in SKILL_GROUPS))
    name = skill_group(element_id)
    return order.index(name) if name in order else len(order)


# Plain examples under each O*NET knowledge area, so a student can find their
# field of study (ADR-0029). The 33 areas and their descriptions are O*NET's;
# these examples are ours: UI wording that helps someone choose, not data the
# model uses.
FIELD_EXAMPLES = {
    "2.C.1.a": "Business management, public administration",
    "2.C.1.b": "Office administration, secretarial studies",
    "2.C.1.c": "BCom, accounting, economics, banking",
    "2.C.1.d": "Marketing, retail, sales",
    "2.C.1.e": "Hospitality, tourism, customer service",
    "2.C.1.f": "Human resource management",
    "2.C.2.a": "Manufacturing, quality control, operations",
    "2.C.2.b": "Agriculture, farming, food technology",
    "2.C.3.a": "IT, computer science, information systems",
    "2.C.3.b": "Engineering: civil, electrical, mechanical, chemical",
    "2.C.3.c": "Drafting, architecture, technical drawing",
    "2.C.3.d": "Building, construction, plumbing, bricklaying",
    "2.C.3.e": "Motor mechanics, fitting and turning, millwright",
    "2.C.4.a": "Mathematics, statistics, actuarial science",
    "2.C.4.b": "Physics, physical science",
    "2.C.4.c": "Chemistry, chemical sciences",
    "2.C.4.d": "Biology, life sciences, environmental science",
    "2.C.4.e": "Psychology",
    "2.C.4.f": "Sociology, social work, anthropology",
    "2.C.4.g": "Geography, surveying, GIS",
    "2.C.5.a": "Nursing, medicine, pharmacy, dentistry",
    "2.C.5.b": "Physiotherapy, occupational therapy, counselling",
    "2.C.6": "Teaching, education, early childhood development",
    "2.C.7.a": "English, journalism, writing",
    "2.C.7.b": "Languages other than English, translation",
    "2.C.7.c": "Music, drama, dance, visual art",
    "2.C.7.d": "History, archaeology, heritage",
    "2.C.7.e": "Philosophy, theology, religious studies",
    "2.C.8.a": "Policing, safety and security, firefighting",
    "2.C.8.b": "Law (LLB), paralegal studies, public policy",
    "2.C.9.a": "Telecommunications, network technology",
    "2.C.9.b": "Media, public relations, film",
    "2.C.10": "Logistics, transport, aviation",
}
