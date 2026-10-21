# Status

**As of 20 October 2026: the prototype is built and its demo path is machine-checked, for presentation on Saturday 24 October. The human rehearsal is still to do.** A welcome screen with plan-code sign-in, the five-screen journey as onboarding, then four tabs (Home, Explore, Skills, Me) with job pages, skill pages, saved jobs and comparison, an interest quiz, progress history, a printable plan, and the proposal's other three modules in reduced, stated forms: a CV check, interview practice, and what employers ask for. All of it is checked by automated tests (counts in `docs/presentation.md` §7), a WCAG 2.1 AA audit and a script that runs the demo. **A minimal Fly.io deploy is ready (`docs/deploy.md`, ADR-0021) as a safety net: saved plans on it reset on redeploy.** The laptop is the main path.

**For the presentation, start at `docs/presentation.md`:** running order, the demo path, the laptop setup, the failure plan, and the questions to expect.

## Decided

- **Data source rule: Kaggle only.** South African statistics are cited as written background, never loaded. (ADR-0002)
- **Data spine: O*NET 29.0**, from Kaggle — importance-rated skills, job zones, an expert-reviewed related-occupations graph. (ADR-0003)
- **Skill capture is shared; the two profiles diverge at target selection.** O*NET has no qualification-to-skills mapping. (ADR-0004)
- **Emerging technology: mean-centred cosine similarity** over 35-dimensional skill vectors, measured rather than asserted.
- **Demo stack: monolith** — one FastAPI service serving both the API and the app, SQLite, React vendored locally.
- **Scope: two modules built, three specified.**

## Done

- **The journey.** Five screens, one at a time — who you are, your skills, pick a target, the gap, the route. Walked end to end in a browser against the real database. `?presenter` on the URL shows each screen's requirements.
- **The API.** Eight endpoints, module names matching the sequence diagram. One connection per request, verified under 20 concurrent calls.
- **All ten functional requirements are built and demonstrable.** FR-10 in the loader, FR-01 to FR-09 in the API and journey.
- **Recommendation engine** measured at 59.7% occupational-family accuracy against a 6.9% baseline, and 8.8 ms p95 latency.
- **Assignment 2 drafted** — all five questions, four UML diagrams, a formatted `.docx` with your name and verified StatsSA figures.
- **Repo on GitHub**, private, at `ShogunLSG/SAYCEP`.

## Built on 30 September (evening) — `docs/plans/ux-and-dashboard.md`

- **Plain language (Task 1).** Words first, figures behind `?presenter`:
  "Critical for this job" rather than 4.00 / 5, and "Vocational training or an
  apprenticeship" rather than Job Zone 3. Labels come from `backend/plain.py`.
- **"What is this job?" panel (Task 2).** It shows the description, the
  preparation needed, and every skill ticked if you have it. The target is set
  from the panel.
- **"My plan" dashboard (Task 3).** It opens after the route, and again on
  every return visit. It shows the goal, readiness counted in must-haves, the
  route with each step ticked when ready, and the next step. ADR-0006 records
  why this doesn't break NFR-02.
- **Progress (Task 4).** Skills move from *Start learning* to *I can do this
  now*, and only the second closes a gap. This is a schema change (ADR-0005).
- **"A day in this job" (Task 5).** It lists O*NET task statements, most
  important first, from the same Kaggle dataset. New table (ADR-0007).
- New screenshots are in `docs/screenshots/v2/` and new transcripts are in
  `docs/test-results/*-v2.txt`. The originals are untouched, because
  Assignment 3 cites them.

## Not done — in order of what hurts most if left

1. **Write the requirements for what the app now does — yours, not mine.**
   FR-11 (progress), and likely FR-12 onward: alternate-title search, job
   pages, saved jobs and compare, the interest quiz, progress history, the
   plan code. `docs/plans/full-app.md` lists each with a measurable figure.
   Assignment 3 went in without them; the presentation is where they're asked.
2. **Read Assignment 3 before submitting:** `docs/ISJ107V_Assignment_3_SAYCEP.docx`, built from `docs/assignment-3-submission.md`. It's in my words, not yours.
4. **User acceptance test.** NFR-02 is reported as *partial* because no first-time user has walked the journey unassisted. Ten minutes with one person, using the demo script below, would turn it into evidence. The document says plainly that it hasn't been done.
5. **Presentation: Saturday 24 October.** The code freezes on the evening of Wednesday 21 October. Present from the laptop, with the live link as a safety net (`docs/deploy.md`); the last days are at the end of `docs/timeline.md`.
6. **Assignment 2 diagrams are small.** If Assignment 2 isn't submitted yet, its use-case, class and sequence diagrams print with text under 6 px. Assignment 3's are fixed; the same landscape-page approach would fix Assignment 2's.

## Done on 30 September

- 41 automated tests — 12 unit, 23 integration, 2 system, 4 performance — all passing; transcripts in `docs/test-results/`.
- The tests found a real defect: rebuilding the database under a running server dropped the profile tables. Fixed in `load_onet.py`.
- **TR-01's baseline corrected.** Assignment 2 compared 59.7% against 6.9%, which measures something different. Against its own baseline the figure is 59.7% vs 25.8% random (2.3x). Still passes the 55% target; the margin was overstated.
- Nine as-built diagrams in `docs/uml/a3/`. The Assignment 2 sequence diagram was wrong — the Pathway Service never calls the Gap Analyser — and is corrected.
- FR-08 reworded to "new or deeper", closing the old item 5.
- `requirements.txt` added; dead `gap.skills_to_acquire` removed.

## The demo script

Moved on 20 October to **`docs/presentation.md`** (§3 is the demo path, §5 the
questions to expect), so there's one copy that can't drift. It's checked by
`frontend/tests/demo_walk.js`: `SHORT=1` for the 7-minute path, no flag for all
15 steps. Screenshots of each step are in `docs/screenshots/v4/`.

## Built on 5 October — accessibility (ADR-0016)

- WCAG 2.1 AA pass. Contrast tokens fixed for both themes, focus moves to each new screen and page and back again, the sheets trap focus and close on Escape, and segmented controls have honest roles. Before and after are in `docs/test-results/accessibility-2026-10-05.txt`.
- Rerun with `frontend/tests/a11y_audit.js` and `frontend/tests/keyboard.js`. Both are test-time scripts and not app dependencies.

## Built on 5 October — what employers ask for (ADR-0017)

- Module 4, as the data allows. Real LinkedIn adverts (US, listed April 2024), linked to O*NET by title, summarised per job: beginners' share, requirements, tools named, skills stressed, titles. It's on the job page and in a Home card for the goal.
- Checked: skills agree weakly but really with O*NET (Spearman +0.23 vs +0.09). The requirement rules were hand-checked at 11–12 of 12. See `docs/test-results/adverts-2026-10-05.txt`.
- The advert file (517 MB) is gitignored in `backend/data/linkedin/`. The counts are cached, so rebuilds stay at about 2.5 s.

## Built on 20 October — presentation preparation

- **The demo path is verified by machine** (`frontend/tests/demo_walk.js`), and `docs/presentation.md` has the script, slide outline, laptop setup, failure plan and a question bank.
- **A clean checkout now runs the whole demo** (ADR-0019). The advert counts are committed under `backend/seed/`, so the laptop needs only the O*NET files and `python backend/load_onet.py`. Before this, "What employers ask for" would have said "not loaded" on a fresh checkout.
- **TR-01 is now reported two ways** (ADR-0020). The submitted 59.7% lets the target job count in its own top five. With it removed, over all 713 jobs with must-haves: **58.5% (interval 54.6–62.1) against 25.9% by chance.** It still clears 55%, with less margin than it looked. PT-01b measures it.
- **Unemployment figures:** StatsSA published Q2 2026 on 11 August (62.8% for ages 15–24, 41.8% for 25–34, 33.6% overall). Assignment 2 used Q1.

## Deferred on purpose

- Light gamification polish — `docs/BACKLOG.md`, only if time remains
- RIASEC interest intake, and the three specified-only modules
