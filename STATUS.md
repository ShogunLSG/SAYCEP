# Status

## Final presentation: Friday 20 November 2026, 18:00 (read this first)

**Where to start:** `docs/presentation.md` (demo path with steps N1–N7, set-up,
Q&A, the numbers in §6) and `docs/presentation-script.md` (what to say over each
of the **8** slides). **Code freeze: Thursday 19 November, 20:00.**

**Still open** (as of 18 November):
- Rehearse with N5 ("How we matched this") at step 3.
- Optional, needs a go: more CV skill phrases (re-measured; plan item 5 in
  `docs/plans/cv-interview-upgrade.md`), and the five-person user test.
- Merge `main-7rly7s` into `main`.
- Rotate the Kaggle token that was pasted into chat.
- `CLAUDE.md` still says the only front-end libraries are React and htm. pdf.js
  (ADR-0023) is now vendored too. It's your file, so it's left for you to update.

**18 November: two improvements tested and not adopted** (ADR-0026): graded
skill ratings (worse than ticks: 54.8% against 58.5%), and the Kaggle course
catalogues (usable licences, but no hands-on skills covered). These are evidence
for "how would you improve it?" (presentation guide §5.9). The app is unchanged.

**18 November: the Markdown docs were brought up to date:** the READMEs,
`architecture.md` (now listing every table, with no LLM), the dev guide,
data sources, the timeline, the presentation guide (8 slides, numbers, test
counts) and the script.

**17 November: the skill-matching model is made visible** (ADR-0025,
`docs/plans/emerging-tech-visible.md`), on `main-7rly7s`:
- **"How we matched you"**: a four-step panel of the real numbers, opened from
  every *For you* job (also in the journey) and from job pages. A
  **"Skill-matching model"** tag wherever the engine runs.
- **"Jobs your CV points to"** (CV skills → the same engine) and **"Jobs with the
  closest skills"** on job pages.
- **PT-05, a second accuracy figure:** 60.6% of jobs' five closest include an
  expert-listed related job, against 5.2% by chance (11.6×).
- **Tests:** 82 unit, 126 API, 6 performance; `engine_visible.js` 21; demo walk
  50/50 (numbers unchanged); all other browser suites and axe (light, dark,
  320 px) green.
- **Fallback:** `git checkout c5d150d` (16 November, before this work).

**16 November: CV advice and the interview upgrade are built and green**
(`docs/plans/cv-interview-upgrade.md` items 1–3, ADR-0024), on `main-7rly7s`:
- **CV "What to add":** requirements, tools and skills the CV lacks, with how
  common each is in real (US) adverts and an example line. Scanner and score
  untouched, so r = 0.27 stands.
- **Interview:** a technical question about a tool the job's adverts name (168
  of 879 jobs), and retry that shows "2 of 7 → 7 of 7" with sentence starters.
- **Tests:** 75 unit, 117 API, 5 performance; demo walk 50/50 (numbers
  unchanged); keyboard walk; CV upload 33; job cards 28; interview and CV advice
  18; axe 0 failures in light, dark and 320 px.
- **Fallback if anything goes wrong:** `git checkout f8d9d55` (6 November's
  tested state, with job cards and CV upload but without these three items).
- **Code freeze: Thursday 19 November, 20:00.** Not done: adding CV skill rules
  (plan item 5, optional, needs a go) and the user test.

## History (everything below this line is earlier state, kept for the record)

## Earlier: presentation day, Friday 6 November 2026

**Slot: Room 2, 18:00–18:30, on Microsoft Teams** (from `Prototype_Presentation_2026_List.xlsx`).

- **Safe, demo-ready snapshot: branch `presentation-2026-11-06`.** All 161 tests,
  the 50-check demo walk, the keyboard walk and the axe audit (0 failures, 23
  screens) pass on it, from a fresh clone (5–6 Nov). **If anything below is
  unfinished at 16:45 SAST, present from this branch.**
- Report and slides were submitted (Q1.1, Q3.5 and Q4.3 rewritten from the
  student's own answers). The spoken script is `docs/presentation-script.md`;
  the demo path, the Teams set-up and the Q&A are in `docs/presentation.md`.
- Screenshots of every demo step: `docs/screenshots/demo-2026-11-06/` (the
  fallback if screen sharing fails).
- How to start the app: `python -m uvicorn app:app --app-dir backend --port 8000`,
  then http://127.0.0.1:8000 (one command serves both the API and the UI).

### Being built on `main-7rly7s` (6 November, from 14:50 SAST; cut-off 16:45)

1. **"Jobs for you" job cards** (`docs/plans/advert-matching.md`, go given 24 Oct).
   - [x] `backend/listings.py`: pure functions (title tidy, beginner_ok, fit, rank).
   - [x] `backend/load_listings.py`: new table `advert_listings` (schema change,
     ADR-0022 to write), 20 newest adverts per occupation as features only.
     Cache committed at `backend/seed/advert_listings.cache.json` (7,094
     listings, 682 occupations, 1.4 MB). Kept apart from `adverts.py` so the
     committed advert-count cache stays valid.
   - [x] Called from `load_onet.py` (cache only).
   - [x] API: `GET /occupations/{soc}/listings?profile_id=` and
     `GET /profiles/{id}/listings` (goal + Pathway steps).
   - [x] UI: `frontend/jobs.js` (job cards, "Sample listings" badge, Apply note),
     a Home card and a job-page section; CSS.
   - [x] Tests: TC-U15a–f, TC-I21a–h; 62 unit + 108 API + 5 performance pass; axe 0 failures (light, dark, 320 px, new screens included); keyboard and demo walks pass.
   - [x] ADR-0022 written. Still to do: `architecture.md` schema, `presentation.md` demo lines.
2. **CV file upload** (`docs/plans/cv-upload.md`, ADR-0023): **done.** PDF,
   Word (.docx) and text, read in the browser; pdf.js 3.11.174 vendored.
   `frontend/tests/cv_upload.js` passes 9 of 9.

**Thorough testing, 6 Nov afternoon** (transcripts in `docs/test-results/*-2026-11-06.txt`):
- `frontend/tests/cv_upload.js`, **33 checks**: Word, PDF (from Word and from
  Chrome, one and two pages, two columns, bullets) and text; an upper-case
  extension, an uncompressed .docx, accented and isiZulu text, the 15,000-character
  cut, the same file twice; refusals for a scanned PDF, a corrupt PDF, a corrupt
  .docx, an old .doc, a picture and a file over 5 MB; and that no file bytes
  reach the server. It found one bug, now fixed: Word's bullets came out of PDFs
  as box characters.
- `frontend/tests/job_cards.js`, **28 checks**: labelling, ranking and fit
  against the API, Apply (mouse and keyboard), the Jobs page, Back and focus,
  card links, the job-page section (show more and fewer), live updates without a
  reload, a goal change, a job with no adverts, the enrolled student, dark mode
  and 320 px.
- With the listings table missing, the cards hide themselves, with no errors,
  and the demo path still passes.
- **Not tested:** password-protected PDFs (they should get "couldn't be opened")
  and CVs that are images (they need pasting; no OCR).

**Both features are done and green (6 Nov, about 15:05 SAST):** 62 unit, 108
API and 5 performance tests; the demo walk (50/50, numbers unchanged); the
keyboard walk; axe 0 failures in light, dark and 320 px, the new screens
included; and a fresh clone without the advert file loads both caches. They are
on `main-7rly7s`; `main` and `presentation-2026-11-06` don't have them.

Every card must say the listings are **real US adverts from March–April 2024,
used as demo data**, not openings to apply to (ADR-0017 still holds).

---


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

0. **The Assignment 4 report and slides. Report drafted 24 October** (`docs/ISJ107V_Assignment4_219045719.pdf`, 10 body pages, five UML types updated in `docs/uml/a4/`); **you still need to read it, confirm the two declarations, and upload it and your slides to Brightspace.** Brief: (found 24 October, from the brief): a searchable PDF of 8–12 pages named `ISJ107V_Assignment4_StudentNumber.pdf` (Q1–Q4, five UML diagrams, tests, measures, limitations, AI and originality declarations) plus the slides, uploaded to Brightspace. The brief also sets the presentation as **5 minutes of talk and a 10-minute demo**. See `docs/presentation.md` §0, §2 and §9.
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
`frontend/tests/demo_walk.js`: `SHORT=1` for the 10-minute path, no flag for all
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
