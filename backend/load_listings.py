"""Load sample job listings into saycep.db (Jobs for you, ADR-0022).

Source: Kaggle arshkon/linkedin-job-postings (CC BY-SA 4.0), the same file as
load_adverts.py. For each O*NET occupation, the most recent linked adverts are
kept as FEATURES only: the advert's title, place, level and what it mentions.
Never its text, company, link or pay.

    python backend/load_listings.py            reuses the cache if no input changed
    python backend/load_listings.py --fresh    recomputes it (about 2.5 minutes)

load_onet.py calls load(compute_if_stale=False), as it does for the advert
counts: a fresh checkout has no 517 MB advert file, so the result is
committed in backend/seed/ and only a valid copy is used.
"""

import csv
import hashlib
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

import adverts
import cvscan
import listings
import load_adverts

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / "seed" / "advert_listings.cache.json"
CODE = [ROOT / n for n in ("listings.py", "load_listings.py")]

SCHEMA = """
DROP TABLE IF EXISTS advert_listings;

-- Sample listings (ADR-0022): recent adverts per occupation, one row each,
-- features only. Lists are comma-separated; tools use '|' (names hold commas).
CREATE TABLE advert_listings (
    advert_id       TEXT PRIMARY KEY,     -- the dataset's job_id
    soc_code        TEXT NOT NULL REFERENCES occupations(soc_code),
    title           TEXT NOT NULL,        -- the advert's own title, tidied
    location        TEXT NOT NULL,
    work_type       TEXT NOT NULL,        -- Full-time, Contract, ...; '' if not stated
    level           TEXT NOT NULL,        -- LinkedIn experience level; '' if not stated
    years           REAL,                 -- minimum years asked, if stated
    reqs            TEXT NOT NULL,        -- adverts.REQUIREMENTS keys
    skills          TEXT NOT NULL,        -- O*NET element_ids the advert mentions
    tools           TEXT NOT NULL,        -- this job's O*NET software and tools it names
    listed          TEXT NOT NULL         -- ISO date
);
CREATE INDEX idx_advert_listings_soc ON advert_listings(soc_code);
"""


def fingerprint(con):
    """The advert counts' own inputs (database rows and their code), plus this code."""
    h = hashlib.sha256(load_adverts.inputs_fingerprint(con).encode())
    for p in CODE:
        h.update(p.read_bytes().replace(b"\r\n", b"\n"))
    return h.hexdigest()


def _read_cache():
    try:
        return json.loads(CACHE.read_text())
    except (OSError, ValueError):
        return None


def load(con, path=load_adverts.POSTINGS, use_cache=True, compute_if_stale=True):
    """Fill advert_listings. Returns True if it was loaded."""
    inputs = fingerprint(con)
    have_file = path.exists()
    cached = _read_cache() if use_cache else None
    if cached and cached.get("inputs") == inputs and (
            not have_file or cached.get("postings") == load_adverts.postings_fingerprint(path)):
        _write(con, cached["rows"])
        print(f"Listings: from cache ({CACHE.name}); {len(cached['rows']):,} sample listings.")
        return True
    if not compute_if_stale or not have_file:
        why = "no cache" if cached is None else "the cache is out of date"
        print(f"Listings: skipped ({why}). Run: python backend/load_listings.py")
        return False
    rows = compute(con, path)
    data = {"inputs": inputs, "postings": load_adverts.postings_fingerprint(path), "rows": rows}
    tmp = CACHE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data))
    os.replace(tmp, CACHE)
    _write(con, rows)
    print(f"Listings: {len(rows):,} sample listings over {len({r[1] for r in rows})} occupations.")
    return True


def compute(con, path):
    """Stream every advert; keep the newest LISTINGS_PER_JOB per occupation.
    Uses exactly the linking and mention rules of the advert counts."""
    csv.field_size_limit(10 ** 9)
    index = cvscan.Index(con)
    skill_rules = [(e, re.compile(rx.pattern)) for e, rx in index.rules]
    lookup = adverts.build_lookup(con)
    tables, per_soc = {}, defaultdict(list)
    with open(path, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            soc = adverts.link(r["title"], lookup)
            if not soc or not r["listed_time"]:
                continue
            text = r["description"] or ""
            low = adverts.clean(text)
            if soc not in tables:
                tables[soc] = adverts.aliases(index.occ_software.get(soc, ()), index.occ_tools.get(soc, ()))
            per_soc[soc].append([
                r["job_id"], soc, listings.listing_title(r["title"]), (r["location"] or "").strip(),
                (r["formatted_work_type"] or "").strip(), (r["formatted_experience_level"] or "").strip(),
                adverts.years_asked(text),
                ",".join(sorted(adverts.requirements(text))),
                ",".join(sorted(e for e, rx in skill_rules if rx.search(low))),
                "|".join(sorted(adverts.named_in(tables[soc], text, common=index.common))),
                load_adverts._date(r["listed_time"])])
    out = []
    for soc, rows in per_soc.items():
        out += sorted(rows, key=lambda x: (x[10], x[0]), reverse=True)[:listings.LISTINGS_PER_JOB]
    return sorted(out)


def _write(con, rows):
    con.executescript(SCHEMA)
    con.executemany("INSERT INTO advert_listings VALUES (?,?,?,?,?,?,?,?,?,?,?)", rows)
    con.commit()


def main():
    import sqlite3
    con = sqlite3.connect(load_adverts.DB)
    try:
        ok = load(con, use_cache="--fresh" not in sys.argv)
    finally:
        con.close()
    if not ok:
        sys.exit(f"Missing {load_adverts.POSTINGS}.")


if __name__ == "__main__":
    main()
