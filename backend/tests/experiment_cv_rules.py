"""Experiment, not a test: can the CV scanner's skill rules catch more of what a
CV shows without hurting the measured goal score? (19 November 2026)

Same benchmark and split as benchmark_cv.py (ADR-0014): the Kaggle Resume
Dataset, CVs split in half with the same seed. Candidate rules below are ours,
written to be general (not tuned to this dataset's tech and office CVs). Each
candidate is kept only if the TUNING half's r does not fall; the TEST half is
then measured once, with a bootstrap over CVs for the change.

The shipped rules are patched in memory only; cvscan.py is not touched here.

Round 1 (looser rules: bare "decisions", "designed", "wrote ...", any "reports")
kept 11 of 16 and moved test r 0.2655 -> 0.2605 (change -0.016 to +0.005), below
the 0.265 bar. Round 2, below, drops those loose phrasings on precision grounds
from the hand-check, not from the test score; its test-half reading is the
SECOND look at the test half, and is reported as such.

Run: python backend/tests/experiment_cv_rules.py   (needs backend/data/resume/)
"""

import csv
import random
import re
import statistics as st
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import benchmark_cv as bm  # noqa: E402
import cvscan  # noqa: E402
import repository  # noqa: E402

# Extra phrasings per skill, added to the shipped rule with "|".
CANDIDATES = {
    "Writing": r"documentation|technical writing|content writing|copywriting|report writing|reporting\b|(financial|sales|technical|written|monthly|weekly|management) reports",
    "Monitoring": r"monitor(ed|ing)?\b|track(ed|ing)? (progress|performance|results)|supervis(ed|ing) (the )?(work|progress)",
    "Operations Monitoring": r"monitor(ed|ing)? (the )?(network|servers?|processes|plant|operations|quality)|process control",
    "Systems Analysis": r"systems? analysis|business analysis|requirements? (gathering|analysis)|data analysis|analys(ed|ing) (the )?(system|process|data)",
    "Operations Analysis": r"requirements? (gathering|analysis)|user (needs|requirements)|business requirements",
    "Judgment and Decision Making": r"decision[- ]making|made decisions",
    "Active Learning": r"eager to learn|fast learner|willing(ness)? to learn|continuous learning",
    "Reading Comprehension": r"\bresearch(ed|ing)?\b|review(ed|ing)? (documents|reports|contracts|literature)",
    "Technology Design": r"software (development|engineering)|web development|ui/ux|\bcad\b|autocad",
    "Science": r"\bresearch(ed|ing)?\b|scientific",
    "Learning Strategies": r"taught myself|learning strateg\\w*",
    "Social Perceptiveness": r"emotional intelligence|interpersonal",
    "Active Listening": r"interpersonal skills|communication skills",
    "Operation and Control": r"operat(ed|ing) (machinery|plant|heavy)|machine operator",
    "Quality Control Analysis": r"six sigma|\btesting\b|audit(ed|ing)?\b",
    "Complex Problem Solving": r"analytical skills|critical problems",
}

SHIPPED = dict(cvscan.SKILL_RULES)


def patch(extra):
    cvscan.SKILL_RULES.clear()
    for k, v in SHIPPED.items():
        cvscan.SKILL_RULES[k] = f"(?:{v})|\\b(?:{extra[k]})" if k in extra else v


def evaluate(extra, rows, job_col, con):
    """Pearson r of the goal score against matched_score, on (tuning, test), and the per-CV pairs."""
    patch(extra)
    index = cvscan.Index(con)
    scanned, pairs = {}, []
    for r in rows:
        key = (r["skills"], r["career_objective"], r["positions"])
        if key not in scanned:
            text = bm.cv_text(r)
            scanned[key] = (cvscan.skill_evidence(index, text),
                            cvscan.software_named(index, text), cvscan.tools_named(index, text))
        soc = bm.MAP[r[job_col].strip()][0]
        ev, sw, tl = scanned[key]
        pairs.append((key, cvscan.goal_score(index, ev, sw, tl, soc)["value"], float(r["matched_score"])))
    keys = sorted(scanned)
    random.Random(11).shuffle(keys)
    tune = set(keys[: len(keys) // 2])
    tu = [p for p in pairs if p[0] in tune]
    te = [p for p in pairs if p[0] not in tune]
    rr = lambda part: bm.pearson([p[1] for p in part], [p[2] for p in part])
    return rr(tu), rr(te), te, scanned, index


def main():
    rows = list(csv.DictReader(bm.DATA.open(encoding="utf-8-sig")))
    job_col = next(c for c in rows[0] if c.endswith("job_position_name"))
    con = repository.connect()
    base_tu, base_te, base_pairs, base_scan, index = evaluate({}, rows, job_col, con)
    print(f"Shipped rules: tuning r = {base_tu:.4f}, test r = {base_te:.4f}\n")
    kept, cur = {}, base_tu
    print("Each candidate on the TUNING half (kept if r does not fall):")
    for skill, rx in CANDIDATES.items():
        tu, _, _, _, _ = evaluate({**kept, skill: rx}, rows, job_col, con)
        ok = tu >= cur - 1e-9
        print(f"  {'keep' if ok else 'drop'}  {skill:30} tuning r {tu:.4f} ({tu - cur:+.4f})")
        if ok:
            kept[skill], cur = rx, tu
    tu, te, te_pairs, scan, index = evaluate(kept, rows, job_col, con)
    print(f"\nKept {len(kept)} of {len(CANDIDATES)}. Tuning r {base_tu:.4f} -> {tu:.4f}; "
          f"TEST r {base_te:.4f} -> {te:.4f} ({te - base_te:+.4f})")
    # Bootstrap the test-half change over CVs (pairs from one CV are not independent).
    by_base, by_new = defaultdict(list), defaultdict(list)
    for p in base_pairs:
        by_base[p[0]].append(p)
    for p in te_pairs:
        by_new[p[0]].append(p)
    cvk, rng, diffs = list(by_new), random.Random(5), []
    for _ in range(1000):
        pick = [rng.choice(cvk) for _ in cvk]
        a = [p for k in pick for p in by_base[k]]
        b = [p for k in pick for p in by_new[k]]
        diffs.append(bm.pearson([p[1] for p in b], [p[2] for p in b]) - bm.pearson([p[1] for p in a], [p[2] for p in a]))
    diffs.sort()
    print(f"95% interval for the change in test r: {diffs[25]:+.4f} to {diffs[974]:+.4f}")
    # What users would see: suggestions per CV, before and after.
    names = {e: index.skills[e][0] for e in index.skills}
    before = Counter(names[e] for ev, _, _ in base_scan.values() for e in ev)
    after = Counter(names[e] for ev, _, _ in scan.values() for e in ev)
    print(f"\nSkills suggested per CV: {st.mean(len(v[0]) for v in base_scan.values()):.2f} -> "
          f"{st.mean(len(v[0]) for v in scan.values()):.2f}")
    print("Skills that now fire more often (CVs):", ", ".join(f"{k} {before[k]}->{after[k]}" for k in sorted(after, key=lambda k: -(after[k] - before[k])) if after[k] > before[k]))
    # Samples of the newly matched lines, for a hand check of precision.
    print("\nSample new evidence lines, for hand-checking:")
    shown = Counter()
    for key, (ev, _, _) in scan.items():
        old = base_scan[key][0]
        for e, (line, *_rest) in ev.items():
            n = names[e]
            if n in kept and e not in old and shown[n] < 4:
                shown[n] += 1
                print(f"  {n:28} \"{str(line)[:90]}\"")
    patch({})


if __name__ == "__main__":
    main()
