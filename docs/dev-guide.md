# Developer guide

What exists, how to run it, what changed over the project, and why each approach
was taken. Written so that you — or a marker, or you in three weeks — can pick the
project up cold and know not just what the code does but why it does it that way.

`CLAUDE.md` is the instruction set for building. This file is the explanation.

---

## 1. Running it

**Requirements:** Python 3.10+. Nothing else — the loader uses only the standard
library. There is no `requirements.txt` yet because nothing has needed one.

**Get the data.** The O*NET 29.0 Database from Kaggle
(`emarkhauser/onet-29-0-database`). Kaggle requires a login to download. Unzip so
the `.txt` files sit directly in `backend/data/onet/`.

```bash
python backend/load_onet.py
```

Rebuilds `backend/saycep.db` from scratch and prints what it loaded:

```
occupations                879
skills                      35
occupation_skills       27,463
related_occupations     17,580
job_zone_reference           5
```

Neither `backend/data/` nor `saycep.db` is committed. Both are reproducible from
the source files, and 97 MB of third-party data has no business in a git history.

**Run the app.** From the repo root:

```bash
python -m uvicorn app:app --app-dir backend --port 8000
```

Open http://127.0.0.1:8000 for the journey, `/docs` for the API. Needs FastAPI
and uvicorn installed. If `saycep.db` is missing the server refuses to start and
says why (NFR-03).

---

## 2. What exists

| Component | File | Diagram name |
|---|---|---|
| Loader | `backend/load_onet.py` | — |
| API — routes only | `backend/app.py` | SAYCEP API |
| Database access | `backend/repository.py` | Occupation Repository |
| Gap analysis | `backend/gap.py` | Gap Analyser |
| Pathway generation | `backend/pathway.py` | Pathway Service |
| Recommendation | `backend/recommend.py` | Recommendation Engine |
| The journey | `frontend/` | Web UI |

Module names match the sequence diagram deliberately, so the code and Figure 4
tell the same story. The API has eight endpoints: the seven the proposal lists,
plus `PUT /profiles/{id}/target`, which FR-03 needs — see
`docs/plans/frontend-journey.md`.

### Schema

```sql
occupations         (soc_code PK, title, description, job_zone, source_dataset)
skills              (element_id PK, name, description, source_dataset)
occupation_skills   (soc_code, element_id, importance, importance_scale_max,
                     source_date, PK(soc_code, element_id))
related_occupations (soc_code, related_soc_code, tier, sort_index)
job_zone_reference  (zone, name, experience, education, training, examples, svp_range)
```

`users` and `user_skills` are designed but not yet created — they arrive with the
API, since nothing can write to them until then.

---

## 3. Why these approaches

The decisions inside the code, and the reasoning you would need if questioned on
them.

**The SOC code is the primary key, not an invented integer.** Every O*NET file
keys on `O*NET-SOC Code`. Generating our own ids would mean maintaining a mapping
table that buys nothing and adds a place for bugs to live. The SOC code is also
citable on screen, which serves FR-4.

**Importance is stored raw; the essential/desirable label is derived at query
time.** The obvious alternative is to store a boolean `is_essential` computed at
load. That would bake the threshold into the data, making a change of mind a full
reload. Storing O*NET's 1–5 rating means the threshold is a single constant read
where the gap is labelled, and it lets the screen show *"Troubleshooting —
essential (4.0 out of 5)"*. The rating on screen answers "how do you decide
essential?" before it is asked.

**Standard library only.** Pandas would do the load in fewer lines, but the whole
job is reading five tab-delimited files and inserting rows. Adding a dependency
for that is against the project's own rule, and a demo that runs on a bare Python
install is one less thing to go wrong on someone else's machine.

**The loader drops and recreates.** No migrations. The O*NET files on disk are the
source of truth, so the database is a derived artifact — rebuilding is always
correct and always fast. Migrations matter when the data is the asset; here the
data is reproducible in seconds.

**It fails loudly on unexpected row counts.** The loader hard-codes the row counts
from O*NET's published data dictionary and exits if the files disagree. A
partially downloaded file would otherwise load cleanly and produce a database that
looks fine and is quietly wrong — and that surfaces in front of the marker rather
than in a test.

**879 occupations, not the 1,016 in the catalogue.** Only 879 are complete across
occupations, skills, job zones and related-occupations. An occupation with no
skills data gives the gap analyser nothing to say, so letting it into target
selection creates a dead end a demo can walk into. The other 137 are excluded at
load.

**"Not relevant" skills are filtered via a join to the Level row.** This one is
counter-intuitive. `Skills.txt` holds two rows per occupation-skill pair — one
Importance (IM), one Level (LV). The `Not Relevant` flag is `n/a` on every IM row
and only ever set on the LV row. Filtering the importance rows directly does
nothing; you have to look at the pair's other row. 3,302 ratings are excluded this
way, and all of them sit at importance of 2.0 or below.

Related: `Recommend Suppress` is never `Y` on an IM row — all 124 are LV. The
filter is kept in the loader anyway, because correctness should not depend on that
staying true in a future O*NET release.

**Monolith, SQLite, one service.** Covered in `architecture.md`. Short version:
three services is where three weeks goes, and the module boundaries are kept clean
so the split stays possible later.

---

## 4. What changed, and why

The project was re-planned twice. Both are recorded as ADRs in `DECISIONS.md`;
this is the narrative.

### August to September: from dissertation to demo

The original plan was a seven-phase build submitting a dissertation on 30 November
2026, with a Node + Python two-service architecture, a 50-profile benchmark and a
20–30 person UAT. The project's endpoint moved to the **October presentation with
a working demo**, which collapsed that plan. The August material is in
`docs/archive/`, each file headed with what replaced it.

### The Kaggle rule killed the original data route (ADR-0002)

The proposal was built on the ESSA public API plus a hand-curated TVET/SETA
dataset. Two things ended that: ESSA has no public API — it is a login-gated
portal — and the course requires all system data to come from Kaggle, with
anything else needing the lecturer's approval in person.

Seeking that approval would have put a meeting and an uncertain ruling on the
critical path of a three-week build. So system data comes from Kaggle, and South
African statistics are cited as written background only.

**This has a consequence worth being honest about.** The original success criteria
required the unqualified-user journey to end at a named institution with real
entry requirements. Kaggle data cannot support that. It went out with the November
submission rather than being solved, and ADR-0002 records it so the fact is on the
record rather than discovered in the room.

### Five datasets verified; two were unusable

Nothing was built until the shortlisted datasets were actually opened. Two failed:

- **"Job Posting Data in South Africa"** is not South African. Its most common
  location is Bangalore, India; bosch.com and zf.com account for 89% of postings;
  the `Ticker` column is 100% null. A global scrape with a country name attached.
- **"Skill & Career Recommendation"** is not a role-to-skill map. It is one row
  per student with psychometric scores and a recommended profession.

And the intended spine had a defect that reached FR-2: its skills field was
documented as semicolon-separated and was not — across 108 rows sampled, zero
semicolons, just multi-word skills run together with no delimiter. With roughly
one row per occupation it also had no within-occupation frequency from which to
derive essential versus desirable.

This is why verification came before building. Every one of those failures would
have surfaced during the demo instead.

### Hybrid to O*NET (ADR-0003)

A hybrid was briefly adopted — occupation catalogue from one dataset, skill
importance inferred from resume frequencies in another. It was superseded within
the day, before any code, after searching Kaggle for the trade coverage the
school-leaver profile needed turned up the full **O*NET 29.0 Database**, published
by the U.S. Department of Labor under CC BY 4.0.

It resolved four problems at once:

| Problem with the hybrid | What O*NET gives |
|---|---|
| Essential/desirable threshold would be invented | A published 1–5 importance rating from an occupational survey |
| Pathway step order needed a heuristic we would defend | `Related Occupations.txt`, ordered by expert review |
| Almost no trade or artisan coverage | The full occupational classification; Job Zones 1–3 are 59% of it |
| An unproven join between job titles and resume roles | Everything keys on the SOC code — no fuzzy matching anywhere |

**It is United States data.** This does not worsen the position ADR-0002 already
established — the South African framing lives in the problem statement, not in
what the system ingests. An authoritative government dataset is easier to defend
than an anonymous synthetic CSV. Be ready to say exactly that.

### What loading it settled

- **FR-1's open risk closed.** The concern was whether a three-step pathway exists
  across the graph. All 879 occupations have three or more reachable primary
  neighbours, so the promise holds catalogue-wide and the planned Job Zone
  fallback is not needed.
- **FR-3's stated reasoning does not hold.** It justifies two capture paths by
  saying an enrolled student has a qualification to infer skills from. O*NET has
  no qualification-to-skills mapping. The school-leaver half is fine — RIASEC
  scores all 923 occupations. The enrolled-student half is an open decision in
  `plans/api-first-slice.md`.
- **Skill capture got easy.** O*NET's skills taxonomy is 35 entries, so a capture
  screen can list all of them. The search-and-match problem the resume-based plan
  would have had does not exist.

---

## 5. Where things are

| File | What it holds |
|---|---|
| `CLAUDE.md` | How to work on this project — constraints, preferences |
| `STATUS.md` | Current state, what is next |
| `docs/DECISIONS.md` | Append-only ADR log — the load-bearing decisions |
| `docs/data-sources.md` | O*NET, and the verified shortlist it replaced |
| `docs/architecture.md` | Demo vs production architecture |
| `docs/functional-requirements.md` | Assignment 2 — FR-1 to FR-4 worked, rest to draft |
| `docs/timeline.md` | Three-week plan and its gates |
| `docs/plans/` | Approach documents, written before code |
| `docs/BACKLOG.md` | Noticed, deliberately deferred |
| `docs/archive/` | The superseded August plan |

The git history is intended to be readable: each commit says what changed and why,
and the two re-plans are visible as commits rather than as silent rewrites.
