# Plan: the CV scorer (module 3 of the proposal)

*Written 5 October 2026. Status: **step 0 done — waiting for a go/no-go.** Findings
are in `data-sources.md` §3 and summarised below.*

## Step 0 result (5 October)

**Usable as a benchmark, with real limits.** There's a ground truth
(`matched_score`), and it's sensible and non-trivial. But there are only 341
CVs, from tech and office domains unlike SAYCEP's users, the CVs' own
experience text is lost, and about half of CV skill phrases don't map to O\*NET
at all. A scorer *can* be measured against it, as TR-01 is. The honest
expectation is a modest correlation, and it would be a result on this
benchmark, not a claim about South African CVs.

**A user question the data raises:** the school-leaver profile usually has no
CV. This module mainly serves the enrolled student.

## Why now

The proposal specifies five modules and builds two. `architecture.md` says the
CV scorer is the "stretch goal if the core lands early". The core has landed,
and the module adds real depth to the emerging-technology story. Hosting comes
after this (decided 5 October).

## What it would do (draft, to be confirmed against your proposal)

1. **The user pastes their CV text.** It's pasted, not uploaded: reading PDF
   or Word files needs a new dependency, so it waits until the paste version
   works.
2. **SAYCEP finds evidence of O\*NET's 35 skills in it** and *suggests* skills
   for the profile, each with the phrase it found ("led a team of five" →
   Coordination). **The user confirms every one.** Nothing is added
   automatically, the same self-report principle as FR-02 and ADR-0005.
3. **It scores the CV against the user's goal.** How many of the goal's
   must-haves the CV shows evidence of, plus completeness checks (objective,
   education, experience and skills sections present). The output is plain
   feedback: "Your CV doesn't show Troubleshooting. Add an example of fixing
   something."
4. **Where it lives:** an *Import from my CV* option on the skills step and
   the Skills tab, and a *CV check* card on Home. It's optional, so NFR-02's
   five screens are untouched.

## How, without an LLM or new dependencies

- **Matching CV text to skills:** build a text profile for each O\*NET skill
  from its description and the O\*NET work activities linked to it (`Skills to
  Work Activities.txt`, same Kaggle download), then use TF-IDF similarity
  sentence by sentence. TF-IDF is a few dozen lines of standard-library
  Python. This is a second, documentable emerging-technology component
  (content-based text matching).
- **The real risk:** CVs say "Excel, customer service, forklift licence", and
  O\*NET says "Operations Monitoring". The vocabulary gap is the whole problem.
  Step 0 measures how big it is before anything is promised.

## Step 0 — verify the data *(the gate)*

The Kaggle **Resume Dataset** (`saugataroyarghya/resume-dataset`, 9,544 rows,
35 columns, CC BY-NC 4.0, already rated best of five in `data-sources.md`).
Download it and check:

1. The real columns and row count against the data card.
2. **Is there a ground truth to evaluate against?** If it pairs CVs with job
   requirements and a match score (column names to confirm), the scorer can be
   *measured* against it, just as TR-01 measures recommendations. That would be
   the strongest possible evaluation story. If it has no such column, the
   evaluation has to be designed differently, and this plan changes.
3. **Vocabulary:** what share of CV skill phrases can be mapped to an O\*NET
   skill at all. If it's low, say so and stop.

## Load-bearing decisions this would need (yours)

- **New requirements.** A new module needs new FRs (CV import, CV score). You
  write them, as before. Each will have a measured figure once step 0 is done.
- **A second dataset in the system.** The Kaggle rule allows it. The
  non-commercial licence suits coursework and gets noted.
- **Privacy.** A CV holds names, addresses and phone numbers. **Proposal:**
  CV text is processed and never stored, so only the confirmed skills are
  saved. That keeps the ADR-0008 argument intact. Storing CVs would bring
  POPIA in.

## Rough size

Step 0 is under an hour. With a good ground truth, the scorer, tests and
screens are about two to three working days. Without one, add a day to
design an honest evaluation.
