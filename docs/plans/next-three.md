# Plan: interview practice, accessibility, opportunity matching (then hosting)

*Written 5 October 2026. Status: **approved — building in this order.***

## 1. Interview practice — proposal module 5, without an LLM

The proposal names an "interview chatbot". CLAUDE.md forbids an LLM in the
build, so this is **interview practice with rule-based feedback**, not a
conversation. That should be said plainly.

- **Questions** come from the goal job, using O\*NET data that's already
  loaded:
  - An opener: "Why do you want to work as a …?"
  - One question per must-have skill (or the top skills where a job has none),
    each from a template we write per skill ("Tell me about a time you fixed
    something that was broken", for Repairing).
  - One question from the job's most important task ("This job involves '…'.
    Have you done anything like it?").
- **Feedback** on a typed answer is a checklist, not a score:
  - Does it show the skill asked about? This reuses the CV scanner's rules.
  - Does it follow **situation → action → result** (the STAR method)?
  - Does the speaker say *I* rather than only *we*?
  - Is there a specific detail (a number, a place, a time)?
  - Is the length right (roughly 40–250 words)?
- **Nothing is stored**, the same as the CV text.
- **No accuracy is claimed.** There's no ground truth for answer quality, so
  the feedback rules are unit-tested and labelled as guidance.
- **New requirement implied:** interview practice. Yours to draft.

## 2. Accessibility pass — WCAG 2.1 AA

- Audit every screen with **axe-core** run from the browser tests. It's a
  test-time tool only, never shipped, so it's not a dependency of the app.
- Check keyboard-only use of the whole demo path, focus handling in the
  panels and cards, and screen-reader names for every control.
- Fix what's found. Report the violation count before and after, and record
  it in the test transcripts.

## 3. Opportunity matching — proposal module 4 *(data check first)*

- **Step 0:** find a Kaggle job-postings dataset and verify it (columns, size,
  licence, country, whether skills or titles can be linked to O\*NET). The
  "South African job postings" dataset on the shortlist was found to be
  mislabelled (`data-sources.md` §5).
- Build only if step 0 passes. Any adverts will almost certainly be from
  outside South Africa, and the screen must say so.
- Needs Kaggle access again, through the environment variable, not the chat.

## 4. Hosting — last

As discussed: split user data from reference data, load the data on deploy,
add rate limiting for plan codes, and run the tests automatically on every
push.
