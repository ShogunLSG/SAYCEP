# Target user profiles

SAYCEP is designed around two user profiles. **If a feature does not serve one of
these two, it is out of scope.**

## 1. Enrolled student

Already enrolled in a qualification — degree, diploma or equivalent — and needs
help planning what comes next: a career pathway, skills gaps relative to their
intended role, and later a CV, matching opportunities and interview prep.

What makes this profile distinct is that a qualification already exists to reason
from. Their current skill set can be inferred from what they are studying, so
capture starts from the qualification rather than from a blank page. What they
need next is specific: internships suited to their year level, certifications
worth working toward, the gap between where the qualification leaves them and
where the target role begins.

## 2. Unqualified youth needing direction

Not currently enrolled or qualified, and needs direction — including trade and
artisan routes, not only university and degree ones.

This profile has no qualification to infer skills from, which is the whole reason
it exists separately. Capture has to start from interests and aptitudes instead.
This user leans most heavily on the Career Pathway Builder, because the question
they are asking is "what could I become, and what would it take" rather than
"how do I finish what I started".

**A limitation to state plainly.** The original design answered this profile with
a curated dataset of TVET colleges and SETA programmes, so a pathway could end in
a named institution with real entry requirements. The Kaggle-only data rule
removed that dataset (ADR-0002 in `DECISIONS.md`). What the system can now show
this user is an occupation and the ordered skills required to reach it — not
which South African college teaches them. That is a real narrowing and it is
better acknowledged than glossed over if the question comes up.

## How the two diverge in the build

FR-3 is where this becomes a functional requirement: two registration paths,
capturing a different initial skill profile for each. The reasoning is above —
one profile has a qualification to infer from and the other does not.

Beyond capture, divergence is not yet designed. Different weighting in pathway
generation, different onboarding depth, different first screens — all open, and
none of it needed for the October demo beyond the two capture paths themselves.
