# Developer guide

What exists, how to run it, what changed over the project, and why each approach
was taken. Written so that you — or a marker, or you in three weeks — can pick the
project up cold and know not just what the code does but why it does it that way.

`CLAUDE.md` is the instruction set for building. This file is the explanation.

---

## 1. Running it

**Requirements:** Python 3.10 or newer, and the two packages in
`requirements.txt` (FastAPI 0.141.1 and uvicorn 0.52.4):
`pip install -r requirements.txt`. Nothing else at run time. React, htm and
pdf.js are vendored in `frontend/vendor/`, so the app works offline.

**Get the data.** The O\*NET 29.0 Database from Kaggle
(`emarkhauser/onet-29-0-database`). Unzip it so the 41 `.txt` files sit
directly in `backend/data/onet/`.

```bash
python backend/load_onet.py
```

This rebuilds `backend/saycep.db` in about 5 seconds and prints what it loaded
(879 occupations, 35 skills, 27,463 ratings, and so on). It ends with two lines
saying the advert counts and the sample listings came **from cache**. Those
caches are committed in `backend/seed/` (ADR-0019, ADR-0022), so a fresh clone
has every screen without the 517 MB advert file. Recomputing them needs that file
(Kaggle `arshkon/linkedin-job-postings`, unzipped into `backend/data/linkedin/`):
`python backend/load_adverts.py --fresh` and
`python backend/load_listings.py --fresh`, about 1–2.5 minutes each. **Any edit
to `adverts.py`, `cvscan.py`, `listings.py` or the two loaders changes the
caches' fingerprint**, so they must then be recomputed and committed. Unit tests
TC-U14d and TC-U15e fail until they are.

`backend/data/` and `saycep.db` are not committed: both are reproducible.

**Run the app.** From the repo root:

```bash
python -m uvicorn app:app --app-dir backend --port 8000
```

One command serves both the API and the app. Open http://127.0.0.1:8000, or
`/docs` for the API. If `saycep.db` is missing, the server refuses to start and
says why (NFR-03).

**Run the tests** (the server running for the API, performance and browser
ones):

```bash
python backend/tests/test_units.py         # 84
python backend/tests/test_api.py           # 126
python backend/tests/test_performance.py   # 6, including PT-01b and PT-05
node frontend/tests/demo_walk.js           # the presentation demo; see frontend/README.md for the rest
```

Dated transcripts of every full run are in `docs/test-results/`.

---

## 2. What exists

| Component | File | Diagram name |
|---|---|---|
| Loaders | `backend/load_onet.py`, `load_adverts.py`, `load_listings.py` | — |
| API: routes only (29 endpoints) | `backend/app.py` | SAYCEP API |
| Database access | `backend/repository.py` | Occupation Repository |
| Gap analysis | `backend/gap.py` | Gap Analyser |
| Pathway generation | `backend/pathway.py` | Pathway Service |
| **The skill-matching model** (the emerging technology) | `backend/recommend.py` | Recommendation Engine |
| CV check, and what to add | `backend/cvscan.py`, `cvadvice.py` | CV Scanner |
| Interview practice | `backend/interview.py` | Interview Practice |
| What employers ask for, and Jobs for you | `backend/adverts.py`, `listings.py` | Advert Summary |
| Interest quiz | `backend/interests.py` | — |
| The app | `frontend/` (one file per part; see `frontend/README.md`) | Web UI |

Module names match the sequence diagram deliberately, so the code and the UML
tell the same story. The API began with eight endpoints (the seven the proposal
lists, plus `PUT /profiles/{id}/target` for FR-03). It now has 29, one group
per module.

### Schema

The schema as built, with every table, is in `docs/architecture.md` (checked
against the database on 18 November). In short:
- the O\*NET tables (occupations, skills, ratings, related jobs, tasks,
  alternate titles, software, tools, interests);
- the advert tables (counts, titles, baseline, sample listings);
- the profile tables (users, their skills, saved jobs, progress events).

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

**The screen leads with words; the figures move to presenter mode.** *(Changed
30 September — see section 4.)* A school leaver reads "Critical for this job",
not "4.00 / 5". The API returns both: every figure still travels in the
response, with a plain label beside it. The labels come from `backend/plain.py`
so the frontend never decides what a number means. `?presenter` shows the
figures again for the marker.

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

### 30 September: words before figures

Walking the journey as a user showed that it spoke to the marker rather than the
user: `3.62 / 5`, `47-2111.00 · Job Zone 3`, a `64%` ring, `1.25 → 3.50`. None of
it meant anything to the school-leaver profile. The plan is in
`plans/ux-and-dashboard.md`. Task 1 of that plan:

- **Importance** becomes one of four labels. The "Very important" line is set
  at the essential threshold (3.5), so a must-have can never be described as
  merely "Important" (checked by TC-U06a/b).
- **Match** becomes Strong / Good / Some overlap. The cut-points (0.55, 0.40)
  were measured: over 300 random 3–12 skill profiles, the top recommendation's
  score has a median of 0.44 and a 90th percentile of 0.56.
- **Job Zone** becomes a preparation sentence. O*NET's education notes are
  American. "Matric" for "high school diploma" is our translation, and the
  original O*NET text is still in the response.
- **Skills** are grouped under seven plain headings, derived from O*NET's own
  element-ID hierarchy. Tapping one explains it using O*NET's description.
- **The "how is essential decided" note** now says the ratings come from
  O*NET's job analysts. That was verified: every row in `Skills.txt` has
  `Domain Source = Analyst`. Workers themselves did not rate these skills, and
  the screen must not suggest they did.

**Task 2, "What is this job?"** Tapping any job opens a panel instead of
setting the target outright. The panel shows O*NET's description (loaded since
September, never shown until now), the preparation needed, and every skill,
ticked if the profile holds it. `GET /occupations/{soc}` takes an optional
`profile_id` for the ticks. Without one, `held` is `null` rather than `false`,
so that a catalogue read never claims the user lacks a skill. The target is set
from the panel's "Aim for this job" button. That adds one tap to the demo path,
and it's the tap that makes exploring possible.

**Tasks 3–4, "My plan" and progress.** Screen 5's button is now "Save as my
plan". It stores the profile id in `localStorage` (ADR-0006) and opens the
dashboard, which shows:

- **The goal and readiness.** Readiness is *counted*: "1 of 2 must-have
  skills". 166 of the 879 occupations have no skill at or above 3.5, so for
  those it counts the five most important skills instead (`ready_basis`).
- **The route, with each step ticked when ready.** `pathway.step_readiness`
  adds `ready` and `ready_missing` to every step.
- **Skills to work on.** Each one moves through *Start learning* to *I can do
  this now*. Only the second closes a gap (ADR-0005, TC-I07).
- **"Update my skills" and "Change my goal".** These reopen screens 2 and 3
  against the *same* profile. When skills are edited from a saved plan, the
  change is applied in place (PUT/DELETE per skill), so "working on it" marks
  survive. Editing before a plan is saved still creates a fresh profile, as
  before.

**Task 5, "A day in this job".** The panel lists what people in the job actually
do, with the most important task first, from O*NET's task statements (ADR-0007).
It's display-only.

These cut-points are presentation choices, not findings from the data. The
classification itself, essential against desirable at 3.5, is unchanged, so
FR-07's behaviour is too.

### 30 September (night): from a journey to an app

The plan is in `plans/full-app.md`. The decisions are in ADR-0008 to ADR-0012.
In short:

- **The front door** is a welcome screen, and sign-in is a plan code, not an
  account (ADR-0008). A real login was asked for and weighed. It would have
  contradicted the privacy argument in the submitted Assignment 3 and added a
  password system to defend.
- **The journey became onboarding.** After *Save as my plan* the app is four
  tabs. Pages (a job, a skill, a comparison) are pushed over a tab that stays
  mounted, so *Back* returns to the same search and scroll position. That was
  a bug the browser walkthrough found.
- **Job pages** add tools, software and related jobs, and search matches
  45,963 alternate titles (ADR-0009).
- **The unlock moment** is computed, not claimed. `PUT
  /profiles/{id}/skills/{element_id}` returns readiness before and after for
  the goal, for its related jobs, and for the whole catalogue.
- **One readiness rule everywhere**: `pathway.step_readiness`, meaning the
  essential skills, or the top five where a job has none. The compare page
  briefly broke this rule ("4 of 5" alongside "nothing to learn") before it
  was fixed (ADR-0010).
- **The interest quiz** correlates twelve of our statements with O\*NET's
  RIASEC profiles (ADR-0011).
- **Progress history** stores a readiness snapshot on each event rather than
  replaying events later (ADR-0012).
- The frontend split into plain scripts that share globals. See
  `frontend/README.md`.

### 5 October: the CV scanner (module 3)

See ADR-0014, which is the important one to read. In short, the obvious design
of TF-IDF from CV text to O\*NET's 35 skills was built three ways, measured,
and lost to plain word overlap each time. The shipped scanner suggests skills
from explicit trigger words (quoted back to the user for confirmation) and
scores a CV against a goal by the software and tools it names. That approach
is measured at r = 0.27 against 0.16 on held-out CVs. The CV is never stored.
The benchmark (`backend/tests/benchmark_cv.py`) scores the shipped code, so
rerun it after changing `cvscan.py`. On 9 October it was rerun after fixing the plural-folding,
which had made "I can" name the tool Canes. Held-out r went from 0.266 to
0.2655 (ADR-0018).

### 5 October: interview practice (module 5)

ADR-0015. The proposal's "chatbot" became practice with rule-based feedback,
because no LLM is allowed. Questions come from the goal's must-have skills and
its top task. Feedback is a checklist: skill shown, situation → action →
result, your own part, a specific detail, length. Nothing is stored and no
accuracy is claimed.

### 5 October: accessibility pass

ADR-0016. The first measurement found 169 axe failures in light mode, nearly
all from one grey text token at 3.0–3.6:1. A keyboard-only walk also showed
that focus never moved: new screens left it on `<body>`, the sheets didn't
trap it, and the tab under a pushed page was still reachable. The fixes were
mostly in shared pieces (tokens, `useDialog`, `focusWhenReady`, `inert` on the
tab host), so they cover every screen at once. Fake tab and radio roles became
honest toggle buttons. The result is 0 automated failures in both themes and
at 320 px, and 19 of 19 keyboard checks. No real screen-reader test has been
done.

### 5 October: what employers ask for (module 4)

ADR-0017. Step 0 found no real South African adverts on Kaggle; the one
labelled as such was generated from four templates. So module 4 summarises
real American adverts from 2024 instead of offering openings. The link to
O\*NET is the advert title, kept strict (one candidate, generic titles
dropped). The tempting shortcut was to reuse the CV scanner's matching
unchanged. Measuring it on adverts found boilerplate ("customers", "teams")
everywhere, and a plural-folding bug that read "can" as the tool Canes. So
skills are shown only where they're over-represented against all adverts,
with a measured, weak agreement with O\*NET. Tools use a stricter matcher.
The advert pass is slow, so it's cached and fingerprinted on its inputs.
Get the data with the Kaggle API (`arshkon/linkedin-job-postings`), unzip it
into `backend/data/linkedin/`, and run `python backend/load_onet.py`.

### 8–24 October: corrections, a committed seed, and honest accuracy

- **A code review found 12 problems, all fixed.** Among them: the cache
  fingerprint hashed a row's memory address, so it never matched.
- **The advert counts were committed** (ADR-0019), so a fresh laptop clone shows
  every screen.
- **TR-01 is reported two ways** (ADR-0020): 59.7% as first defined, and
  58.5% (95% interval 54.6–62.1) with the target job removed, against 25.9% by
  chance. Say the stricter figure if asked.
- **A minimal Fly.io deploy** (ADR-0021).

### 6 November: Jobs for you, and CV upload

- **Job cards** (ADR-0022): real adverts, one per card, ranked by the share of
  the skills each mentions that the user has. They're always labelled as sample
  listings: US, 2024, closed. Kept in their own module and cache, so the
  committed advert counts stayed valid.
- **CV upload** (ADR-0023): PDF, Word or text, read **in the browser**, so only
  the text is sent and the measured scanner is unchanged. pdf.js is vendored with
  `isEvalSupported` off (CVE-2024-4367). Testing a designed two-column CV found
  Word's bullets turning into box characters; now fixed.

### 16 November: what to add, and better interview practice

- **"What to add"** (ADR-0024): requirements, tools and skills a CV lacks for
  the goal, with how common each is in real adverts and an example line. It
  understands South African wording ("Code 8", "N2", "matric").
- **A technical interview question** about the tool the job's adverts name most.
  This is only asked where at least 5 adverts and 5% of them name it, which
  covers 168 of the 879 jobs. O\*NET's "hot technology" list was tried first and
  rejected: it asked coroners about Git.
- **Retry** shows "2 of 7 → 7 of 7" and what improved.
- **No new data:** no Kaggle interview dataset exists, and the course catalogues'
  licences couldn't be verified.

### 17 November: the skill-matching model, made visible

At the 6 November demo the lecturer was unsure what the emerging technology was.
It worked, but nothing on screen showed a model at work. So (ADR-0025):
- **"How we matched you"** walks one person's and one job's real numbers through
  the four steps (five since ADR-0027). It shows how centring spreads the scores: for Thabo, 0.27–0.58
  without it, −0.56 to 0.64 with it.
- **A "Skill-matching model" tag** wherever the engine runs.
- **Two new uses:** "Jobs your CV points to", and "Jobs with the closest skills".
- **PT-05**, a second accuracy figure: 60.6% agreement with O\*NET's experts,
  against 5.2% by chance.
- **Found while measuring:** job to job, centring makes no difference, because
  two jobs' ratings share a scale. It matters for matching a *person*, whose
  ticks are 0 or 1.
- **A claim was corrected before it was built on:** the plan said "about 0.9
  without centring", which was the job-to-job figure, not the person-to-job one.

### 19 November: the model, improved (ADR-0027)

- **The lecturer found the accuracy unconvincing.** So ten techniques were
  tested on PT-01b's measure, with the learning ones cross-validated, and the
  best re-tested on simulated, messy users.
- **The winner:** compare the person's yes/no ticks with each job's yes/no
  must-have list (top 5 for jobs with none), as well as its ratings, and
  average the two cosines. **58.5% → 67.5%**; with messy users 46.8% → 53.6%.
- **What didn't help:** z-scores, LDA, related-job smoothing and PCA. Learned
  weights looked best on the clean test and fell apart on messy users: a
  textbook overfit, caught by testing beyond the training set's shape.
- **The structure:** `recommend.Model` holds both views; every person-to-job
  match goes through it. Job to job stays on ratings, which are better there
  (PT-05). The panel shows the must-have list and the average.

---

## 5. Where things are

| File | What it holds |
|---|---|
| `CLAUDE.md` | How to work on this project — constraints, preferences |
| `STATUS.md` | Current state, what is next |
| `docs/DECISIONS.md` | Append-only ADR log — the load-bearing decisions |
| `docs/data-sources.md` | O*NET, and the verified shortlist it replaced |
| `docs/architecture.md` | Demo vs production architecture |
| `docs/functional-requirements.md` | Assignment 2: the functional requirements |
| `docs/timeline.md` | The plan and its gates, to the final presentation |
| `docs/presentation.md`, `docs/presentation-script.md` | The demo path, set-up and Q&A; what to say over each slide |
| `docs/deploy.md` | The optional Fly.io deploy |
| `docs/test-results/` | Dated transcripts of every test run |
| `docs/plans/` | Approach documents, written before code |
| `docs/BACKLOG.md` | Noticed, deliberately deferred |
| `docs/archive/` | The superseded August plan |

The git history is intended to be readable: each commit says what changed and why,
and the two re-plans are visible as commits rather than as silent rewrites.
