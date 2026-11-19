"""Integration and system tests -- against the live API over HTTP.

The server must already be running (python -m uvicorn app:app --app-dir backend
--port 8000). Run: python backend/tests/test_api.py

Evidence for Assignment 3 Q5.1 (integration and system testing) and the
traceability matrix (Q2.2). The final block, TC-S01, walks the exact path in
STATUS.md's demo script end to end and checks it against the numbers recorded
there, so this file also re-verifies the rehearsed demo on every run.
"""

import concurrent.futures as cf
import json
import sys
import time
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000"
PASS, FAIL = [], []


def call(method, path, body=None):
    req = urllib.request.Request(
        BASE + path, method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Content-Type": "application/json"} if body is not None else {})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, json.load(e)


def check(test_id, description, condition, detail=""):
    (PASS if condition else FAIL).append((test_id, description, detail))
    mark = "PASS" if condition else "FAIL"
    print(f"  {mark}  {test_id}  {description}" + (f"  -- {detail}" if detail else ""))


def main():
    try:
        call("GET", "/skills")
    except Exception as e:
        sys.exit(f"Server not reachable at {BASE}: {e}\n"
                  "Start it first: python -m uvicorn app:app --app-dir backend --port 8000")

    print("\nTC-I01  Catalogue endpoints  (FR-02, FR-04, FR-05)")
    s, skills = call("GET", "/skills")
    check("TC-I01a", "GET /skills returns 200 and 35 skills", s == 200 and skills["total"] == 35, str(skills.get("total")))
    s, zone3 = call("GET", "/occupations?zone=3&limit=300")
    check("TC-I01b", "GET /occupations?zone=3 returns 209 occupations", s == 200 and zone3["total"] == 209, str(zone3.get("total")))
    s, search = call("GET", "/occupations?q=electric&limit=60")
    check("TC-I01c", "GET /occupations?q=electric finds Electricians",
          s == 200 and any(o["soc_code"] == "47-2111.00" for o in search["occupations"]))
    s, bad = call("GET", "/occupations/99-9999.99")
    check("TC-I01d", "GET /occupations/{bad soc} returns 404", s == 404, str(s))

    print("\nTC-I02  Profile lifecycle  (FR-01, FR-02, FR-03)")
    ids = {sk["name"]: sk["element_id"] for sk in skills["skills"]}
    demo_skills = ["Operation and Control", "Operations Monitoring", "Equipment Maintenance",
                   "Active Listening", "Critical Thinking", "Monitoring"]
    held = [ids[n] for n in demo_skills]
    s, prof = call("POST", "/profiles", {"profile_type": "school_leaver", "skills": held})
    check("TC-I02a", "POST /profiles returns 201 with a profile id", s == 201 and "profile_id" in prof, str(s))
    pid = prof["profile_id"]
    s, tgt = call("PUT", f"/profiles/{pid}/target", {"soc_code": "47-2111.00"})
    check("TC-I02b", "PUT target sets Electricians", s == 200 and tgt["target_soc_code"] == "47-2111.00")
    s, tgt2 = call("PUT", f"/profiles/{pid}/target", {"soc_code": "47-2031.00"})
    s, gap1 = call("GET", f"/profiles/{pid}/gap")
    check("TC-I02c", "PUT target replaces the previous one", gap1["target"]["title"] == "Carpenters")
    call("PUT", f"/profiles/{pid}/target", {"soc_code": "47-2111.00"})  # restore for later checks
    s, e = call("PUT", f"/profiles/{pid}/target", {"soc_code": "99-9999.99"})
    check("TC-I02d", "PUT target with an unknown SOC code returns 404", s == 404, str(s))
    s, e = call("PUT", "/profiles/does-not-exist/target", {"soc_code": "47-2111.00"})
    check("TC-I02e", "PUT target on an unknown profile returns 404", s == 404, str(s))

    print("\nTC-I03  Gap analysis  (FR-07, FR-09)")
    s, gap = call("GET", f"/profiles/{pid}/gap")
    check("TC-I03a", "GET gap returns 200", s == 200)
    check("TC-I03b", "6 skills held out of 34 required", gap["already_held_count"] == 6, str(gap["already_held_count"]))
    check("TC-I03c", "2 essential skills missing", gap["missing_essential_count"] == 2, str(gap["missing_essential_count"]))
    check("TC-I03d", "26 desirable skills missing", gap["missing_desirable_count"] == 26, str(gap["missing_desirable_count"]))
    check("TC-I03e", "every missing skill carries a source date (FR-09)",
          all(m["source_date"] for m in gap["missing"]))

    print("\nTC-I04  Pathway generation  (FR-08)")
    s, pw = call("GET", f"/profiles/{pid}/pathway")
    check("TC-I04a", "GET pathway returns 200", s == 200)
    check("TC-I04b", "at least 3 intermediate steps", pw["intermediate_steps"] >= 3, str(pw["intermediate_steps"]))
    check("TC-I04c", "every step names at least one skill", all(len(st["focus"]) > 0 for st in pw["steps"]))
    check("TC-I04d", "the final step is flagged as the target", pw["steps"][-1]["is_target"] is True)

    print("\nTC-I06  Role sheet: an occupation read against a profile  (FR-04, FR-09)")
    s, occ = call("GET", f"/occupations/47-2111.00?profile_id={pid}")
    check("TC-I06a", "GET occupation with a profile marks which skills are held",
          s == 200 and occ["held_count"] == 6 and sum(sk["held"] for sk in occ["required_skills"]) == 6,
          str(occ.get("held_count")))
    check("TC-I06b", "essential counts agree with the gap (2 of the must-haves missing)",
          occ["essential_count"] - occ["essential_held"] == gap["missing_essential_count"],
          f'{occ.get("essential_count")} - {occ.get("essential_held")}')
    check("TC-I06c", "the description and a plain preparation label travel with it",
          bool(occ["description"]) and bool(occ["preparation"]["label"]))
    s, plain_occ = call("GET", "/occupations/47-2111.00")
    check("TC-I06d", "without a profile, 'held' is null rather than a guess",
          s == 200 and plain_occ["held_count"] is None and plain_occ["required_skills"][0]["held"] is None)
    check("TC-I06f", "the job's most important tasks travel with it, rated ones first (ADR-0007)",
          len(occ["tasks"]) == 8 and occ["task_total"] >= 8 and occ["tasks"][0]["importance"] is not None
          and all(a["importance"] >= b["importance"] for a, b in zip(occ["tasks"], occ["tasks"][1:])
                  if a["importance"] is not None and b["importance"] is not None
                  and a["task_type"] == b["task_type"]),
          f'{len(occ.get("tasks", []))} of {occ.get("task_total")}')
    s, e = call("GET", "/occupations/47-2111.00?profile_id=does-not-exist")
    check("TC-I06e", "an unknown profile returns 404", s == 404, str(s))

    print("\nTC-I05  Recommendation engine  (FR-06, TR-02, TR-03)")
    t0 = time.perf_counter()
    s, rec = call("GET", f"/recommendations?profile_id={pid}&limit=5&max_job_zone=3")
    latency_ms = (time.perf_counter() - t0) * 1000
    check("TC-I05a", "GET recommendations returns 5 results", s == 200 and len(rec["recommendations"]) == 5)
    check("TC-I05b", f"single request completed in {latency_ms:.0f} ms (NFR-01: under 2000 ms)", latency_ms < 2000, f"{latency_ms:.0f} ms")
    check("TC-I05c", "every recommendation carries its job zone", all("job_zone" in r for r in rec["recommendations"]))
    s, empty_prof = call("POST", "/profiles", {"profile_type": "student", "skills": []})
    s, empty_rec = call("GET", f"/recommendations?profile_id={empty_prof['profile_id']}")
    check("TC-I05d", "an empty skill set returns no recommendations with a message (TR-03)",
          empty_rec["recommendations"] == [] and bool(empty_rec.get("message")))

    print("\nTC-I07  Progress: working on it and can do it now  (dashboard, ADR-0005)")
    s, pp = call("POST", "/profiles", {"profile_type": "school_leaver", "skills": held})
    ppid = pp["profile_id"]
    call("PUT", f"/profiles/{ppid}/target", {"soc_code": "47-2111.00"})
    s, dash = call("GET", f"/profiles/{ppid}")
    check("TC-I07a", "GET profile reports readiness 0 of 2 must-haves, 6 of 34 overall",
          s == 200 and (dash["readiness"]["have"], dash["readiness"]["total"],
                        dash["readiness"]["overall_have"], dash["readiness"]["overall_total"]) == (0, 2, 6, 34),
          str(dash.get("readiness")))
    trouble = ids["Troubleshooting"]
    s, r = call("PUT", f"/profiles/{ppid}/skills/{trouble}", {"status": "learning"})
    s, g = call("GET", f"/profiles/{ppid}/gap")
    s, dash = call("GET", f"/profiles/{ppid}")
    check("TC-I07b", "'working on it' is recorded but does not close the gap",
          dash["learning_count"] == 1 and g["missing_essential_count"] == 2,
          f'learning {dash["learning_count"]}, essential missing {g["missing_essential_count"]}')
    s, r = call("PUT", f"/profiles/{ppid}/skills/{trouble}", {"status": "held"})
    s, g = call("GET", f"/profiles/{ppid}/gap")
    s, dash = call("GET", f"/profiles/{ppid}")
    check("TC-I07c", "'can do it now' closes it: 1 must-have left, readiness 1 of 2",
          g["missing_essential_count"] == 1 and dash["readiness"]["have"] == 1 and dash["learning_count"] == 0,
          f'{g["missing_essential_count"]}, {dash["readiness"]["have"]}')
    s, pw2 = call("GET", f"/profiles/{ppid}/pathway")
    check("TC-I07d", "the pathway recomputes and still has 3 steps, each saying whether it is ready",
          s == 200 and pw2["intermediate_steps"] >= 3 and all("ready" in st for st in pw2["steps"]))
    s, r = call("DELETE", f"/profiles/{ppid}/skills/{trouble}")
    s, g = call("GET", f"/profiles/{ppid}/gap")
    check("TC-I07e", "DELETE undoes it: back to 2 must-haves missing", g["missing_essential_count"] == 2,
          str(g["missing_essential_count"]))
    s, e = call("PUT", f"/profiles/{ppid}/skills/{trouble}", {"status": "mastered"})
    check("TC-I07f", "an unknown status is rejected with 422", s == 422, str(s))
    s, e = call("PUT", f"/profiles/{ppid}/skills/9.Z.9", {"status": "held"})
    check("TC-I07g", "an unknown skill returns 404", s == 404, str(s))
    s, e = call("GET", "/profiles/does-not-exist")
    check("TC-I07h", "GET an unknown profile returns 404, so the app can forget a stale id", s == 404, str(s))

    print("\nTC-I08  Search by the names people actually use  (FR-04, ADR-0009)")
    s, alt = call("GET", "/occupations?q=conduit%20installer&limit=60")
    hit = next((o for o in alt["occupations"] if o["soc_code"] == "47-2111.00"), None)
    check("TC-I08a", "'conduit installer' finds Electricians through an alternate title",
          s == 200 and hit is not None and hit["also_called"] == "Conduit Installer", str(hit))
    s, off = call("GET", "/occupations?q=electrician&limit=60")
    check("TC-I08b", "official-title matches still come first and carry no also_called",
          off["occupations"][0]["also_called"] is None and "lectrician" in off["occupations"][0]["title"])
    check("TC-I08c", "every title match is still returned (FR-04's criterion holds)",
          any(o["soc_code"] == "47-2111.00" for o in off["occupations"]))

    print("\nTC-I09  Job page: related jobs, software and tools  (ADR-0009)")
    s, job = call("GET", "/occupations/47-2111.00")
    check("TC-I09a", "related jobs are O*NET's primary related occupations, in review order",
          len(job["related"]) >= 3 and job["related"][0]["title"] == "Helpers--Electricians",
          str([r["title"] for r in job["related"][:2]]))
    check("TC-I09b", "software lists hot technologies first",
          job["technology"] and all(a["hot"] >= b["hot"] for a, b in zip(job["technology"], job["technology"][1:])))
    check("TC-I09c", "tools are grouped by category, largest first, with a total",
          job["tool_total"] == 164 and job["tool_groups"][0]["count"] >= job["tool_groups"][-1]["count"],
          str(job.get("tool_total")))

    print("\nTC-I10  Sign in with a plan code  (ADR-0008)")
    s, named = call("POST", "/profiles", {"profile_type": "school_leaver", "skills": held,
                                          "display_name": "  Thabo  "})
    nid = named["profile_id"]
    s, np_ = call("GET", f"/profiles/{nid}")
    code = np_["plan_code"]
    check("TC-I10a", "a new profile gets a plan code like K7M-2QX and a trimmed first name",
          len(code) == 7 and code[3] == "-" and np_["display_name"] == "Thabo", f"{code} {np_.get('display_name')!r}")
    s, back = call("POST", "/plans/resume", {"plan_code": code.lower().replace("-", " ")})
    check("TC-I10b", "the code reopens the same plan, however it is typed",
          s == 200 and back["profile_id"] == nid, str(back))
    s, e = call("POST", "/plans/resume", {"plan_code": "ZZZ-ZZZ"})
    check("TC-I10c", "an unknown code returns 404 with a plain message", s == 404, str(s))
    s, r = call("PUT", f"/profiles/{nid}/name", {"display_name": ""})
    s, np2 = call("GET", f"/profiles/{nid}")
    check("TC-I10d", "the first name can be cleared -- it is optional", np2["display_name"] is None)
    s, e = call("POST", "/profiles", {"profile_type": "student", "skills": [], "display_name": "x" * 41})
    check("TC-I10e", "a name over 40 characters is rejected", s == 422, str(s))

    print("\nTC-I11  Skill pages and what a skill unlocks  (slice 2)")
    s, sk = call("GET", f"/skills/{ids['Troubleshooting']}")
    check("TC-I11a", "a skill page lists where it matters most, most important first",
          s == 200 and sk["must_have_in"] > 0 and
          all(a["importance"] >= b["importance"] for a, b in zip(sk["top_jobs"], sk["top_jobs"][1:])),
          str(sk.get("must_have_in")))
    s, up = call("POST", "/profiles", {"profile_type": "school_leaver", "skills": held, "target_soc_code": "47-2111.00"})
    uid = up["profile_id"]
    s, r1 = call("PUT", f"/profiles/{uid}/skills/{ids['Troubleshooting']}", {"status": "held"})
    c = r1["changes"]
    check("TC-I11b", "marking Troubleshooting held reports the goal moving 0 -> 1 of 2",
          (c["goal"]["before"], c["goal"]["after"], c["goal"]["total"]) == (0, 1, 2), str(c["goal"]))
    check("TC-I11c", "and names the route step it made ready: Electrical Power-Line Installers",
          [j["soc_code"] for j in c["newly_ready_steps"]] == ["49-9051.00"], str(c["newly_ready_steps"]))
    check("TC-I11d", "the count of jobs with every must-have held rises (102 -> 106)",
          (c["ready_jobs_before"], c["ready_jobs_after"]) == (102, 106),
          f'{c["ready_jobs_before"]} -> {c["ready_jobs_after"]}')
    s, r2 = call("PUT", f"/profiles/{uid}/skills/{ids['Speaking']}", {"status": "learning"})
    check("TC-I11e", "marking a skill 'learning' changes nothing, so reports no changes",
          r2["changes"] is None, str(r2["changes"]))
    s, sk2 = call("GET", f"/skills/{ids['Troubleshooting']}?profile_id={uid}")
    check("TC-I11f", "with a profile, the skill page says where the user stands", sk2["status"] == "held")

    print("\nTC-I12  Saved jobs and comparison  (slice 3, ADR-0010)")
    s, cp = call("POST", "/profiles", {"profile_type": "school_leaver", "skills": held, "target_soc_code": "47-2111.00"})
    cid = cp["profile_id"]
    for soc in ("49-9051.00", "47-2111.00", "49-9051.00"):
        call("PUT", f"/profiles/{cid}/saved/{soc}")
    s, sv = call("GET", f"/profiles/{cid}/saved")
    check("TC-I12a", "saving twice keeps one copy; saved jobs come back with readiness",
          [j["soc_code"] for j in sv["saved"]] == ["49-9051.00", "47-2111.00"]
          and sv["saved"][1]["readiness"] == {"basis": "essential", "total": 2, "have": 0, "ready": False},
          str([j["soc_code"] for j in sv["saved"]]))
    s, occ_s = call("GET", f"/occupations/47-2111.00?profile_id={cid}")
    check("TC-I12b", "a job page says whether it is saved", occ_s["saved"] is True)
    s, cmpd = call("GET", f"/profiles/{cid}/compare?soc=49-9051.00&soc=47-2111.00")
    pl, el = cmpd["jobs"]
    check("TC-I12c", "compare: a job with no essential skills counts its top five, and 'to learn' agrees",
          pl["readiness"]["basis"] == "top_5" and pl["readiness"]["total"] - pl["readiness"]["have"] == len(pl["to_learn"]),
          f'{pl["readiness"]} {pl["to_learn"]}')
    check("TC-I12d", "compare: Electricians still needs Troubleshooting and Repairing",
          sorted(m["name"] for m in el["to_learn"]) == ["Repairing", "Troubleshooting"], str(el["to_learn"]))
    s, e = call("GET", f"/profiles/{cid}/compare?soc=47-2111.00")
    check("TC-I12e", "comparing fewer than two jobs is rejected", s == 422, str(s))
    call("DELETE", f"/profiles/{cid}/saved/47-2111.00")
    s, sv2 = call("GET", f"/profiles/{cid}/saved")
    check("TC-I12f", "unsaving removes it", [j["soc_code"] for j in sv2["saved"]] == ["49-9051.00"])

    print("\nTC-I13  Interest quiz  (slice 4, ADR-0011)")
    s, qz = call("GET", "/interests/quiz")
    from collections import Counter
    check("TC-I13a", "twelve statements, two for each of the six interest areas",
          len(qz["questions"]) == 12 and set(Counter(q["area"] for q in qz["questions"]).values()) == {2})
    s, rm = call("GET", "/interests/match?r=4&limit=10")
    check("TC-I13b", "all-hands-on answers rank jobs whose top area is Realistic first (10 of 10)",
          all(j["areas"][0] == "Hands-on" for j in rm["results"]), str([j["areas"] for j in rm["results"][:3]]))
    check("TC-I13c", "results are ordered by fit, best first",
          all(a["correlation"] >= b["correlation"] for a, b in zip(rm["results"], rm["results"][1:])))
    s, flat = call("GET", "/interests/match?r=2&i=2&a=2&s=2&e=2&c=2")
    check("TC-I13d", "answers that lean nowhere get a message, not a meaningless ranking",
          flat["results"] == [] and bool(flat["message"]))
    s, z3 = call("GET", "/interests/match?s=4&max_job_zone=3&limit=20")
    check("TC-I13e", "the school-leaver filter keeps every result at Job Zone 3 or below",
          all(j["job_zone"] <= 3 for j in z3["results"]))
    s, sm = call("GET", f"/interests/match?r=4&profile_id={pid}")
    check("TC-I13f", "with a profile, each result also carries a skill-match label",
          all(j["skill_match"] for j in sm["results"]))

    print("\nTC-I14  Progress history  (slice 5, ADR-0012)")
    s, hp = call("POST", "/profiles", {"profile_type": "school_leaver", "skills": held})
    hid = hp["profile_id"]
    call("PUT", f"/profiles/{hid}/target", {"soc_code": "47-2111.00"})
    call("PUT", f"/profiles/{hid}/target", {"soc_code": "47-2111.00"})   # same goal again: not an event
    call("PUT", f"/profiles/{hid}/skills/{ids['Troubleshooting']}", {"status": "learning"})
    call("PUT", f"/profiles/{hid}/skills/{ids['Troubleshooting']}", {"status": "held"})
    call("DELETE", f"/profiles/{hid}/skills/{ids['Troubleshooting']}")
    s, hist = call("GET", f"/profiles/{hid}/history")
    kinds = [(e["kind"], e["status"]) for e in hist["events"]]
    check("TC-I14a", "every change is recorded once, newest first; re-setting the same goal is not",
          kinds == [("skill", None), ("skill", "held"), ("skill", "learning"), ("goal", None), ("started", None)],
          str(kinds))
    check("TC-I14b", "each event carries the goal's readiness at that moment: 0, 0, 1, then 0 again",
          [e["goal_have"] for e in reversed(hist["events"])][1:] == [0, 0, 1, 0],
          str([e["goal_have"] for e in reversed(hist["events"])]))
    check("TC-I14c", "the start event records how many skills the plan began with",
          hist["events"][-1]["skill_count"] == 6)

    print("\nTC-I15  FR-09 on the newer screens: dataset and record dates")
    import re as _re
    dated = lambda ds: bool(ds) and all(_re.fullmatch(r"\d{2}/\d{4}", d) for d in ds)
    s, jp = call("GET", "/occupations/47-2111.00")
    check("TC-I15a", "job page: dataset plus the dates of its skill ratings and tasks",
          bool(jp["provenance"]["dataset"]) and dated(jp["provenance"]["skill_rating_dates"])
          and dated(jp["provenance"]["task_dates"]), str(jp["provenance"]))
    s, sp = call("GET", f"/skills/{ids['Troubleshooting']}")
    check("TC-I15b", "skill page: every listed job's rating carries its date, and the dates are listed",
          all(j["source_date"] for j in sp["top_jobs"]) and dated(sp["rating_dates"]))
    s, cm = call("GET", f"/profiles/{pid}/compare?soc=49-9051.00&soc=47-2111.00")
    check("TC-I15c", "compare: each job carries its rating dates, and the dataset is named",
          bool(cm["dataset"]) and all(dated(j["rating_dates"]) for j in cm["jobs"]))
    s, im = call("GET", "/interests/match?r=4&limit=5")
    check("TC-I15d", "quiz results: each job's interest profile carries its date",
          bool(im["dataset"]) and all(_re.fullmatch(r"\d{2}/\d{4}", j["source_date"]) for j in im["results"]))

    print("\nTC-I16  FR-06: each recommendation says why")
    s, why = call("GET", f"/recommendations?profile_id={pid}&limit=5&max_job_zone=3")
    reasons = [r["because"] for r in why["recommendations"]]
    check("TC-I16a", "every recommendation names 1-3 reasons, all of them skills the user holds",
          all(1 <= len(b) <= 3 and set(b) <= set(demo_skills) for b in reasons), str(reasons[:2]))
    check("TC-I16b", "skills every job needs (Active Listening, Critical Thinking) are never offered as a reason",
          not any({"Active Listening", "Critical Thinking"} & set(b) for b in reasons))
    check("TC-I16c", "the ranking itself is unchanged: still five, best first",
          len(why["recommendations"]) == 5 and all(a["score"] >= b["score"] for a, b in
              zip(why["recommendations"], why["recommendations"][1:])))

    print("\nTC-I17  FR-08: each route step says why it is there")
    s, rw = call("GET", f"/profiles/{pid}/pathway")
    closes = [st["closeness"] for st in rw["steps"][:-1]]
    check("TC-I17a", "the intermediate steps are ordered by their closeness score, closest first",
          all(a >= b for a, b in zip(closes, closes[1:])), str([round(c, 3) for c in closes]))
    check("TC-I17b", "each step says how many of its skills the user has, and labels its closeness",
          all(st["required_count"] > 0 and 0 <= st["held_count"] <= st["required_count"] and st["closeness_label"]
              for st in rw["steps"]))
    check("TC-I17c", "the demo route is unchanged", [st["soc_code"] for st in rw["steps"]] ==
          ["47-2011.00", "49-9051.00", "49-2094.00", "47-2111.00"], str([st["soc_code"] for st in rw["steps"]]))

    print("\nTC-I18  CV scanner endpoint  (ADR-0014)")
    sample_cv = ("Career objective: become an electrician.\nMatric with Mathematics and Physical Science.\n"
                 "- Helped install wiring and plug points.\n- Fixed broken bicycles for neighbours.\n"
                 "Skills: multimeter, soldering irons, Microsoft Excel, working in a team. Phone 072 555 0134")
    s, before_scan = call("GET", f"/profiles/{pid}")
    s, cvr = call("POST", "/cv/scan", {"text": sample_cv, "profile_id": pid})
    sug = {x["name"]: x for x in cvr["suggestions"]}
    check("TC-I18a", "suggests Repairing and Installation, quoting the lines, and marks skills already held",
          s == 200 and "Repairing" in sug and "Installation" in sug and "wiring" in sug["Installation"]["evidence"]
          and sug.get("Coordination", {}).get("status") in (None, "held"), str(sorted(sug)))
    g = cvr["goal"]
    check("TC-I18b", "with a profile, the goal check uses the profile's goal (Electricians) and names its evidence",
          g and g["soc_code"] == "47-2111.00" and "Multimeters" in g["named_for_this_job"]
          and "Microsoft Excel" in g["named_for_this_job"], str(g and g["named_for_this_job"]))
    check("TC-I18c", "the response says the CV was not stored", cvr["stored"] is False)
    s, after_scan = call("GET", f"/profiles/{pid}")
    s, hist_scan = call("GET", f"/profiles/{pid}/history")
    check("TC-I18d", "scanning changes nothing on the profile: same skills, same history, nothing added",
          before_scan == after_scan and not any(e["kind"] == "skill" and e["element_id"] == sug["Repairing"]["element_id"]
                                                for e in hist_scan["events"]))
    s, e = call("POST", "/cv/scan", {"text": "too short"})
    check("TC-I18e", "a too-short CV is rejected with 422", s == 422, str(s))
    s, e = call("POST", "/cv/scan", {"text": "x" * 15001})
    check("TC-I18f", "a CV over 15,000 characters is rejected with 422", s == 422, str(s))
    s, nog = call("POST", "/cv/scan", {"text": sample_cv})
    check("TC-I18g", "without a profile or job there are suggestions but no goal check",
          s == 200 and nog["goal"] is None and len(nog["suggestions"]) > 0)

    print("\nTC-I19  Interview practice  (ADR-0015)")
    s, iq = call("GET", f"/interview/questions?profile_id={pid}")
    kinds = [q["kind"] for q in iq["questions"]]
    check("TC-I19a", "questions for the profile's goal: an opener, one per must-have, a tool where adverts name one (ADR-0024), one from a task",
          s == 200 and iq["soc_code"] == "47-2111.00" and kinds == ["opener", "skill", "skill", "tool", "task"]
          and {q["skill"]["name"] for q in iq["questions"] if q["skill"]} == {"Troubleshooting", "Repairing"},
          str(kinds))
    sq = next(q for q in iq["questions"] if q["kind"] == "skill")
    s, ifb = call("POST", "/interview/feedback", {"answer": "I fixed it.", "skill_element_id": sq["skill"]["element_id"]})
    check("TC-I19b", "feedback returns a checklist with tips for what is missing, and is not stored",
          s == 200 and ifb["stored"] is False and ifb["met"] < ifb["of"]
          and all(i["tip"] for i in ifb["items"] if not i["ok"]))
    s, e = call("GET", "/interview/questions")
    check("TC-I19c", "questions without a job or a profile goal return 400", s == 400, str(s))
    s, e = call("POST", "/interview/feedback", {"answer": "x", "skill_element_id": "9.Z.9"})
    check("TC-I19d", "an unknown skill returns 404", s == 404, str(s))

    print("\nTC-I20  What employers ask for  (module 4, ADR-0017)")
    s, ad = call("GET", f"/occupations/47-2111.00/adverts?profile_id={pid}")
    if s == 200 and not ad["loaded"]:
        # Optional data (backend/data/linkedin is gitignored): say so, and go on
        # to the demo-path system test rather than crash.
        print("  SKIP  TC-I20  advert data not loaded (run python backend/load_adverts.py)")
    else:
        check("TC-I20a", "Electricians: enough linked adverts, labelled US with the listing month, closed, dataset named",
              s == 200 and ad["enough"] and ad["adverts"] >= 50 and "United States" in ad["note"]
              and ad["period"] in ad["note"] and "closed" in ad["note"] and "CC BY-SA" in ad["dataset"],
              f"{ad.get('adverts')} adverts, {ad.get('period')}")
        reqs = ad.get("requirements", [])
        check("TC-I20b", "a licence or certificate is the commonest requirement; shares come as words",
              bool(reqs) and reqs[0]["key"] == "licence"
              and all(" in 10" in r["words"] or r["words"] in ("a few", "almost all") for r in reqs),
              str([(r["key"], r["words"]) for r in reqs]))
        _, prof = call("GET", f"/profiles/{pid}")
        held_ids = {k["element_id"] for k in prof["skills"] if k["status"] == "held"}
        skills = ad.get("skills", [])
        check("TC-I20c", "skills stressed include Troubleshooting and Repairing, each lifted 1.5x+, marked from the profile",
              {"Troubleshooting", "Repairing"} <= {k["name"] for k in skills}
              and all(k["lift"] >= 1.5 for k in skills)
              and all((k["status"] == "held") == (k["element_id"] in held_ids) for k in skills),
              str([(k["name"], k["status"]) for k in skills]))
        check("TC-I20d", "only counts and titles come back -- no advert text, companies or links",
              not any(key in json.dumps(ad).lower() for key in ("description", "company_name", "job_posting_url", "http")))
        check("TC-I20h", "beginners are counted over adverts that state a level, never more than all adverts",
              ad["entry_level"] <= ad["levels_stated"] <= ad["adverts"],
              f"{ad['entry_level']}/{ad['levels_stated']}/{ad['adverts']}")
        # Which jobs have too few or no adverts is a fact of the data, so look it up.
        import sqlite3
        from pathlib import Path
        dbc = sqlite3.connect(Path(__file__).resolve().parents[1] / "saycep.db")
        few_soc = dbc.execute("SELECT soc_code FROM advert_summary WHERE adverts < 5 ORDER BY soc_code LIMIT 1").fetchone()[0]
        none_soc = dbc.execute("SELECT soc_code FROM occupations WHERE soc_code NOT IN "
                               "(SELECT soc_code FROM advert_summary) ORDER BY soc_code LIMIT 1").fetchone()[0]
        dbc.close()
        s, few = call("GET", f"/occupations/{few_soc}/adverts")
        check("TC-I20e", "an occupation with 1-4 adverts says there are too few, with no lists",
              s == 200 and 0 < few["adverts"] < 5 and few["enough"] is False and "requirements" not in few,
              f"{few_soc}: {few.get('adverts')}")
        s, none = call("GET", f"/occupations/{none_soc}/adverts")
        check("TC-I20f", "an occupation with no linked adverts returns 0, not an error",
              s == 200 and none["adverts"] == 0, none_soc)
    s, e = call("GET", "/occupations/99-9999.99/adverts")
    check("TC-I20g", "an unknown occupation returns 404", s == 404, str(s))

    print("\nTC-I21  Jobs for you: sample listings  (module 4, ADR-0022)")
    s, lp = call("POST", "/profiles", {"profile_type": "school_leaver", "skills": held})
    lpid = lp["profile_id"]
    s, none_yet = call("GET", f"/profiles/{lpid}/listings")
    check("TC-I21a", "no goal yet: no listings, not an error", s == 200 and none_yet["listings"] == [], str(s))
    call("PUT", f"/profiles/{lpid}/target", {"soc_code": "47-2111.00"})
    s, jl = call("GET", f"/profiles/{lpid}/listings?limit=40")
    if s == 200 and not jl["loaded"]:
        print("  SKIP  TC-I21  listings not loaded (run python backend/load_listings.py)")
    else:
        _, lpw = call("GET", f"/profiles/{lpid}/pathway")
        items = jl["listings"]
        check("TC-I21b", "listings come from the goal and the jobs on the route, and only those",
              set(jl["occupations"]) == {st["soc_code"] for st in lpw["steps"]}
              and items and {x["soc_code"] for x in items} <= set(jl["occupations"]), str(jl["occupations"]))
        check("TC-I21c", "every listing is labelled: US adverts, demo data, closed, not openings; dataset named",
              all(w in jl["note"] for w in ("United States", "demo data", "closed", "not openings")) and "CC BY-SA" in jl["dataset"])
        shares = [x["fit"]["have"] / x["fit"]["mentioned"] if x["fit"]["mentioned"] else 0 for x in items]
        check("TC-I21d", "best fit first: the share of named skills held never rises down the list",
              all(a >= b for a, b in zip(shares, shares[1:])), str([round(v, 2) for v in shares[:6]]))
        check("TC-I21e", "fit counts agree with the skills listed and the profile",
              all(x["fit"]["have"] == sum(k["status"] == "held" for k in x["skills"]) for x in items))
        check("TC-I21f", "no advert text, company, link or pay comes back",
              not any(k in json.dumps(jl).lower() for k in ("description", "company", "http", "salary")))
        s, one = call("GET", f"/occupations/47-2111.00/listings?profile_id={lpid}&limit=3")
        check("TC-I21g", "a job page gets at most the limit, all for that job",
              s == 200 and 0 < len(one["listings"]) <= 3 and all(x["soc_code"] == "47-2111.00" for x in one["listings"]))
    s, _ = call("GET", "/occupations/99-9999.99/listings")
    check("TC-I21h", "an unknown occupation returns 404", s == 404, str(s))

    print("\nTC-I22  CV advice and the technical interview question  (ADR-0024)")
    weak_cv = ("Lerato Nkosi. Matric 2023. Shop assistant at Pick n Pay: served customers at the till, kept stock records. "
               "Volunteer: replaced plugs in the community hall.")
    s, sc = call("POST", "/cv/scan", {"text": weak_cv, "soc_code": "47-2111.00"})
    add = sc["goal"]["add"] if s == 200 and sc.get("goal") else []
    check("TC-I22a", "a CV scan with a goal returns what to add: requirements, then skills, each with a reason and an example",
          s == 200 and add and all(x["kind"] in ("requirement", "tool", "skill") and x["why"] and x["example"] for x in add)
          and {x["kind"] for x in add} >= {"requirement", "skill"}, str([(x["kind"], x["title"]) for x in add]))
    adv_ok = repository_has_adverts = "adverts" in json.dumps(add)
    check("TC-I22b", "advert figures say how many US adverts, and when",
          all("US adverts for this job (" in x["why"] for x in add if x["kind"] != "skill"))
    s, lic = call("POST", "/cv/scan", {"text": weak_cv + " I hold a trade certificate and a Code 8 driver's licence.", "soc_code": "47-2111.00"})
    check("TC-I22c", "naming a licence in the CV removes the licence advice",
          s == 200 and not [x for x in lic["goal"]["add"] if x["title"] in ("A trade licence or certificate", "A driver's licence")],
          str([x["title"] for x in lic["goal"]["add"]]))
    s, nogoal = call("POST", "/cv/scan", {"text": weak_cv})
    check("TC-I22d", "no goal, no advice: goal stays empty and nothing is stored", s == 200 and nogoal["goal"] is None and nogoal["stored"] is False)
    import sqlite3
    from pathlib import Path
    dbc = sqlite3.connect(Path(__file__).resolve().parents[1] / "saycep.db")
    no_adverts = dbc.execute("SELECT soc_code FROM occupations WHERE soc_code NOT IN (SELECT soc_code FROM advert_summary) AND soc_code IN "
                             "(SELECT soc_code FROM occupation_skills) ORDER BY soc_code LIMIT 1").fetchone()[0]
    dbc.close()
    s, na = call("POST", "/cv/scan", {"text": weak_cv, "soc_code": no_adverts})
    check("TC-I22e", "a job with no adverts: skill advice only, and no advert figure claimed",
          s == 200 and na["goal"]["add"] and all(x["kind"] == "skill" for x in na["goal"]["add"]), no_adverts)
    s, iq = call("GET", "/interview/questions?soc_code=47-2111.00")
    tq = [q for q in iq.get("questions", []) if q["id"] == "tool"]
    check("TC-I22f", "Electricians get a technical question about a tool the adverts name, after the skill questions",
          s == 200 and len(tq) == 1 and tq[0]["tool"] in tq[0]["text"] and iq["questions"][-1]["id"] == "task", str(tq))
    s, nq = call("GET", f"/interview/questions?soc_code={no_adverts}")
    check("TC-I22g", "a job with no adverts gets no technical question", s == 200 and all(q["id"] != "tool" for q in nq["questions"]))
    s, f1 = call("POST", "/interview/feedback", {"answer": "Last year I used " + tq[0]["tool"] + " at school to track the club's stock list. I made a sheet and it saved us time.", "tool": tq[0]["tool"]})
    s, f2 = call("POST", "/interview/feedback", {"answer": "Last year at school I tracked the club's stock list by hand. I made a list and it saved us time.", "tool": tq[0]["tool"]})
    check("TC-I22h", "feedback checks the tool is named: green when it is, a tip when it isn't",
          s == 200 and f1["items"][0]["key"] == "tool" and f1["items"][0]["ok"] and not f2["items"][0]["ok"] and f2["items"][0]["tip"])
    s, _ = call("POST", "/interview/feedback", {"answer": "x" * 10, "tool": "t" * 200})
    check("TC-I22i", "an over-long tool name is refused (422), never stored", s == 422, str(s))

    print("\nTC-I23  The skill-matching model, made visible  (ADR-0025)")
    s, mp = call("POST", "/profiles", {"profile_type": "school_leaver", "skills": held})
    mpid = mp["profile_id"]
    s, rec5 = call("GET", f"/recommendations?profile_id={mpid}&limit=5&max_job_zone=3")
    top = rec5["recommendations"][0]
    s, mx = call("GET", f"/profiles/{mpid}/match/{top['soc_code']}")
    check("TC-I23a", "How we matched you: the same score, match words and reasons as the For you list",
          s == 200 and mx["explained"] and mx["score"] == top["score"] and mx["match"] == top["match"]
          and mx["because"] == top["because"], f"{top['title']}: {mx.get('score')} vs {top['score']}")
    check("TC-I23b", "it carries all 35 skills, each with the job's rating, its centred value, yours and the product",
          len(mx["skills"]) == 35 and all({"importance", "job_centred", "you_centred", "contribution", "held", "group"} <= set(k) for k in mx["skills"])
          and sum(k["held"] for k in mx["skills"]) == len(held))
    check("TC-I23c", "with and without centring, and the range across every job",
          mx["spread"]["jobs"] >= 800 and mx["spread"]["centred"]["low"] < 0 < mx["spread"]["uncentred"]["low"]
          and "score_uncentred" in mx, str(mx["spread"]))
    s, e1 = call("GET", f"/profiles/{mpid}/match/99-9999.99")
    s2, e2 = call("GET", "/profiles/nobody/match/47-2111.00")
    check("TC-I23d", "an unknown job or profile returns 404", s == 404 and s2 == 404, f"{s}, {s2}")
    s, ep = call("POST", "/profiles", {"profile_type": "student", "skills": [held[0]]})
    call("DELETE", f"/profiles/{ep['profile_id']}/skills/{held[0]}")
    s, em = call("GET", f"/profiles/{ep['profile_id']}/match/47-2111.00")
    check("TC-I23e", "a profile with no skills gets a message, not an error", s == 200 and em["explained"] is False and em["message"], str(em.get("message")))
    s, sj = call("GET", "/occupations/47-2111.00/similar")
    check("TC-I23f", "closest jobs: five, best first, never the job itself, each marked if O*NET's experts also list it",
          s == 200 and len(sj["similar"]) == 5 and all(x["soc_code"] != "47-2111.00" for x in sj["similar"])
          and [x["score"] for x in sj["similar"]] == sorted([x["score"] for x in sj["similar"]], reverse=True)
          and any(x["expert_listed"] for x in sj["similar"]), str([(x["title"][:20], x["expert_listed"]) for x in sj["similar"]]))
    s, _ = call("GET", "/occupations/99-9999.99/similar")
    check("TC-I23g", "closest jobs for an unknown job: 404", s == 404, str(s))
    s, pt = call("POST", "/cv/scan", {"text": "I fixed bicycles and repaired small appliances for neighbours. I installed plug points with my uncle.",
                                      "profile_id": mpid})
    _, zones = call("GET", "/occupations?zone=4&limit=1")
    check("TC-I23h", "Jobs your CV points to: ranked by the same engine, with reasons, within Job Zones 1-3 for a school-leaver",
          s == 200 and pt["points_to"] and all(x["job_zone"] <= 3 and x["because"] for x in pt["points_to"])
          and [x["score"] for x in pt["points_to"]] == sorted([x["score"] for x in pt["points_to"]], reverse=True),
          str([(x["title"][:25], x["job_zone"]) for x in pt["points_to"]]))
    s, nopt = call("POST", "/cv/scan", {"text": "Hello, my name is Sipho and I am looking for work in Pretoria."})
    check("TC-I23i", "a CV that shows no skills points to no jobs, and nothing is added to a profile",
          s == 200 and nopt["points_to"] == [] and nopt["stored"] is False)

    print("\nTC-I24  A student's field of study  (ADR-0029)")
    s, ka = call("GET", "/knowledge-areas")
    check("TC-I24a", "the 33 O*NET knowledge areas, each with O*NET's description and plain examples",
          s == 200 and len(ka["areas"]) == 33 and all(a["description"] and a["examples"] for a in ka["areas"])
          and ka["weight"] == 0.1, f"{len(ka.get('areas', []))} areas")
    comp = "2.C.3.a"   # Computers and Electronics
    s, fp = call("POST", "/profiles", {"profile_type": "student", "skills": held, "field_element_id": comp})
    fpid = fp["profile_id"]
    s, nf = call("POST", "/profiles", {"profile_type": "student", "skills": held})
    s, g = call("GET", f"/profiles/{fpid}")
    check("TC-I24b", "a profile can be created with a field, and reads it back with its name",
          s == 200 and g["field"] == {"element_id": comp, "name": "Computers and Electronics"}, str(g.get("field")))
    s, bad = call("POST", "/profiles", {"profile_type": "student", "skills": held, "field_element_id": "9.Z.9"})
    s2, _ = call("PUT", f"/profiles/{fpid}/field", {"element_id": "2.A.1.a"})   # a skill, not a knowledge area
    check("TC-I24c", "an unknown field is refused (422), whether at creation or later", s == 422 and s2 == 422, f"{s}, {s2}")
    s, rf = call("GET", f"/recommendations?profile_id={fpid}&limit=10")
    s, rn = call("GET", f"/recommendations?profile_id={nf['profile_id']}&limit=10")
    check("TC-I24d", "recommendations say which field they used, and the field changes the scores",
          rf["field"]["name"] == "Computers and Electronics" and rn["field"] is None
          and [x["score"] for x in rf["recommendations"]] != [x["score"] for x in rn["recommendations"]])
    soc = rf["recommendations"][0]["soc_code"]
    s, mf = call("GET", f"/profiles/{fpid}/match/{soc}")
    check("TC-I24e", "How we matched you: the same score as the list, and the skills' shares plus the field's add up to it",
          mf["score"] == rf["recommendations"][0]["score"] and mf["field"]["name"] == "Computers and Electronics"
          and abs(sum(k["contribution"] for k in mf["skills"]) + mf["field"]["contribution"] - mf["score"]) < 0.002
          and abs(0.9 * mf["score_skills"] + 0.1 * mf["field"]["score"] - mf["score"]) < 0.002, str(mf["field"]))
    s, mn = call("GET", f"/profiles/{nf['profile_id']}/match/{soc}")
    check("TC-I24f", "without a field the explanation has none, and the score is the skills' score",
          mn["field"] is None and mn["score"] == mn["score_skills"])
    s, cl = call("PUT", f"/profiles/{fpid}/field", {"element_id": None})
    s, rc = call("GET", f"/recommendations?profile_id={fpid}&limit=10")
    check("TC-I24g", "clearing the field puts the scores back exactly as without one",
          s == 200 and cl["field"] is None and rc["recommendations"] == rn["recommendations"])
    call("PUT", f"/profiles/{fpid}/field", {"element_id": comp})
    call("PUT", f"/profiles/{fpid}/target", {"soc_code": "15-1251.00"})
    call("PUT", f"/profiles/{nf['profile_id']}/target", {"soc_code": "15-1251.00"})
    s, pw = call("GET", f"/profiles/{fpid}/pathway")
    check("TC-I24h", "the Pathway still builds with a field (its order uses the same model)",
          s == 200 and pw["target"]["soc_code"] == "15-1251.00", str(s))
    s, nope = call("PUT", "/profiles/nobody/field", {"element_id": comp})
    check("TC-I24i", "setting the field of an unknown profile: 404", s == 404, str(s))
    s, jf = call("GET", f"/knowledge-areas/{comp}/jobs?profile_id={fpid}&limit=20")
    imps = [j["importance"] for j in jf["jobs"]]
    check("TC-I24j", "jobs in your field: 20, most-needed first, each with O*NET's rating, its label and a skills match",
          s == 200 and len(jf["jobs"]) == 20 and imps == sorted(imps, reverse=True)
          and all(j["need"] and j["preparation"]["label"] and j["skill_match"] for j in jf["jobs"])
          and jf["field"]["name"] == "Computers and Electronics", f"{jf['jobs'][0]['title']} {imps[0]}")
    s, jn = call("GET", f"/knowledge-areas/{comp}/jobs?limit=5")
    s2, _ = call("GET", "/knowledge-areas/9.Z.9/jobs")
    check("TC-I24k", "without a profile there's no skills match; an unknown area is refused (422)",
          s == 200 and len(jn["jobs"]) == 5 and all(j["skill_match"] is None for j in jn["jobs"]) and s2 == 422, f"{s}, {s2}")

    print("\nTC-S01  System test: the rehearsed demo path, start to finish")
    s, sprof = call("POST", "/profiles", {"profile_type": "school_leaver", "skills": held})
    spid = sprof["profile_id"]
    call("PUT", f"/profiles/{spid}/target", {"soc_code": "47-2111.00"})
    s, sgap = call("GET", f"/profiles/{spid}/gap")
    s, spw = call("GET", f"/profiles/{spid}/pathway")
    check("TC-S01a", "fresh run of the demo profile reproduces 6/2/26",
          (sgap["already_held_count"], sgap["missing_essential_count"], sgap["missing_desirable_count"]) == (6, 2, 26))
    check("TC-S01b", "fresh run reproduces a 3-step pathway to Electricians",
          spw["intermediate_steps"] == 3 and spw["target"]["title"] == "Electricians")

    print("\nTC-N01  Concurrency (NFR-01, the connection-per-request fix)")
    paths = [f"/recommendations?profile_id={pid}&limit=5&max_job_zone=3", "/occupations?zone=3&limit=300",
             "/occupations?q=electric&limit=60", "/skills"] * 5
    with cf.ThreadPoolExecutor(8) as ex:
        results = list(ex.map(lambda p: call("GET", p)[0], paths))
    check("TC-N01a", f"20 concurrent requests, {results.count(200)} succeeded", results.count(200) == 20, str(results))

    print(f"\n{len(PASS)} passed, {len(FAIL)} failed, {len(PASS)+len(FAIL)} total")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
