"""Is "What employers ask for" telling the truth? (ADR-0017)

1. Skill validity: for each occupation with 20+ linked adverts, rank O*NET's
   35 skills by how much more its adverts mention them than adverts in
   general (lift), and compare with O*NET's importance ranking for that job
   (Spearman). Baseline: the same lifts against a *different* occupation's
   importance. If adverts only reflected boilerplate, both would be equal.
2. Requirement rules: print a sample of matched snippets per rule for a
   hand check of precision.

Run after loading: python backend/tests/check_adverts.py
"""

import csv
import random
import re
import sqlite3
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import adverts          # noqa: E402
import load_adverts     # noqa: E402

con = sqlite3.connect(load_adverts.DB)


def ranks(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2
        i = j + 1
    return r


def spearman(a, b):
    ra, rb = ranks(a), ranks(b)
    ma, mb = statistics.mean(ra), statistics.mean(rb)
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    den = (sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb)) ** 0.5
    return num / den if den else 0.0


total = con.execute("SELECT n FROM advert_baseline WHERE kind='all'").fetchone()[0]
base = {i: n / total for i, n in con.execute("SELECT item, n FROM advert_baseline WHERE kind='skill'")}
skills = sorted(base)
big = [s for (s,) in con.execute("SELECT soc_code FROM advert_summary WHERE adverts >= 20")]
imp = {}
for soc, e, v in con.execute("SELECT soc_code, element_id, importance FROM occupation_skills"):
    imp.setdefault(soc, {})[e] = v


def lifts(soc):
    n = con.execute("SELECT adverts FROM advert_summary WHERE soc_code=?", (soc,)).fetchone()[0]
    c = dict(con.execute("SELECT item, n FROM advert_counts WHERE soc_code=? AND kind='skill'", (soc,)))
    return [(c.get(e, 0) / n) / base[e] for e in skills]


def importance(soc):
    return [imp[soc].get(e, 0.0) for e in skills]


rng = random.Random(17)
real, shuffled = [], []
for soc in big:
    li = lifts(soc)
    real.append(spearman(li, importance(soc)))
    other = rng.choice([s for s in big if s != soc])
    shuffled.append(spearman(li, importance(other)))

print(f"Skill validity over {len(big)} occupations with 20+ adverts ({total:,} linked adverts)")
print(f"  Spearman(lift, O*NET importance), same job:      median {statistics.median(real):+.3f}"
      f"  (IQR {statistics.quantiles(real, n=4)[0]:+.3f} to {statistics.quantiles(real, n=4)[2]:+.3f})")
print(f"  Spearman(lift, O*NET importance), another job:   median {statistics.median(shuffled):+.3f}")
print(f"  same job beats another job in {sum(a > b for a, b in zip(real, shuffled))} of {len(big)}")

# What the screen would show: skills with lift >= 1.5 and share >= 25%.
shown_imp, all_imp = [], []
for soc in big:
    n = con.execute("SELECT adverts FROM advert_summary WHERE soc_code=?", (soc,)).fetchone()[0]
    c = dict(con.execute("SELECT item, n FROM advert_counts WHERE soc_code=? AND kind='skill'", (soc,)))
    for e in skills:
        all_imp.append(imp[soc].get(e, 0))
        if c.get(e, 0) / n >= 0.25 and (c.get(e, 0) / n) / base[e] >= 1.5:
            shown_imp.append(imp[soc].get(e, 0))
print(f"  skills the screen would show: {len(shown_imp)}; mean O*NET importance {statistics.mean(shown_imp):.2f}"
      f" vs {statistics.mean(all_imp):.2f} for all skills of those jobs;"
      f" {sum(v >= 3.5 for v in shown_imp) / len(shown_imp):.0%} are must-haves (3.5+)"
      f" vs {sum(v >= 3.5 for v in all_imp) / len(all_imp):.0%} overall")

print("\nRequirement rules: 12 random matches each, with context, for a hand check")
csv.field_size_limit(10 ** 9)
lookup = adverts.build_lookup(con)
rows = [r for r in csv.DictReader(open(load_adverts.POSTINGS, encoding="utf-8"))
        if adverts.link(r["title"], lookup)]
rng = random.Random(5)
for key, label, rx in adverts._REQ:
    hits = [r for r in rows if rx.search((r["description"] or "").lower())]   # rules run on lower case
    print(f"\n[{key}] {label}: {len(hits):,} of {len(rows):,} linked adverts")
    for r in rng.sample(hits, 12):
        m = rx.search(r["description"].lower())
        a, b = max(0, m.start() - 60), m.end() + 50
        print("   …" + re.sub(r"\s+", " ", r["description"][a:b]) + "…")
yrs = [(r, adverts.years_asked(r["description"])) for r in rows]
yrs = [(r, y) for r, y in yrs if y is not None]
print(f"\n[years] {len(yrs):,} adverts state years; sample:")
for r, y in rng.sample(yrs, 10):
    m = adverts._YEARS.search(r["description"])
    print(f"   {y} ← …" + re.sub(r"\s+", " ", r["description"][max(0, m.start() - 30):m.end() + 20]) + "…")
