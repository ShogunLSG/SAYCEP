# Plan: a field-of-study input for the skill-matching model

*19 November 2026. Status: **built** (go given the same day; see ADR-0029,
which records two choices: no new screen, and O\*NET's names with our
examples rather than a mapped South African list). Was: **waiting for go.** This changes the schema, adds a
question to the journey and needs a new functional requirement, which is
yours to write (CLAUDE.md: FR-5 onward are yours).*

## What the experiment found

`backend/tests/experiment_field_of_study.py`; transcript in
`docs/test-results/experiment-field-of-study-2026-11-19.txt`.

O\*NET 29.0 (the same Kaggle release) rates all 879 jobs on **33 knowledge
areas**, such as "Economics and Accounting", "Biology" and "Mechanical". The
person picks one. The model then compares it with each job's knowledge
must-haves, the same way it compares skills (ADR-0027), and blends that in
with a small weight.

PT-01b's protocol: same family in the top 5, with the target job removed. The
weight was chosen on half the jobs (w = 0.1; 0.1 to 0.33 are all within 0.3
points, so it isn't finely tuned) and reported on the other half (357 jobs):

| Field given | Skills clean | Skills messy |
|---|---|---|
| none (the shipped model) | 65.8% | 39.2% |
| one of the job's top 3 areas, at random | 68.9% | 40.9% |
| the job's top area | 69.7% | 43.1% |

- **Gain:** +3 to +4 points. Clean skills: significant either way. Messy
  skills: significant only when the field is the job's top area (+3.9, interval
  +0.6 to +7.3). A noisy field is +1.7 (interval −0.8 to +4.5), so not proven.
- **Chance:** 25.9%.
- **Read it honestly:** a small, real improvement, but not a big one. Its main
  value is probably in the product rather than the number. It's a question a
  student can answer, and it gives the model a second kind of evidence besides
  self-ticked skills.
- **Caveat:** the field is simulated from the job itself, which is
  favourable. No real students have been tested.

## Who it's for

**Students only.** A school-leaver has no field of study, so they don't see the
question and their model is unchanged. That matters for the demo: **Thabo's
walk doesn't change at all.**

## What gets built (about a day)

1. **Data:** `load_onet.py` loads `Knowledge.txt` into two new tables,
   `knowledge_areas` (33 rows) and `occupation_knowledge` (879 × 33, importance
   only). Rebuilding the database stays the way to get them. **This is a
   schema change; `docs/architecture.md` gets the two tables.**
2. **Profile:** a nullable `users.field_element_id` column, added in place by
   `ensure_profile_tables` (the same upgrade path `plan_code` used).
   `PUT /profiles/{id}/field` sets or clears it, and `GET /knowledge-areas`
   lists the 33.
3. **Model:** `recommend.Model` gains an optional knowledge view. With no field,
   the score is exactly today's, which a unit test will lock. With a field, the
   score is 0.9 × skills + 0.1 × knowledge. *For you*, the Pathway order and the
   CV's points-to all pick it up through the one model.
4. **Journey:** on the student path, one optional question after the skills
   step: "What are you studying?" There's a search box over the 33 areas,
   with plain examples under each ("Economics and Accounting: BCom,
   accounting, finance"), plus a "Skip" button.
5. **Panel:** "How we matched you" gains a line when a field is set: "Your
   field, Economics and Accounting, added +0.04." The contributions still add up
   to the score.
6. **Tests:**
   - unit: no field means an identical score; a field changes only the
     knowledge part;
   - API: set, clear and validate the field;
   - **PT-06:** the experiment's protocol, as a gated measurement;
   - the browser suites, with the student path including the question;
   - axe on the new screen.
7. **ADR-0029, and docs:** the user-data split moves to ADR-0030.

## Decisions for you

1. **Go or no go.** It's a +3 to +4 point gain that only students see, the day
   before the presentation.
   - **My view:** worth building only if you want "students give their
     field" as a talking point. If the aim is the demo, the gain is too small
     to show on screen, and Thabo, the demo persona, doesn't use it.
2. **The FR.** It needs a requirement, say "FR-xx: a student can give their
   field of study, and recommendations take it into account". That's yours
   to word.
3. **The list.** Should students see O\*NET's 33 area names, or a shorter list
   of South African qualification fields mapped onto them? A mapped list reads
   better, but the mapping would be ours, not Kaggle's. Under ADR-0002 that's
   fine as UI wording, but say so if asked.
