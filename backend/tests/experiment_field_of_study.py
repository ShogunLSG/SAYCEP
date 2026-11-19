"""Experiment, not a test: would asking for a field of study improve the match?
(19 November 2026)

O*NET rates every job on 33 knowledge areas (Knowledge.txt, the same Kaggle
release as the skills): "Economics and Accounting", "Biology", "Mechanical" and
so on. A student could pick their field from that list. The skill-matching
model (ADR-0027) would then add a third view: the same must-have comparison,
over knowledge areas instead of skills, and blend it in with weight w.

Protocol is PT-01b's: for each job with must-have skills, the simulated person
ticks those skills; the job itself is removed; a hit is a job from the same
family in the top 5. The field is simulated three ways:
  own    the job's top knowledge area (the person studied exactly this job's field)
  noisy  one area picked at random from the job's top 3
  none   no field given (the shipped model)
Skills are also tested "messy": each must-have kept with p=0.5, plus 3 random
others (as in experiment_model_upgrades.py).

The weight is chosen on half the jobs and reported on the other half.
The knowledge file is read straight from backend/data/onet/; nothing is loaded
into the database. Run: python backend/tests/experiment_field_of_study.py
"""

import csv
import math
import random
import statistics as st
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))
import recommend  # noqa: E402
import repository  # noqa: E402

KNOWLEDGE = BACKEND / "data" / "onet" / "Knowledge.txt"


def load_knowledge(socs):
    areas, vec = {}, {}
    with KNOWLEDGE.open(encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            if r["Scale ID"] == "IM" and r["O*NET-SOC Code"] in socs:
                areas.setdefault(r["Element ID"], r["Element Name"])
                vec.setdefault(r["O*NET-SOC Code"], {})[r["Element ID"]] = float(r["Data Value"])
    ids = sorted(areas)
    return ids, areas, {s: [v.get(e, 0.0) for e in ids] for s, v in vec.items()}


def main():
    con = repository.connect()
    skills = recommend.Model.load(con)
    k_ids, k_names, k_vec = load_knowledge(set(skills.vectors))
    know = recommend.Model(k_ids, k_vec)
    socs = [s for s in skills.vectors if s in k_vec]
    print(f"{len(k_ids)} knowledge areas; {len(socs)} of {len(skills.vectors)} jobs rated on them")

    must = {}
    for soc, e in con.execute("SELECT soc_code, element_id FROM occupation_skills WHERE importance >= 3.5"):
        if soc in k_vec:
            must.setdefault(soc, []).append(e)
    jobs = sorted(must)
    family = {}
    for s in socs:
        family[s[:2]] = family.get(s[:2], 0) + 1
    chance = st.mean(1 - math.comb(len(socs) - 1 - (family[s[:2]] - 1), 5) / math.comb(len(socs) - 1, 5) for s in jobs)

    def top_areas(soc, n):
        return [k_ids[i] for i in sorted(range(len(k_ids)), key=lambda i: -k_vec[soc][i])[:n]]

    def held_skills(soc, messy, rng):
        if not messy:
            return must[soc]
        h = [e for e in must[soc] if rng.random() < 0.5] or [rng.choice(must[soc])]
        return h + rng.sample([e for e in skills.ids if e not in must[soc]], 3)

    def field(soc, how, rng):
        return {"own": top_areas(soc, 1), "noisy": [rng.choice(top_areas(soc, 3))], "none": []}[how]

    def hits(subset, how, messy, w, seed=7):
        rng, out = random.Random(seed), []
        for soc in subset:
            ps = skills.profile(held_skills(soc, messy, rng))
            f = field(soc, how, rng)
            pk = know.profile(f) if f else None
            scored = []
            for o in socs:
                if o == soc:
                    continue
                s = skills.score(ps, o)
                if pk is not None:
                    s = (1 - w) * s + w * know.score(pk, o)
                scored.append((-s, o))
            scored.sort()
            out.append(any(o[:2] == soc[:2] for _, o in scored[:5]))
        return out

    rng = random.Random(19)
    order = jobs[:]
    rng.shuffle(order)
    tune, test = order[: len(order) // 2], order[len(order) // 2:]
    weights = (0.1, 0.2, 0.33, 0.5)

    print(f"\nChoosing the weight on {len(tune)} jobs (field 'noisy', skills clean):")
    best = (None, -1)
    for w in weights:
        h = st.mean(hits(tune, "noisy", False, w)) * 100
        print(f"  w = {w:<4}  {h:5.1f}%")
        if h > best[1]:
            best = (w, h)
    w = best[0]
    print(f"  chosen w = {w}")

    print(f"\nReported on the other {len(test)} jobs (same family in top 5; chance {chance * 100:.1f}%):")
    print(f"  {'':22}{'skills clean':>14}{'skills messy':>14}")
    rows = {}
    for how in ("none", "noisy", "own"):
        rows[how] = [hits(test, how, m, w) for m in (False, True)]
        print(f"  field {how:16}" + "".join(f"{st.mean(r) * 100:13.1f}%" for r in rows[how]))
    boot = random.Random(5)
    for how in ("noisy", "own"):
        for mi, label in ((0, "clean"), (1, "messy")):
            a, b = rows["none"][mi], rows[how][mi]
            idx = range(len(a))
            d = sorted(st.mean(b[i] - a[i] for i in boot.choices(idx, k=len(a))) * 100 for _ in range(1000))
            print(f"  gain from field '{how}', skills {label}: {st.mean(b) * 100 - st.mean(a) * 100:+.1f} points "
                  f"(95% interval {d[25]:+.1f} to {d[974]:+.1f})")

    print("\nThe 33 areas a user would choose from:")
    print("  " + "; ".join(sorted(k_names.values())))


if __name__ == "__main__":
    main()
