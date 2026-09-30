# Status

**As of 30 September 2026: Assignment 3 is drafted and due today.** The demo is no longer on 1 October; its new date is not yet known. The journey is built, tested (41 automated tests) and runs without internet.

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

## Not done — in order of what hurts most if left

1. **Submit Assignment 3 today.** `docs/ISJ107V_Assignment_3_SAYCEP.docx`, built from `docs/assignment-3-submission.md` by `node docs/build-assignment-3.js`. Read it first — it's a draft in my words, not yours.
2. **User acceptance test.** NFR-02 is reported as *partial* because no first-time user has walked the journey unassisted. Ten minutes with one person, using the demo script below, would turn it into evidence. The document says plainly that it hasn't been done.
3. **Confirm the new demo date.** Then rehearsal and slides, which are both still not started.
4. **Assignment 2 diagrams are small.** If Assignment 2 isn't submitted yet, its use-case, class and sequence diagrams print with text under 6 px. Assignment 3's are fixed; the same landscape-page approach would fix Assignment 2's.

## Done on 30 September

- 41 automated tests — 12 unit, 23 integration, 2 system, 4 performance — all passing; transcripts in `docs/test-results/`.
- The tests found a real defect: rebuilding the database under a running server dropped the profile tables. Fixed in `load_onet.py`.
- **TR-01's baseline corrected.** Assignment 2 compared 59.7% against 6.9%, which measures something different. Against its own baseline the figure is 59.7% vs 25.8% random (2.3x). Still passes the 55% target; the margin was overstated.
- Nine as-built diagrams in `docs/uml/a3/`. The Assignment 2 sequence diagram was wrong — the Pathway Service never calls the Gap Analyser — and is corrected.
- FR-08 reworded to "new or deeper", closing the old item 5.
- `requirements.txt` added; dead `gap.skills_to_acquire` removed.

## The demo script

The path that's been verified, so rehearsal repeats it exactly:

1. **I left school**
2. Tick: Operation and Control · Operations Monitoring · Equipment Maintenance · Active Listening · Critical Thinking · Monitoring
3. *For you* shows operator roles (Gas Plant Operators, 64%). Switch to *Search*, type "electric", pick **Electricians**
4. The gap: **6 held, 2 essential, 26 desirable** — Troubleshooting and Repairing are the two amber bars
5. The route: Boilermakers → Power-Line Installers → Electronics Repairers → Electricians

Expect the question "why do the recommendations not include Electrician?" The honest answer: the six skills ticked are operator skills, and the engine ranks by them. The target was reached by search, which is exactly what search is for.

## Deferred on purpose

- Light gamification polish — `docs/BACKLOG.md`, only if time remains
- RIASEC interest intake, and the three specified-only modules
