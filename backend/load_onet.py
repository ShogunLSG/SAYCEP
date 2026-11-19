"""Build saycep.db from the O*NET 29.0 text database.

Idempotent: drops and recreates every reference table on each run. The O*NET
files on disk are the source of truth, so there are no migrations.

Usage:  python backend/load_onet.py
"""

import csv
import sqlite3
import sys
from pathlib import Path

import repository

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "onet"
DB = ROOT / "saycep.db"

SOURCE = "O*NET 29.0 (August 2024 release)"
IMPORTANCE_SCALE_MAX = 5.0

# Expected row counts, from O*NET's published data dictionary. The load fails
# loudly if the files on disk disagree -- a silently truncated download is the
# kind of thing that surfaces in a demo rather than in a test.
EXPECTED = {
    "Occupation Data.txt": 1016,
    "Skills.txt": 61530,
    "Job Zones.txt": 923,
    "Related Occupations.txt": 18460,
    # Added 30 September for "A day in this job" (ADR-0007). Counted from the
    # Kaggle copy, whose other four files match the data dictionary exactly.
    "Task Statements.txt": 18796,
    "Task Ratings.txt": 158751,
    # Added 30 September for job pages and search (ADR-0009). Counted from the
    # Kaggle copy.
    "Alternate Titles.txt": 55120,
    "Technology Skills.txt": 32470,
    "Tools Used.txt": 41650,
    # Added 30 September for the interest quiz (ADR-0011).
    "Interests.txt": 8307,
    # Added 19 November for the field of study (ADR-0029). Counted from the
    # Kaggle copy.
    "Knowledge.txt": 58014,
}

SCHEMA = """
DROP TABLE IF EXISTS occupations;
DROP TABLE IF EXISTS skills;
DROP TABLE IF EXISTS occupation_skills;
DROP TABLE IF EXISTS related_occupations;
DROP TABLE IF EXISTS job_zone_reference;
DROP TABLE IF EXISTS occupation_tasks;
DROP TABLE IF EXISTS occupation_alt_titles;
DROP TABLE IF EXISTS occupation_technology;
DROP TABLE IF EXISTS occupation_tools;
DROP TABLE IF EXISTS occupation_interests;
DROP TABLE IF EXISTS knowledge_areas;
DROP TABLE IF EXISTS occupation_knowledge;

CREATE TABLE occupations (
    soc_code        TEXT PRIMARY KEY,
    title           TEXT NOT NULL,
    description     TEXT,
    job_zone        INTEGER NOT NULL,
    source_dataset  TEXT NOT NULL
);

CREATE TABLE skills (
    element_id      TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    description     TEXT,
    source_dataset  TEXT NOT NULL
);

-- importance is stored raw, on O*NET's 1-5 Importance scale. The
-- essential/desirable label is derived at query time from the threshold, so
-- changing the threshold is a config change rather than a reload.
CREATE TABLE occupation_skills (
    soc_code                TEXT NOT NULL REFERENCES occupations(soc_code),
    element_id              TEXT NOT NULL REFERENCES skills(element_id),
    importance              REAL NOT NULL,
    importance_scale_max    REAL NOT NULL,
    source_date             TEXT,
    PRIMARY KEY (soc_code, element_id)
);

CREATE TABLE related_occupations (
    soc_code            TEXT NOT NULL REFERENCES occupations(soc_code),
    related_soc_code    TEXT NOT NULL,
    tier                TEXT NOT NULL,
    sort_index          INTEGER NOT NULL,
    PRIMARY KEY (soc_code, related_soc_code)
);

CREATE TABLE job_zone_reference (
    zone        INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    experience  TEXT,
    education   TEXT,
    training    TEXT,
    examples    TEXT,
    svp_range   TEXT
);

-- What someone in the job actually does, in O*NET's own plain sentences.
-- importance is the task's IM rating (1-5); null where O*NET gives none --
-- analyst-written tasks, or a rating marked Recommend Suppress. 298 of the
-- 17,931 loaded tasks, measured 30 September. They sort last.
CREATE TABLE occupation_tasks (
    soc_code        TEXT NOT NULL REFERENCES occupations(soc_code),
    task_id         INTEGER NOT NULL,
    task            TEXT NOT NULL,
    task_type       TEXT,
    importance      REAL,
    source_date     TEXT,
    PRIMARY KEY (soc_code, task_id)
);

-- Other names a job goes by, so search finds "Conduit Installer" (ADR-0009).
CREATE TABLE occupation_alt_titles (
    soc_code        TEXT NOT NULL REFERENCES occupations(soc_code),
    title           TEXT NOT NULL,
    short_title     TEXT
);

-- Software used in the job; hot = O*NET's "Hot Technology" flag.
CREATE TABLE occupation_technology (
    soc_code        TEXT NOT NULL REFERENCES occupations(soc_code),
    example         TEXT NOT NULL,
    category        TEXT NOT NULL,
    hot             INTEGER NOT NULL,
    in_demand       INTEGER NOT NULL
);

-- Physical tools used in the job, grouped by O*NET commodity category.
CREATE TABLE occupation_tools (
    soc_code        TEXT NOT NULL REFERENCES occupations(soc_code),
    example         TEXT NOT NULL,
    category        TEXT NOT NULL
);

-- O*NET's RIASEC interest profile: six scores per job on its 1-7 OI scale
-- (ADR-0011). area is the initial: R, I, A, S, E or C.
CREATE TABLE occupation_interests (
    soc_code        TEXT NOT NULL REFERENCES occupations(soc_code),
    area            TEXT NOT NULL CHECK (area IN ('R','I','A','S','E','C')),
    score           REAL NOT NULL,
    source_date     TEXT,
    PRIMARY KEY (soc_code, area)
);

-- The 33 knowledge areas (ADR-0029): a student's field of study is one of
-- these. Importance on the same 1-5 scale as skills, filtered the same way.
CREATE TABLE knowledge_areas (
    element_id      TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    description     TEXT,
    source_dataset  TEXT NOT NULL
);

CREATE TABLE occupation_knowledge (
    soc_code        TEXT NOT NULL REFERENCES occupations(soc_code),
    element_id      TEXT NOT NULL REFERENCES knowledge_areas(element_id),
    importance      REAL NOT NULL,
    PRIMARY KEY (soc_code, element_id)
);

CREATE INDEX idx_occ_skills_soc ON occupation_skills(soc_code);
CREATE INDEX idx_alt_titles_soc ON occupation_alt_titles(soc_code);
CREATE INDEX idx_tech_soc ON occupation_technology(soc_code);
CREATE INDEX idx_tools_soc ON occupation_tools(soc_code);
CREATE INDEX idx_occ_tasks_soc ON occupation_tasks(soc_code);
CREATE INDEX idx_occ_skills_imp ON occupation_skills(importance DESC);
CREATE INDEX idx_occupations_zone ON occupations(job_zone);
"""


def read(filename):
    """Read one tab-delimited O*NET file, checking its length if we know it."""
    path = DATA / filename
    if not path.exists():
        sys.exit(f"Missing {path}. Unzip the O*NET database into {DATA}.")
    with path.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
    expected = EXPECTED.get(filename)
    if expected is not None and len(rows) != expected:
        sys.exit(
            f"{filename}: expected {expected} rows, found {len(rows)}. "
            "The download looks incomplete or is a different O*NET release."
        )
    return rows


def main():
    occupations = read("Occupation Data.txt")
    skills_rows = read("Skills.txt")
    job_zones = read("Job Zones.txt")
    related = read("Related Occupations.txt")
    zone_ref = read("Job Zone Reference.txt")
    content_model = read("Content Model Reference.txt")
    tasks = read("Task Statements.txt")
    task_ratings = read("Task Ratings.txt")
    alt_titles = read("Alternate Titles.txt")
    technology = read("Technology Skills.txt")
    tools = read("Tools Used.txt")
    interests = read("Interests.txt")
    knowledge = read("Knowledge.txt")

    zone_by_soc = {r["O*NET-SOC Code"]: int(r["Job Zone"]) for r in job_zones}

    # A skill is "not relevant" to an occupation via a flag carried on the LV
    # row of the pair, never the IM row. Excluding them means looking there.
    not_relevant = {
        (r["O*NET-SOC Code"], r["Element ID"])
        for r in skills_rows
        if r["Scale ID"] == "LV" and r["Not Relevant"] == "Y"
    }

    importance = [
        r for r in skills_rows
        if r["Scale ID"] == "IM"
        and r["Recommend Suppress"] != "Y"
        and (r["O*NET-SOC Code"], r["Element ID"]) not in not_relevant
    ]

    # Only occupations complete across all four files are usable. An occupation
    # with no skills has nothing for the gap analyser to say about it, so it
    # must not appear in target selection.
    with_skills = {r["O*NET-SOC Code"] for r in importance}
    with_related = {r["O*NET-SOC Code"] for r in related}
    usable = {
        r["O*NET-SOC Code"] for r in occupations
        if r["O*NET-SOC Code"] in zone_by_soc
        and r["O*NET-SOC Code"] in with_skills
        and r["O*NET-SOC Code"] in with_related
    }

    skill_ids = {r["Element ID"] for r in importance}
    skill_names = {
        r["Element ID"]: (r["Element Name"], r["Description"])
        for r in content_model if r["Element ID"] in skill_ids
    }

    DB.unlink(missing_ok=True)
    con = sqlite3.connect(DB)
    con.executescript(SCHEMA)

    con.executemany(
        "INSERT INTO occupations VALUES (?,?,?,?,?)",
        [
            (r["O*NET-SOC Code"], r["Title"], r["Description"],
             zone_by_soc[r["O*NET-SOC Code"]], SOURCE)
            for r in occupations if r["O*NET-SOC Code"] in usable
        ],
    )
    con.executemany(
        "INSERT INTO skills VALUES (?,?,?,?)",
        [
            (eid, name, desc, SOURCE)
            for eid, (name, desc) in sorted(skill_names.items())
        ],
    )
    con.executemany(
        "INSERT INTO occupation_skills VALUES (?,?,?,?,?)",
        [
            (r["O*NET-SOC Code"], r["Element ID"], float(r["Data Value"]),
             IMPORTANCE_SCALE_MAX, r["Date"])
            for r in importance if r["O*NET-SOC Code"] in usable
        ],
    )
    con.executemany(
        "INSERT INTO related_occupations VALUES (?,?,?,?)",
        [
            (r["O*NET-SOC Code"], r["Related O*NET-SOC Code"],
             r["Relatedness Tier"], int(r["Index"]))
            for r in related if r["O*NET-SOC Code"] in usable
        ],
    )
    con.executemany(
        "INSERT INTO job_zone_reference VALUES (?,?,?,?,?,?,?)",
        [
            (int(r["Job Zone"]), r["Name"], r["Experience"], r["Education"],
             r["Job Training"], r["Examples"], r["SVP Range"])
            for r in zone_ref
        ],
    )
    task_importance = {
        (r["O*NET-SOC Code"], r["Task ID"]): float(r["Data Value"])
        for r in task_ratings
        if r["Scale ID"] == "IM" and r["Recommend Suppress"] != "Y"
    }
    con.executemany(
        "INSERT INTO occupation_tasks VALUES (?,?,?,?,?,?)",
        [
            (r["O*NET-SOC Code"], int(r["Task ID"]), r["Task"],
             None if r["Task Type"] == "n/a" else r["Task Type"],
             task_importance.get((r["O*NET-SOC Code"], r["Task ID"])), r["Date"])
            for r in tasks if r["O*NET-SOC Code"] in usable
        ],
    )
    con.executemany(
        "INSERT INTO occupation_alt_titles VALUES (?,?,?)",
        [(r["O*NET-SOC Code"], r["Alternate Title"],
          None if r["Short Title"] == "n/a" else r["Short Title"])
         for r in alt_titles if r["O*NET-SOC Code"] in usable],
    )
    con.executemany(
        "INSERT INTO occupation_technology VALUES (?,?,?,?,?)",
        [(r["O*NET-SOC Code"], r["Example"], r["Commodity Title"],
          int(r["Hot Technology"] == "Y"), int(r["In Demand"] == "Y"))
         for r in technology if r["O*NET-SOC Code"] in usable],
    )
    con.executemany(
        "INSERT INTO occupation_tools VALUES (?,?,?)",
        [(r["O*NET-SOC Code"], r["Example"], r["Commodity Title"])
         for r in tools if r["O*NET-SOC Code"] in usable],
    )
    con.executemany(
        "INSERT INTO occupation_interests VALUES (?,?,?,?)",
        [(r["O*NET-SOC Code"], r["Element Name"][0], float(r["Data Value"]), r["Date"])
         for r in interests if r["Scale ID"] == "OI" and r["O*NET-SOC Code"] in usable],
    )
    # Knowledge areas (ADR-0029), with the same exclusions as skills.
    k_not_relevant = {(r["O*NET-SOC Code"], r["Element ID"]) for r in knowledge
                      if r["Scale ID"] == "LV" and r["Not Relevant"] == "Y"}
    k_importance = [r for r in knowledge if r["Scale ID"] == "IM" and r["Recommend Suppress"] != "Y"
                    and (r["O*NET-SOC Code"], r["Element ID"]) not in k_not_relevant
                    and r["O*NET-SOC Code"] in usable]
    k_ids = {r["Element ID"] for r in k_importance}
    con.executemany(
        "INSERT INTO knowledge_areas VALUES (?,?,?,?)",
        [(r["Element ID"], r["Element Name"], r["Description"], SOURCE)
         for r in content_model if r["Element ID"] in k_ids])
    con.executemany(
        "INSERT INTO occupation_knowledge VALUES (?,?,?)",
        [(r["O*NET-SOC Code"], r["Element ID"], float(r["Data Value"])) for r in k_importance])
    # The profile tables are empty but must exist. The loader deletes the whole
    # file and the API only creates them at startup, so without this,
    # rebuilding the data under a running server breaks every profile call
    # until a restart. Found by backend/tests/test_api.py.
    repository.ensure_profile_tables(con)
    con.commit()

    print(f"Built {DB.name} from {SOURCE}\n")
    for table in ("occupations", "skills", "occupation_skills",
                  "related_occupations", "job_zone_reference", "occupation_tasks",
                  "occupation_alt_titles", "occupation_technology", "occupation_tools",
                  "occupation_interests", "knowledge_areas", "occupation_knowledge"):
        n = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table:22} {n:>7,}")

    dropped = len(occupations) - len(usable)
    print(f"\n  {dropped} occupations excluded as incomplete "
          f"(no skills, job zone or related occupations).")
    print(f"  {len(not_relevant)} skill ratings excluded as not relevant "
          f"to their occupation.")

    # "What employers ask for" (ADR-0017) is optional. Only a valid cache is
    # used here: recomputing takes ~2.5 minutes (NFR-04) and is load_adverts.py's
    # job. Without it the job page says the advert data isn't loaded.
    import load_adverts
    print()
    try:
        load_adverts.load(con, compute_if_stale=False)
    except Exception as e:   # the O*NET database above is complete either way
        print(f"Adverts: skipped ({e}).")
    import load_listings     # Jobs for you (ADR-0022): the same rule, its own cache
    try:
        load_listings.load(con, compute_if_stale=False)
    except Exception as e:
        print(f"Listings: skipped ({e}).")
    con.close()


if __name__ == "__main__":
    main()
