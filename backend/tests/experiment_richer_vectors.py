"""Experiment, not a test: does adding O*NET Knowledge and Abilities to the
job vectors raise TR-01? Same sample, seed and metric as PT-01.
Run: python backend/tests/experiment_richer_vectors.py
Result and decision: ADR-0013 (no -- not without asking users for more)."""
import csv, random, statistics, sys
from pathlib import Path
BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))
import repository, recommend

con = repository.connect()
skill_ids, vectors = recommend.load_vectors(con)
socs = list(vectors)
means = recommend.skill_means(vectors, len(skill_ids))

def load_extra(fname):
    rows = list(csv.DictReader(open(BACKEND / 'data' / 'onet' / fname, encoding='utf-8'), delimiter='\t'))
    ids = sorted({r['Element ID'] for r in rows if r['Scale ID'] == 'IM'})
    idx = {e: i for i, e in enumerate(ids)}
    vec = {s: [0.0] * len(ids) for s in socs}
    for r in rows:
        if r['Scale ID'] == 'IM' and r['O*NET-SOC Code'] in vec and r['Recommend Suppress'] != 'Y':
            vec[r['O*NET-SOC Code']][idx[r['Element ID']]] = float(r['Data Value'])
    return ids, vec

k_ids, kv = load_extra('Knowledge.txt')
a_ids, av = load_extra('Abilities.txt')
extra = {s: kv[s] + av[s] for s in socs}
w = len(k_ids) + len(a_ids)
xmeans = [statistics.mean(extra[s][i] for s in socs) for i in range(w)]
cent_skill = recommend.centre_occupations(vectors, means)
cent_full = {s: cent_skill[s] + [extra[s][i] - xmeans[i] for i in range(w)] for s in socs}

def essential(soc):
    return [e for e, _ in con.execute("SELECT element_id, importance FROM occupation_skills "
                                      "WHERE soc_code = ? AND importance >= 3.5", (soc,))]

rng = random.Random(42)
targets = [soc for soc in rng.sample(socs, 150) if essential(soc)]

def run(name, centred, profile_for):
    hits, share = [], []
    for soc in targets:
        top = [s for s, _ in recommend.rank(profile_for(soc), centred, 5)]
        same = sum(s[:2] == soc[:2] for s in top)
        hits.append(same > 0); share.append(same / 5)
    print(f"{name:58} any-of-5 {statistics.mean(hits)*100:5.1f}%   mean share {statistics.mean(share)*100:5.1f}%")

base = lambda soc: recommend.centre_profile(skill_ids, essential(soc), means)
run("V0  baseline: 35 skills (PT-01 as shipped)", cent_skill, base)
run(f"V1  jobs get +{w} knowledge/ability dims; user unknown (0)", cent_full, lambda soc: base(soc) + [0.0] * w)
def upper(soc):  # pretend the user also told us the target's high knowledge/abilities
    ex = extra[soc]
    return base(soc) + [(1.0 if ex[i] >= 3.5 else 0.0) - (1.0 if xmeans[i] >= 3.5 else 0.0) for i in range(w)]
run("V2  upper bound: user ALSO records knowledge/abilities", cent_full, upper)
print(f"n={len(targets)}, extra dims: {len(k_ids)} knowledge + {len(a_ids)} abilities")
