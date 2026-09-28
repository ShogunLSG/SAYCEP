# Status

**As of 26 September 2026: the demo journey is built and runs end to end against the real data.** Presentation assumed first week of October, planned against 1 October.

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

1. **Presentation date still unconfirmed, and it could be in 2 days.** As of 29 September this is still open, and the earliest assumed date — 1 October — is Thursday. If it's the 1st, everything below competes for two days, not a week; ask today.
2. **Rehearsal.** The build works, which is not the same as the demo being ready. Run the path start to finish without touching code — twice, per the timeline's own gate. Use the demo script below so it's the same every time.
3. **Slides.** Not started. Build them from the ten requirements, not from the code.
4. **Assignment document, if not yet submitted:** it's my draft, not your voice; it asserts the 3.5 threshold as fact; and whether PlantUML counts as a "recognised UML tool" is unchecked.
5. **FR-08's wording** says steps name skills "to be acquired". The build names skills to acquire *and* to deepen. Either reword or be ready to explain.

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
