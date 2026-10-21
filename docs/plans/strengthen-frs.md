# Plan: strengthen the existing requirements, add no new ones

*Written 4 October 2026. Status: **done 4 October.** A, B and C are built and tested. D was measured and not built (ADR-0013).*

The aim is to make FR-01 to FR-10 easier to defend in the presentation without
promising anything new. Every change below shows more of what a requirement
already promises, or closes a gap against it. There are no new FRs, no new data
sources, and nothing changes in how the gap, route or recommendations are
calculated.

## A. FR-09: provenance on the new screens *(closes a gap)*

FR-09 promises that "the source dataset name **and that record's publication
date** are visible" for every occupation and skill shown. The journey screens
meet this. The screens added on 30 September (job page, skill page, compare,
quiz results) show only the dataset name.

- **Job page:** the dataset, plus the dates of the skill ratings and task
  statements it shows.
- **Skill page:** the dataset and the dates of the ratings it lists.
- **Compare:** the dataset and the dates of the ratings behind each job's
  must-haves.
- **Quiz results:** O\*NET dates the interest profiles too, so
  `occupation_interests` gains `source_date` (a reference-table column; the
  loader rebuilds it). Each result shows its date.
- **Tests:** each endpoint returns the dates it displays.

## B. FR-06: say why each job is recommended *(more of the same requirement)*

FR-06 ranks jobs and shows the top five with scores. Each one now also says
**why**: the user's skills that matter most to that job ("You share Operation
and Control, Operations Monitoring…"), from O\*NET importance. That answers the
ethics concern in Assignment 3 §5.4, that a score can read as advice, by making
the reasoning visible. The ranking itself is unchanged, so TR-01 and TR-02 are
unaffected.

## C. FR-08: say why each step is on the route *(more of the same requirement)*

The steps are ordered by closeness to the user's skills, but the screen never
says so per step. Each step now shows "You have *n* of its *m* skills" and the
same match label used elsewhere, so "why Boilermakers first?" is answered on
screen. The ordering is unchanged.

## D. FR-06: richer skill vectors — *measure before building*

Assignment 3 §5.4 names Knowledge and Abilities as the way to raise TR-01's
narrow margin. **There's a catch to check first.** Users record only *skills*,
not knowledge or abilities. Adding those dimensions to the job vectors without
a user value for them might change nothing, or might add noise. This item
starts as a measurement: PT-01 with and without the extra dimensions. It's
built only if accuracy rises, and either way the result is recorded.

## Order and checks

A → B → C → D (measurement first). Each item gets tests, a browser check and its
own commit. The demo script in `STATUS.md` is updated where the screens change.
