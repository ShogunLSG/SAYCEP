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
SKILL_GROUPS = [
    ("2.A.1", "Reading, writing, speaking and maths"),
    # 2.B.2 holds one skill, Complex Problem Solving; it sits with its neighbours.
    ("2.A.2", "Thinking and problem solving"),
    ("2.B.2", "Thinking and problem solving"),
    ("2.B.1", "Working with people"),
    ("2.B.3", "Hands-on and technical"),
    ("2.B.4", "Judgement and decisions"),
    ("2.B.5", "Managing time, money and people"),
]


def importance_level(importance):
    return next(label for cut, label in IMPORTANCE_LEVELS if importance >= cut)


def match_level(score):
    return next(label for cut, label in MATCH_LEVELS if score >= cut)


def preparation(zone):
    short, detail = ZONES.get(zone, ("", ""))
    return {"label": short, "detail": detail}


def skill_group(element_id):
    return next((name for prefix, name in SKILL_GROUPS
                 if element_id.startswith(prefix)), "Other skills")
