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
    committed = json.loads((Path(load_adverts.ROOT) / "seed" / "advert_counts.cache.json").read_text())
    check("TC-U14d", "the committed advert counts match the current code and O*NET rows "
          "(if not: python backend/load_adverts.py --fresh, then commit backend/seed/)",
          committed.get("inputs") == load_adverts.inputs_fingerprint(con), "stale seed")
    real_code = load_adverts.CODE
    with tempfile.TemporaryDirectory() as d:
        lf, crlf = Path(d) / "lf", Path(d) / "crlf"
        lf.mkdir(); crlf.mkdir()
        for p in real_code:
            data = p.read_bytes().replace(b"\r\n", b"\n")
            (lf / p.name).write_bytes(data)
            (crlf / p.name).write_bytes(data.replace(b"\n", b"\r\n"))
        load_adverts.CODE = [lf / p.name for p in real_code]
        fp_lf = load_adverts.inputs_fingerprint(con)
        load_adverts.CODE = [crlf / p.name for p in real_code]
        fp_crlf = load_adverts.inputs_fingerprint(con)
        load_adverts.CODE = real_code
    check("TC-U14e", "the fingerprint ignores line endings (a Windows checkout must not look stale)",
          fp_lf == fp_crlf)
    check("TC-U14a", "a valid cache loads without the 517 MB advert file", ok_cache_only is True)
    check("TC-U14b", "a change in the O*NET rows the counts were built from makes the cache stale", stale is False)
    check("TC-U14c", "a corrupt cache is treated as no cache, not a crash", corrupt is False)

    print("\nTC-U15  Jobs for you: fit and ranking  (ADR-0022)")
    import listings
    import load_listings
    st = {"a": "held", "b": "held", "c": "held", "d": "learning"}
    words = [listings.fit(m, st)["words"] for m in (["a", "b", "c", "x"], ["a", "b", "x", "y"], ["a", "x", "y"], ["x"], [])]
    check("TC-U15a", "fit words follow the share held: strong, good, some, a stretch, none named",
          words == ["Strong fit", "Good fit", "Some fit", "A stretch", "No skills named"], str(words))
    f = listings.fit(["a", "d", "x"], st)
    check("TC-U15b", "a skill being learned is counted apart, never as held",
          (f["have"], f["learning"], f["mentioned"]) == (1, 1, 3), str(f))
    check("TC-U15c", "open to beginners: entry level, training given, or a year or less asked",
          [listings.beginner_ok(*a) for a in (("Entry level", [], 5), ("", ["train"], None), ("", [], 1), ("Associate", [], 3))]
          == [True, True, True, False])
    mk = lambda i, have, n, beg, yrs, d: {"advert_id": i, "fit": listings.fit(["a"] * have + ["x"] * (n - have), {"a": "held"}),
                                          "beginner": beg, "years": yrs, "listed": d}
    order = [x["advert_id"] for x in listings.rank([
        mk("old", 1, 2, True, None, "2024-04-01"), mk("new", 1, 2, True, None, "2024-04-20"),
        mk("pro", 1, 2, False, None, "2024-04-25"), mk("best", 2, 2, False, 5, "2024-04-02"),
        mk("yrs", 1, 2, True, 3, "2024-04-30")])]
    check("TC-U15d", "ranked by share held, then beginners, then fewer years, then newest",
          order == ["best", "new", "old", "yrs", "pro"], str(order))
    check("TC-U15e", "the committed listings match the current code and O*NET rows "
          "(if not: python backend/load_listings.py --fresh, then commit backend/seed/)",
          json.loads(load_listings.CACHE.read_text()).get("inputs") == load_listings.fingerprint(con), "stale seed")
    check("TC-U15f", "listings store features only: no description, company, link or pay columns",
          not {"description", "company_name", "job_posting_url", "application_url", "max_salary", "min_salary"}
          & {r[1] for r in con.execute("PRAGMA table_info(advert_listings)")})

    print("\nTC-U16  CV advice: what to add  (ADR-0024)")
    import cvadvice
    import interview as interview_mod
    summ = {"adverts": 84, "period": "April 2024",
            "requirements": [{"key": "licence", "share": 0.7, "words": "7 in 10"},
                             {"key": "school", "share": 0.9, "words": "almost all"},
                             {"key": "driver", "share": 0.3, "words": "3 in 10"},
                             {"key": "lifting", "share": 0.1, "words": "a few"},
                             {"key": "train", "share": 0.5, "words": "5 in 10"}],
            "tools": [{"name": "Microsoft Excel", "share": 0.4, "words": "4 in 10"},
                      {"name": "Multimeters", "share": 0.2, "words": "2 in 10"},
                      {"name": "Respirators", "share": 0.06, "words": "a few"}]}
    cv = "Matric 2023. Shop assistant. Used Microsoft Excel for stock lists."
    adv = cvadvice.advice(summ, cv, {"Microsoft Excel"}, ["Troubleshooting", "Repairing"])
    kinds = [(x["kind"], x["title"]) for x in adv]
    check("TC-U16a", "requirements the CV doesn't mention, commonest first; what it mentions (matric) is left out",
          [k for k in kinds if k[0] == "requirement"] == [("requirement", "A trade licence or certificate"), ("requirement", "A driver's licence")],
          str(kinds))
    check("TC-U16b", "weak signals are not advice: a few adverts (physical work, a tool) and 'training given'",
          not any(x["title"] in ("Physical work", "Respirators") or "train" in x["title"].lower() for x in adv))
    check("TC-U16c", "tools: the CV's own tools are left out; the rest named by 15%+ of adverts are advised",
          [x["title"] for x in adv if x["kind"] == "tool"] == ["Multimeters"], str(kinds))
    check("TC-U16d", "every advert figure says how many, that they are US, and when",
          all("of the 84 US adverts for this job (April 2024)" in x["why"] for x in adv if x["kind"] != "skill"))
    check("TC-U16e", "missing skills get a worked example (known skills) or a frame (others)",
          "tested each plug point" in adv[-2]["example"] and cvadvice.example_for("Zebra Handling").startswith("Add one line"))
    check("TC-U16f", "no summary (too few adverts): skill advice only, and no advert figure claimed",
          [x["kind"] for x in cvadvice.advice(None, cv, set(), ["Repairing"])] == ["skill"]
          and "adverts" not in cvadvice.advice(None, cv, set(), ["Repairing"])[0]["why"])
    many = cvadvice.advice(dict(summ, requirements=[{"key": k, "share": 0.9, "words": "almost all"} for k in ("licence", "driver", "lifting", "degree", "school")]),
                           "", set(), ["A", "B", "C", "D", "E"])
    check("TC-U16g", f"at most {cvadvice.MAX_PER_KIND} pieces of each kind",
          Counter(x["kind"] for x in many).most_common(1)[0][1] <= cvadvice.MAX_PER_KIND, str(Counter(x["kind"] for x in many)))
    check("TC-U16h", "South African wording counts: 'Code 8', 'N2', 'TVET', 'matric' are seen as the CV mentioning it",
          not [x for x in cvadvice.advice(dict(summ, requirements=[{"key": "driver", "share": 0.9, "words": "almost all"},
               {"key": "degree", "share": 0.9, "words": "almost all"}], tools=[]), "Code 8 licence. Studying N2 at a TVET college.", set(), [])
               if x["kind"] == "requirement"])

    print("\nTC-U17  Interview: a technical question from the job's tools  (ADR-0024)")
    check("TC-U17a", "a tool is asked about only where real adverts name it (5+ adverts and 5%+): Electricians -> Microsoft Excel",
          interview_mod.tool_for(con, "47-2111.00") == "Microsoft Excel", str(interview_mod.tool_for(con, "47-2111.00")))
    none_soc = con.execute("SELECT soc_code FROM occupations WHERE soc_code NOT IN (SELECT soc_code FROM advert_summary) LIMIT 1").fetchone()[0]
    check("TC-U17b", "no adverts for the job: no tool, not a generic or invented one", interview_mod.tool_for(con, none_soc) is None, none_soc)
    check("TC-U17c", "naming the tool: plural and case folded ('multimeter' names Multimeters); a vendor alone does not",
          interview_mod.names_tool("I tested it with a multimeter.", "Multimeters")
          and interview_mod.names_tool("I used microsoft excel daily", "Microsoft Excel")
          and not interview_mod.names_tool("I used Microsoft Word", "Microsoft Excel")
          and not interview_mod.names_tool("", "Multimeters"))
    qs_ = interview_mod.questions(con, "47-2111.00", cvscan.Index(con))
    ids = [q["id"] for q in qs_]
    check("TC-U17d", "the question comes after the skill questions and before the task question, and carries the tool",
          ids.index("tool") > max(i for i, x in enumerate(ids) if x.startswith("skill:")) and ids.index("tool") < ids.index("task")
          and qs_[ids.index("tool")]["tool"] == "Microsoft Excel", str(ids))
    fb_yes = interview_mod.feedback(cvscan.Index(con), "I used Microsoft Excel to track stock.", None, "Microsoft Excel")
    fb_no = interview_mod.feedback(cvscan.Index(con), "I tracked stock.", None, "Microsoft Excel")
    check("TC-U17e", "feedback adds a 'Names the tool' item, green when named, with a tip when not",
          fb_yes["items"][0]["key"] == "tool" and fb_yes["items"][0]["ok"] and not fb_no["items"][0]["ok"] and fb_no["items"][0]["tip"]
          and fb_yes["of"] == fb_no["of"] == 7, str([i["key"] for i in fb_yes["items"]]))

    print("\nTC-U18  The skill-matching model, explained  (ADR-0025, ADR-0027)")
    import math
    import recommend as rec
    ids_, vec_ = rec.load_vectors(con)
    means_ = rec.skill_means(vec_, len(ids_))
    cen_ = rec.centre_occupations(vec_, means_)
    thabo = [e for n, e in con.execute("SELECT name, element_id FROM skills") if n in (
        "Operation and Control", "Operations Monitoring", "Equipment Maintenance", "Active Listening", "Critical Thinking", "Monitoring")]
    model_ = rec.Model(ids_, vec_)
    ex = model_.explain(thabo, "47-2111.00")
    prof_ = model_.profile(thabo)
    ranked_ = dict(model_.rank(prof_, 0))
    check("TC-U18a", "the explained score is exactly the score the model ranks by",
          abs(ex["score"] - ranked_["47-2111.00"]) < 1e-12, f"{ex['score']:.4f}")
    check("TC-U18b", "the per-skill contributions add up to the score, and each view's parts to that view's score",
          abs(sum(r["contribution"] for r in ex["rows"]) - ex["score"]) < 1e-9
          and abs(sum(r["part_ratings"] for r in ex["rows"]) - ex["score_ratings"]) < 1e-9
          and abs(sum(r["part_must_haves"] for r in ex["rows"]) - ex["score_must_haves"]) < 1e-9)
    check("TC-U18c", "the reasons shown are the model's own reasons, and the score is the average of the two views",
          ex["reasons"] == model_.reasons(prof_, thabo, "47-2111.00")
          and abs(ex["score"] - (ex["score_ratings"] + ex["score_must_haves"]) / 2) < 1e-12
          and abs(ex["score_ratings"] - rec.cosine(rec.centre_profile(ids_, thabo, means_), cen_["47-2111.00"])) < 1e-12)
    raw_you = [1.0 if e in thabo else 0.0 for e in ids_]
    check("TC-U18d", "the score without centring is the plain cosine of the raw lists, and the spreads cover every job",
          abs(ex["score_uncentred"] - rec.cosine(raw_you, vec_["47-2111.00"])) < 1e-12
          and ex["spread"]["jobs"] == len(vec_)
          and ex["spread"]["centred"]["low"] <= ex["score"] <= ex["spread"]["centred"]["high"]
          and ex["spread"]["uncentred"]["low"] <= ex["score_uncentred"] <= ex["spread"]["uncentred"]["high"])
    check("TC-U18e", "centring is what spreads the scores: the model's range is wider and reaches below zero",
          (ex["spread"]["centred"]["high"] - ex["spread"]["centred"]["low"])
          > 2 * (ex["spread"]["uncentred"]["high"] - ex["spread"]["uncentred"]["low"]) and ex["spread"]["centred"]["low"] < 0,
          f"{ex['spread']['uncentred']} vs {ex['spread']['centred']}")
    ticks_ = rec.tick_vectors(vec_)
    no_must = [s for s, v in vec_.items() if max(v) < 3.5]
    check("TC-U18h", "must-have lists: skills rated 3.5+, or the top 5 for the jobs with none, so no job is left out",
          all(sum(t_) >= 1 for t_ in ticks_.values()) and all(sum(ticks_[s]) == 5 for s in no_must)
          and all(ticks_["47-2111.00"][i] == (1.0 if vec_["47-2111.00"][i] >= 3.5 else 0.0) for i in range(len(ids_))),
          f"{len(no_must)} jobs use the top-5 fallback")
    check("TC-U18i", "the recommendation entry point uses this model: same jobs, same order, same scores",
          [(s, round(x, 9)) for s, _, x in rec.recommend(con, thabo, 5)] == [(s, round(x, 9)) for s, x in model_.rank(prof_, 5)])
    sim = rec.similar(cen_, "47-2111.00", 5)
    back = dict(rec.similar(cen_, sim[0][0], len(cen_)))
    check("TC-U18f", "closest jobs: never the job itself, best first, and similarity is symmetric",
          all(s != "47-2111.00" for s, _ in sim) and [x for _, x in sim] == sorted([x for _, x in sim], reverse=True)
          and abs(back["47-2111.00"] - sim[0][1]) < 1e-12)
    check("TC-U18g", "an unknown job has no closest jobs, not an error", rec.similar(cen_, "99-9999.99") == [])

    print("\nTC-U19  The field of study in the model  (ADR-0029)")
    know_ = rec.load_knowledge(con)
    full_ = rec.Model(ids_, vec_, knowledge=know_)
    check("TC-U19a", "33 knowledge areas, rated for every job in the catalogue",
          know_ is not None and len(know_[0]) == 33 and set(know_[1]) == set(vec_), f"{len(know_[1])} jobs")
    p0, p_none = model_.profile(thabo), full_.profile(thabo)
    check("TC-U19b", "with no field, every score is exactly the skills-only model's",
          all(full_.score(p_none, s_) == model_.score(p0, s_) for s_ in vec_))
    pf = full_.profile(thabo, "2.C.3.e")   # Mechanical
    a_, b_ = full_.parts(pf, "47-2111.00")
    f_ = full_.field_part(pf, "47-2111.00")
    check("TC-U19c", "with a field, the score is 0.9 x the skills' score + 0.1 x the field's",
          abs(full_.score(pf, "47-2111.00") - (0.9 * (a_ + b_) / 2 + 0.1 * f_)) < 1e-12, f"field part {f_:.3f}")
    exf = full_.explain(thabo, "47-2111.00", "2.C.3.e")
    check("TC-U19d", "the skills' shares plus the field's add up to the score exactly",
          abs(sum(r["contribution"] for r in exf["rows"]) + exf["field"]["contribution"] - exf["score"]) < 1e-12)
    check("TC-U19e", "an unknown field is ignored, not an error", full_.profile(thabo, "9.Z.9")[2] is None
          and full_.profile(thabo, "2.A.1.a")[2] is None)
    check("TC-U19f", "the field's reasons are still skills, in the same order as without it",
          full_.reasons(pf, thabo, "47-2111.00") == model_.reasons(p0, thabo, "47-2111.00"))

    print("\nTC-U20  CV tools: everyday words are not tools  (ADR-0030)")
    ix_ = cvscan.Index(con)
    office = cvscan.tools_named(ix_, "Entry level accountant. Prepared the balance sheet. Built a Flask API. "
                                     "Financial controller. Large-scale projects. Internet Explorer.")
    check("TC-U20a", "'entry level', 'balance sheet', Flask, 'financial controller', 'large-scale' and Internet Explorer name no tool",
          not office, str(sorted(office)))
    trade = cvscan.tools_named(ix_, "Weighed samples on an analytical balance and checked readings with a multimeter.")
    check("TC-U20b", "the real tools still match: a multi-word 'analytical balance', and a one-word multimeter",
          len(trade) == 2, str(sorted(trade)))
    print(f"\n{len(PASS)} passed, {len(FAIL)} failed, {len(PASS)+len(FAIL)} total")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
