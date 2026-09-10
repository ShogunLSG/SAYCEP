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
