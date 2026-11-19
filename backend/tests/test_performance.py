"""Performance and emerging-technology measurements.

Reproduces every quantitative claim in the Assignment 2 requirements and the
Assignment 3 evaluation, so none of them rests on a number typed into a
document. Needs the API running for PT-03.

Run: python backend/tests/test_performance.py

  PT-01  TR-01  recommendation accuracy (occupational-family agreement)
  PT-01b TR-01  the same with the target removed, over every occupation (stricter)
  PT-02  TR-02  recommendation inference latency
  PT-05  ADR-0025  job-to-job similarity agrees with O*NET's expert lists (a second, independent check)
  PT-06  ADR-0029  PT-01b with a field of study added (simulated), against the same people without one
  PT-03  NFR-01 end-to-end API response time, over HTTP
  PT-04  NFR-04 full database rebuild time
"""

import json
import random
import statistics
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

import recommend
import repository

PASS, FAIL = [], []


def check(test_id, description, condition, detail=""):
    (PASS if condition else FAIL).append(test_id)
    print(f"  {'PASS' if condition else 'FAIL'}  {test_id}  {description}  -- {detail}")


def main():
    con = repository.connect()
    skill_ids, vectors = recommend.load_vectors(con)
    means = recommend.skill_means(vectors, len(skill_ids))
    centred = recommend.centre_occupations(vectors, means)     # the ratings view: PT-05 (job to job)
    model = recommend.Model(skill_ids, vectors)                # the shipped model (ADR-0027): PT-01, 01b, 02
    socs = list(vectors)
    rng = random.Random(42)  # fixed seed: the same sample every run

    def essential(soc):
        return [e for e, _ in con.execute(
            "SELECT element_id, importance FROM occupation_skills "
            "WHERE soc_code = ? AND importance >= 3.5", (soc,))]

    print("\nPT-01  TR-01 accuracy against a random baseline of the SAME metric")
    targets = [soc for soc in rng.sample(socs, 150) if essential(soc)]
    any_hit, share = [], []
    for soc in targets:
        top = [s for s, _ in model.rank(model.profile(essential(soc)), 5)]
        same = sum(s[:2] == soc[:2] for s in top)
        any_hit.append(same > 0)
        share.append(same / 5)
    # Baseline: 2,000 random draws of five occupations per target, excluding
    # the target itself. Assignment 2 compared the any-of-five rate against a
    # mean-share baseline. They are different metrics, so each is reported
    # here against its own baseline.
    base = random.Random(7)
    r_any, r_share = [], []
    for soc in targets:
        pool = [x for x in socs if x != soc]
        for _ in range(2000):
            same = sum(x[:2] == soc[:2] for x in base.sample(pool, 5))
            r_any.append(same > 0)
            r_share.append(same / 5)
    acc = statistics.mean(any_hit) * 100
    # Since ADR-0027 the must-have view finds the target job itself almost every
    # time, so PT-01 (which lets the target count) is flattering by design.
    # Quote PT-01b, which removes the target.
    check("PT-01", f"(target may count, so flattering: quote PT-01b) at least one of top 5 in family: {acc:.1f}% vs random {statistics.mean(r_any)*100:.1f}% "
          f"({statistics.mean(any_hit)/statistics.mean(r_any):.1f}x), n={len(targets)} (target >= 55%)",
          acc >= 55,
          f"mean family share {statistics.mean(share)*100:.1f}% vs random {statistics.mean(r_share)*100:.1f}% "
          f"({statistics.mean(share)/statistics.mean(r_share):.1f}x)")

    # PT-01b: the stricter reading, over every occupation, not a sample of 150.
    # PT-01 lets the target occupation appear in its own top five (it does in
    # 20% of cases), which a marker can fairly call flattering. Here the target is
    # removed and the next five are used. The random baseline is exact: the
    # chance that five draws from the other 878 include a family member.
    import math
    every = {}
    for soc, e, imp in con.execute("SELECT soc_code, element_id, importance FROM occupation_skills WHERE importance >= 3.5"):
        every.setdefault(soc, []).append(e)
    family = {}
    for soc in socs:
        family[soc[:2]] = family.get(soc[:2], 0) + 1
    hits, chance = [], []
    for soc, held in every.items():
        ranked = model.rank(model.profile(held), 0)
        hits.append(any(x[:2] == soc[:2] for x, _ in [r for r in ranked if r[0] != soc][:5]))
        k, n_other = family[soc[:2]] - 1, len(socs) - 1
        chance.append(1 - math.comb(n_other - k, 5) / math.comb(n_other, 5))
    acc_b, base_b = statistics.mean(hits) * 100, statistics.mean(chance) * 100
    boot = random.Random(3)
    means_b = sorted(statistics.mean(boot.choices(hits, k=len(hits))) * 100 for _ in range(1000))
    check("PT-01b", f"target removed, all {len(every)} occupations with must-haves: {acc_b:.1f}% vs random {base_b:.1f}% "
          f"({acc_b / base_b:.1f}x) (target >= 55%)", acc_b >= 55,
          f"95% interval {means_b[25]:.1f} to {means_b[974]:.1f}; the target may not count as a recommendation of itself")

    # PT-05: a second, independent check of the engine (ADR-0025). For each job,
    # its five closest jobs by centred skill vectors, compared with the related
    # jobs O*NET's experts list for it (primary tier). No requirement sets a
    # target for this, so the gate is only "well above chance" (3x); the figure
    # is reported, not tuned. The random baseline is exact, as in PT-01b.
    print("\nPT-05  Job-to-job similarity against O*NET's expert lists of related jobs")
    expert = {}
    for soc, rel in con.execute("SELECT soc_code, related_soc_code FROM related_occupations WHERE tier LIKE 'Primary%'"):
        if soc in centred and rel in centred and rel != soc:
            expert.setdefault(soc, set()).add(rel)
    hit5, share5, chance5 = [], [], []
    for soc, rel in expert.items():
        top = [o for o, _ in recommend.similar(centred, soc, 5)]
        n_hit = len(set(top) & rel)
        hit5.append(n_hit > 0)
        share5.append(n_hit / 5)
        n_other = len(socs) - 1
        chance5.append(1 - math.comb(n_other - len(rel), 5) / math.comb(n_other, 5))
    acc5, base5 = statistics.mean(hit5) * 100, statistics.mean(chance5) * 100
    check("PT-05", f"top 5 includes an expert-listed related job for {acc5:.1f}% of {len(expert)} jobs, vs random {base5:.1f}% "
          f"({acc5 / base5:.1f}x)", acc5 >= 3 * base5,
          f"share of the top 5 the experts list: {statistics.mean(share5) * 100:.1f}%; no requirement sets a target")

    # PT-06: the field of study (ADR-0029). PT-01b's people again, now also
    # giving a field: either the job's top knowledge area, or (noisier) one of
    # its top three at random. Same metric, same people, so the difference is
    # the field's alone. The field is simulated from the job itself, which is
    # favourable; real students haven't been tested. The gate is only that a
    # noisy field doesn't make matching worse.
    print("\nPT-06  PT-01b with a field of study added (ADR-0029)")
    full = recommend.Model.load(con)
    kids, kvec = full.know.ids, full.know.vectors
    pick = random.Random(6)
    def top_area(soc, n):
        return [kids[i] for i in sorted(range(len(kids)), key=lambda i: (-kvec[soc][i], i))[:n]]
    def hit(prof, soc):
        return any(x[:2] == soc[:2] for x, _ in [r for r in full.rank(prof, 6) if r[0] != soc][:5])
    res = {"none": [], "noisy": [], "own": []}
    for soc, held in every.items():
        res["none"].append(hit(full.profile(held), soc))
        res["noisy"].append(hit(full.profile(held, pick.choice(top_area(soc, 3))), soc))
        res["own"].append(hit(full.profile(held, top_area(soc, 1)[0]), soc))
    pct = {k: statistics.mean(v) * 100 for k, v in res.items()}
    bo = random.Random(4)
    idx = range(len(res["none"]))
    gains = sorted(statistics.mean(res["noisy"][i] - res["none"][i] for i in bo.choices(idx, k=len(idx))) * 100 for _ in range(1000))
    check("PT-06", f"same family in top 5: no field {pct['none']:.1f}%, a noisy field {pct['noisy']:.1f}%, "
          f"the job's own field {pct['own']:.1f}% (n={len(res['none'])}; gate: a noisy field doesn't lower it)",
          pct["noisy"] >= pct["none"],
          f"noisy-field gain {pct['noisy'] - pct['none']:+.1f} points, 95% interval {gains[25]:+.1f} to {gains[974]:+.1f}; simulated students")

    print("\nPT-02  TR-02 latency: rank all 879 occupations, top 5")
    lat = []
    for soc in rng.sample(socs, 60):
        held = essential(soc)
        if not held:
            continue
        t = time.perf_counter()
        model.rank(model.profile(held), 5)
        lat.append((time.perf_counter() - t) * 1000)
    lat.sort()
    p95 = lat[int(len(lat) * 0.95) - 1]
    check("PT-02", f"p95 {p95:.1f} ms, median {statistics.median(lat):.1f} ms, n={len(lat)} (target <= 100 ms)",
          p95 <= 100, f"max {max(lat):.1f} ms")

    print("\nPT-03  NFR-01 response time over HTTP, every demo-path endpoint")
    base = "http://127.0.0.1:8000"
    try:
        body = json.dumps({"profile_type": "school_leaver", "skills": essential("47-2111.00")}).encode()
        req = urllib.request.Request(base + "/profiles", data=body, method="POST",
                                     headers={"Content-Type": "application/json"})
        pid = json.load(urllib.request.urlopen(req, timeout=30))["profile_id"]
        put = urllib.request.Request(base + f"/profiles/{pid}/target", method="PUT",
                                     data=json.dumps({"soc_code": "51-8092.00"}).encode(),
                                     headers={"Content-Type": "application/json"})
        urllib.request.urlopen(put, timeout=30).read()
        paths = ["/skills", "/occupations?zone=3&limit=300", "/occupations?q=electric",
                 f"/recommendations?profile_id={pid}&max_job_zone=3",
                 f"/profiles/{pid}/gap", f"/profiles/{pid}/pathway"]
        times = []
        for _ in range(10):
            for p in paths:
                t = time.perf_counter()
                urllib.request.urlopen(base + p, timeout=30).read()
                times.append((time.perf_counter() - t) * 1000)
        times.sort()
        p95h = times[int(len(times) * 0.95) - 1]
        check("PT-03", f"{len(times)} requests: p95 {p95h:.0f} ms, max {max(times):.0f} ms (target: 95% under 2000 ms)",
              p95h < 2000, f"median {statistics.median(times):.0f} ms")
    except OSError as e:
        check("PT-03", "API reachable", False, f"start the server first: {e}")

    print("\nPT-04  NFR-04 full rebuild of saycep.db from the O*NET files")
    # Release this process's own handle first: Windows will not let the loader
    # delete a file another process holds open. The API is unaffected because
    # it opens and closes a connection per request.
    con.close()
    t = time.perf_counter()
    r = subprocess.run([sys.executable, str(BACKEND / "load_onet.py")], capture_output=True, text=True)
    secs = time.perf_counter() - t
    check("PT-04", f"rebuild took {secs:.2f} s (target <= 60 s)", r.returncode == 0 and secs <= 60,
          r.stdout.splitlines()[0] if r.stdout else r.stderr[-120:])

    print(f"\n{len(PASS)} passed, {len(FAIL)} failed, {len(PASS)+len(FAIL)} total")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
