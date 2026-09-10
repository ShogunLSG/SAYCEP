# SAYCEP — SA Youth Career and Employment Platform

An AI-driven career and employment platform for South African youth. University project (ISJ107V), solo developer.

**Working demo due beginning of October 2026.** Nothing is coded yet. Current state and next actions: [STATUS.md](STATUS.md). Building from this repo: start at [CLAUDE.md](CLAUDE.md).

## What it is

SAYCEP serves two kinds of user: a student already enrolled in a qualification who needs help planning what comes next, and a young person with no qualification who needs direction, including trade and artisan routes rather than only degree ones. Detail in [docs/user-profiles.md](docs/user-profiles.md).

## Modules

Five are specified. Two are being built for October — the Career Pathway Builder (the central hub) and the skills gap analyser, which share a single data spine. The CV builder/scorer, opportunity matching engine and interview prep chatbot are documented but not implemented. See [docs/architecture.md](docs/architecture.md).

## Data

All system data comes from Kaggle, per course requirement. South African labour statistics are cited as background in the written proposal only and never loaded into the system. The dataset shortlist is in [docs/data-sources.md](docs/data-sources.md) and **none of it is verified yet** — that's the first job.

## Assessment

Assignment 2 is at least 10 functional requirements, and the presentation is built on them with questions drawn directly from them. Four are worked as examples, the rest are to be drafted: [docs/functional-requirements.md](docs/functional-requirements.md). The written proposal follows a rubric — sections in [docs/proposal-outline.md](docs/proposal-outline.md).

## Layout

```
saycep/
├── CLAUDE.md       # start here when building
├── STATUS.md       # current state, next actions
├── backend/        # FastAPI service (not built)
├── frontend/       # React client (not built)
└── docs/
    ├── functional-requirements.md   # Assignment 2
    ├── data-sources.md              # Kaggle decision + shortlist
    ├── architecture.md              # demo vs production, data spine
    ├── timeline.md                  # three-week plan with gates
    ├── proposal-outline.md          # written proposal rubric
    ├── user-profiles.md             # the two target users
    ├── DECISIONS.md                 # append-only ADR log
    ├── BACKLOG.md                   # noticed, deliberately deferred
    ├── plans/                       # approach docs awaiting approval
    └── archive/                     # the superseded August plan
```
