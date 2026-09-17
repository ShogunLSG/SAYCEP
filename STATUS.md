# Status

**As of 17 September 2026: the data spine is built and loaded. Working demo due beginning of October.** Roughly two weeks.

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
- **Data spine built and loaded.** `backend/load_onet.py` rebuilds `saycep.db` from the O*NET files: 879 occupations, 35 skills, 27,463 skill ratings, 17,580 pathway links. Gap and pathway queries verified against real rows
- **FR-1's open risk closed** — all 879 occupations have 3+ reachable primary neighbours, so the three-step promise holds catalogue-wide
- FR-1 to FR-4 worked as examples, with the criteria for the rest
- Three-week plan with weekly gates

## Not done

- **Presentation date still unconfirmed.** Untouched since this file was written, and still the single question that changes the plan most.
- **FR-1 and FR-2 carry stale answers.** Both were written against the old dataset: FR-1 says pathway steps come from "skill-overlap distance", FR-2 says essential/desirable comes from "a set percentage of records". Under O*NET both answers changed — and they changed for the better — but the file still holds the old ones. Rehearsing those would go badly.
- **FR-5 onward not drafted.** Yours to write; questioned directly on these.
- **Opportunity-matching guidance is stale.** The drafting notes say it's blocked pending verification of the SA job postings dataset. That dataset is now verified and dead, so those requirements are specified-not-built regardless.
- All code. Backend, frontend, data loading — none of it exists.
- Proposal writing: every rubric section still empty (`docs/proposal-outline.md`)
- SMART goals and the five success criteria
- Open calls: LLM provider (may not be needed), auth approach for the demo, whether hosting is required

## Do these first

1. **Confirm the exact presentation date and what "working demo" means** — local run or deployed URL. One message, and it changes the plan more than anything else. Still not done.
2. **Draft FR-5 onward** — the remaining half of the Week 1 gate, and nothing on the build side unblocks it.
3. **Pick the essential/desirable threshold** on O*NET's 1–5 importance scale. Not urgent: importance is stored raw and the label is derived at query time, so this is a config change whenever you decide.

Week 1 gate: real data queryable in SQLite, and 10+ requirements written. Week 2 doesn't start without both.

**Gate status, 17 September:** data half ✅ — real data queryable in SQLite, gap and pathway queries both returning sensible results. Requirements half ✗ — still 4 of 10, and that half is yours.

Week 2 (build the core) can start on the data; it does not depend on the requirement count. But the gate exists because the requirements are what the presentation is built on, so the shortfall is real and carrying it into week 3 would be worse than dealing with it now.
