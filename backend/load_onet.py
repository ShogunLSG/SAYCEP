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
}

SCHEMA = """
DROP TABLE IF EXISTS occupations;
DROP TABLE IF EXISTS skills;
DROP TABLE IF EXISTS occupation_skills;
DROP TABLE IF EXISTS related_occupations;
DROP TABLE IF EXISTS job_zone_reference;
DROP TABLE IF EXISTS occupation_tasks;

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

CREATE INDEX idx_occ_skills_soc ON occupation_skills(soc_code);
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
    # The profile tables are empty but must exist. The loader deletes the whole
    # file and the API only creates them at startup, so without this,
    # rebuilding the data under a running server breaks every profile call
    # until a restart. Found by backend/tests/test_api.py.
    repository.ensure_profile_tables(con)
    con.commit()

    print(f"Built {DB.name} from {SOURCE}\n")
    for table in ("occupations", "skills", "occupation_skills",
                  "related_occupations", "job_zone_reference", "occupation_tasks"):
        n = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table:22} {n:>7,}")

    dropped = len(occupations) - len(usable)
    print(f"\n  {dropped} occupations excluded as incomplete "
          f"(no skills, job zone or related occupations).")
    print(f"  {len(not_relevant)} skill ratings excluded as not relevant "
          f"to their occupation.")
    con.close()


if __name__ == "__main__":
    main()
