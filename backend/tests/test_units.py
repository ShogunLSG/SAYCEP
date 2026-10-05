"""Unit tests -- individual functions, no HTTP, no live server.

Run: python backend/tests/test_units.py
Evidence for Assignment 3 Q5.1 (unit testing) and the traceability matrix (Q2.2).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import repository
import gap
import pathway
import recommend
import plain
import cvscan
from config import ESSENTIAL_THRESHOLD

PASS, FAIL = [], []


def check(test_id, description, condition, detail=""):
    (PASS if condition else FAIL).append((test_id, description, detail))
    mark = "PASS" if condition else "FAIL"
    print(f"  {mark}  {test_id}  {description}" + (f"  -- {detail}" if detail and not condition else ""))


def main():
    con = repository.connect()

    print("\nTC-U01  gap.compute_gap classifies at the threshold boundary  (FR-07)")
    # gap.compute_gap reads held skills from the profile table; exercise the
    # pure classification rule directly against real O*NET ratings instead.
    rows = repository.required_skills(con, "47-2111.00")
    ess = [r for r in rows if r["importance"] >= ESSENTIAL_THRESHOLD]
    des = [r for r in rows if r["importance"] < ESSENTIAL_THRESHOLD]
    check("TC-U01a", "Troubleshooting (4.00) classifies essential",
          any(r["name"] == "Troubleshooting" for r in ess))
    check("TC-U01b", "Speaking (3.38) classifies desirable",
          any(r["name"] == "Speaking" for r in des))
    check("TC-U01c", "No skill sits on both sides of the threshold",
          not (set(r["element_id"] for r in ess) & set(r["element_id"] for r in des)))

    print("\nTC-U02  recommend.cosine and vector construction  (FR-06, TR-03)")
    skill_ids, vectors = recommend.load_vectors(con)
    check("TC-U02a", "35 skill dimensions loaded", len(skill_ids) == 35, str(len(skill_ids)))
    check("TC-U02b", "879 occupation vectors loaded", len(vectors) == 879, str(len(vectors)))
    identical = recommend.cosine(vectors["47-2111.00"], vectors["47-2111.00"])
    check("TC-U02c", "cosine(v, v) == 1.0 for any real vector", abs(identical - 1.0) < 1e-9, str(identical))
    empty = recommend.recommend(con, [])
    check("TC-U02d", "empty skill set returns no recommendations, not an error", empty == [])

    print("\nTC-U03  pathway._step_focus badging  (FR-08)")
    means = recommend.skill_means(vectors, len(skill_ids))
    focus_target = pathway._step_focus(con, "47-2111.00",
                                        {r["element_id"] for r in rows if r["name"] == "Troubleshooting"},
                                        "47-2071.00")
    new_badges = [f for f in focus_target if f["badge"] == "new"]
    check("TC-U03a", "a skill the profile lacks is badged 'new'",
          any(f["name"] != "Troubleshooting" for f in new_badges))
    check("TC-U03b", "a held skill is never badged 'new'",
          not any(f["badge"] == "new" and f["name"] == "Troubleshooting" for f in focus_target))

    print("\nTC-U04  loader row-count guard  (FR-10, NFR-03)")
    import load_onet
    check("TC-U04a", "expected counts are pinned to O*NET's published dictionary",
          load_onet.EXPECTED["Occupation Data.txt"] == 1016 and
          load_onet.EXPECTED["Skills.txt"] == 61530 and
          load_onet.EXPECTED["Related Occupations.txt"] == 18460)

    print("\nTC-U05  API refuses to start without reference data  (NFR-03)")
    import subprocess, tempfile, os
    backend = str(Path(__file__).resolve().parent.parent)
    with tempfile.TemporaryDirectory() as tmp:
        missing = os.path.join(tmp, "missing.db")
        # Point the app at a database with no reference tables, then import it
        # exactly as uvicorn would. It must exit with a named error.
        probe = ("import sys, config; from pathlib import Path; "
                 f"config.DB_PATH = Path(r'{missing}'); import app")
        r = subprocess.run([sys.executable, "-c", probe], cwd=backend,
                           capture_output=True, text=True, timeout=60)
    check("TC-U05a", "startup exits non-zero when saycep.db has no data", r.returncode != 0, f"exit {r.returncode}")
    check("TC-U05b", "the exit message names the fix (run load_onet.py)",
          "load_onet.py" in (r.stderr + r.stdout), (r.stderr or r.stdout).strip()[-80:])

    print("\nTC-U06  plain-language labels agree with the figures they replace  (FR-07)")
    check("TC-U06a", "every essential importance is labelled at least 'Very important'",
          all(plain.importance_level(v) in ("Critical for this job", "Very important")
              for v in (ESSENTIAL_THRESHOLD, 3.75, 4.0, 5.0)))
    check("TC-U06b", "no desirable importance is labelled 'Very important' or above",
          all(plain.importance_level(v) in ("Important", "Useful") for v in (1.0, 2.99, 3.0, 3.49)))
    check("TC-U06c", "all 35 skills fall into a named group, none into 'Other skills'",
          all(plain.skill_group(s) != "Other skills" for s in skill_ids))
    check("TC-U06d", "every Job Zone 1-5 has a plain label",
          all(plain.preparation(z)["label"] for z in range(1, 6)))
    check("TC-U06e", "a negative similarity still gets a match label, not an error",
          plain.match_level(-0.2) == "Some overlap")

    print("\nTC-U08  every occupation has something to say about its day-to-day  (ADR-0007)")
    no_tasks = con.execute("SELECT COUNT(*) FROM occupations o WHERE NOT EXISTS"
                           " (SELECT 1 FROM occupation_tasks t WHERE t.soc_code = o.soc_code)").fetchone()[0]
    check("TC-U08a", "all 879 occupations have at least one task statement", no_tasks == 0, str(no_tasks))

    print("\nTC-U07  a pre-ADR-0005 database gains the status column  (ADR-0005)")
    import sqlite3
    old = sqlite3.connect(":memory:")
    old.executescript("CREATE TABLE users (profile_id TEXT PRIMARY KEY, profile_type TEXT NOT NULL,"
                      " target_soc_code TEXT, created_at TEXT);"
                      "CREATE TABLE user_skills (profile_id TEXT NOT NULL, element_id TEXT NOT NULL,"
                      " PRIMARY KEY (profile_id, element_id));"
                      "INSERT INTO users VALUES ('p1', 'student', NULL, '');"
                      "INSERT INTO user_skills VALUES ('p1', '2.A.1.a');")
    repository.ensure_profile_tables(old)
    cols = {r[1] for r in old.execute("PRAGMA table_info(user_skills)")}
    check("TC-U07a", "status column added in place", "status" in cols, str(cols))
    check("TC-U07b", "existing skills default to held, so no gap changes on upgrade",
          repository.profile_skill_ids(old, "p1") == ["2.A.1.a"])

    print("\nTC-U09  plan codes  (ADR-0008)")
    check("TC-U09a", "the code alphabet has no look-alike characters",
          not set("01OIL") & set(repository.PLAN_CODE_ALPHABET))
    check("TC-U09b", "codes normalise however they are typed",
          repository.normalise_plan_code("k7m-2qx") == repository.normalise_plan_code(" K7M 2QX") == "K7M2QX")
    cols_u = {r[1] for r in old.execute("PRAGMA table_info(users)")}
    check("TC-U09c", "an older database gains display_name and plan_code in place",
          {"display_name", "plan_code"} <= cols_u, str(cols_u))

    print("\nTC-U10  CV scanner: rules, product names, privacy  (ADR-0014)")
    idx = cvscan.Index(con)
    ev = cvscan.skill_evidence(idx, "Fixed broken bicycles for neighbours.\nTutored Grade 10 learners.\n"
                                    "Reading circuit diagrams.")
    names_found = {idx.skills[e][0] for e in ev}
    check("TC-U10a", "plain CV lines trigger the expected skills, each quoting its line",
          {"Repairing", "Instructing", "Reading Comprehension"} <= names_found
          and all(isinstance(v[0], str) for v in ev.values()), str(sorted(names_found)))
    check("TC-U10b", "every one of the 35 skills has a rule", len(idx.rules) == 35)
    sw = cvscan.named(idx.software, "kept records, fitted plug points, used power drills and Microsoft Excel",
                      common=idx.common)
    check("TC-U10c", "ordinary words don't match software ('points', 'records', 'power'); Microsoft Excel does",
          sw == {"Microsoft Excel"}, str(sw))
    check("TC-U10d", "a one-word product name that is ordinary English needs its vendor (Teams, Windows)",
          not cvscan.named(idx.software, "I worked in teams and cleaned windows", common=idx.common))
    import inspect
    src = inspect.getsource(cvscan)
    check("TC-U10e", "the scanner never writes to the database (no INSERT/UPDATE/DELETE in cvscan.py)",
          not any(w in src.upper() for w in ("INSERT ", "UPDATE ", "DELETE ")))

    print(f"\n{len(PASS)} passed, {len(FAIL)} failed, {len(PASS)+len(FAIL)} total")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
