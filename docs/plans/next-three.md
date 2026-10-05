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

*Done 5 October (ADR-0016): axe 169 → 0 light, 34 → 0 dark, 0 at 320 px; keyboard walk 19/19.*

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

### Step 0 result (5 October) — the data links, but it isn't "opportunities"

Script: `backend/tests/check_job_postings.py`. Output:
`test-results/job-postings-step0-2026-10-05.txt`.

**Rejected: `samanthalucywu/2023-2025-mba-jobs-data-south-africa`.** It's the
only South African candidate, and it's **synthetic**:
- 3,817 rows sampled, with only 40 titles, 10 summaries and **4 description
  templates**;
- invented company names, with every row claiming Adzuna as its source;
- MBA roles only.

Loading it would present made-up adverts as real ones.

**Candidate: `arshkon/linkedin-job-postings`** (CC BY-SA 4.0, 123,849 real
LinkedIn adverts).
- **US only, listed 24 March – 20 April 2024.** Every advert has expired.
- Its "skills" are LinkedIn's 35 broad job functions (Sales, IT…), which
  don't map onto O\*NET's 35 skills. The only possible link is **advert
  title → O\*NET title or alternate title**.
- Exact title match links 41.8% of adverts, but generic titles go wrong at
  volume:
  - "director" → Producers and Directors (824);
  - "project manager" → Construction Managers (837);
  - "sales associate" → Online Merchants (530).
- **Strict link** (one candidate occupation only, generic titles dropped):
  - 26,472 adverts (21.4%);
  - **438 of 879 occupations have 5 or more adverts**, and 219 have 20 or
    more;
  - by preparation level: Job Zone 2, 105 of 285; Zone 3, 116 of 209;
    Zone 1, only 8 of 31;
  - Electricians 84, truck drivers 91, customer service 89, restaurant
    cooks 11;
  - 7,542 strictly linked adverts are entry level or internships.
- **Precision, my hand check of 50 random strict links:** 44 clearly right,
  4 debatable (for example, HR Coordinator → HR Managers), 2 wrong (Shuttle
  Driver → underground mining loaders; Solution Architect → QA testers).
  This is one person's judgement, not an independent check.

**Verdict.** The linking problem is solvable: about 88% precision on half
the occupations. But the data can't do what "opportunity matching"
promises. These are expired American adverts, so there's nothing a South
African user can apply for. What it honestly supports is **"What employers
ask for"**: real advert examples for the goal job, how many there were, the
share open to entry-level applicants, and the requirements they repeat. It
would be labelled as US, April 2024.

**That changes what module 4 promises, so it's your decision.** Also:
- **CC BY-SA ShareAlike** applies to anything derived from the adverts
  that's redistributed. That's fine for coursework, but it needs
  attribution.
- Advert text can name recruiters, so show titles, levels and extracted
  requirement phrases, not full adverts.

## 4. Hosting — last

As discussed: split user data from reference data, load the data on deploy,
add rate limiting for plan codes, and run the tests automatically on every
push.
