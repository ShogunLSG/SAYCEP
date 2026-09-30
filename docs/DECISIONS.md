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

