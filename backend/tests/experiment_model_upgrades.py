"""Experiment, not a test: can a more advanced technique make the
skill-matching model more accurate, with the data we have? (19 November 2026)

Scored exactly as PT-01b: for every job with must-have skills (713), a profile
of its must-haves, the job itself removed, and a hit if any of the five
closest jobs is in the same occupational family (first two SOC digits).
Random baseline 25.9%. Anything that LEARNS from the family labels is
cross-validated: fitted on 4/5 of the jobs and scored only on the other 1/5,
so no job is ever scored by a model that saw its own label.

Test-time only: needs numpy and scikit-learn, which the app never loads. A
winner would ship as a small table of numbers in backend/seed/, read with the
standard library.

  M0  as shipped: mean-centred cosine
  M1  standardised: each skill divided by its spread across jobs (z-scores)
  M2  PCA: cosine in the top-k latent "skill factors" (unsupervised)
  M3  LDA: a projection learned to separate occupational families (supervised, CV)
  M4  graph smoothing: each job's vector blended with its O*NET related jobs'
  M5  LDA on standardised skills (M1 + M3)

Run: python backend/tests/experiment_model_upgrades.py
"""

import random
import sqlite3
import sys
from pathlib import Path

import numpy as np
from sklearn.decomposition import PCA
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))
import recommend  # noqa: E402

con = sqlite3.connect(BACKEND / "saycep.db")
ids, vectors = recommend.load_vectors(con)
socs = sorted(vectors)
V = np.array([vectors[s] for s in socs])                  # 879 x 35 raw importance
mu = V.mean(axis=0)
C = V - mu                                                 # centred, as the engine does
typical = (mu >= 3.5).astype(float)
fam = np.array([s[:2] for s in socs])
pos = {s: i for i, s in enumerate(socs)}

targets = [i for i, s in enumerate(socs) if (V[i] >= 3.5).any()]
P = np.array([(V[i] >= 3.5).astype(float) - typical for i in targets])   # profiles, centred as shipped
T = np.array(targets)

related = {}
for a, b in con.execute("SELECT soc_code, related_soc_code FROM related_occupations WHERE tier LIKE 'Primary%'"):
    if a in pos and b in pos and a != b:
        related.setdefault(pos[a], []).append(pos[b])


def unit(X):
    n = np.linalg.norm(X, axis=1, keepdims=True)
    return X / np.where(n == 0, 1, n)


def hits(jobs, profiles, rows):
    """Top-5 family hit for each profile row (index into targets), target removed."""
    S = unit(profiles) @ unit(jobs).T
    out = []
    for r, srow in zip(rows, S):
        t = targets[r]
        srow = srow.copy()
        srow[t] = -np.inf
        top = np.argpartition(-srow, 5)[:5]
        out.append(bool((fam[top] == fam[t]).any()))
    return np.array(out)


def score(jobs, profiles):
    return hits(jobs, profiles, range(len(targets)))


def cv(fit_transform, folds=5, seed=11):
    """fit_transform(train_job_idx) -> (job_matrix, profile_fn). Scored on held-out targets."""
    order = list(range(len(targets)))
    random.Random(seed).shuffle(order)
    out = np.zeros(len(targets), dtype=bool)
    for k in range(folds):
        test = order[k::folds]
        held = {targets[r] for r in test}
        train = [i for i in range(len(socs)) if i not in held]
        jobs, prof = fit_transform(train)
        out[test] = hits(jobs, prof(P[test]), test)
    return out


def boot(h, seed=3):
    rng = np.random.default_rng(seed)
    m = np.sort([h[rng.integers(0, len(h), len(h))].mean() * 100 for _ in range(1000)])
    return m[25], m[974]


results = []
base = score(C, P)
results.append(("M0 as shipped: mean-centred cosine", base))

sd = C.std(axis=0)
results.append(("M1 standardised (z-scores)", score(C / sd, P / sd)))

for k in (6, 10, 15, 20):
    pca = PCA(n_components=k, random_state=0).fit(C)
    results.append((f"M2 PCA, {k} skill factors", score(pca.transform(C), pca.transform(P + mu) - pca.transform(mu[None, :]))))


def lda_fit(scale):
    def fit(train):
        X = C[train] / scale
        lda = LinearDiscriminantAnalysis(solver="eigen", shrinkage="auto").fit(X, fam[train])
        W = lda.scalings_[:, :min(20, lda.scalings_.shape[1])]
        return (C / scale) @ W, (lambda p: (p / scale) @ W)
    return fit


results.append(("M3 LDA, families (cross-validated)", cv(lda_fit(np.ones(C.shape[1])))))

for beta in (0.3, 0.5):
    S_ = C.copy()
    for i, rel in related.items():
        S_[i] = (1 - beta) * C[i] + beta * C[rel].mean(axis=0)
    results.append((f"M4 graph smoothing with O*NET related jobs, beta {beta}", score(S_, P)))

results.append(("M5 LDA on standardised skills (cross-validated)", cv(lda_fit(sd))))

# ---- round 2: the user's side (19 November, after round 1 showed the jobs' side isn't the bottleneck)
from sklearn.linear_model import Ridge  # noqa: E402

B = (V >= 3.5).astype(float)                                # every job's must-haves, as ticks

for k in (25, 30):
    pca = PCA(n_components=k, random_state=0).fit(C)
    results.append((f"M2 PCA, {k} skill factors", score(pca.transform(C), pca.transform(P + mu) - pca.transform(mu[None, :]))))


def expand_fit(alpha):
    """M6: learn ticks -> the full centred 35-skill picture (ridge regression),
    on training jobs only; a user's ticks are expanded the same way."""
    def fit(train):
        r = Ridge(alpha=alpha).fit(B[train], C[train])
        return C, (lambda p: r.predict(p + typical))
    return fit


for a_ in (1.0, 5.0):
    results.append((f"M6 learned profile expansion, ridge {a_} (CV)", cv(expand_fit(a_))))

Bc = B - B.mean(axis=0)
results.append(("M7 ticks against ticks (jobs' must-haves only)", score(Bc, P + typical - B.mean(axis=0))))


def blend_scores(parts):
    """Average several methods' cosine scores (each already in -1..1)."""
    def run(rows):
        S = sum(w * (unit(pr) @ unit(j).T) for w, j, pr in parts)
        out = []
        for r, srow in zip(rows, S):
            tt = targets[r]
            srow = srow.copy()
            srow[tt] = -np.inf
            top = np.argpartition(-srow, 5)[:5]
            out.append(bool((fam[top] == fam[tt]).any()))
        return np.array(out)
    return run(range(len(targets)))


pca20 = PCA(n_components=20, random_state=0).fit(C)
Pp = pca20.transform(P + mu) - pca20.transform(mu[None, :])
results.append(("M8 blend: shipped + ticks-vs-ticks", blend_scores([(1, C, P), (1, Bc, P + typical - B.mean(axis=0))])))
results.append(("M8 blend: shipped + PCA 20", blend_scores([(1, C, P), (1, pca20.transform(C), Pp)])))


def weights_fit(train):
    """M9: one learned weight per skill, by coordinate ascent on training
    targets' hit rate; scored on held-out ones."""
    tr = [r for r, t_ in enumerate(targets) if t_ in set(train)]
    w = np.ones(C.shape[1])
    for _ in range(2):
        for d in range(C.shape[1]):
            best, bv = w[d], hits(C * w, P[tr] * w, tr).mean()
            for v in (0.0, 0.5, 1.5, 2.0):
                w[d] = v
                hv = hits(C * w, P[tr] * w, tr).mean()
                if hv > bv + 1e-9:
                    best, bv = v, hv
            w[d] = best
    return C * w, (lambda p: p * w)


results.append(("M9 learned per-skill weights (CV)", cv(weights_fit)))

print(f"Experiment: model upgrades. {len(targets)} jobs with must-haves, target removed (as PT-01b). Random 25.9%.\n")
print(f"{'method':58}{'same family in top 5':>21}{'95% interval':>15}{'vs M0':>12}")
for name, h in results:
    lo, hi = boot(h)
    g, l = int((h & ~base).sum()), int((base & ~h).sum())
    print(f"{name:58}{h.mean() * 100:>20.1f}%{f'{lo:.1f}-{hi:.1f}':>15}{f'+{g}/-{l}':>12}")


# ---- round 3: realistic, messy users (the by-construction check) ----
# A real person doesn't tick exactly a job's must-haves. Each test profile
# keeps each must-have with probability `keep` and adds `extra` random other
# skills; averaged over three seeds. Learned methods stay cross-validated.
def messy(keep, extra, seed):
    rng = np.random.default_rng(seed)
    out = []
    for i in targets:
        held = [d for d in range(B.shape[1]) if B[i, d] and rng.random() < keep]
        if not held:                                   # never an empty profile
            held = [int(rng.choice(np.flatnonzero(B[i])))]
        others = [d for d in range(B.shape[1]) if not B[i, d]]
        held += list(rng.choice(others, size=min(extra, len(others)), replace=False))
        x = np.zeros(B.shape[1]); x[held] = 1
        out.append(x - typical)
    return np.array(out)


# M7b: a job's tick set is its must-haves, or, for the 166 jobs with none, its
# top 5 skills: the app's own readiness rule (pathway.READY_FALLBACK_TOP_N).
B2 = B.copy()
for i in np.flatnonzero(B.sum(axis=1) == 0):
    B2[i, np.argsort(-V[i])[:5]] = 1
m2 = B2.mean(axis=0)
Bc2 = B2 - m2


def run_all(Pm):
    global P
    keep_P, P = P, Pm
    x = Pm + typical
    r = {"M0 shipped": score(C, Pm),
         "M6 profile expansion (CV)": cv(expand_fit(5.0)),
         "M7 ticks vs ticks": score(Bc, x - B.mean(axis=0)),
         "M7b ticks vs ticks, top-5 fallback": score(Bc2, x - m2),
         "M8 blend shipped + ticks": blend_scores([(1, C, Pm), (1, Bc, x - B.mean(axis=0))]),
         "M8b blend shipped + M7b (candidate)": blend_scores([(1, C, Pm), (1, Bc2, x - m2)]),
         "M9 learned weights (CV)": cv(weights_fit)}
    P = keep_P
    return r


print("\nRound 3: messy users. Same family in top 5, mean of 3 seeds (vs M0 in that condition)")
for keep, extra in ((0.7, 2), (0.5, 3)):
    agg = {}
    for seed in (1, 2, 3):
        for k_, h in run_all(messy(keep, extra, seed)).items():
            agg.setdefault(k_, []).append(h.mean() * 100)
    print(f"  keeps {int(keep * 100)}% of the must-haves, plus {extra} random other skills:")
    for k_, v in agg.items():
        print(f"    {k_:34}{np.mean(v):6.1f}%   (seeds {', '.join(f'{x:.1f}' for x in v)})")

print("\nClean protocol, the candidate:", f"M8b {run_all(P)['M8b blend shipped + M7b (candidate)'].mean() * 100:.1f}%")


def pt05(J):
    U = unit(J)
    S = U @ U.T
    np.fill_diagonal(S, -np.inf)
    return np.mean([len(set(np.argpartition(-S[i], 5)[:5]) & set(r)) > 0 for i, r in related.items()]) * 100


print(f"Job to job against O*NET's expert lists (PT-05): graded centred {pt05(C):.1f}%, "
      f"tick sets {pt05(Bc):.1f}%, tick sets with fallback {pt05(Bc2):.1f}%  -> keep graded for job to job")
