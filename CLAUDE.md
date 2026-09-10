# SAYCEP — context for Claude Code

Read this first, then `STATUS.md` for current state. This file is the pack entry point: it carries the constraints that aren't obvious from the code, because there isn't any code yet.

## What this is

SAYCEP — an AI-driven career and employment platform for South African youth. University project (ISJ107V), solo developer, assessed.

## Hard constraints

These are not preferences. They come from the course and they override normal engineering instincts.

**Working demo, beginning of October 2026.** Roughly three weeks from 10 September, built around a full-time job. Optimise every decision for demonstrable-by-then. See `docs/timeline.md`.

**All system data must come from Kaggle.** Anything else needs the lecturer's approval in person. South African statistics are cited as written background only and never loaded into the system. See `docs/data-sources.md`. If a task seems to need non-Kaggle data, stop and raise it rather than reaching for an API.

**Two modules get built, three get specified.** Career Pathway Builder and skills gap analyser are the build. CV scorer, opportunity matching and interview chatbot are documented but not implemented unless the core lands early. Do not scaffold the three unbuilt ones — empty folders read as abandoned work in a demo.

**The demo is a monolith on purpose.** Single FastAPI service, SQLite, React. The proposal documents a multi-service production architecture; that is deliberately not what gets built now. Do not "helpfully" split out the ML service. Keep module boundaries clean in code so the split stays possible later.

## Stack

Python (FastAPI), SQLite, React. LLM API from the backend if needed — the two built modules may not need one at all. Kaggle CSVs load into SQLite at startup.

Data spine schema is in `docs/architecture.md`. Adjust it to fit the real dataset columns rather than forcing the data to fit; the schema was written before the datasets were verified.

## Where things are

- `STATUS.md` — what's done, what's not, what's next
- `docs/functional-requirements.md` — Assignment 2, the spine of the presentation
- `docs/data-sources.md` — the Kaggle decision and the dataset shortlist
- `docs/architecture.md` — demo vs production architecture, data spine
- `docs/timeline.md` — the three-week plan and its gates
- `docs/proposal-outline.md` — the written proposal's rubric sections
- `docs/user-profiles.md` — the two target users

## One thing to leave alone

`docs/functional-requirements.md` has four worked requirements and a scaffold for the rest. **FR-5 onward are the student's own to draft** — this is assessed work and he is questioned on it directly in the presentation. Help refine, pressure-test and challenge what he writes. Don't write them for him.

Everything else — code, schema, data loading, UI — is fair game to build.

## Working rules

Verify data before building on it. A requirement that promises what the data can't deliver is the failure mode that matters here, and it surfaces in front of the marker rather than in a test.

Prefer ugly and working over polished and partial. Every week has a gate in `docs/timeline.md`; hitting the gate is the goal.

When scope and deadline conflict, cut scope. One module demoed properly beats two half-built.
