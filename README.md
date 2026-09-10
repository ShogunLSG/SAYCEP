# SAYCEP — SA Youth Career and Employment Platform

An AI-driven career and employment platform for South African youth — pitched as "LinkedIn-like." School project, solo developer, running Feb–Nov 2026.

Status: planning/proposal stage. Nothing has been coded yet. See [STATUS.md](STATUS.md).

**Presentation begins beginning of October 2026**, built on 10 functional requirements (Assignment 2 — see [docs/functional-requirements.md](docs/functional-requirements.md)). Project data must come from Kaggle, or from a lecturer-approved alternative — see the data sourcing rule in [docs/architecture.md](docs/architecture.md).

## What it is

SAYCEP helps two kinds of users:

1. A student already enrolled in a qualification who needs help planning their career path.
2. An unqualified young person who needs direction — including trade/artisan paths, not just degree routes.

Full detail on both profiles: [docs/user-profiles.md](docs/user-profiles.md).

## Core modules

Five modules, with the Career Pathway Builder as the central hub the other four feed into:

1. **Career Pathway Builder** (central)
2. **CV builder / scorer**
3. **Skills gap analyser**
4. **Opportunity matching engine**
5. **Interview prep chatbot**

Architecture and tech stack: [docs/architecture.md](docs/architecture.md).

## Repo layout

```
saycep/
├── backend/        # Node.js API (placeholder — not started)
├── frontend/        # React client (placeholder — not started)
├── ml-service/     # Python ML microservice (placeholder — not started)
├── docs/
│   ├── proposal-outline.md         # rubric structure for the written proposal
│   ├── architecture.md              # tech stack + module breakdown + data sourcing rule
│   ├── user-profiles.md             # the two target user profiles
│   ├── functional-requirements.md   # Assignment 2 — 10+ functional requirements
│   └── timeline.md                  # phases, Feb–Nov 2026, presentation date
└── STATUS.md       # what's actually done vs. still on paper
```

## Proposal / rubric

The written proposal has to be built against a marking rubric. Section-by-section breakdown: [docs/proposal-outline.md](docs/proposal-outline.md).

## Timeline

Feb–Nov 2026, seven phases. Details (and gaps to fill in): [docs/timeline.md](docs/timeline.md).
