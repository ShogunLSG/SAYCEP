# Plan — the API and the first vertical slice

**Status:** FR-3 decision resolved 17 September (ADR-0004). Awaiting go on the build.
**Depends on:** the data spine, built and loaded 17 September.
**Gate it serves:** Week 2 — the demo path runs end to end, ugly but working.

## What this builds

One complete user path, crude but whole:

```
choose profile type → capture skills → pick target → see gap → see pathway
```

FastAPI over the existing `saycep.db`, plus the thinnest React that can walk that
path. Not "the backend" then "the frontend" — one slice, both ends, working.

## Endpoints

```
GET  /occupations?zone=&q=          target selection, filterable by job zone
GET  /occupations/{soc}             title, description, zone, provenance
GET  /skills                        all 35, for the capture screen
POST /profiles                      {profile_type, skills[], target_soc}
GET  /profiles/{id}/gap             missing skills, labelled, by importance
GET  /profiles/{id}/pathway         ordered steps, each naming its skills
GET  /interests/match               RIASEC scores in, ranked occupations out
```

Seven endpoints. Each maps to something visible on screen — nothing built because
it might be needed later.

## The good news on skill capture

There are **35 skills total** in O*NET's skills taxonomy. Not hundreds. A capture
screen can list all 35 with a checkbox and it fits on a page. No search, no
autocomplete, no typeahead matching against a messy vocabulary — the problem that
would have eaten days under the old resume-derived plan simply isn't there.

## FR-3 needs a decision — O*NET doesn't support its stated reasoning

FR-3 says the two profiles need different capture because *"an enrolled student
has a qualification to infer skills from; a school-leaver has no qualification, so
entry has to be interest- or aptitude-based."*

The second half holds. `Interests.txt` scores all 923 occupations on the six
RIASEC types, so a short interest questionnaire ranks the catalogue. That path is
buildable as described.

**The first half does not.** O*NET has no mapping from a qualification to the
skills it confers. What it has is `Education, Training, and Experience.txt` — the
distribution of education levels held by people *in* each occupation. That answers
"what schooling do people in this job have", not "what skills does this diploma
give you".

So the enrolled-student path has to work differently. Three ways, and this is
yours to pick because it changes what FR-3 promises:

1. **Nearest-occupation pre-fill.** The student names the role they're closest to
   or heading for; we pre-fill their skill profile from that occupation and they
   correct it. Closest to FR-3's intent, and the correction step is honest about
   being an estimate.
2. **Education-level filter.** The student states their level; we use the
   education distribution to filter the catalogue to occupations that level
   actually reaches. Simpler, uses real O*NET data, but captures no skills — it
   narrows targets rather than building a profile.
3. **Self-assessment against all 35.** Both profiles tick the same 35 skills; the
   difference between them becomes what happens *after* capture, not during it.
   Simplest to build, but it weakens FR-3, which promises a different initial
   skill profile for each.

**Decided 17 September: option 3**, once the real time budget was clear — four
full days plus ten evenings. Both profiles self-assess against the same 35 skills;
the divergence moves to target selection, where the school-leaver browses Job
Zones 1–3 and the student searches directly. FR-3 is reworded and the reasoning is
in ADR-0004. RIASEC intake is specified but not built.

## The threshold lives in one place

A single constant, `ESSENTIAL_THRESHOLD`, read where the gap is labelled and
nowhere else. Changing your mind is a one-line edit and no reload, which is why
importance was stored raw.

The gap response returns the raw importance alongside the label, so the screen can
show *"Troubleshooting — essential (4.0 out of 5)"*. That turns the question "how
do you decide essential?" into something the screen has already answered.

## No authentication

A profile is a row with an id. No login, no passwords, no sessions.

This is defensible and worth saying out loud rather than hiding: authentication
demonstrates nothing about career pathways, it is the most common place a rushed
demo leaks credentials, and FR-3 concerns *profiles*, not accounts — your own
vocabulary note already draws that line. If asked, the answer is that auth was
scoped out deliberately so the two built modules could be built properly.

## What could go wrong

- **Pathway direction.** 436 of 879 occupations have a primary neighbour in a
  higher job zone, so upward progression exists for about half the catalogue. For
  the rest the pathway is lateral. Needs a rule for what "progress" means when the
  graph offers no step up — likely ordering by importance-weighted skill distance.
- **Gap of zero.** If a user ticks most of the 35, the gap may be empty. The
  screen needs something sensible to say rather than rendering a blank list.
- **35 checkboxes is dull.** It works, but it is not a demo highlight. Worth
  grouping them by O*NET's content-model families if there's time.

## Not in this plan

CV scorer, opportunity matching, interview chatbot — all specified-not-built.
Demo seed users and slide content are week 3.
