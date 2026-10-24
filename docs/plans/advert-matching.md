# Plan: "Past adverts you'd fit": matching the user to real adverts

*Written 24 October 2026. Status: **plan only, waiting for go.** Would
partly supersede ADR-0017. It keeps that ADR's "never offered as openings"
rule and adds per-advert matching.*

## Why

The proposal's module 4 is *opportunity matching*. Today the app only
summarises the adverts for a job ("What employers ask for"). The owner wants
matching built even with non-South African data, with the mismatch listed as
a limitation (decided 24 October).

## What the user sees

On a job page and on the dashboard, a section **"Past adverts you'd fit"**
lists up to 10 real adverts for that job, best fit first. Each shows:

- the advert title and US state;
- **how you fit:** "You have 4 of the 6 skills it mentions";
- whether it is open to beginners, and the years of experience it asks;
- what it requires: matric, degree, trade or driver's licence, training given.

It always says **United States, March–April 2024, closed: examples, not
openings to apply to.** It shows no company name, no link and no salary
(US dollars would confuse a South African user).

## How the fit is scored (simple and explainable)

1. **Skills:** of the O\*NET skills the advert mentions (the same rules as
   now), the share the user holds.
2. **Beginner-friendly** adverts rank higher for a school-leaver: entry level,
   or no years asked.
3. A tie-break on the job's software and tools that the user's CV named, if
   they used the CV check.

The score is shown as plain words, never as a percentage that suggests
precision. **No accuracy is claimed.** There's no ground truth (nobody was
hired), and adverts mention skills loosely (median Spearman +0.23 against
O\*NET, ADR-0017). The rules are unit-tested on worked examples, as for
interview practice.

## Data

- **New table `advert_examples` (a schema change).** One row per advert,
  keeping only features: occupation, cleaned title, state, experience level,
  years asked, requirement keys, and the skills, software and tools it
  mentions. Never the advert text, company or link.
- **Limited to the 30 most recent adverts per occupation**, so about 10,000
  rows. It's computed in the same pass as the existing counts, and the
  committed seed grows from 0.7 MB to about 2–3 MB.
- Adding to the advert pass changes the code fingerprint, so the seed is
  regenerated (`load_adverts.py --fresh`, about 2.5 minutes) and committed.
  TC-U14d keeps it honest.

## Tests

- **Unit:** fit scoring on worked examples; beginner ordering; nothing
  personal stored.
- **API:** `GET /occupations/{soc}/adverts/examples?profile_id=`
  - returns at most 10;
  - 404 for an unknown job;
  - "too few" below 5 adverts;
  - works without a profile (no fit shown).
- **Demo walk, axe audit and keyboard walk:** extended to the new section.

## Docs

ADR-0023, `architecture.md` schema, the report (Q1.2 row, Q2.3 data, Q4.3
limitation 1 already covers non-SA data; add "closed adverts, cannot be
applied to"), the slide features table, `presentation.md`, `STATUS.md`.

## Load-bearing

- A schema change: a new table.
- It changes what module 4 promises. It matches the user to adverts, but
  they're examples, not openings.

## Size

About 4–5 hours with tests and docs.
