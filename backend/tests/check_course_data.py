"""Could a Kaggle course catalogue teach the skills SAYCEP's users are missing?

A data check, not part of the app (18 November 2026; data-sources.md). It reads
two Kaggle course catalogues, the only ones of the six checked with a usable
licence:

  siddharthm1698/coursera-course-dataset              GPL-2.0, 891 Coursera courses (titles only)
  jilkothari/finance-accounting-courses-udemy-13k-course  CC0-1.0, 13,608 Udemy finance courses

and, for each of O*NET's 35 skills, counts the course titles that plainly match
it (our keywords, kept narrow), weighted by how often the skill is a must-have
(importance 3.5+) for the jobs a school-leaver is shown (Job Zones 1-3). It
prints every Coursera match for hand-checking: a keyword hit is not a relevant
course ("Troubleshooting" matches "AI for Medical Diagnosis").

Download the two datasets (kaggle datasets download --unzip) into one folder,
one subfolder each, then:

    python backend/tests/check_course_data.py <that folder>
"""

import csv
import glob
import re
import sqlite3
import sys
from collections import Counter
from pathlib import Path

DB = Path(__file__).resolve().parents[1] / "saycep.db"

# Our keyword(s) per skill: the skill's own name plus the plainest synonym.
KEYWORDS = {
    "Active Learning": r"learning how to learn|learn(ing)? to learn",
    "Active Listening": r"\blistening\b",
    "Complex Problem Solving": r"problem[- ]solving",
    "Coordination": r"\bcoordinat\w*|teamwork|collaborat\w*",
    "Critical Thinking": r"critical thinking",
    "Equipment Maintenance": r"\bmaintenance\b|\bmaintain\w* (equipment|machines?)",
    "Equipment Selection": r"selecting (tools|equipment)",
    "Installation": r"\binstall\w*",
    "Instructing": r"\bteaching\b|\binstruct\w*|train the trainer",
    "Judgment and Decision Making": r"decision[- ]making",
    "Learning Strategies": r"learning strateg\w*|how to learn",
    "Management of Financial Resources": r"\bbudget\w*|financial management|personal finance",
    "Management of Material Resources": r"inventory|supply chain|logistics",
    "Management of Personnel Resources": r"people management|managing people|human resource|leadership",
    "Mathematics": r"\bmath\w*|algebra|calculus|statistics",
    "Monitoring": r"\bmonitoring\b",
    "Negotiation": r"negotiat\w*",
    "Operation and Control": r"operating (machines?|equipment)|machine operat\w*",
    "Operations Analysis": r"requirements analysis|business analysis",
    "Operations Monitoring": r"process monitoring|\bscada\b",
    "Persuasion": r"persuasi\w*|influenc\w*",
    "Programming": r"programming|python|\bjava\b|javascript|\bcoding\b|c\+\+|software development",
    "Quality Control Analysis": r"quality (control|assurance|management)|six sigma",
    "Reading Comprehension": r"reading comprehension|\breading\b",
    "Repairing": r"\brepair\w*",
    "Science": r"\bscience\b|physics|chemistry|biology",
    "Service Orientation": r"customer service|customer experience",
    "Social Perceptiveness": r"emotional intelligence|empathy",
    "Speaking": r"public speaking|presentation skills|speaking",
    "Systems Analysis": r"systems analysis|systems thinking",
    "Systems Evaluation": r"(program|system) evaluation",
    "Technology Design": r"\bdesign\b",
    "Time Management": r"time management|productivity",
    "Troubleshooting": r"troubleshoot\w*|fault[- ]finding|diagnos\w*",
    "Writing": r"\bwriting\b",
}

# The hands-on skills that trade and operator jobs depend on.
HANDS_ON = {"Operations Monitoring", "Operation and Control", "Repairing", "Troubleshooting",
            "Equipment Maintenance", "Installation", "Equipment Selection"}


def titles(folder, pattern, column):
    path = glob.glob(f"{folder}/{pattern}/*.csv")[0]
    with open(path, encoding="utf-8", errors="replace") as f:
        return [r[column] for r in csv.DictReader(f)]


def main():
    folder = sys.argv[1]
    coursera = titles(folder, "siddharthm1698*", "course_title")
    udemy = titles(folder, "jilkothari*", "title")
    con = sqlite3.connect(DB)
    names = dict(con.execute("SELECT element_id, name FROM skills"))
    assert set(KEYWORDS) == set(names.values()), "keyword list must cover the 35 skills exactly"
    must = Counter(names[e] for (e,) in con.execute(
        "SELECT os.element_id FROM occupation_skills os JOIN occupations o USING (soc_code)"
        " WHERE o.job_zone <= 3 AND os.importance >= 3.5"))
    jobs = con.execute("SELECT COUNT(*) FROM occupations WHERE job_zone <= 3").fetchone()[0]
    total = sum(must.values())
    rows = []
    for skill, rx in KEYWORDS.items():
        r = re.compile(rx, re.I)
        rows.append((must[skill], skill, [t for t in coursera if r.search(t)], [t for t in udemy if r.search(t)]))
    rows.sort(key=lambda x: (-x[0], x[1]))

    print(f"Courses: Coursera {len(coursera)} (GPL-2.0), Udemy finance {len(udemy)} (CC0-1.0)")
    print(f"School-leaver jobs (Zones 1-3): {jobs}; must-have slots: {total}")
    hit = sum(m for m, _, c, _ in rows if c)
    print(f"Must-have slots with at least one Coursera keyword match: {hit / total:.0%}  (before checking relevance)")
    hands = sum(m for m, s, _, _ in rows if s in HANDS_ON)
    print(f"Must-have slots that are hands-on skills: {hands / total:.0%}")
    print(f"\n{'skill':34}{'must-have':>10}{'coursera':>9}{'udemy-fin':>10}")
    for m, s, c, u in rows:
        print(f"{s:34}{m:>10}{len(c):>9}{len(u):>10}")
    print("\nEvery Coursera match, for hand-checking:")
    for m, s, c, _ in rows:
        if c:
            print(f"  {s}: {c}")


if __name__ == "__main__":
    main()
