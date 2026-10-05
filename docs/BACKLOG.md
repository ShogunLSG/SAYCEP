# Backlog

Things noticed but deliberately deferred, so they don't derail the current
concern. Pull from here when there's room. Not a task tracker — just a holding
pen so nothing gets lost.

---

- **The monolith decision isn't in the ADR log.** `architecture.md` explains why
  the demo is a single FastAPI + SQLite + React service rather than the
  multi-service design in the proposal, but it lives there as prose. It is a
  load-bearing decision and the presentation will likely ask about it. Worth an
  ADR of its own so the reasoning sits alongside ADR-0002 and ADR-0003 in one
  place. (Noticed 2026-09-10.)

- **Folder is named `SAYEC`, project is `SAYCEP`.** Cosmetic mismatch. Renaming
  risks breaking anything pointing at the path, so it's deferred rather than
  done. (Noticed 2026-09-10.)

---

- **Light gamification polish, only if time remains at the very end.** Discussed
  26 September against the journey mockup (`docs/plans/` / the artifact, not
  committed code). Explicitly *not* streaks, XP, badges or leaderboards — those
  were considered and rejected: the school-leaver user is making a high-stakes
  decision against a 60.9% unemployment rate for their age band, and comparable
  real career apps (LinkedIn, Handshake) deliberately avoid that mechanic for
  that reason. It would also add state with no functional requirement behind it
  and risks breaking NFR-02's five-screen cap.
  What's in scope, cheap, and stays on the shelf until the demo path is solid:
  a satisfying tick animation on skill selection, the gap counts on the gap
  screen visibly counting down as skills are ticked rather than snapping, and
  a touch more weight on the pathway screen's completion checkmark. Hours, not
  days — and only after FR-01 to FR-10 actually work end to end.
  (Noticed 2026-09-26.)

- **Freeze the dashboard route at save time?** The route re-sequences whenever a
  skill is marked held (FR-08 orders by closeness to the current profile).
  The dashboard says so on screen. Freezing it would need a stored route (a
  schema change), so it's deferred unless user testing shows the reshuffle
  confuses people. (Noticed 2026-09-30.)

- **"How people got into this job"** from `Education, Training, and
  Experience.txt`. It was left out of the job page on purpose. It covers 858 of
  879 jobs, and its categories are US qualifications (Associate's degree,
  GED). Showing US percentages to a South African school-leaver invites a
  question we can't answer. Revisit only with a defensible mapping.
  (Noticed 2026-09-30.)
- **Plan-code rate limiting.** A plan code is a bearer credential, and nothing
  stops someone guessing codes. That's fine on a laptop, but it's needed before
  any public deployment (ADR-0008). (Noticed 2026-09-30.)

- **Capture knowledge and abilities from users, if TR-01 must go higher.**
  Measured on 4 October (ADR-0013): richer job vectors alone take TR-01 from
  59.7% to 60.5%, which is noise. With user input the upper bound is 90.3%,
  but that's inflated by how PT-01 builds its profiles. Doing it needs a new
  capture screen, a new FR, and a way to ask about 85 items without breaking
  NFR-02. Possibly a short quiz like the interest one. (Noticed 2026-10-04.)

- **Software Developers and Data Scientists can't be goals.** O\*NET 29.0 has
  no skill ratings for these newer codes, so they're among the 137 excluded
  jobs. A school-leaver interested in software is pointed at Computer
  Programmers or Web Developers instead. Revisit when O\*NET rates them.
  (Noticed 2026-10-05.)
- **Measure the CV scanner on trades CVs.** Its tool evidence is built but
  unmeasured, because the benchmark has no trades CVs. A Kaggle dataset of
  trades or South African CVs would fix that. (Noticed 2026-10-05.)

---

## Cleared 2026-09-10

The four items carried here from August all concerned the ESSA/Adzuna job-data
route — registering an Adzuna key, verifying SA listing volume, reading Adzuna's
terms, and closing the loop with the Department of Employment and Labour. All are
moot under the Kaggle-only rule (ADR-0002). They are recorded in
`archive/2026-08-*` if the history is ever needed.

The fifth — a path mismatch between `CLAUDE.md` and `ROADMAP.md` — resolved
itself when the roadmap was archived.
