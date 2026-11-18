# Architecture Decisions

Append-only log. Each entry is an ADR (Architecture Decision Record). Never
rewrite a past decision — if it changes, add a new entry that supersedes it and
say so.

Status values: **Proposed** (awaiting sign-off) · **Accepted** · **Superseded**.

---

## ADR-0001 — Job data source: Adzuna, not ESSA

**Date:** 2026-08-03
**Status:** Superseded by ADR-0002 (2026-09-10) — never advanced past Proposed
**Phase:** 0 (spike), feeds Phase 2 integration
**Relates to:** RISKS.md risk 1, ROADMAP Phase 0 spike "Can I get job data?"

### Context

The proposal assumed ESSA (Employment Services of South Africa) exposes an API.
Phase 0 requires confirming a real, machine-readable job-data source before any
architecture is built on it.

### Findings

**ESSA — no usable public API.** The ESSA system is a login-gated JSF web
application at `essa.labour.gov.za` (the `/EssaOnline/WebBeans/` path confirms a
server-rendered JavaServer Faces portal). Registration requires a South African
ID number. A genuine search surfaced only how-to guides for job seekers and
government PDFs on applying through the portal — no developer documentation, no
API, no feed, no machine-readable endpoint. Confirming its non-existence with
total certainty would mean contacting the Department of Employment and Labour
directly, but for architecture purposes ESSA must be treated as unavailable.
Scraping it is not viable: it is login-walled behind an SA ID, and building on a
scraper of a government JSF portal is fragile and out of scope for this project.

**Adzuna — confirmed suitable.** Adzuna runs a RESTful JSON API covering 12
countries including South Africa (country code `za`). Auth is a simple
`app_id` + `app_key` pair obtained by registering at developer.adzuna.com. The
jobs search endpoint is country-scoped in the path:

```
https://api.adzuna.com/v1/api/jobs/za/search/1?app_id=...&app_key=...
```

Free developer tier: approximately 1,000 API calls per month, rate-limited to
about 25 requests per minute. Returns JSON. Also exposes salary, regional, and
category endpoints that may be useful later for the roadmap's salary-range data.

### Decision

Use **Adzuna** as the job-data source. Do not architect around ESSA.

### Why this fits the project constraints

- The CLAUDE.md rule "job data is cached, not fetched live per request — fetch on
  a schedule into our own store" aligns exactly with Adzuna's quota. A scheduled
  batch pull of SA listings (paginated, 50/page) costs a few hundred calls per
  refresh cycle at most — comfortably inside 1,000/month. Live per-request
  fetching would blow the quota; the rule already forbids it.
- Simple key-pair auth, no OAuth, no scraping, no login wall.
- JSON responses fit the "validate against a schema before it touches the DB"
  rule directly.

### Open verification (blocks moving this to Accepted)

- [ ] Register for an Adzuna key and run one `/jobs/za/search/1` call to confirm
      (a) the volume of real SA listings is enough to be useful and (b) the field
      shape (title, company, location, salary_min/max, category, redirect_url).
      This needs the sandbox (currently down) or a manual test with curl/Postman.
- [ ] Read Adzuna's Terms of Service re: caching results into our own DB and
      displaying them to users, and any attribution requirement. Link:
      https://developer.adzuna.com/docs/terms_of_service

### Consequences

- `.env.example` will need `ADZUNA_APP_ID` and `ADZUNA_APP_KEY` placeholders.
- The Phase 2 "one script, real data, in the DB" deliverable targets Adzuna ZA.
- If live volume turns out to be too thin for SA, revisit: candidate fallbacks
  are other aggregators with ZA coverage, or a curated seed set. Record as a new
  ADR that supersedes this one.

---

## ADR-0002 — All system data comes from Kaggle; the job-API route is abandoned

**Date:** 2026-09-10
**Status:** Accepted
**Supersedes:** ADR-0001
**Relates to:** `data-sources.md`, `archive/2026-08-risks.md`, FR-4

### Context

Two things changed after ADR-0001 was written.

The course requires that project data come from Kaggle. Where no suitable Kaggle
dataset exists, the process is a consultation with the lecturer in his office,
presenting the proposed own or simulated data, and he decides whether it is
acceptable or which Kaggle dataset to use instead.

Separately, the project's endpoint moved. It is now assessed at the October 2026
presentation with a working demo, not at a 30 November dissertation submission.
Three weeks, one developer, alongside a full-time job.

### Decision

System data comes from Kaggle. South African statistics are cited as background
in the written proposal only, and are never loaded into the system.

The alternative — building on ESSA or Adzuna and seeking approval for it — puts a
consultation and a decision that cannot be guaranteed onto the critical path of a
three-week build. That risk is not affordable.

### Consequences

- **ADR-0001 is superseded.** Adzuna never advanced past Proposed and no code was
  written against it, so there is nothing to unwind. The finding it records —
  that ESSA has no public API and is a login-gated JSF portal — stays useful, and
  is worth having ready if anyone asks why an obvious South African data source
  went unused.
- **The curated TVET/SETA dataset is dropped.** The August plan called it the
  hidden critical path. It is now out of scope entirely.
- **A collision worth knowing about.** The August success criteria required the
  unqualified-user journey to terminate in a named institution with real entry
  requirements, and called that the criterion the project would actually be judged
  on. Kaggle data cannot support it. That criterion went out with the November
  submission rather than being solved, and this entry exists so that fact is on
  the record rather than discovered in the room.
- **Provenance becomes a feature.** FR-4 records and displays the source dataset
  and publication date for every occupation and skill record shown to the user.
  Two columns and a label, and it answers the data question before it is asked.
- **Nothing gets built on unverified data.** The five shortlisted datasets in
  `data-sources.md` have unconfirmed columns and row counts. That verification is
  the Week 1 gate.

### The answer to "where does your data come from?"

The system processes Kaggle-sourced data. The South African framing lives in the
problem statement and the design decisions, not in the data the system ingests.
State the distinction plainly — it shows the rule was understood rather than
worked around.

---

## ADR-0003 — The O*NET 29.0 Database is the data spine

**Date:** 2026-09-10
**Status:** Accepted
**Relates to:** ADR-0002, `data-sources.md`, `plans/data-spine.md`, FR-1 to FR-4

### Context

Verifying the five shortlisted datasets (recorded in `data-sources.md`) left the
intended spine unusable as specified: its skills field has no delimiter, and with
roughly one row per occupation there is no within-occupation frequency from which
to derive essential versus desirable. A hybrid was briefly adopted — occupation
catalogue from one dataset, skill importance inferred from resume frequencies in
another — and written up as a plan.

That hybrid had two weaknesses. It rested on an unproven join between job titles
and resume roles, and the essential/desirable threshold would have been invented
rather than measured. It also left the school-leaver profile thin, because the
resume data skews technical and carries little trade or artisan coverage.

Searching Kaggle for trade coverage surfaced the full O*NET database, published
under CC BY 4.0 by the U.S. Department of Labor. It resolves all three problems
at once, and it is on Kaggle, so ADR-0002 is satisfied without a consultation.

### Decision

The data spine is the **O*NET 29.0 Database**, obtained from Kaggle
(`emarkhauser/onet-29-0-database`).

### Verification

File structure was confirmed against O*NET's own published data dictionary at
onetcenter.org, not assumed. Reading that documentation is not a second data
source — the data itself comes from the Kaggle copy.

| File | Rows | What it gives |
|---|---|---|
| `Occupation Data.txt` | 1,016 | SOC code, title, description |
| `Skills.txt` | 61,530 | Skill ratings per occupation, `Scale ID` of IM (Importance) or LV (Level), plus confidence intervals |
| `Job Zones.txt` | 923 | Preparation level 1–5 per occupation |
| `Related Occupations.txt` | 18,460 | 10 primary + 10 supplemental related occupations, with a relatedness tier and an `Index` ordering them by expert review |

### Why this over the hybrid

- **FR-2's threshold stops being invented.** O*NET publishes an Importance rating
  per skill per occupation from an occupational survey. The essential/desirable
  split becomes a cut on a published scale rather than a percentage we chose. The
  question "why that number?" gets a defensible answer.
- **FR-1's ordering gets a provenance.** `Related Occupations.txt` is ordered by
  expert review. Pathway steps can cite that instead of a similarity heuristic
  we would then have to justify.
- **FR-3's second profile becomes buildable.** `Job Zones.txt` grades occupations
  1–5 by required preparation. Zones 1–2 are the non-degree routes the
  school-leaver profile exists to serve. `Interests.txt` supplies a RIASEC
  interest inventory for aptitude-based intake where no qualification exists.
- **Trade and artisan coverage.** O*NET covers the full occupational
  classification. The data dictionary's own worked example is SOC 47-2231.00, a
  construction trade.
- **FR-4 gets its strongest form.** "O*NET 29.0, U.S. Department of Labor, CC BY
  4.0, dated" is a better provenance label than any other candidate offered.
- **The join risk disappears.** Every file keys on the O*NET-SOC code. No fuzzy
  title matching anywhere.

### Consequences

- The hybrid plan is superseded before anything was built on it. That plan lived
  in `plans/data-spine.md` and is rewritten, not archived — nothing depended on it.
- **The data is United States occupational data.** This does not worsen the
  position ADR-0002 already established: the South African framing lives in the
  problem statement, not in what the system ingests. It arguably improves it,
  since an authoritative government source is easier to defend than an anonymous
  synthetic CSV. Be ready to say so.
- Loading is more work — around 30 tab-delimited files rather than two CSVs — but
  the joins are clean rather than fuzzy, so the risk is lower even as the effort
  rises.
- `Skills.txt` carries `Recommend Suppress` and `Not Relevant` flags. Rows so
  marked are low-precision and must be filtered, or the gap analyser will present
  ratings the source itself does not stand behind.
- The Resume Dataset stays a candidate for the CV scorer if that module is ever
  built. The other four from the original shortlist are now unused.


---

## ADR-0004 — Skill capture is shared; the two profiles diverge after it

**Date:** 2026-09-17
**Status:** Accepted
**Relates to:** ADR-0003, FR-3, `plans/api-first-slice.md`, `user-profiles.md`

### Context

FR-3 originally promised a *different initial skill profile* for each of the two
user types, justified by an enrolled student having a qualification to infer
skills from and a school-leaver having none.

Loading O*NET showed the first half of that cannot be built. O*NET carries the
distribution of education levels held by people already *in* an occupation. It has
no mapping from a qualification to the skills that qualification confers. Nothing
in the Kaggle-sourced data does.

A second factor: with the presentation in the first week of October, the real
remaining budget is four full days plus ten evenings. An extra capture screen and
its pre-fill logic is roughly a day of that.

### Decision

Both profile types capture skills the same way — self-assessment against O*NET's
35-skill taxonomy. The two paths diverge at **target selection**: the enrolled
student searches for a target directly; the school-leaver browses by Job Zone,
which surfaces the occupations reachable without a degree.

FR-3 is reworded accordingly.

### Alternatives rejected

- **Nearest-occupation pre-fill.** The student names their closest role and we
  pre-fill skills from it. Preserves FR-3's original wording and was the
  recommendation before the time budget was clear. Rejected on cost: an extra
  screen and extra logic on the tightest weekend in the plan, and a half-built
  version would be worse than a complete simple one.
- **Education-level filtering.** Uses real O*NET data but captures no skills, so
  it narrows targets without building a profile. Kept as a possible later
  refinement of the school-leaver route.

### Consequences

- **The divergence is now visible rather than internal.** Two different screens
  beats two different hidden capture rules — easier to demonstrate, and easier to
  answer questions about.
- **It is defensible on honesty grounds, which is stronger than the original.**
  The answer to "why the same capture?" is that inferring someone's skills from
  their qualification would be inventing data the source does not contain. That is
  a better answer than the one it replaces.
- **RIASEC intake is deferred.** `Interests.txt` scores all 923 occupations and
  remains the right long-term answer for the school-leaver. Specified in the
  proposal, not built for October. Say which is which.
- FR-3's wording changed on assessed material. The change and its reason are
  recorded here so the original can be explained if asked.

---

## ADR-0005 — Progress has two states; only "can do it now" closes a gap

**Date:** 2026-09-30
**Status:** Accepted
**Relates to:** `plans/ux-and-dashboard.md` (Tasks 3–4), FR-02, FR-07, ADR-0006

### Context

The "My plan" dashboard lets a user record progress on the skills their gap
names. The choice was between one state ("I can do this now"), which only adds
rows to `user_skills` and needs no schema change, and two states, which add
"working on it". The two-state option was chosen on 30 September.

### Decision

`user_skills` gains `status` (`held` | `learning`, default `held`) and
`updated_at`. `repository.profile_skill_ids` returns only `held` rows. It is the
single function the gap analyser, pathway service and recommendation engine read
a profile through, so **`learning` cannot close a gap, change a pathway, or move
a recommendation**. Three endpoints serve it: `GET /profiles/{id}` reads it,
`PUT /profiles/{id}/skills/{element_id}` sets a status, and `DELETE` removes one.

### Consequences

- **Schema change on the as-built schema.** `architecture.md` is updated.
  `ensure_profile_tables` adds the column in place when it opens an older
  database, and existing rows default to `held`, so no gap changes on upgrade
  (TC-U07).
- **Progress is self-reported.** SAYCEP has no way to check that someone can
  now troubleshoot. That is the same trust basis as FR-02's skill capture, and
  it should be said plainly if asked. Qualification verification is out of
  scope.
- **A new functional requirement is implied.** Recording progress and
  recomputing the gap isn't covered by FR-01 to FR-10. Drafting it is the
  project owner's work (CLAUDE.md), and it isn't recorded here.

---

## ADR-0006 — The dashboard comes after the journey, not inside it

**Date:** 2026-09-30
**Status:** Accepted
**Relates to:** NFR-02, ADR-0005, `plans/ux-and-dashboard.md`

### Context

NFR-02 requires that a first-time user reaches a displayed pathway in no more
than five screens. Walking the built journey showed that it ended abruptly after
the pathway, with nothing to come back to. The "My plan" dashboard answers that,
so where it sits relative to NFR-02 needs a written answer.

### Decision

The journey stays at five screens and still ends on the displayed pathway. The
dashboard opens only when the user chooses "Save as my plan" on screen 5. From
then on it's the screen the app opens on. NFR-02 measures the path *to* the
pathway, and that path is unchanged.

The saved plan is a profile id in the browser's `localStorage`, **not an
account**. There's no login, no password and no personal data beyond the
skills ticked. If the browser forgets the id, the user walks the journey again.

### Alternatives rejected

- **Accounts.** They would give the plan real persistence, but they add a
  security surface the demo would have to defend, and a sign-up screen would
  break NFR-02's spirit even if it sat outside the count.
- **The dashboard as screen 6.** That would break NFR-02 outright.

### Consequences

- Gamification stays off the table, as `BACKLOG.md` recorded on 26 September:
  there are no streaks, XP or badges. Progress is counted in skills toward the
  user's own goal ("1 of 2 must-haves").
- The route on the dashboard re-sequences as skills are added, because FR-08
  orders steps by closeness to the current profile. The screen says so. Freezing
  the route at save time would need another schema change, and it's in
  `BACKLOG.md`.

---

## ADR-0007 — Load O*NET task statements for "A day in this job"

**Date:** 2026-09-30
**Status:** Accepted
**Relates to:** ADR-0002, ADR-0003, `plans/ux-and-dashboard.md` (Task 5), NFR-03, NFR-04

### Context

The "What is this job?" panel had O*NET's one-paragraph description and nothing
else to show what a job involves. A school leaver choosing between
"Boilermakers" and "Power-Line Installers" needs to know what the day looks
like. The same Kaggle O*NET 29.0 dataset (ADR-0003) already contains
`Task Statements.txt`, which holds plain sentences such as *"Work from ladders,
scaffolds, or roofs to install, maintain, or repair electrical wiring"*.

### Decision

Load it into a new `occupation_tasks` table. Each task's importance comes from
`Task Ratings.txt` (the IM scale, suppressed ratings excluded), and it is used
only to put the most important tasks first. The panel shows four tasks by
default and up to eight on request.

### Verification (30 September)

- 18,796 statements, of which 17,931 belong to the 879 usable occupations.
  **Every one of the 879 has at least one** (TC-U08).
- Task Ratings has exactly one IM rating per task: 17,639 in total, 6 marked
  Recommend Suppress. 298 loaded tasks have no usable rating and sort last.
- Most statements are incumbent-sourced (13,064 of 18,796). That is unlike
  skill importance, which is entirely analyst-rated.

### Consequences

- **Schema change** to the reference data. `architecture.md` is updated, and
  the loader's row-count guard (NFR-03) covers both new files. The rebuild rises
  from about 0.5 s to 1.1–2.0 s (measured three times, plus PT-04), still well
  inside NFR-04's 60 s.
- **No new data source.** It's the same Kaggle dataset, so ADR-0002 holds.
- The tasks are display-only. They do not feed the gap, the pathway or the
  recommendations, so none of FR-06 to FR-08's measured behaviour changes.

---

## ADR-0008 — Sign-in is a plan code, not an account

**Date:** 2026-09-30
**Status:** Accepted
**Relates to:** ADR-0006 (extends it), `plans/full-app.md`, Assignment 3 §4.2 and §5.4

### Context

The project owner asked for a login page. Assignment 3, submitted today, lists
user accounts as out of scope. Its privacy section argues that no login is
needed because SAYCEP holds no personal data. Real accounts would mean
passwords, hashing, sessions and POPIA obligations in the demo.

### Decision

- A welcome screen becomes the app's front door. It offers *I'm new*, with an
  optional first name, or *I have a plan code*.
- Every profile gets a **plan code**: six characters from an alphabet with no
  look-alikes (`23456789ABCDEFGHJKMNPQRSTUVWXYZ`, about 887 million codes),
  shown as `K7M-2QX`.
- `POST /plans/resume` opens a plan by its code on any device. Case, spaces
  and dashes are ignored.
- `users` gains `display_name` (optional, at most 40 characters) and
  `plan_code` (unique index), and both are upgraded in place.

### Alternatives rejected

- **Username and password accounts.** They contradict the submitted document's
  scope and privacy argument, and add a security surface to defend.
- **A login screen that doesn't authenticate.** It would be misleading, and it
  fails the first time someone types a wrong password and still gets in.

### Consequences

- **The code is a bearer credential, not a password.** Anyone holding it can
  open and change that plan. That's acceptable only because a plan holds
  nothing personal beyond an optional first name. The dashboard says so next
  to the code. There's no rate limiting, which would be needed before public
  use (Assignment 3 §5.4 already names this).
- The first name is the first personal detail SAYCEP stores. It's optional,
  never required and clearable. The privacy argument is weaker but still
  holds.
- Tests: TC-I10a–e, TC-U09a–c.

---

## ADR-0009 — Load alternate titles, software and tools for job pages and search

**Date:** 2026-09-30
**Status:** Accepted
**Relates to:** ADR-0002, ADR-0003, ADR-0007, `plans/full-app.md` slice 1, FR-04

### Context

Jobs were shallow, a panel and nothing more. Search matched only O\*NET's 879
official titles, so a user who knew a job by another name found nothing. The
same Kaggle O\*NET 29.0 download contains three files that fix both.

### Decision

Load three new tables, row-count guarded like the rest:

- `occupation_alt_titles`: 45,963 titles, covering all 879 jobs. Search
  matches them, and official titles rank first.
- `occupation_technology`: 30,134 software examples, all 879 jobs, with
  O\*NET's *Hot Technology* flag used to order them.
- `occupation_tools`: 40,659 tools, covering 878 jobs. O\*NET doesn't rank
  tools, so they're grouped by category, largest group first.

The job page also shows O\*NET's primary related occupations, which are
already loaded, as *Jobs like this*.

### Verification (30 September)

- "conduit installer" finds Electricians through its alternate title (TC-I08a).
- Every official-title match is still returned, so FR-04's criterion holds
  (TC-I08c).
- Electricians has 164 tools. Its first related job is Helpers--Electricians,
  in O\*NET's review order (TC-I09).
- O\*NET's titles are American, so "sparky" finds nothing. The search hint
  suggests only examples that do return results.

### Consequences

- Schema change: three reference tables added, and no existing table changed.
- It's display- and search-only. The gap, pathway and recommendations are
  unchanged.
- *Education, Training, and Experience* was considered and left out. It covers
  858 of 879 jobs, and its US qualification percentages would mislead a South
  African user (`plans/full-app.md`).

---

## ADR-0010 — Saved jobs and comparison

**Date:** 2026-09-30
**Status:** Accepted
**Relates to:** ADR-0005, `plans/full-app.md` slice 3

### Context

Once a user has found a few jobs they like, their real question is "which of
these is closest for me?" There was nowhere to keep jobs, and no way to set them
side by side.

### Decision

- A new profile table: `saved_occupations (profile_id, soc_code, saved_at)`.
  Saving the same job twice is a no-op.
- `GET /profiles/{id}/saved` returns saved jobs with the user's readiness for
  each.
- `GET /profiles/{id}/compare?soc=…` takes two or three jobs and returns
  training, readiness, all-skills coverage, what is still to learn, and the
  must-haves they share.
- Readiness uses the same rule everywhere: `pathway.step_readiness`, meaning
  the essential skills, or the top five where a job has none. "Still to learn"
  is drawn from that same rule, so a job can never read as "4 of 5" and
  "nothing to learn" at once. That bug was found in the browser before release
  (TC-I12c).

### Consequences

- Schema change: one table added to the profile schema, created on startup
  like the others.
- Display only. The gap, pathway and recommendations are unchanged.

---

## ADR-0011 — A short interest quiz, matched to O\*NET's RIASEC profiles

**Date:** 2026-09-30
**Status:** Accepted
**Relates to:** ADR-0004 (acts on its deferred RIASEC intake), `plans/full-app.md` slice 4

### Context

ADR-0004 said the school-leaver should start from interests rather than job
names, and deferred it. `Interests.txt`, in the same Kaggle download, scores
all 879 jobs on O\*NET's six interest areas (1–7 scale).

### Decision

- Load the six OI scores per job into `occupation_interests`: 5,274 rows,
  which is 879 × 6.
- **Twelve statements, two per area, written by us.** O\*NET's own Interest
  Profiler is 60 items and wasn't used. The screen labels this as a
  simplified version. Answers are *Not for me*, *Maybe* or *I'd enjoy it*
  (0/1/2), summed per area (0–4).
- Rank jobs by **Pearson correlation** between the user's six area scores
  and each job's. Correlation compares the shape of the two profiles, which
  suits two different scales. Answers with no variance get a message rather
  than a ranking, following the TR-03 principle.
- Fit labels are *Close fit* (≥ 0.8), *Good fit* (≥ 0.6) and *Some fit*. These
  are a presentation choice, like the other labels in `plain.py`.
- The quiz is a fourth tab in Explore, both in the journey and in the app.
  The school-leaver sees only Job Zones 1–3.

### Verification (30 September)

All-hands-on answers put 10 of 10 top results in jobs whose top area is
Realistic (TC-I13b). Helping plus creating answers rank teachers and nannies
first. The school-leaver filter holds (TC-I13e).

### Consequences

- Schema change: one reference table.
- It's discovery only. It doesn't feed the gap or the pathway. It isn't a
  validated instrument and must not be presented as one.

---

## ADR-0012 — Record progress as dated events with a readiness snapshot

**Date:** 2026-09-30
**Status:** Accepted
**Relates to:** ADR-0005, `plans/full-app.md` slice 5

### Context

The dashboard showed where a user stands now, but not how they got there.
Progress needs a history to read as a story rather than a bar.

### Decision

- A new profile table, `progress_events`. It records one row per plan start,
  goal change or skill-status change, in UTC.
- **Each row stores the goal's readiness at that moment** (`goal_have`,
  `goal_total`) instead of rebuilding it later by replaying events. Replaying
  would give wrong answers once a goal changes or O\*NET's ratings are
  updated. A snapshot records what the user actually saw.
- Setting the same goal again is not an event.
- Home shows a *Your progress* card: the climb toward the current goal, for
  example 0 → 0 → 1 → 2 of 2, and a dated timeline.

### Consequences

- Schema change: one table added to the profile schema.
- History starts from this change. Plans saved earlier have no history before
  it, which is stated here rather than back-filled with invented dates.

---

## ADR-0013 — Richer job vectors are not built: they need richer user input

**Date:** 2026-10-04
**Status:** Accepted
**Relates to:** TR-01, FR-06, Assignment 3 §5.4, `plans/strengthen-frs.md` item D

### Context

TR-01 passes at 59.7% against a 55% target, a margin of 4.7 points. Assignment
3 §5.4 named adding O\*NET Knowledge (33) and Abilities (52) to the vectors as
"the most direct way to raise TR-01". There was a catch: users record only
skills, so the new dimensions have no user value.

### Measurement

Same 124 profiles, seed and metric as PT-01
(`backend/tests/experiment_richer_vectors.py`, output in
`docs/test-results/experiment-richer-vectors-2026-10-04.txt`).

| Variant | Same family in top 5 | Mean share |
|---|---|---|
| V0, as shipped: 35 skills | 59.7% | 30.6% |
| V1, jobs gain 85 knowledge/ability dimensions; user value unknown | 60.5% | 31.8% |
| V2, upper bound: users also record knowledge and abilities | 90.3% | 57.4% |

### Decision

**Don't build V1.** Its gain is one profile in 124, which is noise, and not
worth two new tables and a re-measured TR-01.

**V2 isn't built either.** It would need a new capture step, which means a new
requirement, a longer journey (against NFR-02) and asking a school-leaver to
rate 85 items. Its 90.3% is also an **upper bound, not an estimate**: PT-01
builds each test profile from the target job's own data, so giving the
profile more of that data makes it match its own family almost by
construction.

### Consequences

- **Assignment 3 §5.4's improvement claim was wrong as stated.** Richer job
  vectors don't raise TR-01 on their own. They help only if users also record
  knowledge and abilities. Say so if it comes up in the presentation. Finding
  this out by measuring is the better answer.
- The real lever is **richer user input**, recorded in `BACKLOG.md` as future
  work with its cost.

---

## ADR-0014 — The CV scanner: rule-based skill suggestions, a measured goal score, nothing stored

**Date:** 2026-10-05
**Status:** Accepted
**Relates to:** proposal module 3, `plans/cv-scorer.md`, ADR-0002, ADR-0005, ADR-0008, FR-02

### Context

The core modules had landed, so the proposal's CV scorer was built: paste a
CV, get skill suggestions and a check against your goal. The Kaggle Resume
Dataset (`saugataroyarghya/resume-dataset`, CC BY-NC 4.0) was verified first
(`data-sources.md` §3). It holds 344 CVs crossed with 28 adverts, each pair
with a human-style `matched_score`. The CVs' own experience text is lost to a
data defect, and the domain is South Asian tech and office work.

### What was measured

Benchmark: `backend/tests/benchmark_cv.py`, which scores the shipped code.
CVs are split in half with a fixed seed, settings were chosen on the tuning
half, and the test half is reported. Transcript:
`docs/test-results/benchmark-cv-2026-10-05.txt`.

| Held-out test half (172 CVs, 4,750 pairs) | r vs matched_score |
|---|---|
| Naive word overlap | 0.163 |
| **Shipped goal score** | **0.266** (95% CI 0.195–0.333) |
| Shipped minus naive | +0.023 to +0.178 (bootstrap over CVs) |

**Three free-text designs were tried and rejected.** Each tried to infer
O\*NET's 35 skills from CV wording:

1. TF-IDF against each skill's O\*NET wording (anchors, linked work
   activities).
2. The same, adding 95,742 linked task statements.
3. The nearest single O\*NET sentence.

All three tracked the benchmark *worse* than naive word overlap. In practice
they suggested "Writing" for "Fixed broken bicycles". **What carries the
score is concrete evidence: the software and tools a job uses (as O\*NET lists
them) that the CV names.**

### Decision

- **Skill suggestions come from explicit trigger words per skill**
  (`cvscan.SKILL_RULES`), written by us and kept conservative. Each
  suggestion quotes the CV line that triggered it, and **the user confirms
  every one** (FR-02's self-report rule). No accuracy is claimed for the
  suggestions.
- **The goal score** is the software and tools the job uses that the CV
  names, plus 0.3 × the share of the job's eight most important skills with
  rule evidence. The screen shows the parts, not a single number. The number
  is visible in presenter mode.
- **Ordinary English is not software.** A one-word product name ("Calyx
  Point" → "point") only counts if the word appears in fewer than 3 O\*NET
  task statements. Real product names appear in none.
- **The CV text is never stored.** `cvscan.py` has no write statements
  (TC-U10e), scanning changes nothing on the profile (TC-I18d), and the
  response says `stored: false`. ADR-0008's privacy argument holds.
- The resume dataset is **a benchmark only**. It is never loaded into
  `saycep.db`.

### Honest limits

- **The test half was viewed more than once.** It was viewed once in the
  experiment and again for each shipped revision (three in total). No setting
  was tuned on it, but the reader should know.
- **r = 0.27 is modest**, and it's a result on South Asian tech and office
  CVs, not a claim about South African school-leavers. Trades evidence (tools
  such as multimeters) is included but **isn't measured**, because the
  benchmark has no trades CVs.
- **O\*NET 29.0 has no skill ratings for "Software Developers" or "Data
  Scientists"**, which are newer job codes. They're among the 137 jobs
  SAYCEP excludes, so neither can be a goal.

### Consequences

- New code: `cvscan.py`, `POST /cv/scan`, the CV page.
- **No schema change.** It uses existing tables.
- New requirements are implied (CV import, CV check). As before, drafting
  them is the project owner's job.

---

## ADR-0015 — Interview practice with rule-based feedback, not a chatbot

**Date:** 2026-10-05
**Status:** Accepted
**Relates to:** proposal module 5, `plans/next-three.md`, CLAUDE.md (no LLM), ADR-0014

### Context

The proposal specifies an "interview chatbot". CLAUDE.md rules out an LLM in
the build. A real conversation isn't possible without one, but useful
practice is.

### Decision

- **Questions are built from the goal job's O\*NET data:**
  - an opener;
  - one behavioural question per must-have skill (or the top three where a
    job has none), from 35 templates in our wording, written so that school,
    home, church, sport and piece work all count;
  - one question quoting the job's most important task.
- **Feedback is a checklist with a tip for each miss, not a score.** It
  checks five things: the skill asked about is shown (the CV scanner's rules,
  plus a few spoken-answer phrasings kept in `interview.py` so the measured
  CV rules don't change); situation → action → result; the speaker's own
  part ("I", not only "we"); a specific detail; and a length of 40–250
  words.
- **Answers are never stored**, the same as CVs (ADR-0014).
- **No accuracy is claimed.** There's no ground truth for answer quality.
  The rules are unit-tested on worked examples: a full answer meets 7 of 7;
  "I need a job" isn't counted as an action; a "we"-only story is flagged
  (TC-U11).

### Consequences

- Four of the proposal's five modules are now built. Opportunity matching
  remains.
- It must be presented as **practice with guidance**, never as an AI
  interviewer.
- A new requirement is implied (interview practice). Drafting it is the
  project owner's job.


## ADR-0016 — Accessibility: WCAG 2.1 AA, checked by automated audit and a keyboard walk

**Date:** 2026-10-05
**Status:** Accepted
**Relates to:** `plans/next-three.md` §2, NFR-02, `test-results/accessibility-2026-10-05.txt`

### Context

The users are young people, often on cheap phones in bright light, and some
will rely on a screen reader or a keyboard. Accessibility had never been
measured. An axe-core audit of all 22 screens of the demo path found 169
failing elements in light mode and 34 in dark mode. A scripted keyboard-only
walk failed every focus check it could run.

### Decision

- **Target WCAG 2.1 level AA**, the level that public-sector and education
  sites are usually held to.
- **Contrast.** `--muted` is darkened to #5C6772 in light mode (at least
  4.84:1 on every surface it sits on) and lightened to #8C98A4 in dark mode.
  A new `--on-fill` token replaces hard-coded white text on accent and green
  fills, because white on dark mode's light accent was 2.44:1. The muted
  grey is now a little closer to body text; size and weight carry the
  hierarchy instead.
- **Focus follows the user.**
  - A new journey step, or arriving in the app, moves focus to the new
    heading.
  - A pushed page puts focus on its title, and Back returns focus to
    whatever opened it.
  - The tab underneath a page is `inert` (it was only `aria-hidden`, so Tab
    still walked into invisible controls).
  - The job sheet and the unlock card trap focus, close on Escape, and
    return focus to the opener (`useDialog` in `app.js`).
- **Honest roles.** Segmented controls (Explore's four ways, Skills filters,
  the welcome screen's two doors, the quiz answers) were marked as tabs and
  radio buttons, which promise arrow-key behaviour they didn't have. They're
  now plain toggle buttons (`aria-pressed`) in a labelled group, which is
  what they are. Tick marks have `role="img"` and a name; meters have names;
  decorative SVGs are hidden.
- **Labels and announcements.** The search box, the CV box and the answer box
  (labelled by the question) have names. The search count is a status
  region, interview feedback is announced politely, and CV and quiz results
  take focus when they arrive.
- **The checks are scripts, not a dependency.**
  - `frontend/tests/a11y_audit.js` runs axe-core 4.13 through Playwright in
    light mode, dark mode, and at 320 px wide (reflow).
  - `frontend/tests/keyboard.js` walks the demo path using only the keyboard.
  - Neither is loaded by the app, and there's no `package.json`. The
    backend's dependencies are unchanged.

### Result

| | Before | After |
|---|---|---|
| axe, light mode | 169 | 0 |
| axe, dark mode | 34 | 0 |
| axe at 320 px, plus overflow | not run | 0 |
| Keyboard walk | 17 of 17 checks that could run failed | 19 of 19 pass |

### Consequences

- **"Zero automated violations" isn't the same as "accessible".** No one has
  tested with a real screen reader or with disabled users, and the printed
  plan wasn't audited. The transcript says so, and so should the
  presentation.
- Any new screen should be added to both scripts. A colour that isn't a token
  is how this regresses.

## ADR-0017 — Module 4 becomes "What employers ask for": real adverts, summarised, never offered as openings

**Date:** 2026-10-05
**Status:** Accepted. The project owner chose this over leaving module 4
unbuilt.
**Relates to:** proposal module 4 (opportunity matching), ADR-0002 (Kaggle
only), ADR-0014, `plans/next-three.md` §3, `plans/employers-ask-for.md`

### Context

Opportunity matching needs live adverts that a South African user can apply
to. Step 0 found none on Kaggle:
- The only South African dataset is synthetic (4 description templates).
- The best real one is 123,849 LinkedIn adverts from the **US, March–April
  2024**, all closed.

Its "skills" are LinkedIn job functions, so the only link to O\*NET is the
advert title.

### Decision

- **Summarise, don't match.** For each job, the screen shows:
  - how many adverts there were;
  - how many were open to beginners;
  - the requirements they mention (school, degree, trade licence, driver's
    licence, training given, lifting, years of experience);
  - the job's own O\*NET tools and software they name;
  - example advert titles;
  - the skills they mention more than adverts in general.

  It always says **United States, March–April 2024, closed**.
- **Strict title linking.** A link needs one candidate occupation, with
  generic titles ("director", "project manager") dropped. 26,472 adverts are
  linked (21.4%), and 438 of 879 jobs have 5 or more. On a hand check, 44 of
  50 links were clearly right.
- **Below 5 adverts, the screen says there are too few** rather than show
  noise.
- **Skills are a weak signal, and the screen frames them that way.** A skill
  is shown only if 25% or more of the adverts mention it and it's 1.5 times
  more common than in adverts generally. Against O\*NET's importance ranking
  for the same job, the median Spearman is +0.23, against +0.09 for another
  job; the right job wins in 179 of 219 occupations. So these are "words these
  adverts use more than most", and O\*NET's ratings stay the guide to what
  the job needs.
- **Requirement rules are ours and hand-checked**, 11–12 of 12 per rule.
  The false matches found were fixed: "certified as a Great Place to Work"
  and "CDL" as a military data link.
- **Software and tools use stricter matching than the CV scanner:**
  - only the job's own list;
  - one-word names need 4 or more letters;
  - the vendor can be dropped only for known vendors.

  This found a scanner bug, now logged in `BACKLOG.md`.
- **Only counts and normalised titles are stored.** Never advert text,
  companies or links, partly because advert text can name recruiters.
- **The two-minute advert pass is cached** beside the data, fingerprinted on
  every input (the advert file, the O\*NET files it links through, the rule
  code). An O\*NET rebuild stays at about 2.5 s, inside NFR-04, and only a
  changed input triggers recomputing.
- **Where it appears:**
  - a section on the job page;
  - a card on Home for the goal.

  It isn't in the journey's quick panel, so NFR-02's five screens are
  unchanged.

### Consequences

- **All five proposal modules are now built, three of them in a reduced
  form** (CV scanner, this module, interview practice). Each is stated
  plainly.
- **The "real South African jobs" question gets a better answer than before:**
  "We looked twice, and both 'South African' sets on Kaggle failed
  verification. Here's what real adverts ask for, labelled as American."
- **New requirements are implied.** Drafting them is the project owner's
  job.
- **The advert file isn't in the repo:** it's 517 MB and gitignored. Without
  it, the section says the data isn't loaded. Hosting must fetch it, or ship
  the 717 KB cache.

### Corrections, 8 October (after code review)

The decision stands, but a code review found errors in what the screen said.
They are corrected here rather than by rewriting the entry above:

- **The period.** The adverts linked to O\*NET were listed **5–20 April
  2024**, not March–April; only the dataset as a whole starts in March. The
  screen now takes the month from the data ("listed in April 2024").
- **Beginners.** 26% of adverts give no experience level, and they were being
  counted as "not open to beginners". The share is now of adverts that state a
  level (`advert_summary.level_n`, a new column), and the screen says how many
  that was. For Electricians that's 7 in 10 of 73, not 6 in 10 of 84.
- **Years of experience** are shown only when 5 or more adverts state them, with
  the count ("30 adverts said … typically about 4 years"), not as "usually".
- **Rule errors, all now unit-tested (TC-U13):**
  - curly apostrophes ("driver’s license") were missed, which halved the
    driver's-licence share;
  - "1.5 years" was read as 5;
  - driving-licence wording also counted as a trade licence;
  - "certified B Corp" and similar boilerplate counted as a trade licence;
  - one product name also counted the shorter names inside it.

  Re-checked: driver 12/12, licence 11/12, years 10/10. The skill validity
  figures are unchanged (+0.23 vs +0.09, 179 of 219).
- **Titles** keep their acronyms ("IT Project Manager", not "It").
- **The cache:**
  - It's fingerprinted on the database rows the counts are built from, not a
    list of O\*NET files, so a change to `load_onet.py`'s filtering is caught.
  - It works without the 517 MB advert file, so hosting can ship the cache
    alone.
  - It's written atomically, and a corrupt cache is treated as missing.
  - `load_onet.py` now only ever reuses the cache, and otherwise says to run
    `load_adverts.py`, so NFR-04 can't be broken by the advert pass.
- **Focus.** If the adverts request fails after "See what employers ask for",
  focus now still moves into the page (ADR-0016). This is tested by forcing the
  request to fail.
- **Not changed on purpose:** the advert matcher stays separate from the CV
  scanner's, because that one is tied to a measured benchmark (ADR-0014). See
  `BACKLOG.md`.

## ADR-0018 — CV scanner: plurals folded correctly; the benchmark re-measured

**Date:** 2026-10-09
**Status:** Accepted. It corrects ADR-0014's software and tool matching;
ADR-0014's decision and figures otherwise stand.
**Relates to:** ADR-0014, ADR-0017, `BACKLOG.md`,
`test-results/benchmark-cv-2026-10-09.txt`

### Context

While building ADR-0017, I found that the CV scanner read "I can" as the
tool **Canes**. The cause was the plural-folding in `cvscan._words`: it
dropped "-es" from every word, so "Canes" became "can" and "Planes" became
"plan". Across the 344 benchmark CVs, that wrongly named Canes in 29 and
Planes in 19. One-word tools that are three-letter words had the same
problem: "I saw" named **Saws**, and "tap" named **Taps**.

### Decision

- **Fold plurals properly.** Drop "-es" only after s, x, z, ch and sh (boxes
  → box), turn "-ies" into "-y", and otherwise drop just the "s" (canes →
  cane). Words ending in "-is" or "-us" (analysis, status) are left alone.
- **A one-word tool name needs four or more letters.** Software keeps three:
  SQL, Git and AWS are real evidence on CVs.
- **Callers can't forget the rules.** They go through
  `cvscan.software_named` and `cvscan.tools_named`.
- **Chosen on the tuning half only; the test half was run once.**

  | Variant (tuning half) | r |
  |---|---|
  | shipped | 0.3111 |
  | fixed folding | 0.3114 |
  | **fixed folding + 4-letter tools** | **0.3114** |

  Two alternatives were rejected:
  - 4+ letters for software too: 0.2930;
  - the everyday-word filter applied to tools: 0.2937, because it also
    removes real tools like Routers and Forklifts.

### Result

- **Held-out r is 0.2655**, against 0.266 before, with a 95% interval of
  0.196 to 0.332. The figure quoted in the presentation stays **r = 0.27**.
  The fix removes false matches without costing accuracy.

### Consequences

- **"What employers ask for" shares the same folding,** so its counts were
  recomputed.
- **Not fixed, and logged:** one-word tools that are everyday words in CVs.
  "Trial balance" names **Balances** and "entry level" names **Levels**. A
  word list to stop them would have been picked by looking at every CV,
  including the held-out half, so it needs a fresh test set first.
- **The interim numbering in `plans/hosting.md` moves.** The user-data split
  becomes ADR-0019, and the host choice ADR-0020.

## ADR-0019 — The advert counts are committed, so a fresh checkout runs the whole demo

**Date:** 2026-10-20
**Status:** Accepted
**Relates to:** ADR-0017, `plans/hosting.md` item 3, `presentation.md` §4

### Context

Preparing the presentation, I tried the laptop path from a clean clone. The
O\*NET files, `saycep.db` and the 517 MB advert file are all gitignored, and the
advert counts cache sat in that ignored folder. A fresh checkout therefore had
no advert counts. "What employers ask for" would have said "advert data isn't
loaded" in the middle of the demo, with no error. The same review found two
faults in the cache fingerprint, both caught by new tests:
- it hashed `repr(row)`, which for the app's `sqlite3.Row` objects includes a
  memory address, so it changed on every call;
- it hashed code bytes, so git's Windows line-ending conversion would have made
  a correct cache look stale.

### Decision

- **Commit the counts:** `backend/seed/advert_counts.cache.json` (0.7 MB). It
  holds counts and titles only, never advert text, and the screens still carry
  the CC BY-SA attribution. The 517 MB advert file stays out of git.
- **Fix the fingerprint:** it hashes row values, and normalises line endings.
- **A unit test fails if the committed counts are stale** (TC-U14d), so the
  seed can't silently drift from the code. After changing `adverts.py`,
  `cvscan.py`, `load_adverts.py` or the O\*NET loading, run
  `python backend/load_adverts.py --fresh` (about 2.5 minutes) and commit the seed.
- A second test (TC-U14e) checks that CRLF and LF checkouts give the same
  fingerprint.

### Consequences

- A clean clone needs only the O\*NET files and `python backend/load_onet.py`.
- This is the shipped-counts item of the hosting plan, done early because the
  presentation runs from a laptop.
- It's the first derived data file in git. The O\*NET files and the database
  remain derived and ignored.

## ADR-0020 — TR-01 is reported two ways: as defined, and with the target removed

**Date:** 2026-10-20
**Status:** Accepted
**Relates to:** FR-06, ADR-0013, `test-results/performance-2026-10-20.txt`

### Context

Assignment 3 reports 59.7% (n = 124) against a random baseline of 25.8%. Reviewing
how the test works for the presentation, I found two things:
- the engine's top five is chosen from all 879 jobs, so **the target job itself
  can appear in it**, and then counts as a same-family hit. It does in 25 of
  124 cases (20%);
- the random baseline excludes the target.

The asymmetry in the baseline is small (about half a point). The size of the
self-hit effect is not.

### Decision

- **PT-01 stays as defined**, because that's what Assignments 2 and 3 report and
  it's a legitimate reading: a profile that matches a job should find it.
- **PT-01b is added: every one of the 713 jobs that have must-have skills (not a
  sample), the target removed, the next five used, an exact random baseline,
  and a bootstrap interval.**
- Result: **58.5% against 25.9% by chance, 95% interval 54.6–62.1.** It clears
  the 55% threshold, but the interval's lower end is just under it.
- **When asked, say the stricter figure.** Nothing submitted is withdrawn: 59.7%
  is correct for what it measured.

### Consequences

- The margin over the threshold is thinner than "59.7%" suggests. That's what
  `STATUS.md` and the presentation Q&A now say.
- ADR-0013's comparison (59.7% against 60.5%) is unaffected: both sides used
  the same measure.
- If you want TR-01's wording to mean the strict version, that's your
  requirement to redefine. I haven't changed it.

## ADR-0021 — Hosting on Fly.io, minimal: always on, no disk, deployed from the laptop

**Date:** 2026-10-21
**Status:** Accepted. It supersedes the sequencing in `plans/hosting.md`, not its
destination.
**Relates to:** ADR-0019, `plans/hosting.md`, `deploy.md`

### Context

Hosting was cut on 19 October to protect the code freeze. On 21 October the
project owner asked for a live link as a safety net for Saturday's
presentation. The full plan in `plans/hosting.md` needs about a day of work
(splitting user data into its own file, rate limiting, CI), which is too much
to build and verify between now and the freeze.

### Decision

Build the smallest thing that gives a working link, and change no application
code:
- **A two-stage Dockerfile.** The build stage runs `load_onet.py` on the O\*NET
  files, and the run stage holds only the app, its database and the frontend. The
  build fails loudly if the advert counts didn't load.
- **O\*NET comes from the folder you deploy from.** `fly deploy` uploads the
  directory, gitignored files included, so **no Kaggle token is involved
  anywhere**. The build context is about 100 MB, almost all of it O\*NET.
- **`fly.toml`:** Johannesburg, one 512 MB machine, always on, health check on
  `/skills`, HTTPS only. Deployed with `--ha=false`.
- **No volume, so saved plans reset on every redeploy or restart.** The split
  of user data into its own file (so plans could live on a volume) stays
  deferred.
- **No rate limiting and no CI.** Both stay deferred.
- **`.gitattributes` keeps the Dockerfile on LF line endings** under a Windows
  checkout.

### Consequences

- **Cost:** an estimated $4.80 a month running (derived from Fly's price table
  and the Johannesburg rate, not a published figure), so about $1.20 for a
  week, and the app is destroyed afterwards.
- **Verified:** the build and run steps, performed by hand, serve all 15 demo
  steps. **Not verified:** Docker and Fly themselves, because there's no Docker
  engine in the environment where this was built. The first real build is the
  project owner's deploy.
- **Plans don't persist.** The link is a demo, not a service. Anyone who needs
  their plan to last should use the printed plan.
- **No schema change,** so the user-data split moves to ADR-0022 if it's ever
  built, and `plans/hosting.md` renumbers accordingly.

---

## ADR-0022 — Jobs for you: real adverts as labelled sample listings, ranked by fit

**Date:** 2026-11-06
**Status:** Accepted. The project owner asked for job cards ("Jobs for you")
on presentation day, and the go was given on 24 October with every card
labelled as sample data.
**Partly supersedes:** ADR-0017. It keeps that ADR's rule that closed US
adverts are never offered as openings, and adds per-advert matching.
**Relates to:** `plans/advert-matching.md`, ADR-0002 (Kaggle only), ADR-0019
(committed seed). It takes the number ADR-0021 had reserved for the user-data
split, which becomes ADR-0023 if it's ever built.

### Decision

- **One advert per card.** For the goal and the jobs on the user's Pathway,
  the app shows real LinkedIn adverts as job cards: the advert's title, US
  place, work type, listing date, whether it's open to beginners, years asked,
  requirements, and **how you fit**: "You have 3 of the 8 skills it mentions".
- **Fit is plain counting.** It's the share of the O\*NET skills an advert
  mentions that the user holds, shown in words (Strong fit, Good fit, Some fit,
  A stretch), never as a percentage. Ranking is by that share, then open to
  beginners, then fewer years asked, then newest. **No accuracy is claimed**:
  nobody was hired, so there's no ground truth. The rules are unit-tested
  (TC-U15).
- **Labelled every time.** Each section carries a "Sample listings" badge and
  says the adverts are from the United States, spring 2024, used as demo data,
  and closed. **Apply** explains that it's a demo and that the full system
  would open the live advert.
- **Features only.** New table `advert_listings`: the 20 most recent linked
  adverts per occupation (7,094 over 682 occupations), with no advert text,
  company, link or pay. TC-U15f and TC-I21f check this.
- **Its own module and cache.** It lives in `listings.py` and
  `load_listings.py`, with the cache committed at
  `backend/seed/advert_listings.cache.json` (1.4 MB). It's kept apart from
  `adverts.py`, so the committed advert-count cache (ADR-0019) stays valid.
  Linking and mention rules are the same as the counts'.

### Consequences

- **A schema change:** one new, optional table. Without it, the cards simply
  don't appear.
- **The skills signal is weak** (ADR-0017: median Spearman +0.23 against
  O\*NET), so the cards present fit as a rough guide. O\*NET's ratings stay the
  guide to what a job needs.
- **The next step is a live South African source.** Adzuna's South Africa API
  is the candidate (ADR-0001), but it needs the lecturer's approval under
  ADR-0002. The cards are built so that a source can replace the sample data
  without a redesign.

---

## ADR-0023 — CV upload is read in the browser: PDF, Word and text

**Date:** 2026-11-06
**Status:** Accepted. The project owner asked for it on presentation day,
following `plans/cv-upload.md` (the browser option).
**Relates to:** ADR-0014 (the CV scanner), ADR-0018. It takes the next number,
so the user-data split, if ever built, becomes ADR-0024.

### Decision

- **The browser pulls the text out of the file and puts it in the CV box**, so
  the user can check it before scanning. **Only the text is sent**, as when
  it's pasted, so the backend, the scanner and its measured r = 0.27 are
  unchanged. The file never leaves the device.
- **.txt** is read directly. **.docx** is a zip of XML: `word/document.xml` is
  unzipped with the browser's own `DecompressionStream`, with no library.
- **.pdf** uses **pdf.js 3.11.174** (Mozilla, Apache-2.0), vendored in
  `frontend/vendor/` and loaded only when a PDF is chosen. This is a **new
  front-end dependency**: reading PDFs without one isn't realistic. That version
  is affected by CVE-2024-4367 when `isEvalSupported` is on, so it's turned
  off, which is the published fix. Version 4 is fixed, but it ships only as ES
  modules, and serving `.mjs` with the right type isn't reliable on every
  laptop.
- **Refused, with a plain message:** other file types and old `.doc` files,
  files over 5 MB, and a PDF with no text layer ("This looks like a scanned
  document… Paste the text instead"). Text over the scanner's 15,000-character
  limit is cut, and the screen says so.

### Consequences

- **No OCR,** so scanned CVs still need pasting.
- **Tests:** `frontend/tests/cv_upload.js` uploads real fixture files (9
  checks, including that no request carries a file). The axe audit and the
  keyboard walk cover the new control.
- The written report (submitted earlier) says "pasted text only". **In the
  presentation, describe upload as added since the report.**

---

## ADR-0024 — CV advice and a technical interview question, from data already in the app

**Date:** 2026-11-16
**Status:** Accepted. The project owner approved items 1–3 of
`plans/cv-interview-upgrade.md` for the final presentation (Friday 20 November).
**Relates to:** ADR-0014 (CV scanner), ADR-0015 (interview practice), ADR-0017
(adverts). It takes the next number, so the user-data split, if ever built,
becomes ADR-0025.

### Context

The CV check said what a CV shows but not what to add, and interview practice
asked skill questions only and gave feedback once per answer. No new data was
sought: **no Kaggle interview-question dataset was found** (the nearest are on
Hugging Face, which ADR-0002 rules out without approval), and the Kaggle
LiveCareer CVs have category labels but no match scores, so they can't improve
or measure the goal score.

### Decision

- **CV: "What to add".** For the goal job, `cvadvice.py` turns the advert
  counts (ADR-0017) into up to three pieces of each kind of advice:
  - **requirements** adverts commonly ask for (25%+ of adverts) that the CV
    doesn't mention, in South African terms ("Code 8", "N2", "matric"), each
    with an example line;
  - **tools** at least 15% of adverts name that the CV doesn't;
  - **key skills** (O\*NET essential) the CV doesn't show, with a worked example
    for 15 common skills and a frame for the rest.
  Every advert figure says how many US adverts and when ("7 in 10 of the 84 US
  adverts for this job (April 2024)"). A job with too few adverts gets skill
  advice only and no advert figure. **The scanner, its rules and the goal score
  are not touched**, so r = 0.27 stands, and the advice claims no accuracy.
- **Interview: a technical question.** After the skill questions, "Tell me about
  a time you used *X*, or how you would use it in this job", where X is the tool
  or software the most real adverts name (at least 5 adverts and 5% of them).
  **168 of 879 jobs get one;** the rest don't, rather than a generic or silly
  question. (O\*NET's "hot technology" list was tried first and rejected: it
  offered Git for coroners and Apache Spark for nurses.) Feedback gains a
  "Names *X*" item, matched word by word with plurals folded.
- **Interview: retry.** Checking an answer again shows "2 of 7 → 7 of 7" and
  what is now there, kept per question and never stored; sentence starters
  appear only for the missing parts of the story.

### Consequences

- **No schema change, no new data, no seed change:** `cvscan.py` and the
  advert cache fingerprint are untouched.
- Electricians' technical question is about **Microsoft Excel**: that is what
  their adverts name most (8%), though multimeters are the more natural tool.
- **Deferred (backlog):** adding CV skill rules. It would invalidate both
  committed seeds and need a re-measure of r = 0.27.
- **Tests:** TC-U16a–h, TC-U17a–e, TC-I22a–i, a corrected TC-I19a, and
  `frontend/tests/interview_retry.js` (18 checks); the axe audit covers the CV
  result and the retry state.

---

## ADR-0025 — The skill-matching model, made visible and used in two more places

**Date:** 2026-11-17
**Status:** Accepted. The project owner approved `plans/emerging-tech-visible.md`
(A, B1, B2) and the on-screen name "Skill-matching model".
**Relates to:** FR-06, TR-01, ADR-0013, ADR-0014. It takes the next number, so
the user-data split, if ever built, becomes ADR-0026.

### Context

At the 6 November demo the lecturer was unsure what the emerging technology was.
The engine (mean-centred cosine similarity over 35 O\*NET skill ratings) ranked
*For you* and ordered the Pathway, but nothing on screen showed a model at work.
More data was not the fix: ADR-0013 measured richer job vectors at 59.7% →
60.5%, which is noise.

### Decision

- **A. "How we matched you".** A panel, opened from every *For you*
  recommendation, from "How does it work?" on the model's tag, and from a job
  page, walks the real numbers for one person and one job:
  1. the job's 35 ratings;
  2. the person's ticks (with the skills almost every job needs marked as
     ordinary);
  3. the job after subtracting the average job;
  4. the score and the skills that lifted or held it back.
  It also shows the score without centring, and the range across all 879 jobs.
  For Thabo, uncentred scores bunch between 0.27 and 0.58; centred ones spread
  from −0.56 to 0.64. It's built from `recommend.explain()`, which uses the
  engine's own functions, so it cannot disagree with the list (TC-U18a–c). The
  panel is rendered at the app's top level, so it works inside the journey.
- **A "Skill-matching model" tag** wherever the engine runs: *For you*, the
  Pathway, "Jobs your CV points to", and "Jobs with the closest skills".
- **B1. "Jobs your CV points to".** The skills a CV seems to show go through the
  same engine (`_ranked`, now shared with *For you*), limited to Job Zones 1–3
  for a school-leaver. They're unconfirmed, the screen says so, and nothing is
  added to the profile. The scanner is untouched (r = 0.27 stands).
- **B2. "Jobs with the closest skills".** `recommend.similar()` compares one
  job's centred vector with every other job's. Each result says whether O\*NET's
  experts also list it as related.

### Measured: PT-05 (a second, independent check)

Over all 879 jobs, the engine's five closest include a job O\*NET's experts list
as related **60.6%** of the time, against an exact random baseline of **5.2%**
(**11.6×**). On average **19.8%** of the five are expert-listed. No requirement
sets a target, so the gate is only "well above chance" (3×). An earlier sampled
baseline of 4.7%, in the plan, is replaced by the exact figure.

**A finding to say in the Q&A:** job to job, centring changes nothing (plain
cosine also gives 60.6%), because two jobs' ratings are on the same scale.
Centring matters when matching a *person*, whose ticks are all 0 or 1, to jobs.
That's what the panel's "Why step 3 matters" shows.

### Consequences

- No schema change, no new data and no new dependency. The seeds and the
  scanner are untouched.
- **A correction made before building:** the plan's first draft said that
  without centring "every job scores about 0.9 against you". That's the
  job-to-job figure. Measured for a person, it is 0.27–0.58. Corrected in the
  plan.
- **Tests:** TC-U18a–g, TC-I23a–i, PT-05, and `frontend/tests/engine_visible.js`
  (21 checks); the axe audit covers the panel (with all 35 rows), the job page
  with closest jobs, and the CV result with "points to".

---

## ADR-0026 — Two improvements tested and not adopted: skill grades, and Kaggle course catalogues

**Date:** 2026-11-18
**Status:** Accepted. Both checks were asked for by the project owner, as
evidence for the presentation's "next steps". The app is unchanged.
**Relates to:** ADR-0013 (richer vectors), ADR-0014 (text matching), ADR-0002
(Kaggle only). It takes the next number, so the user-data split, if ever built,
becomes ADR-0027.

### 1. Grading skills ("a bit" or "well") instead of ticking them

`backend/tests/experiment_skill_ratings.py` uses PT-01b's method (713 jobs,
target removed; random baseline 25.9%). Transcript:
`test-results/experiment-skill-ratings-2026-11-18.txt`.

| Variant | Same family in top 5 | vs ticks |
|---|---|---|
| V0 ticks, as shipped | **58.5%** (54.8–62.3) | — |
| V1 same skills, graded | 54.8% (51.3–58.5) | +45 / −71 jobs |
| V1b the same, with everyday skills counted as ordinary at any grade | 56.5% (52.9–60.4) | +23 / −37 |
| V2 V1 with a third of the grades wrong | 57.1% (53.6–60.7) | +39 / −49 |
| V3 more skills, graded (an upper bound) | 52.9% (49.1–56.7) | +79 / −119 |

**Not adopted.** No variant beats ticks, even with perfect grades copied from
the target job, which flatters them. Part of the loss is how the engine centres
a half-grade (V1 against V1b), but even the fairer centring doesn't win. Adding
mid-importance skills (V3) dilutes what makes a job distinctive. **So the
"richer user input" ADR-0013 points to is *other dimensions*, such as a field
of study (O\*NET Knowledge), not finer grades of the same 35 skills.** That's
the next step to name.

### 2. Kaggle course catalogues, for "how to learn each missing skill"

Licences were read from Kaggle's own metadata, with the owner's API key, on
18 November. Of six candidates, only two are usable: the **Coursera Course
Dataset** (`siddharthm1698`, **GPL-2.0**, 891 courses, titles only, scraped from
Coursera) and **Udemy Finance & Accounting** (`jilkothari`, **CC0-1.0**,
13,608 courses, finance only). Coursera 2021, Udemy (andrewmvd) and both edX
sets are "unknown" or unspecified.

`backend/tests/check_course_data.py` measured coverage against the skills
school-leavers' jobs (Zones 1–3) need. Transcript:
`test-results/course-data-check-2026-11-18.txt`.
- **62%** of must-have slots have a keyword-matched Coursera course, but **about
  29% after hand-checking relevance**. "Troubleshooting" matched "AI for Medical
  Diagnosis", and "Reading Comprehension" matched a course for teachers.
- **The hands-on skills** (operating and monitoring equipment, repairing,
  troubleshooting, maintenance) are 19% of must-have slots and have **no
  relevant course**.

**Not adopted.** The usable data teaches office and soft skills, not the
hands-on skills most school-leaver jobs depend on. Keyword matching needs hand
curation, and the GPL-2.0 set is scraped from Coursera. The source that would
cover hands-on training is South African (TVET courses, SETA learnerships). It
isn't on Kaggle, so it needs the lecturer's approval: limitation 2 of the
report.
