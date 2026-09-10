# Status

**As of 10 September 2026: nothing coded. Working demo due beginning of October.** Roughly three weeks.

## Decided

- **Data: hybrid.** System data from Kaggle; South African statistics cited as written background only, never loaded into the system. Avoids the consultation dependency. (`docs/data-sources.md`)
- **Demo stack: monolith.** Single FastAPI service + SQLite + React. The original Node + separate Python ML microservice design stays as the documented production architecture but is not what gets built. (`docs/architecture.md`)
- **Scope: two modules built, three specified.** Career Pathway Builder and skills gap analyser get built — they share one data spine, which is why they're the cheap pair. CV scorer, opportunity matching and interview chatbot are documented only.
- Five core modules, two user profiles, and the proposal rubric structure — all unchanged from the original plan.

## Done
- Repo and pack structure, with `CLAUDE.md` as the entry point for building
- Kaggle dataset shortlist assembled
- FR-1 to FR-4 worked as examples, with the criteria for the rest
- Three-week plan with weekly gates

## Not done
- **Kaggle datasets unverified.** Columns and row counts not confirmed — schemas render client-side and need a logged-in session. Nothing should be built until this is done.
- **FR-5 onward not drafted.** Yours to write; the presentation is questioned directly on these.
- All code. Backend, frontend, data loading — none of it exists.
- Proposal writing: every rubric section still empty (`docs/proposal-outline.md`)
- SMART goals and the five success criteria
- Open calls: LLM provider (may not be needed), auth approach for the demo, whether hosting is required

## Do these first

1. **Confirm the exact presentation date and what "working demo" means** — local run or deployed URL. This changes the plan more than anything else and it's a one-message question.
2. **Verify the Kaggle datasets** and record real columns in `docs/data-sources.md`. Everything downstream depends on what's actually in them.
3. **Draft FR-5 onward** against the four tests in `docs/functional-requirements.md`.

Week 1 gate: real data queryable in SQLite, and 10+ requirements written. Week 2 doesn't start without both.
