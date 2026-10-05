"""Load per-occupation advert counts into saycep.db (ADR-0017).

Source: Kaggle arshkon/linkedin-job-postings (CC BY-SA 4.0), unzipped into
backend/data/linkedin/. Only counts and normalised titles are written --
never advert text, company names or links.

Run after load_onet.py (which calls this itself when the file is present):
    python backend/load_adverts.py            reuses the cached counts if no input changed
    python backend/load_adverts.py --fresh    recomputes them (about two minutes)
"""

import csv
import datetime
import hashlib
import json
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

import adverts
import cvscan

ROOT = Path(__file__).resolve().parent
POSTINGS = ROOT / "data" / "linkedin" / "postings.csv"
# The counts take about two minutes to compute from 517 MB of adverts, and
# change only when an input does. They're cached beside the data with a
# fingerprint of every input, so an O*NET rebuild stays within NFR-04.
CACHE = POSTINGS.with_name("advert_counts.cache.json")
ONET = ROOT / "data" / "onet"
INPUTS = [ONET / n for n in ("Occupation Data.txt", "Alternate Titles.txt", "Technology Skills.txt",
                             "Tools Used.txt", "Task Statements.txt")]
CODE = [ROOT / n for n in ("adverts.py", "cvscan.py", "load_adverts.py")]
DB = ROOT / "saycep.db"
DATASET = "LinkedIn Job Postings 2023-2024 (Kaggle arshkon/linkedin-job-postings, CC BY-SA 4.0)"
EXPECTED_ROWS = 123_849

SCHEMA = """
DROP TABLE IF EXISTS advert_summary;
DROP TABLE IF EXISTS advert_counts;
DROP TABLE IF EXISTS advert_titles;
DROP TABLE IF EXISTS advert_baseline;

-- One row per O*NET occupation with at least one strictly linked advert.
CREATE TABLE advert_summary (
    soc_code        TEXT PRIMARY KEY REFERENCES occupations(soc_code),
    adverts         INTEGER NOT NULL,
    entry_level     INTEGER NOT NULL,     -- LinkedIn level "Entry level" or "Internship"
    years_n         INTEGER NOT NULL,     -- adverts that state years of experience
    years_median    REAL,                 -- median of the minimum years they ask
    listed_from     TEXT NOT NULL,
    listed_to       TEXT NOT NULL,
    source_dataset  TEXT NOT NULL
);

-- How many of an occupation's adverts mention each thing.
-- kind: skill (O*NET element_id), tool / software (O*NET example), req (adverts.REQUIREMENTS key)
CREATE TABLE advert_counts (
    soc_code        TEXT NOT NULL REFERENCES occupations(soc_code),
    kind            TEXT NOT NULL CHECK (kind IN ('skill','tool','software','req')),
    item            TEXT NOT NULL,
    n               INTEGER NOT NULL,
    PRIMARY KEY (soc_code, kind, item)
);

-- The commonest advert titles per occupation, normalised (no seniority,
-- location or employer).
CREATE TABLE advert_titles (
    soc_code        TEXT NOT NULL REFERENCES occupations(soc_code),
    title           TEXT NOT NULL,
    n               INTEGER NOT NULL
);

-- The same counts across every linked advert: what "noticeably more than
-- adverts in general" is measured against. kind 'all' holds the total.
CREATE TABLE advert_baseline (
    kind            TEXT NOT NULL,
    item            TEXT NOT NULL,
    n               INTEGER NOT NULL,
    PRIMARY KEY (kind, item)
);

CREATE INDEX idx_advert_counts_soc ON advert_counts(soc_code);
CREATE INDEX idx_advert_titles_soc ON advert_titles(soc_code);
"""


def _date(ms):
    return datetime.datetime.fromtimestamp(int(float(ms)) / 1000, datetime.timezone.utc).date().isoformat()


def fingerprint(path):
    h = hashlib.sha256()
    st = path.stat()
    h.update(f"{st.st_size}:{int(st.st_mtime)}".encode())
    for p in INPUTS + CODE:
        h.update(p.read_bytes())
    return h.hexdigest()


def load(con, path=POSTINGS, use_cache=True):
    fp = fingerprint(path)
    if use_cache and CACHE.exists():
        cached = json.loads(CACHE.read_text())
        if cached.get("fingerprint") == fp:
            _write(con, cached)
            print(f"Adverts: from cache ({CACHE.name}); inputs unchanged.")
            _report(cached)
            return
    data = compute(con, path)
    data["fingerprint"] = fp
    CACHE.write_text(json.dumps(data))
    _write(con, data)
    _report(data)


def compute(con, path):
    """Read every advert and count, per occupation, what it mentions."""
    csv.field_size_limit(10 ** 9)
    with open(path, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if len(rows) != EXPECTED_ROWS:
        sys.exit(f"{path.name}: expected {EXPECTED_ROWS:,} rows, found {len(rows):,}. Wrong file?")

    index = cvscan.Index(con)
    skill_rules = [(e, re.compile(rx.pattern)) for e, rx in index.rules]   # run on lower-cased text
    lookup = adverts.build_lookup(con)
    summary = defaultdict(lambda: {"n": 0, "entry": 0, "years": [], "dates": []})
    counts = Counter()          # (soc, kind, item) -> adverts
    base = Counter()            # (kind, item) -> adverts
    titles = defaultdict(Counter)
    tables = {}                 # soc -> its software/tool aliases
    linked = 0

    for r in rows:
        soc = adverts.link(r["title"], lookup)
        if not soc:
            continue
        linked += 1
        text = r["description"] or ""
        s = summary[soc]
        s["n"] += 1
        s["entry"] += adverts.is_entry(r["formatted_experience_level"])
        if r["listed_time"]:
            s["dates"].append(_date(r["listed_time"]))
        y = adverts.years_asked(text)
        if y is not None:
            s["years"].append(y)
        titles[soc][adverts.norm(r["title"])] += 1

        found = [("req", k) for k in adverts.requirements(text)]
        low = text.lower()
        found += [("skill", e) for e, rx in skill_rules if rx.search(low)]
        if soc not in tables:
            tables[soc] = adverts.aliases(index.occ_software.get(soc, ()), index.occ_tools.get(soc, ()))
        for t in adverts.named_in(tables[soc], text, common=index.common):
            found.append(("software" if t in index.occ_software.get(soc, ()) else "tool", t))
        for kind, item in found:
            counts[(soc, kind, item)] += 1
            if kind in ("req", "skill"):
                base[(kind, item)] += 1
    base[("all", "adverts")] = linked
    return {
        "read": len(rows), "linked": linked,
        "summary": [[soc, x["n"], x["entry"], len(x["years"]),
                     statistics.median(x["years"]) if x["years"] else None,
                     min(x["dates"]), max(x["dates"])] for soc, x in summary.items() if x["dates"]],
        "counts": [[soc, kind, item, n] for (soc, kind, item), n in counts.items()],
        "titles": [[soc, t.title(), n] for soc, c in titles.items() for t, n in c.most_common(6)],
        "baseline": [[kind, item, n] for (kind, item), n in base.items()],
    }


def _write(con, d):
    con.executescript(SCHEMA)
    con.executemany("INSERT INTO advert_summary VALUES (?,?,?,?,?,?,?,?)",
                    [(*row, DATASET) for row in d["summary"]])
    con.executemany("INSERT INTO advert_counts VALUES (?,?,?,?)", d["counts"])
    con.executemany("INSERT INTO advert_titles VALUES (?,?,?)", d["titles"])
    con.executemany("INSERT INTO advert_baseline VALUES (?,?,?)", d["baseline"])
    con.commit()


def _report(d):
    shown = sum(1 for row in d["summary"] if row[1] >= adverts.MIN_ADVERTS)
    print(f"Adverts: {d['read']:,} read, {d['linked']:,} linked to one O*NET occupation "
          f"({d['linked'] / d['read']:.1%}); {len(d['summary'])} occupations, {shown} with "
          f"{adverts.MIN_ADVERTS}+ adverts.")


def main():
    import sqlite3
    if not POSTINGS.exists():
        sys.exit(f"Missing {POSTINGS}. Unzip Kaggle arshkon/linkedin-job-postings into {POSTINGS.parent}.")
    con = sqlite3.connect(DB)
    load(con, use_cache="--fresh" not in sys.argv)
    con.close()


if __name__ == "__main__":
    main()
