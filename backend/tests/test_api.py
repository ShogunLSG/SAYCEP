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
