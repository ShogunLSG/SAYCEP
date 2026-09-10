# Archive

The August 2026 version of this project, kept for reference. **Nothing in here is
a live plan.** Each file carries a header saying what replaced it.

At that point SAYCEP was a seven-phase build submitting a dissertation on 30
November 2026, with five success criteria, a 50-profile benchmark, a 20–30 person
UAT, a Node + Python two-service architecture, and job data from the Adzuna API
alongside a hand-curated TVET/SETA dataset.

Two things collapsed that plan into the current one: the course rule that all
system data comes from Kaggle, and the project's endpoint moving to the October
2026 presentation. See ADR-0002 in `../DECISIONS.md`.

| File | Was | Replaced by |
|---|---|---|
| `2026-08-claude.md` | Operating instructions | `../../CLAUDE.md` |
| `2026-08-roadmap.md` | Seven-phase plan to November | `../timeline.md` |
| `2026-08-risks.md` | Risk register (ESSA, Adzuna, LLM cost) | Closed by supersession |
| `2026-08-saycep-starter.zip` | Original scaffold | — |

Worth keeping in mind: `2026-08-claude.md` records the five success criteria the
project was originally judged on. The fifth — an unqualified-user journey ending
in a named institution with real entry requirements — is not achievable on Kaggle
data. It went out with the November submission rather than being solved.
