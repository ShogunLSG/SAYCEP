# Timeline

Solo developer. The proposal describes a Feb–Nov 2026 seven-phase plan; that stays in the written document as the project's formal schedule. What follows is the real working plan from today, which is what actually needs executing.

## Fixed point

**Presentation: beginning of October 2026, with a working demo expected.** From 10 September that is roughly three weeks, worked around a full-time job.

**Confirm first, before anything else:** the exact date, and what "working demo" means to him — a local run on your laptop, or a deployed URL. A demo due 1 October rather than 7 October is a quarter of the available time, and "deployed" adds a workstream that "local" doesn't. This one question changes the plan below more than any other decision, so ask it this week.

## Three-week plan

### Week 1 — 10 to 17 September: data and requirements
Nothing gets built on unverified data. This week is about removing that risk and locking the requirements.

- Confirm the presentation date and demo expectations with the lecturer
- Open each shortlisted Kaggle dataset, record real columns and row counts in `data-sources.md`
- Settle on the role↔skill dataset that becomes the spine; discard the rest for now
- Load it into SQLite against the schema in `architecture.md`; adjust the schema to the data rather than forcing the data into the schema
- Draft FR-5 onward and finalise the full list of 10+

Gate: real data queryable in SQLite, and 10+ requirements written. Do not start week 2 without both.

### Week 2 — 18 to 24 September: build the core
- FastAPI service over the SQLite spine
- Skills gap analyser first — it's the simpler of the two and the pathway builder depends on the same queries
- Career Pathway Builder on top of it
- Minimal React UI: profile capture, target selection, gap view, pathway view

Gate: the demo path runs end to end, ugly but working. Ugly and working beats polished and partial.

### Week 3 — 25 September to 1 October: demo-ready
- Seed a believable demo user for each of the two profile types, so the story lands
- Add the source-dataset labels for FR-4 — small, visible, and it pre-empts the provenance question
- Tighten only the screens that appear in the demo; leave the rest
- Build the slides directly from the 10 requirements
- Rehearse the Q&A: for each requirement, say it out loud, then answer the question it invites

Gate: run the whole demo start to finish without touching code. Twice.

## After October

Build-out to November: the CV scorer, then opportunity matching if the job postings data proves usable. Both are specified in the proposal regardless of whether they get built.

## Slippage rule

If week 1 runs over, cut scope, not the gates. One module demoed properly with data you can account for beats two half-modules and a question you can't answer.
