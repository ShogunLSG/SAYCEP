# Plan: sharper CV advice and interview practice, before the final presentation

*Written 15 November 2026. Status: **plan only, waiting for go.** Final
presentation: **Tuesday 17 November, 18:00**. Code freeze: **Monday 16
November, 20:00**. Tuesday is rehearsal only.*

## What exists today (checked in the code, 15 November)

- **CV check:** skill suggestions from trigger words, each quoting the line
  that showed it. A goal check that lists the job's tools and software the CV
  names, up to 6 "worth mentioning" tools it doesn't, the job's key skills with
  or without evidence, and a section checklist. Score r = 0.27 against human
  match scores (ADR-0014).
- **Interview practice:** an opener, one question per key skill, one question
  from the job's top O\*NET task. Feedback is a five-item checklist with a tip
  for each miss. Nothing is stored.

## Data check first (CLAUDE.md: verify before building)

- **No Kaggle dataset of interview questions was found** (15 Nov). The nearest
  are on Hugging Face, which the Kaggle-only rule (ADR-0002) forbids without
  the lecturer's approval. **So no new data is used for the interview.**
- The Kaggle LiveCareer resume set has CV text and category labels but **no
  match scores**, so it can't improve or measure the goal score. Not used.
- **Everything below uses data already in the database:** O\*NET tools and
  tasks, and the advert counts.

## What I'd build (in this order; stop at any point and the rest still works)

### 1. CV: "what to add", with evidence (about 2 hours)
For each key skill the CV doesn't show, and each tool the job names that the CV
lacks, say **how common it is in real adverts for this job** and **how to word
it**:

> "7 in 10 adverts for electricians mention a trade licence. If you have one,
> say so: *I hold a …*."
> "Multimeters are named in these adverts. If you've used one: *I used a
> multimeter to test circuits.*"

- Additive fields on `POST /cv/scan` (`goal.add`), from `advert_counts` and
  O\*NET tools. **No change to the scanner or the score**, so r = 0.27 stands.
- Example sentences are ours, one per requirement and per skill, in the same
  style as the interview questions.

### 2. Interview: a technical question from the job's own tools (about 1 hour)
After the skill questions, add one: *"Tell me how you would use a multimeter in
this job, or when you have."* It's built from the job's O\*NET tools and
software. Feedback checks the tool is named. In `interview.py`, which is **not**
part of the advert-cache fingerprint.

### 3. Interview: retry and see the checklist improve (about 1 hour)
Resubmitting an answer shows **"2 of 7 → 5 of 7"** and which items turned green.
Front-end only, plus a short worked example answer for the missing parts
(situation, action, result) built from the user's own wording where possible.

### 4. Optional, only if 1–3 are done and green by Monday 16:00
- **More CV tips:** contact details, dates, length. Small rules, no accuracy
  claim.

## What I'd deliberately not do
- **Change the CV skill rules** (to catch more phrases). `cvscan.py` is part of
  the advert-cache fingerprint (ADR-0019), so any edit invalidates **both**
  committed seeds and needs the 517 MB advert file and about 4 minutes of
  recomputing, plus a re-measure of r = 0.27. Too risky two days out.
  Backlog it.
- **An LLM interviewer,** or data from outside Kaggle.

## Tests (same standard as the last two features)
- Unit: advice text from advert counts; the technical question per job; retry
  comparison. API: `goal.add` shape, 404s, nothing stored.
- Browser: extend `demo_walk.js` only where the demo path changes; new
  `frontend/tests/interview_retry.js`. Then the full regression: 62 unit, 108
  API and 5 performance tests, demo walk, keyboard walk, CV upload, job cards,
  and axe in light, dark and 320 px.
- If anything fails and isn't fixed by **Monday 20:00**, I revert that item, and
  the rest ships.

## Safety net
- Make a snapshot branch of the current tested state (**`final-fallback-2026-11-15`**)
  before the first change. It includes job cards and CV upload, unlike
  `presentation-2026-11-06`.
- The submitted report and slides don't change. In the talk, say these are
  "added since the report".

## Docs
ADR-0024, `STATUS.md`, `presentation.md` demo lines, `presentation-script.md`,
and a note in `BACKLOG.md` for the CV rules.

## Load-bearing decisions in here
- **No new data and no schema change,** so no seed changes.
- **No change to the measured scanner,** so no new accuracy claims.
