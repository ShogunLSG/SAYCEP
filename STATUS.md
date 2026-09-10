# Status

**As of 10 September 2026: nothing coded. Working demo due beginning of October.** Roughly three weeks.

## Decided

- **Data source rule: Kaggle only.** System data from Kaggle; South African statistics cited as written background only, never loaded into the system. Avoids the consultation dependency. (ADR-0002)
- **Data spine: O*NET 29.0**, taken from Kaggle. Replaced the original five-dataset shortlist after verification. Gives importance ratings per skill, job zones 1–5, and an expert-reviewed related-occupations graph. (ADR-0003, `docs/data-sources.md`)
- **Demo stack: monolith.** Single FastAPI service + SQLite + React. The Node + separate Python ML microservice design stays as the documented production architecture but is not what gets built. (`docs/architecture.md`)
- **Scope: two modules built, three specified.** Career Pathway Builder and skills gap analyser get built — they share one data spine, which is why they're the cheap pair.
- Five core modules, two user profiles, and the proposal rubric structure — unchanged.

## Done

- Repo consolidated: the August dissertation-era plan merged with the September rescope, superseded material in `docs/archive/`
- **All five shortlisted datasets verified.** Two are unusable — the "South Africa" job postings set is not South African, and the career-recommendation set is student aptitude scores, not a role↔skill map. Recorded in `docs/data-sources.md`
- **O*NET found, verified and adopted.** File structures confirmed against O*NET's published data dictionary, not assumed
- Data spine plan written — `docs/plans/data-spine.md`, awaiting approval
- FR-1 to FR-4 worked as examples, with the criteria for the rest
- Three-week plan with weekly gates

## Not done

- **Presentation date still unconfirmed.** Untouched since this file was written, and still the single question that changes the plan most.
- **O*NET files not downloaded.** Kaggle needs a login. Blocks all building.
- **FR-1 and FR-2 carry stale answers.** Both were written against the old dataset: FR-1 says pathway steps come from "skill-overlap distance", FR-2 says essential/desirable comes from "a set percentage of records". Under O*NET both answers changed — and they changed for the better — but the file still holds the old ones. Rehearsing those would go badly.
- **FR-5 onward not drafted.** Yours to write; questioned directly on these.
- **Opportunity-matching guidance is stale.** The drafting notes say it's blocked pending verification of the SA job postings dataset. That dataset is now verified and dead, so those requirements are specified-not-built regardless.
- All code. Backend, frontend, data loading — none of it exists.
- Proposal writing: every rubric section still empty (`docs/proposal-outline.md`)
- SMART goals and the five success criteria
- Open calls: LLM provider (may not be needed), auth approach for the demo, whether hosting is required

## Do these first

1. **Confirm the exact presentation date and what "working demo" means** — local run or deployed URL. One message, and it changes the plan more than anything else. Still not done.
2. **Download the O*NET dataset from Kaggle** into `backend/data/onet/`. Everything downstream is blocked on it.
3. **Approve or correct `docs/plans/data-spine.md`**, then the loader gets built.
4. **Draft FR-5 onward** against the four tests in `docs/functional-requirements.md`.

Week 1 gate: real data queryable in SQLite, and 10+ requirements written. Week 2 doesn't start without both.

**Gate status:** data source settled and verified, which was the larger half of the risk. Neither half of the gate is met yet — nothing is loaded, and the requirement count stands at 4 of 10.
