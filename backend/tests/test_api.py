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
