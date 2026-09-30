# Status

**As of 30 September 2026 (evening): the UX pass is built.** The journey speaks in plain words, every job can be opened to see what it involves, and there is a "My plan" dashboard with progress tracking after it. 63 automated tests pass. Assignment 3 is drafted but **describes the system as it was this morning**. Its submission was deliberately held back to build this.

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

1. **Draft the requirement(s) for the new features — yours, not mine.**
   Progress tracking (and arguably the saved plan) isn't covered by FR-01 to
   FR-10. ADR-0005 and ADR-0006 describe what the system now does. The FR
   wording is assessed work for you to write, and I'll pressure-test it.
2. **Bring Assignment 3 up to the built system, then submit it.** Its
   screenshots, API list (now 11 endpoints), schema, test counts (41 → 63)
   and sequence diagram describe this morning's build.
3. **Assignment 3 as originally drafted:** `docs/ISJ107V_Assignment_3_SAYCEP.docx`, built from `docs/assignment-3-submission.md` by `node docs/build-assignment-3.js`. Read it first — it's a draft in my words, not yours.
4. **User acceptance test.** NFR-02 is reported as *partial* because no first-time user has walked the journey unassisted. Ten minutes with one person, using the demo script below, would turn it into evidence. The document says plainly that it hasn't been done.
5. **Confirm the new demo date.** Then rehearsal and slides, which are both still not started.
6. **Assignment 2 diagrams are small.** If Assignment 2 isn't submitted yet, its use-case, class and sequence diagrams print with text under 6 px. Assignment 3's are fixed; the same landscape-page approach would fix Assignment 2's.

## Done on 30 September

- 41 automated tests — 12 unit, 23 integration, 2 system, 4 performance — all passing; transcripts in `docs/test-results/`.
- The tests found a real defect: rebuilding the database under a running server dropped the profile tables. Fixed in `load_onet.py`.
- **TR-01's baseline corrected.** Assignment 2 compared 59.7% against 6.9%, which measures something different. Against its own baseline the figure is 59.7% vs 25.8% random (2.3x). Still passes the 55% target; the margin was overstated.
- Nine as-built diagrams in `docs/uml/a3/`. The Assignment 2 sequence diagram was wrong — the Pathway Service never calls the Gap Analyser — and is corrected.
- FR-08 reworded to "new or deeper", closing the old item 5.
- `requirements.txt` added; dead `gap.skills_to_acquire` removed.

## The demo script

The path that's been verified (30 September, evening), so rehearsal repeats it exactly:

1. **I left school**
2. Tick: Operation and Control · Operations Monitoring · Equipment Maintenance · Active Listening · Critical Thinking · Monitoring
3. *For you* shows operator roles, all "Strong match". Switch to *Search*, type "electric", tap **Electricians**. The panel shows *A day in this job* and "0 of 2 must-haves". Tap **Aim for this job**, then **See what's missing**
4. The gap: "You already have **6 of the 34** skills this job uses. **2 must-haves** still to learn". Those are Troubleshooting and Repairing
5. The route: Boilermakers → Power-Line Installers → Electronics Repairers → Electricians. Tap a step to show the panel again
6. **Save as my plan**. The dashboard shows 0 of 2 must-haves, and Boilermakers already ticked on the route
7. Troubleshooting → **Start learning** (nothing changes; working on it doesn't count), then **I can do this now**. The bar moves to 1 of 2, and the route recalculates
8. Reload the page. The plan comes back
9. For the marker, add `?presenter`: every SOC code, Job Zone and rating is back

Expect the question "why do the recommendations not include Electrician?" The honest answer: the six skills ticked are operator skills, and the engine ranks by them. The target was reached by search, which is exactly what search is for.

Expect "how do you know they can really do it now?" The honest answer: we don't. Progress is self-reported, just as the original skill capture is (ADR-0005).

## Deferred on purpose

- Light gamification polish — `docs/BACKLOG.md`, only if time remains
- RIASEC interest intake, and the three specified-only modules
