"""Benchmark -- the CV scanner's goal score against the Kaggle Resume Dataset
(ADR-0014). Scores the shipped code (cvscan.py), not a copy.

Run: python backend/tests/benchmark_cv.py      (about a minute)
Needs backend/data/resume/resume_data.csv from Kaggle
(saugataroyarghya/resume-dataset, CC BY-NC 4.0).

The dataset is 341 CVs crossed with 28 job adverts, each pair carrying a
matched_score. Each advert is mapped by hand to its nearest O*NET occupation
(MAP below; 'judgement' rows are ours). CVs are split in half with a fixed
seed: the model's two settings (SUGGEST_AT, COVERAGE_WEIGHT) were chosen on
the tuning half on 5 October, and the test half is reported.
"""

import ast
import csv
import math
import random
import re
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

import cvscan
import repository

DATA = BACKEND / "data" / "resume" / "resume_data.csv"

# advert -> (O*NET-SOC, how the match was made)
MAP = {
    "AI Engineer": ("15-1221.00", "alt title"),
    "Asst. Manager/ Manger (Administrative)": ("11-3012.00", "alt title"),
    "Business Development Executive": ("11-2022.00", "alt title"),
    "Civil Engineer": ("17-2051.00", "title"),
    "Data Engineer": ("15-1243.00", "alt title"),
    "Data Science Engineer": ("15-2041.00", "judgement: Data Scientists has no O*NET skill ratings"),
    "Database Administrator (DBA)": ("15-1242.00", "title"),
    "DevOps Engineer": ("15-1244.00", "judgement"),
    "Executive - VAT": ("13-2011.00", "judgement"),
    "Executive/ Senior Executive- Trade Marketing, Hygiene Products": ("13-1161.00", "judgement"),
    "Executive/ Sr. Executive -IT": ("15-1232.00", "judgement"),
    "Full Stack Developer (Python,React js)": ("15-1254.00", "alt title"),
    "HR Officer": ("13-1071.00", "judgement"),
    "Head of Internal Control & Compliance (ICC) - SEVP/DMD": ("11-9199.02", "alt title"),
    "Intern (Generative AI Engineering - 2D/3D Image Generation)": ("15-1221.00", "judgement"),
    "Machine Learning (ML) Engineer": ("15-1221.00", "alt title"),
    "Management Trainee - Mechanical": ("17-2141.00", "judgement"),
    "Manager- Human Resource Management (HRM)": ("11-3121.00", "alt title"),
    "Marketing Officer": ("13-1161.00", "judgement"),
    "Mechanical Designer": ("17-3013.00", "alt title"),
    "Mechanical Engineer": ("17-2141.00", "title"),
    "Network Support Engineer": ("15-1231.00", "alt title"),
    "Project Coordinator (Civil)": ("11-9021.00", "alt title"),
    "Senior Software Engineer": ("15-1251.00", "judgement: Software Developers has no O*NET skill ratings"),
    "Senior iOS Engineer": ("15-1251.00", "judgement: as above"),
    "Site Engineer": ("17-2051.00", "judgement"),
    "Sr.Officer / Executive - Internal Audit": ("13-2011.00", "alt title"),
    "System Administrator (Operation & Maintenance of Server, Storage & Network)": ("15-1244.00", "alt title"),
    "System Administrator (Operation & Maintenance of Server, Storage & Service Desk System)": ("15-1244.00", "alt title"),
}


def as_list(x):
    try:
        v = ast.literal_eval(x)
    except Exception:
        return [x] if x else []
    out = []
    for i in (v if isinstance(v, list) else [v]):
        out += as_list(repr(i)) if isinstance(i, list) else ([str(i)] if i else [])
    return out


def cv_text(r):
    # responsibilities is excluded: in this dataset it duplicates the advert's (data-sources.md).
    parts = [r["career_objective"]] + as_list(r["skills"]) + as_list(r["positions"]) \
        + as_list(r["degree_names"]) + as_list(r["major_field_of_studies"]) \
        + as_list(r["certification_skills"]) + as_list(r["role_positions"]) + as_list(r["related_skils_in_job"])
    return "\n".join(p for p in parts if p and p not in ("None", "N/A"))


def pearson(a, b):
    ma, mb = st.mean(a), st.mean(b)
    da, db = [x - ma for x in a], [y - mb for y in b]
    n = math.sqrt(sum(x * x for x in da) * sum(y * y for y in db))
    return sum(x * y for x, y in zip(da, db)) / n if n else 0.0


def ranks(v):
    order = sorted(range(len(v)), key=lambda i: v[i])
    r, i = [0.0] * len(v), 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2
        i = j + 1
    return r


def spearman(a, b):
    return pearson(ranks(a), ranks(b))


def naive(r):
    words = lambda s: set(re.findall(r"[a-z][a-z+#.]{1,}", (s or "").lower()))
    req = words(r["skills_required"] + " " + r["educationaL_requirements"])
    have = set(w for s in as_list(r["skills"]) for w in words(s))
    return len(have & req) / len(req) if req else 0.0


def main():
    if not DATA.exists():
        sys.exit(f"Missing {DATA}. Download saugataroyarghya/resume-dataset from Kaggle into it.")
    rows = list(csv.DictReader(DATA.open(encoding="utf-8-sig")))
    job_col = next(c for c in rows[0] if c.endswith("job_position_name"))
    index = cvscan.Index(repository.connect())

    scanned = {}
    pairs = []
    for r in rows:
        key = (r["skills"], r["career_objective"], r["positions"])
        if key not in scanned:
            text = cv_text(r)
            scanned[key] = (cvscan.skill_evidence(index, text),
                            cvscan.named(index.software, text, common=index.common), cvscan.named(index.tools, text))
        soc = MAP[r[job_col].strip()][0]
        ev, sw, tl = scanned[key]
        pairs.append((key, cvscan.goal_score(index, ev, sw, tl, soc)["value"], naive(r), float(r["matched_score"])))

    keys = sorted(scanned)
    random.Random(11).shuffle(keys)
    tune = set(keys[: len(keys) // 2])
    print(f"{len(rows)} pairs = {len(scanned)} CVs x {len({r[job_col].strip() for r in rows})} adverts; "
          f"{len({v[0] for v in MAP.values()})} O*NET occupations")

    for name, part in (("tuning half", [p for p in pairs if p[0] in tune]),
                       ("TEST half", [p for p in pairs if p[0] not in tune])):
        ys = [p[3] for p in part]
        model, base = [p[1] for p in part], [p[2] for p in part]
        by_cv = defaultdict(list)
        for k, m, _, y in part:
            by_cv[k].append((m, y))
        per_cv = st.mean(spearman([m for m, _ in v], [y for _, y in v])
                         for v in by_cv.values() if len({y for _, y in v}) > 1)
        print(f"\n[{name}] {len(part)} pairs, {len(by_cv)} CVs")
        print(f"  naive word overlap   r = {pearson(base, ys):.3f}   rho = {spearman(base, ys):.3f}")
        print(f"  CV scanner (shipped) r = {pearson(model, ys):.3f}   rho = {spearman(model, ys):.3f}"
              f"   ranking each CV's adverts rho = {per_cv:.3f}")
        if name == "TEST half":
            # Bootstrap over CVs, not pairs: pairs from one CV are not independent.
            cvk = list(by_cv)
            grouped = defaultdict(list)
            for p in part:
                grouped[p[0]].append(p)
            rng, diffs, rs = random.Random(5), [], []
            for _ in range(1000):
                sample = [p for k in (rng.choice(cvk) for _ in cvk) for p in grouped[k]]
                y = [p[3] for p in sample]
                rm, rb = pearson([p[1] for p in sample], y), pearson([p[2] for p in sample], y)
                rs.append(rm)
                diffs.append(rm - rb)
            rs.sort(); diffs.sort()
            print(f"  95% interval, scanner r: {rs[25]:.3f} to {rs[974]:.3f}; "
                  f"scanner minus naive: {diffs[25]:+.3f} to {diffs[974]:+.3f}")


if __name__ == "__main__":
    main()
