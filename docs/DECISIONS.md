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
