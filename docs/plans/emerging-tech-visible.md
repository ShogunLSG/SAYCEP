# Plan: make the emerging technology visible, and use it in two more places

*Written 16 November 2026. Status: **plan only, waiting for go.** Final
presentation: **Friday 20 November, 18:00.** Code freeze: **Thursday 19
November, 20:00.** Fallback: commit `c5d150d` (16 November, all tests green).*

## Why

At the demo the lecturer was unsure what the emerging technology was. The
engine (mean-centred cosine similarity over 35 O\*NET skill ratings, the
recommendation engine) works, but on screen it is invisible: five jobs appear
with "Because you have: …", and nothing shows a model at work. It currently
drives three things, none of them labelled: the *For you* list, the order of the
Pathway, and (a separate matcher) the interest quiz.

**No new data.** ADR-0013 measured richer job vectors (85 more O\*NET
dimensions): 59.7% → 60.5%, which is noise. Kaggle course catalogues exist, but
their licences couldn't be verified (15 November) and linking courses to skills
is the text matching that failed in ADR-0014. Both are backlog items.

## A. "How we matched you": the engine, shown step by step (about 3 hours)

A page that opens from **"How did we match you?"** on each *For you*
recommendation and on a job page (when there's a profile). It walks the real
numbers for this person and this job, in the four steps the presentation uses:

1. **The job as 35 numbers.** Bars for how much the job needs each skill (O\*NET
   importance, 1–5), grouped as on the Skills tab.
2. **You as 35 numbers.** The skills you ticked.
3. **What makes this job different.** The same bars after subtracting the
   average job: above-average needs to the right, below-average to the left.
   Reading and listening shrink to almost nothing, which is the point of
   centring.
4. **The score.** "Similarity 0.47: Good match", and the skills that lifted it
   most. These are the same reasons the list shows, so the panel explains the
   list.

Plus one comparison the lecturer will remember. It shows this job's score before
and after centring, and the range across all 879 jobs. For Thabo, **without
step 3 every job scores between 0.27 and 0.58**, all squeezed together and all
positive; **with it they spread from −0.56 to 0.64**, and unsuitable jobs go
negative. *(Corrected 17 November: the first draft said "about 0.9", which is
the job-to-job figure, not the person-to-job one. Measured before building.)*

- **Backend:** `GET /profiles/{id}/match/{soc}`. Per skill: job importance, its
  centred value, whether you hold it, your centred value, and its contribution
  (the product). Also the score, the score without centring, the match words and
  the top reasons. Built from `recommend.py`'s own functions, so it can't
  disagree with the list.
- **Front end:** a new page, with CSS bars and no chart library. Every bar has
  its number as text; the bars themselves are decorative to screen readers.
- **A label wherever the engine runs:** a small **"Skill-matching model"** tag
  on *For you*, the Pathway, and the two new sections below, linking to this
  page. *(Wording to confirm: "skill-matching model" is accurate. "AI" is
  catchier but invites "which AI?" questions.)*

## B1. "Jobs your CV points to" (about 1 hour)

After a CV check, the skills the CV seems to show go **into the same engine**,
which returns the five closest jobs, each with its reasons. For a school-leaver
they're limited to Job Zones 1–3, as on *For you*.

- It's labelled "based on the skills your CV seems to show". The suggestions
  are unconfirmed, and the section says so. Nothing is added to the profile.
- It needs at least one skill found; otherwise it shows a short message.
- **Backend:** a `points_to` field on `POST /cv/scan`. The scanner is untouched,
  so r = 0.27 stands.

## B2. "Jobs with the closest skills" on a job page (about 1.5 hours)

The engine compares this job with every other job and lists the five closest,
marking those **O\*NET's experts also list** as related. It sits beside the
existing "Jobs like this" (the experts' list).

**Measured on 16 November, before building:**

| Measure, over all 879 jobs | Engine | Random |
|---|---|---|
| Top 5 includes at least one job the experts list as related | **60.6%** | 4.7% |
| Share of the top 5 the experts also list | **19.8%** | 0.9% |

- This becomes **PT-05** in `test_performance.py`: a second accuracy figure for
  the presentation, independent of PT-01.
- **An honest note for the Q&A:** comparing job with job, centring changes
  nothing (plain cosine also gives 60.6%). Centring matters when matching a
  *person*, whose ticks are all 0 or 1, to jobs. The panel in A shows exactly
  that.
- **Backend:** `GET /occupations/{soc}/similar?limit=5`.

## What does not change
- No schema change, no new data, no new dependency, no change to `cvscan.py`,
  so the committed seeds stay valid.
- The demo path's numbers are unchanged: `demo_walk.js` must still pass 50/50.

## Tests
- **Unit:** the per-skill contributions add up to the score's numerator; the
  panel's reasons equal `recommend.reasons`; the before-centring score is the
  plain cosine; similarity excludes the job itself and is symmetric;
  `points_to` respects the zone limit.
- **API:** 404s for an unknown job or profile; a profile with no skills gets a
  message, not an error; nothing is stored.
- **Browser:** new `frontend/tests/engine_visible.js`. The panel's numbers match
  the API; tags link to the panel; the CV page shows "points to"; the job page
  shows the closest jobs with expert marks. Then the full regression, with axe
  (light, dark and 320 px) covering the new screens.

## Schedule
| Day | Work |
|---|---|
| Tue 17 | A (the panel and the tags) |
| Wed 18 | B1, B2 and PT-05; tests |
| Thu 19 | Full regression, docs (ADR-0025, STATUS, demo steps, a line in the script for slide 4), rehearsal. **Freeze 20:00** |

If anything isn't green by Thursday 19:00, it's reverted, and the rest ships.

## Backlog (named in the talk as next steps, not built)
- **Field of study as input** (O\*NET Knowledge): the "richer user input"
  ADR-0013 found is the real lever. It needs a schema change and a new screen.
- **Courses per missing skill** from a Kaggle course catalogue, once a licence
  is verified.

## Load-bearing decisions in here
- **What to call it on screen** ("Skill-matching model", or something else).
- **Adding PT-05 as a second accuracy figure.**
