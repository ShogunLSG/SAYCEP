"""Experiment, not a test: one-word tool names that are everyday CV words.
(19 November 2026; BACKLOG "CV scanner: one-word tools that are everyday words")

O*NET's tool list includes "Balances", "Levels", "Controllers", "Flasks" and
"Explorers", so "trial balance", "entry level" and "financial controller" name
tools. A stop-list is the fix, but it must not be chosen by looking at the
CVs the score is reported on. So, with benchmark_cv.py's own split (seed 11):

  python backend/tests/experiment_cv_tool_words.py list
      every one-word tool match in the TUNING half only, with lines of context,
      for a hand judgement of each word (recorded in STOP below, with reasons);
  python backend/tests/experiment_cv_tool_words.py
      the goal score's r with and without STOP: tuning half, then the TEST half
      once, with a bootstrap over CVs for the change.

The shipped scanner is patched in memory only.
"""

import csv
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import benchmark_cv as bm  # noqa: E402
import cvscan  # noqa: E402
import repository  # noqa: E402

# Judged on the tuning half's contexts only (run with "list"). Each is a tool
# name that, in those CVs, was an everyday or office word, never the tool.
# The multi-word tools ("analytical balance", "bench scale", "erlenmeyer
# flask", "spirit"-style levels) still match; only the bare word stops.
STOP = {
    "level",        # "entry level", "entry-level" (3 of 3 contexts)
    "controller",   # "financial controller", "fund controller": job titles
    "flask",        # the Python web framework, in tech skill lists
    "balance",      # "balance sheet"
    "explorer",     # "Internet Explorer"
    "platform",     # "machine learning platform", "Windows platforms"
    "scale",        # "large-scale"
    "transformer",  # the NLP model family
    "range",        # "a range of people"
    "guide",        # "who can guide me"
    "hone",         # "hone my skills"
    "pick",         # a bare skill-list word, not a pick tool
}
# Kept, though some contexts were not the tool: ladder ("Ladder Logic"),
# filter ("Digital Filter design"), laser, scanner, generator. Each is a real
# tool a trades CV would name, and stopping it would hurt those users.


def split_keys(rows):
    keys = sorted({(r["skills"], r["career_objective"], r["positions"]) for r in rows})
    random.Random(11).shuffle(keys)
    return set(keys[: len(keys) // 2]), keys


def one_word_hits(index, text):
    """[(word, tool)] for single-word tool matches, as tools_named makes them."""
    ws = cvscan._words(text)
    out = []
    for w in ws:
        hit = index.tools.get((w,))
        if hit and len(w) >= cvscan.TOOL_MIN_LEN and w not in cvscan.AMBIGUOUS:
            out.append((w, hit))
    return out


def listing(rows, index):
    tune, _ = split_keys(rows)
    seen, ctx, cvs = Counter(), defaultdict(list), {}
    for r in rows:
        key = (r["skills"], r["career_objective"], r["positions"])
        if key not in tune or key in cvs:
            continue
        text = bm.cv_text(r)
        cvs[key] = 1
        for w, tool in set(one_word_hits(index, text)):
            seen[(w, tool)] += 1
            if len(ctx[(w, tool)]) < 3:
                m = re.search(r".{0,40}\b" + re.escape(w) + r"\w*.{0,30}", text.replace("\n", " "), re.I)
                ctx[(w, tool)].append(m.group(0) if m else "?")
    print(f"One-word tool matches in the {len(cvs)} tuning-half CVs (CVs naming it):\n")
    for (w, tool), n in seen.most_common():
        print(f"  {n:3}  {w:16} -> {tool}")
        for c in ctx[(w, tool)]:
            print(f"         \"{c.strip()}\"")


def evaluate(rows, index, job_col, stop):
    real = cvscan.tools_named
    if stop:
        cvscan.tools_named = lambda ix, t: {x for x in real(ix, t)} - {
            tool for w, tool in one_word_hits(ix, t) if w in stop
            and not any(tool == h for h in cvscan.named(
                {k: v for k, v in ix.tools.items() if len(k) > 1}, t))}
    try:
        tune, _ = split_keys(rows)
        scanned, pairs = {}, []
        for r in rows:
            key = (r["skills"], r["career_objective"], r["positions"])
            if key not in scanned:
                t = bm.cv_text(r)
                scanned[key] = (cvscan.skill_evidence(index, t), cvscan.software_named(index, t), cvscan.tools_named(index, t))
            ev, sw, tl = scanned[key]
            pairs.append((key, cvscan.goal_score(index, ev, sw, tl, bm.MAP[r[job_col].strip()][0])["value"], float(r["matched_score"])))
    finally:
        cvscan.tools_named = real
    tu = [p for p in pairs if p[0] in tune]
    te = [p for p in pairs if p[0] not in tune]
    rr = lambda ps: bm.pearson([p[1] for p in ps], [p[2] for p in ps])
    return rr(tu), rr(te), te, scanned


def main():
    rows = list(csv.DictReader(bm.DATA.open(encoding="utf-8-sig")))
    job_col = next(c for c in rows[0] if c.endswith("job_position_name"))
    index = cvscan.Index(repository.connect())
    if sys.argv[1:] == ["list"]:
        return listing(rows, index)
    b_tu, b_te, b_pairs, b_scan = evaluate(rows, index, job_col, set())
    s_tu, s_te, s_pairs, s_scan = evaluate(rows, index, job_col, STOP)
    print(f"Stop-list of {len(STOP)} words: {', '.join(sorted(STOP))}\n")
    print(f"Tuning half: r {b_tu:.4f} -> {s_tu:.4f} ({s_tu - b_tu:+.4f})")
    print(f"TEST half (once): r {b_te:.4f} -> {s_te:.4f} ({s_te - b_te:+.4f})")
    by_b, by_s = defaultdict(list), defaultdict(list)
    for p in b_pairs:
        by_b[p[0]].append(p)
    for p in s_pairs:
        by_s[p[0]].append(p)
    ks, rng, d = list(by_s), random.Random(5), []
    for _ in range(1000):
        pick = [rng.choice(ks) for _ in ks]
        a = [p for k in pick for p in by_b[k]]
        b = [p for k in pick for p in by_s[k]]
        d.append(bm.pearson([p[1] for p in b], [p[2] for p in b]) - bm.pearson([p[1] for p in a], [p[2] for p in a]))
    d.sort()
    print(f"95% interval for the change in test r: {d[25]:+.4f} to {d[974]:+.4f}")
    gone = sum(len(b_scan[k][2] - s_scan[k][2]) for k in b_scan)
    cvs = sum(1 for k in b_scan if b_scan[k][2] - s_scan[k][2])
    print(f"\nFalse tool matches removed: {gone}, from {cvs} of {len(b_scan)} CVs (both halves).")


if __name__ == "__main__":
    main()
