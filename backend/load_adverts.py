"""Load per-occupation advert counts into saycep.db (ADR-0017).

Source: Kaggle arshkon/linkedin-job-postings (CC BY-SA 4.0), unzipped into
backend/data/linkedin/. Only counts and titles are written -- never advert
text, company names or links.

    python backend/load_adverts.py            reuses the cached counts if no input changed
    python backend/load_adverts.py --fresh    recomputes them (about 2.5 minutes)

load_onet.py calls load(compute_if_stale=False): it reuses a valid cache and
otherwise says to run this script, so the O*NET rebuild never takes the slow
path (NFR-04) and never fails because of the optional advert data.
"""

import csv
import datetime
import hashlib
import json
import os
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

import adverts
import cvscan

ROOT = Path(__file__).resolve().parent
POSTINGS = ROOT / "data" / "linkedin" / "postings.csv"
# The counts take about 2.5 minutes to compute from 517 MB of adverts, and
# change only when an input does. They're cached with a fingerprint of every
# input: the database rows the computation reads (so a change to load_onet.py's
# filtering counts too), the code, and the advert file. The cache is COMMITTED
# (backend/seed/, 0.7 MB, counts only, no advert text): a fresh checkout has
# neither the 517 MB advert file nor the time to compute, and without it the
# job pages would say the advert data isn't loaded (ADR-0019). A unit test
# fails if the committed counts no longer match the code.
CACHE = ROOT / "seed" / "advert_counts.cache.json"
CODE = [ROOT / n for n in ("adverts.py", "cvscan.py", "load_adverts.py")]
INPUT_QUERIES = [
    "SELECT soc_code, title FROM occupations ORDER BY 1",
    "SELECT soc_code, title, short_title FROM occupation_alt_titles ORDER BY 1, 2, 3",
    "SELECT soc_code, example FROM occupation_technology ORDER BY 1, 2",
    "SELECT soc_code, example FROM occupation_tools ORDER BY 1, 2",
    "SELECT DISTINCT task FROM occupation_tasks ORDER BY 1",
    "SELECT element_id, name FROM skills ORDER BY 1",
]
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
    level_n         INTEGER NOT NULL,     -- adverts that state a LinkedIn experience level
    entry_level     INTEGER NOT NULL,     -- of those, "Entry level" or "Internship"
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

-- The commonest advert titles per occupation: normalised (no seniority,
-- location or employer), acronyms kept as the adverts write them.
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


class AdvertError(Exception):
    """The advert data can't be loaded; the rest of the database is fine."""


def _date(ms):
    return datetime.datetime.fromtimestamp(int(float(ms)) / 1000, datetime.timezone.utc).date().isoformat()


def inputs_fingerprint(con):
    """Everything the computation reads, apart from the advert file itself."""
    h = hashlib.sha256()
    for q in INPUT_QUERIES:
        for row in con.execute(q):
            h.update(repr(tuple(row)).encode())   # values, not the row object (sqlite3.Row's repr is an address)
    for p in CODE:
        # Line endings are normalised: git on Windows checks files out with CRLF,
        # and that must not make a correct cache look stale.
        h.update(p.read_bytes().replace(b"\r\n", b"\n"))
    return h.hexdigest()


def postings_fingerprint(path):
    st = path.stat()
    return f"{st.st_size}:{int(st.st_mtime)}"


def _read_cache():
    try:
        return json.loads(CACHE.read_text())
    except (OSError, ValueError):
        return None          # missing or corrupt (an interrupted write): treat as no cache


def _write_cache(data):
    tmp = CACHE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data))
    os.replace(tmp, CACHE)   # atomic: a crash leaves the old cache, never half a file


def load(con, path=POSTINGS, use_cache=True, compute_if_stale=True):
    """Fill the advert tables. Returns True if they were loaded.

    A cache is valid when its inputs fingerprint matches and, if the advert
    file is present, the file matches too -- so the cache alone (717 KB) is
    enough on a machine without the 517 MB file."""
    inputs = inputs_fingerprint(con)
    have_file = path.exists()
    cached = _read_cache() if use_cache else None
    if cached and cached.get("inputs") == inputs and (
            not have_file or cached.get("postings") == postings_fingerprint(path)):
        _write(con, cached)
        print(f"Adverts: from cache ({CACHE.name}); inputs unchanged.")
        _report(cached)
        return True
    if not compute_if_stale or not have_file:
        why = "no cache" if cached is None else "the cache is out of date"
        print(f"Adverts: skipped ({why}). Run: python backend/load_adverts.py"
              + ("" if have_file else f"  (needs {os.path.relpath(path, ROOT.parent)})"))
        return False
    data = compute(con, path)
    data.update(inputs=inputs, postings=postings_fingerprint(path))
    _write_cache(data)
    _write(con, data)
    _report(data)
    return True


def compute(con, path):
    """Stream every advert and count, per occupation, what it mentions."""
    csv.field_size_limit(10 ** 9)
    index = cvscan.Index(con)
    skill_rules = [(e, re.compile(rx.pattern)) for e, rx in index.rules]   # run on adverts.clean(text)
    lookup = adverts.build_lookup(con)
    summary = defaultdict(lambda: {"n": 0, "levels": 0, "entry": 0, "years": [], "dates": []})
    counts = Counter()          # (soc, kind, item) -> adverts
    base = Counter()            # (kind, item) -> adverts
    titles = defaultdict(lambda: defaultdict(Counter))   # soc -> key -> raw title -> n
    tables = {}                 # soc -> its software/tool aliases
    read = linked = 0

    with open(path, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            read += 1
            soc = adverts.link(r["title"], lookup)
            # An advert with no listing date can't be placed in time; leave it
            # out everywhere so the summary, counts and baseline agree.
            if not soc or not r["listed_time"]:
                continue
            linked += 1
            text = r["description"] or ""
            low = adverts.clean(text)
            s = summary[soc]
            s["n"] += 1
            if r["formatted_experience_level"]:
                s["levels"] += 1
                s["entry"] += adverts.is_entry(r["formatted_experience_level"])
            s["dates"].append(_date(r["listed_time"]))
            y = adverts.years_asked(text)
            if y is not None:
                s["years"].append(y)
            titles[soc][adverts.norm(r["title"])][r["title"].strip()] += 1

            found = [("req", k) for k in adverts.requirements(text)]
            found += [("skill", e) for e, rx in skill_rules if rx.search(low)]
            if soc not in tables:
                tables[soc] = adverts.aliases(index.occ_software.get(soc, ()), index.occ_tools.get(soc, ()))
            for t in adverts.named_in(tables[soc], text, common=index.common):
                found.append(("software" if t in index.occ_software.get(soc, ()) else "tool", t))
            for kind, item in found:
                counts[(soc, kind, item)] += 1
                if kind in ("req", "skill"):
                    base[(kind, item)] += 1
    if read != EXPECTED_ROWS:
        raise AdvertError(f"{path.name}: expected {EXPECTED_ROWS:,} rows, found {read:,}. Wrong file?")
    base[("all", "adverts")] = linked

    top_titles = []
    for soc, keys in titles.items():
        ranked = sorted(keys.items(), key=lambda kv: (-sum(kv[1].values()), kv[0]))[:6]
        top_titles += [[soc, adverts.display_title(k, raws), sum(raws.values())] for k, raws in ranked]
    return {
        "read": read, "linked": linked,
        "summary": [[soc, x["n"], x["levels"], x["entry"], len(x["years"]),
                     statistics.median(x["years"]) if x["years"] else None,
                     min(x["dates"]), max(x["dates"])] for soc, x in summary.items()],
        "counts": sorted([soc, kind, item, n] for (soc, kind, item), n in counts.items()),
        "titles": top_titles,
        "baseline": sorted([kind, item, n] for (kind, item), n in base.items()),
    }


def _write(con, d):
    con.executescript(SCHEMA)
    con.executemany("INSERT INTO advert_summary VALUES (?,?,?,?,?,?,?,?,?)",
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
    con = sqlite3.connect(DB)
    try:
        ok = load(con, use_cache="--fresh" not in sys.argv)
    except AdvertError as e:
        sys.exit(str(e))
    finally:
        con.close()
    if not ok:
        sys.exit(f"Missing {POSTINGS}. Unzip Kaggle arshkon/linkedin-job-postings into {POSTINGS.parent}.")


if __name__ == "__main__":
    main()
