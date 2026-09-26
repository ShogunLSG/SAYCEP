# SAYCEP — context for Claude Code

Read this first, then `STATUS.md` for current state. This file is the entry point
for building: it carries the constraints that aren't obvious from the code itself.
For how the code works and why it was built that way, see `docs/dev-guide.md`.

## What this is

SAYCEP — an AI-driven career and employment platform for South African youth.
University project (ISJ107V), solo developer, assessed. The project ends at the
October 2026 presentation.

## Who I am

Solo developer. My background is business analysis and project management, not
heavy engineering. Explain architectural trade-offs before implementing them —
do not assume I will catch a bad decision inside generated code. If I ask for
something that will cause problems later, say so before building it.

## Hard constraints

These are not preferences. They come from the course and they override normal
engineering instincts.

**Working demo, beginning of October 2026.** Roughly three weeks from 10
September, built around a full-time job. Optimise every decision for
demonstrable-by-then. See `docs/timeline.md`.

**All system data must come from Kaggle.** Anything else needs the lecturer's
approval in person. South African statistics are cited as written background only
and never loaded into the system. See `docs/data-sources.md`. If a task seems to
need non-Kaggle data, stop and raise it rather than reaching for an API. This
rule is what killed the original ESSA/Adzuna job-data route — see ADR-0002 in
`docs/DECISIONS.md` before proposing anything that fetches live data.

**Two modules get built, three get specified.** Career Pathway Builder and skills
gap analyser are the build. CV scorer, opportunity matching and interview chatbot
are documented but not implemented unless the core lands early. Do not scaffold
the three unbuilt ones — empty folders read as abandoned work in a demo.

**The demo is a monolith on purpose.** Single FastAPI service, SQLite, React. The
proposal documents a multi-service production architecture; that is deliberately
not what gets built now. Do not "helpfully" split out the ML service. Keep module
boundaries clean in code so the split stays possible later.

## Stack

Python (FastAPI), SQLite, React. The backend's only third-party dependencies are
FastAPI and uvicorn; the frontend loads React and `htm` from a CDN with no build
step. Do not add a dependency without saying why. No LLM in the build.

Run the app from the repo root with
`python -m uvicorn app:app --app-dir backend --port 8000`.

Data comes from the O*NET 29.0 text files, loaded by `backend/load_onet.py` into
`backend/saycep.db`. That is a command you run, not something that happens at
startup — the database is a derived artifact and rebuilding it is always correct.

The schema in `docs/architecture.md` is now the schema as built, fitted to the
real columns. It is no longer a sketch, so changing it is a load-bearing decision:
say so rather than adjusting it in passing.

## How I want you to work

**Verify data before building on it.** A requirement that promises what the data
can't deliver is the failure mode that matters here, and it surfaces in front of
the marker rather than in a test.

**Plan before code.** For anything beyond a small fix, write the approach to
`docs/plans/<slug>.md` first and stop. I read it, correct it, then say go.
Catching a wrong approach in a plan costs minutes; catching it in 800 lines costs
a day I do not have.

**Vertical slices, not layers.** Build one complete user path end to end before
thickening any part of it. Never "build the data layer" then "build the gap
analyser" — build profile capture → target selection → gap → pathway, crude but
whole, then improve it. Prefer ugly and working over polished and partial.

**One concern per session.** Do not drift into adjacent work. If you spot
something else that needs doing, add it to `docs/BACKLOG.md` and carry on.

**Stop and ask when a decision is load-bearing.** Schema changes, new
dependencies, anything that changes what a functional requirement promises.
Do not decide these silently.

**Say when you are unsure.** If you are guessing at an API's behaviour or a
library's interface, say so and verify rather than producing confident code built
on an assumption.

**When scope and deadline conflict, cut scope.** One module demoed properly beats
two half-built. Every week has a gate in `docs/timeline.md`; hitting the gate is
the goal.

**Commit at every green point.** Small commits with real messages.

**Record decisions.** `docs/DECISIONS.md` is an append-only ADR log. Never
rewrite a past decision — if it changes, add an entry that supersedes it and say
so. The "why isn't this using real South African job data?" question is live, and
that log is where the answer lives.

## Things I do not want

- Do not build an employer-facing portal, a mobile app, payments, or
  qualification verification. All explicitly out of scope.
- Do not add a dependency to solve something a few lines of code would handle.
- Do not silently change scope to something easier. Tell me it is hard.
- No secrets in code. If an LLM key is ever needed it comes from an environment
  variable, `.env` stays gitignored, and the placeholder goes in `.env.example`.

If an LLM does end up in the build: every call gets a timeout, a retry limit and
a fallback, and its output is validated against a schema before it touches the
database or the UI. Assume it will occasionally return malformed JSON.

## Domain vocabulary

Use these consistently in code, comments and docs — they are the terms in the
written proposal, and mismatched naming costs marks.

- **Pathway** — the ordered plan the Career Pathway Builder generates for a user.
  This is the central artifact and the module is named for it.
- **Occupation** — a role in the reference data, with a required skill set.
- **Skill** — an entry in the skills table, classified essential or desirable
  relative to an occupation.
- **Profile** — the user's captured skills and target, not their account.
- **TVET** — Technical and Vocational Education and Training college.
- **SETA** — Sector Education and Training Authority.

*Note:* the August plan drew a distinction between "roadmap" (the personalised
plan) and "pathway" (a route in reference data). The current proposal uses
"pathway" for the personalised plan, so that usage wins. TVET and SETA remain
project vocabulary but no longer name data sources — the Kaggle rule removed
them from the system.

## Where things are

- `STATUS.md` — what's done, what's not, what's next
- `docs/dev-guide.md` — how the code works, what changed over the project, and why each approach was taken
- `docs/functional-requirements.md` — Assignment 2, the spine of the presentation
- `docs/data-sources.md` — the Kaggle decision and the dataset shortlist
- `docs/architecture.md` — demo vs production architecture, data spine
- `docs/timeline.md` — the three-week plan and its gates
- `docs/proposal-outline.md` — the written proposal's rubric sections
- `docs/user-profiles.md` — the two target users
- `docs/DECISIONS.md` — append-only ADR log
- `docs/BACKLOG.md` — noticed but deliberately deferred
- `docs/archive/` — the August dissertation-era plan, superseded

## One thing to leave alone

`docs/functional-requirements.md` has four worked requirements and a scaffold for
the rest. **FR-5 onward are mine to draft** — this is assessed work and I am
questioned on it directly in the presentation. Help refine, pressure-test and
challenge what I write. Don't write them for me.

Everything else — code, schema, data loading, UI — is fair game to build.
