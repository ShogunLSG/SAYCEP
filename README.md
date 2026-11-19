# SAYCEP — SA Youth Career and Employment Platform

An AI-driven career and employment platform for South African youth. University project (ISJ107V), solo developer.

**Final presentation: Friday 20 November 2026.** The prototype is built and running against real Kaggle data, with all five proposal modules in working form and every figure measured by a test. Current state and next actions: [STATUS.md](STATUS.md). How it works and why: [docs/dev-guide.md](docs/dev-guide.md). Building from this repo: start at [CLAUDE.md](CLAUDE.md).

## What it is

SAYCEP serves two kinds of user: a student already enrolled in a qualification who needs help planning what comes next, and a young person with no qualification who needs direction, including trade and artisan routes rather than only degree ones. Detail in [docs/user-profiles.md](docs/user-profiles.md).

## Modules

All five proposal modules exist. Two are built in full, and three in reduced forms that are stated plainly on screen:

| Module | What it does | Built as |
|---|---|---|
| **Career Pathway Builder** (the hub) | Skills → a target → an ordered Pathway of nearby jobs, with progress tracking | Full |
| **Skills gap analyser** | Must-have and desirable skills between you and a job | Full |
| **CV check** | Upload (PDF, Word, text) or paste; skills it shows, a goal score, what to add, jobs it points to | Reduced: rule-based reading, no OCR |
| **Opportunity matching** | What employers ask for, plus "Jobs for you" cards ranked by fit | Reduced: real US adverts from 2024, labelled as sample listings |
| **Interview practice** | Skill, tool and task questions; checklist feedback; retry | Reduced: guidance, not a chatbot |

**The emerging technology** is a content-based recommender, the **skill-matching model**: mean-centred cosine similarity over 35 O\*NET skills, comparing a person with each job's ratings and its must-have list. It ranks *For you*, orders the Pathway, turns a CV into job suggestions and finds each job's closest jobs. A "How we matched you" panel shows its numbers step by step. Measured: 67.5% against 25.9% by chance (PT-01b; 58.5% before the 19 November improvement, ADR-0027), and 60.6% agreement with O\*NET's experts against 5.2% (PT-05). There is no LLM. See [docs/architecture.md](docs/architecture.md).

## Data

All system data comes from Kaggle, per course requirement. South African labour statistics are cited as background in the written proposal only and never loaded into the system.

The spine is the **O*NET 29.0 Database** (U.S. Department of Labor, CC BY 4.0, via Kaggle) — 879 occupations with importance-rated skills, job zones and an expert-ordered related-occupations graph. It replaced an earlier five-dataset shortlist after verification found two of those unusable. Job adverts come from **LinkedIn Job Postings 2023–2024** (Kaggle, CC BY-SA 4.0; US, closed), stored as counts and features only, never advert text. The CV check was measured on the Kaggle **Resume Dataset**. Detail in [docs/data-sources.md](docs/data-sources.md); the reasoning in [docs/DECISIONS.md](docs/DECISIONS.md).

## Assessment

Assignment 2 is at least 10 functional requirements, and the presentation is built on them with questions drawn directly from them: [docs/functional-requirements.md](docs/functional-requirements.md). Assignment 4 (the prototype report and slides) is submitted; the presentation guide is [docs/presentation.md](docs/presentation.md) and the spoken script [docs/presentation-script.md](docs/presentation-script.md). The written proposal follows a rubric — sections in [docs/proposal-outline.md](docs/proposal-outline.md).

## Layout

```
saycep/
├── CLAUDE.md       # start here when building
├── STATUS.md       # current state, next actions
├── requirements.txt            # fastapi and uvicorn: the only packages
├── backend/
│   ├── load_onet.py            # builds saycep.db from the O*NET files (then loads the two advert caches)
│   ├── load_adverts.py         # advert counts (Kaggle LinkedIn postings), cached in seed/
│   ├── load_listings.py        # sample listings for "Jobs for you", cached in seed/
│   ├── app.py                  # the API (32 endpoints), and serves the app
│   ├── gap.py, pathway.py      # the two core modules
│   ├── recommend.py            # the emerging technology: the skill-matching model
│   ├── cvscan.py, cvadvice.py  # CV check: reading, and what to add
│   ├── interview.py            # interview practice
│   ├── adverts.py, listings.py # what employers ask for, and job cards
│   ├── seed/                   # committed caches, so a fresh clone runs everything
│   └── tests/                  # unit, API and performance tests
├── frontend/       # the app (React + htm, vendored, no build step); tests/ has the browser checks
└── docs/
    ├── dev-guide.md                # how it works, what changed, and why
    ├── functional-requirements.md   # Assignment 2
    ├── data-sources.md              # Kaggle decision + shortlist
    ├── architecture.md              # demo vs production, data spine
    ├── timeline.md                  # the plan and its gates, to the final presentation
    ├── presentation.md              # presentation guide: demo path, set-up, Q&A
    ├── presentation-script.md       # what to say over each slide
    ├── deploy.md                    # optional Fly.io deployment
    ├── test-results/                # dated transcripts of every test run
    ├── proposal-outline.md          # written proposal rubric
    ├── user-profiles.md             # the two target users
    ├── DECISIONS.md                 # append-only ADR log
    ├── BACKLOG.md                   # noticed, deliberately deferred
    ├── plans/                       # approach docs awaiting approval
    └── archive/                     # the superseded August plan
```
