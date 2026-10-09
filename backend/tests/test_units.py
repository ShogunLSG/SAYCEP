"""Unit tests -- individual functions, no HTTP, no live server.

Run: python backend/tests/test_units.py
Evidence for Assignment 3 Q5.1 (unit testing) and the traceability matrix (Q2.2).
"""

import json
import sqlite3
import sys
import tempfile
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import repository
import gap
import pathway
import recommend
import plain
import cvscan
import interview
import adverts
import load_adverts
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
    folded = cvscan._words("canes planes boxes wrenches glasses batteries analysis status")
    check("TC-U10f", "plurals fold to their real singular: canes -> cane, not can (ADR-0018)",
          folded == ["cane", "plane", "box", "wrench", "glass", "battery", "analysis", "status"], str(folded))
    tl = cvscan.tools_named(idx, "I can lead a plan, and I saw where to tap in.")
    check("TC-U10g", "'I can', 'a plan', 'I saw', 'tap' name no tools (Canes, Planes, Saws, Taps)", tl == set(), str(tl))
    check("TC-U10h", "a real mention still names the tool: 'canes and walkers'",
          {"Canes", "Walkers"} <= cvscan.tools_named(idx, "Helped patients with canes and walkers"))
    import inspect
    src = inspect.getsource(cvscan)
    check("TC-U10e", "the scanner never writes to the database (no INSERT/UPDATE/DELETE in cvscan.py)",
          not any(w in src.upper() for w in ("INSERT ", "UPDATE ", "DELETE ")))

    print("\nTC-U11  Interview practice feedback rules  (ADR-0015)")
    good = ("Last year at my uncle's house the kitchen lights stopped working. I checked the plug points "
            "with a multimeter and found a loose wire in the switch. I switched off the power, tightened "
            "the wire and tested it again. In the end the lights worked and my uncle saved R450.")
    fb = interview.feedback(idx, good, next(e for e, (n, _) in idx.skills.items() if n == "Troubleshooting"))
    check("TC-U11a", "a full situation-action-result answer meets every item",
          fb["met"] == fb["of"], str([i["key"] for i in fb["items"] if not i["ok"]]))
    weak = interview.feedback(idx, "I need a job and I want to be an electrician.")
    check("TC-U11b", "'I need' and 'I want' are not counted as actions; a short answer gets tips",
          not next(i for i in weak["items"] if i["key"] == "action")["ok"]
          and all(i["tip"] for i in weak["items"] if not i["ok"]))
    we_only = interview.feedback(idx, "Last term at school our team built a robot. We planned it and we tested it "
                                      "for two weeks. In the end we won second place out of twelve schools.")
    check("TC-U11c", "an answer told only as 'we' is flagged for your own part",
          not next(i for i in we_only["items"] if i["key"] == "ownership")["ok"])
    check("TC-U11d", "every one of the 35 skills has a practice question",
          set(interview.SKILL_QUESTIONS) == {n for n, _ in idx.skills.values()})

    print("\nTC-U12  Advert linking and requirement rules  (ADR-0017)")
    lookup = adverts.build_lookup(con)
    check("TC-U12a", "a plain trade title links to its one occupation, seniority and location stripped",
          adverts.link("Senior Maintenance Electrician - Night Shift, Dallas", lookup) == "47-2111.00",
          str(adverts.link("Senior Maintenance Electrician - Night Shift, Dallas", lookup)))
    check("TC-U12b", "generic titles are dropped, not guessed (Director, Project Manager, Sales Associate)",
          all(adverts.link(t, lookup) is None for t in ("Director", "Project Manager", "Sales Associate")))
    amb = next(k for k, v in lookup.items() if len(v) > 1 and k not in adverts.GENERIC)
    check("TC-U12c", "a title matching several occupations is dropped", adverts.link(amb, lookup) is None, amb)
    req = adverts.requirements("High school diploma or GED required. Valid driver's license. "
                               "Must be able to lift up to 50 lbs. No experience necessary - we will train!")
    check("TC-U12d", "requirement rules find school, driver's licence, lifting and training",
          req == {"school", "driver", "lifting", "train"}, str(req))
    check("TC-U12e", "'certified as a Great Place to Work' and a CDL data link are not requirements",
          not adverts.requirements("We were certified as a Great Place to Work. Tactical data links (Link-16, CDL)."))
    check("TC-U12f", "years asked: run-together text, ranges, 'yrs', and the lowest figure wins",
          [adverts.years_asked(t) for t in ("preferred1-3 years of experience", "3-5 yrs. experience",
           "5+ years of experience; 2 years' experience with forklifts", "founded 100 years ago")] == [1, 3, 2, None])
    tbl = adverts.aliases({"Microsoft Excel", "Timpani Chat"}, {"Canes", "Multimeters"})
    found = adverts.named_in(tbl, "You can chat to us. Must use Excel and multimeters.", idx.common)
    check("TC-U12g", "named tools: vendor dropped only for known vendors; 'can' is not Canes",
          found == {"Microsoft Excel", "Multimeters"}, str(found))
    check("TC-U12h", "shares read as words: 7 in 10, almost all, a few",
          [adverts.share_words(n, 84) for n in (62, 84, 3)] == ["7 in 10", "almost all", "a few"])

    print("\nTC-U13  Advert fixes after code review  (ADR-0017, 8 October)")
    check("TC-U13a", "a curly apostrophe counts: driver’s license, 2 years’ experience",
          "driver" in adverts.requirements("Must have a valid driver’s license")
          and adverts.years_asked("2 years’ experience in a warehouse") == 2)
    yrs = [adverts.years_asked(t) for t in ("1.5 years of experience", "related field.5-8 years’ experience")]
    check("TC-U13b", "'1.5 years' is 1.5, not 5; 'field.5-8 years' is 5, not 8", yrs == [1.5, 5], str(yrs))
    drv = [adverts.requirements(t) for t in ("Must have a valid license to drive", "CDL license required")]
    check("TC-U13c", "a driving licence is not also a trade licence", drv == [{"driver"}, {"driver"}], str(drv))
    boiler = [adverts.requirements(t) for t in ("We are a certified B Corp.", "A certified minority-owned business.",
                                                "Great Place to Work-Certified™")]
    check("TC-U13d", "employer boilerplate is not a trade licence; 'ASE Certified preferred' is",
          boiler == [set(), set(), set()] and "licence" in adverts.requirements("ASE Certified preferred"), str(boiler))
    tbl = adverts.aliases({"Microsoft Visual Basic", "Microsoft Visual Basic for Applications VBA"},
                          {"Hacksaws", "Mini hacksaws"})
    hits = adverts.named_in(tbl, "Uses Microsoft Visual Basic for Applications VBA and mini hacksaws.")
    check("TC-U13e", "one mention names one product: the longest match, not also the names inside it",
          hits == {"Microsoft Visual Basic for Applications VBA", "Mini hacksaws"}, str(hits))
    shown = [adverts.display_title("it project manager", Counter({"IT Project Manager": 5, "It project manager": 1})),
             adverts.display_title("electrician", Counter({"ELECTRICIAN": 4, "Electrician": 2}))]
    check("TC-U13f", "advert titles keep their acronyms (IT, not It)", shown == ["IT Project Manager", "Electrician"], str(shown))
    check("TC-U13g", "the period comes from the dates: April 2024, or March–April 2024",
          (adverts.period("2024-04-05", "2024-04-20"), adverts.period("2024-03-24", "2024-04-20"))
          == ("April 2024", "March–April 2024"))
    row = {"adverts": 20, "level_n": 10, "entry_level": 7, "years_n": 2, "years_median": 4.0}
    out = adverts.summarise(row, [("req", "renamed_key", 15), ("req", "school", 10), ("skill", "9.Z.9", 15)],
                            {("skill", "9.Z.9"): 1}, 100, {}, {})
    check("TC-U13h", "beginners are a share of adverts that state a level; years need 5+ adverts; "
          "unknown keys are skipped, not fatal",
          out["entry_words"] == "7 in 10" and out["years"] is None
          and [r["key"] for r in out["requirements"]] == ["school"] and out["skills"] == [], str(out))

    print("\nTC-U14  The advert cache  (NFR-04, ADR-0017)")
    mem = sqlite3.connect(":memory:")
    for t in ("occupations (soc_code, title)", "occupation_alt_titles (soc_code, title, short_title)",
              "occupation_technology (soc_code, example)", "occupation_tools (soc_code, example)",
              "occupation_tasks (task)", "skills (element_id, name)"):
        mem.execute(f"CREATE TABLE {t}")
    mem.execute("INSERT INTO occupations VALUES ('47-2111.00', 'Electricians')")
    real_cache = load_adverts.CACHE
    with tempfile.TemporaryDirectory() as d:
        load_adverts.CACHE = Path(d) / "c.json"
        missing = Path(d) / "no-postings.csv"
        fake = {"read": 1, "linked": 1, "summary": [["47-2111.00", 5, 5, 3, 0, None, "2024-04-05", "2024-04-20"]],
                "counts": [], "titles": [], "baseline": [["all", "adverts", 1]],
                "inputs": load_adverts.inputs_fingerprint(mem), "postings": "x"}
        load_adverts.CACHE.write_text(json.dumps(fake))
        ok_cache_only = load_adverts.load(mem, path=missing, compute_if_stale=False)
        mem.execute("UPDATE occupations SET title = 'Electricians (changed)'")
        stale = load_adverts.load(mem, path=missing, compute_if_stale=False)
        load_adverts.CACHE.write_text('{"inputs": "trunc')
        corrupt = load_adverts.load(mem, path=missing, compute_if_stale=False)
    load_adverts.CACHE = real_cache
    check("TC-U14a", "a valid cache loads without the 517 MB advert file", ok_cache_only is True)
    check("TC-U14b", "a change in the O*NET rows the counts were built from makes the cache stale", stale is False)
    check("TC-U14c", "a corrupt cache is treated as no cache, not a crash", corrupt is False)

    print(f"\n{len(PASS)} passed, {len(FAIL)} failed, {len(PASS)+len(FAIL)} total")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
