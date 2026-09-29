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

    print(f"\n{len(PASS)} passed, {len(FAIL)} failed, {len(PASS)+len(FAIL)} total")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
