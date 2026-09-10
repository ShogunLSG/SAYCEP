# Backlog

Things noticed but deliberately deferred, so they don't derail the current
concern. Pull from here when there's room. Not a task tracker — just a holding
pen so nothing gets lost.

---

- **The monolith decision isn't in the ADR log.** `architecture.md` explains why
  the demo is a single FastAPI + SQLite + React service rather than the
  multi-service design in the proposal, but it lives there as prose. It is a
  load-bearing decision and the presentation will likely ask about it. Worth an
  ADR-0003 so the reasoning sits alongside ADR-0002 in one place.
  (Noticed 2026-09-10.)

- **Folder is named `SAYEC`, project is `SAYCEP`.** Cosmetic mismatch. Renaming
  risks breaking anything pointing at the path, so it's deferred rather than
  done. (Noticed 2026-09-10.)

---

## Cleared 2026-09-10

The four items carried here from August all concerned the ESSA/Adzuna job-data
route — registering an Adzuna key, verifying SA listing volume, reading Adzuna's
terms, and closing the loop with the Department of Employment and Labour. All are
moot under the Kaggle-only rule (ADR-0002). They are recorded in
`archive/2026-08-*` if the history is ever needed.

The fifth — a path mismatch between `CLAUDE.md` and `ROADMAP.md` — resolved
itself when the roadmap was archived.
