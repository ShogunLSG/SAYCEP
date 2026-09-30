# Plan: plain-language pass, role detail, and a "My plan" dashboard

*Written 30 September 2026. Status: **approved 30 September — building.***

**Decisions taken (30 September):**
1. Progress has **two states, "working on it" and "I can do this now"**. This
   is a schema change: a `status` column on `user_skills`, recorded as an ADR.
   Only "I can do this now" counts as holding a skill. "Working on it" never
   closes a gap.
2. **Task 5 is approved**, and runs after Tasks 1–4.
3. Data comes from the **Kaggle copy**, downloaded into this environment with
   an API token. Nothing is committed.
4. The order is **1 → 2 → 3 → 4 → 5**, with a commit after each.

## The problem, in the user's words

After walking the journey, three things stood out:

1. **It shows numbers the user won't understand.** Examples: `3.62 / 5`,
   `47-2111.00 · Job Zone 3`, a `64%` ring, `1.25 → 3.50`. These make sense to a
   marker checking FR-07 and FR-09. They mean nothing to a 19-year-old who has
   just left school.
2. **It ends abruptly.** Five screens, then "Start again". After the user sees a
   route, the app gives them nothing to come back to.
3. **It feels thin.** There's not much to explore. For example, a school leaver
   who taps "Boilermakers" is never told what a boilermaker actually does,
   although the description is already in the database.

## Who this is for

We are designing for the two profiles in `docs/user-profiles.md`, especially the
school leaver. That user is deciding under pressure, doesn't know the job titles,
and has never heard of an importance scale. The rule for every screen: **a
sentence first, a figure only if it earns its place.**

The marker still needs the numbers. The raw figures stay available behind
`?presenter`, which already exists. Nothing is removed from the evidence. It just
stops being the first thing a user sees.

## Constraints this plan respects

- **NFR-02 (five screens to a pathway) stays intact.** The dashboard comes
  *after* the pathway is displayed. It is not a sixth step in the journey, and
  the journey still reaches a pathway on screen 5. This interpretation should be
  recorded as an ADR so the question has a written answer.
- **The backlog's gamification decision stands.** No streaks, XP, badges or
  leaderboards (see `BACKLOG.md`, 26 September). Progress here means progress
  toward the user's own target, measured in skills, and nothing else.
- **The frontend never calculates.** The backend decides what a number means
  (for example, that 4.1 counts as "very important"). The frontend only displays
  the label, and the rule lives in `config.py` next to `ESSENTIAL_THRESHOLD`.
- **Kaggle-only data.** Tasks 1–4 use nothing that isn't already loaded. Task 5
  is the only one that touches data, and it only loads another file from the
  same Kaggle O\*NET dataset.
- **No new dependencies.**

## The tasks — each one is shippable on its own

They are ordered so we can stop after any task and still have a better demo than
today. The new demo date isn't known yet, so this order is the scope-cut order.

### Task 1 — Plain-language pass *(small; frontend plus small backend additions)*

Replace the figures with words everywhere. Keep the figures in presenter mode.

| Now | Becomes |
|---|---|
| `3.62 / 5` + bar | "Very important for this job" + the bar (bands below) |
| `47-2111.00 · Job Zone 3` | "Some training after school" (plain names for zones 1–5) |
| `64%` ring | "Strong match" / "Good match" / "Some overlap", keeping the ring |
| "6 · 2 · 26" stat tiles | "You already have 6 of the 34 skills this job uses. **2 are must-haves you don't have yet.**" |
| "Essential / Desirable" tags | "Must-have" / "Nice to have" |
| `1.25 → 3.50` in the route | "You'll use this more here" |
| "Essential means O\*NET rates it 3.5 or above…" | Moved to presenter mode. The user gets a one-line "Why?" they can tap |

Bands: the backend adds a `level` label to each skill, using cut-points in
`config.py`: *critical* at 4.0 and above, *very important* at 3.5, *important*
at 3.0, *useful* below that. The 3.5 cut-point matches the existing
essential/desirable threshold, so the two labels can't contradict each other.
Match bands follow the same approach. These cut-points are a presentation choice,
not a finding from the data, and the dev guide will say so.

This touches the words FR-07 and FR-09 are checked against. The requirements
themselves don't change: the classification and the source still display, just
in plain words. FR-09's acceptance test is about showing the source, so the
source line stays.

### Task 2 — "What is this job?" sheet *(small; uses existing endpoint)*

Tap any occupation, whether in recommendations, browse, search or a pathway step,
and a sheet slides up. It shows:

- the O\*NET description, which is loaded but never shown
- the preparation level in plain words, with its education and experience notes
  from `job_zone_reference`
- its top five skills, each marked ✓ if you have it
- a "Set as my target" button

`GET /occupations/{soc_code}` already returns most of this. It may need the
"which of these do you have" flag, which means passing an optional `profile_id`.
This task is what lets a school leaver *explore* rather than guess from job
titles.

### Task 3 — "My plan" dashboard *(medium; the headline feature)*

The journey's last button changes from "Start again" to **"Save this as my
plan"**. That opens a dashboard, which becomes the home screen from then on:

- **Goal card.** The target role, with one sentence on what it is.
- **Readiness.** A progress bar and a sentence: *"You have 6 of the 8 must-have
  skills."* It counts **must-have skills held**. It deliberately avoids a
  weighted percentage the user would have to take on trust. Nice-to-haves appear
  as a second, quieter line.
- **Your next step.** The first step of the route and the two or three skills it
  builds, with "See the whole route" linking to the existing pathway view.
- **Skills to work on.** Must-haves first, as a checklist (this is where Task 4
  comes in).
- **Change my goal / Explore other roles.** These go back into screen 3 and
  keep the profile.

To make the dashboard a real "come back to it" screen, the profile id is kept in
the browser's `localStorage`. Reopening the app goes straight to the dashboard,
with a "Start over" link. This isn't an account (there's no login, and none is
planned). If the browser forgets it, the user starts the journey again, and
nothing else breaks.

**Backend:** one new read endpoint, `GET /profiles/{id}` (type, target, skills
held, readiness counts), so the dashboard can rebuild itself after a reload.

### Task 4 — Progress: "I can do this now" *(small–medium)*

Each skill on the dashboard checklist gets an **"I can do this now"** action.
Ticking it:

- adds the skill to the profile (`user_skills`, **no schema change**)
- recomputes the gap and route, so the readiness bar moves and the route may
  shorten
- gives immediate feedback, such as a short tick animation and the count
  stepping down. This is the "gap counts visibly counting down" item already
  approved in the backlog.

**Backend:** `POST` / `DELETE /profiles/{id}/skills/{element_id}`, so a skill
can also be un-ticked. Tests go in `test_api.py`.

This is the feature that turns the demo from "a report" into "a tool". The
presentation can show the readiness bar moving live.

### Task 5 — *Optional, needs your decision:* "A day in this job"

O\*NET's `Task Statements.txt` is in the same Kaggle dataset we already use. It
contains 18,000 plain-English sentences like *"Install, maintain, and repair
electrical wiring…"*. In the role sheet from Task 2, these explain a job better
than anything else we have.

It is **a schema change** (new `occupation_tasks` table, a new loader step, and
an updated NFR-03 row-count check). That makes it load-bearing under CLAUDE.md,
so it only happens if you say yes. Estimate: half a day including tests.

### Task 6 — Carry it into the documentation *(do alongside each task)*

- New screenshots in `docs/screenshots/`, plus the dev guide, the API list in
  `architecture.md`, and the sequence diagram if the new endpoints appear in it
- An ADR: "The dashboard is after the journey, not in it", covering NFR-02
- An ADR if Task 5 goes ahead (new table)
- Tests for every new endpoint. The 41-test count and `docs/test-results/`
  transcripts get rerun
- **A new functional requirement is needed for progress tracking** (it's
  probably FR-11: the user records a skill as acquired and the gap and pathway
  recompute). That's yours to draft, per CLAUDE.md. I'll pressure-test it, not
  write it. The same may apply to the dashboard itself.
- Assignment 3 describes the system as it is today. If it's submitted later, it
  should describe what's built. We decide that when the build lands.

## What this plan does *not* do

- No accounts or login. `localStorage` is enough for a demo, and accounts are a
  security surface we'd have to defend in Q&A.
- No "where to study this" links. We don't have TVET or SETA data (ADR-0002),
  and inventing it would break the Kaggle rule. The role sheet says what the
  preparation level typically involves, from O\*NET, and stops there.
- None of the three specified-only modules.
- Nothing that changes how recommendations, gaps or pathways are *calculated*.
  Only how they're shown, plus user-driven profile updates.

## Decisions I need from you before starting

1. **Progress states.** Is a single "I can do this now" tick enough, or do you
   also want "working on it"? The single tick needs no schema change. "Working
   on it" needs a `status` column on `user_skills`, which is a schema change and
   a little more UI. I recommend the single tick.
2. **Task 5 (day-to-day tasks data):** yes or no? I recommend yes if the demo is
   more than a week away, and no otherwise.
3. **Running it here.** The O\*NET files are gitignored, so this cloud
   environment has no database, and I can't run the app or the tests until it
   does. Options:
   (a) I download the Kaggle copy here. This needs a Kaggle API token set as an
   environment secret.
   (b) I build blind against the tests and you run it on your laptop. This is
   riskier for UI work.
   (c) I fetch the identical O\*NET 29.0 release from onetcenter.org *for local
   testing only*, never committed. It's the same files, but strictly speaking
   it's a non-Kaggle fetch, so it's your call.
   I recommend (a) if you can add the token, otherwise (c).
4. **Order.** I propose 1 → 2 → 3 → 4, then 5 if approved. Tasks 1 and 2 are
   the cheapest big improvement, and 3 and 4 are the "more" you asked for.
