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
