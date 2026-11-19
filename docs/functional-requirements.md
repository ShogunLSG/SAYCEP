# Functional requirements (Assignment 2, Question 2.1)

> **Drafted 19 September as a starting point — rewrite these in your own words.**
> They are assessed and you are questioned on them directly. Every statement below
> is grounded in what is actually in `saycep.db`, so the acceptance criteria are
> testable rather than aspirational, but the phrasing should sound like you.
>
> IDs, actor names and component names match the four UML diagrams in `docs/uml/`.
> The rubric marks that consistency, so if you renumber anything here, renumber it
> there too.

## The ten requirements

| ID | Priority | Requirement | Acceptance criterion |
|---|---|---|---|
| **FR-01** | Must | The system shall allow a user to create a profile by selecting one of two profile types: enrolled student or school-leaver. | **Given** a visitor on the profile creation screen, **when** they select a profile type and confirm, **then** the system creates a profile of that type and returns a unique profile identifier. |
| **FR-02** | Must | The system shall allow a user to record which of the 35 O\*NET skills they currently hold, by self-assessment. | **Given** a user with a created profile, **when** they select any subset of the 35 skills and submit, **then** the system stores exactly those skills against that profile and no others. |
| **FR-03** | Must | The system shall allow a user to select exactly one target occupation from the catalogue of 879 occupations. | **Given** a user with a captured skill profile, **when** they choose an occupation, **then** the system records that occupation's SOC code as the profile's target and replaces any target previously set. |
| **FR-04** | Should | The system shall allow a user to search the occupation catalogue by title and return all matching occupations. | **Given** the catalogue is loaded, **when** a user enters a search term of at least two characters, **then** the system returns every occupation whose title contains that term, case-insensitively, or states explicitly that there are no matches. |
| **FR-05** | Must | The system shall allow a user to filter the occupation catalogue by O\*NET Job Zone and shall display the preparation level description for the selected zone. | **Given** a user selects Job Zone 3, **when** the catalogue is displayed, **then** only the 209 occupations graded Job Zone 3 are listed, together with that zone's education, experience and training description. |
| **FR-06** | Must | The system shall rank candidate occupations by cosine similarity between the user's 35-dimensional skill vector and each occupation's O\*NET importance vector, and shall display the five highest-ranked with their similarity scores. | **Given** a profile holding at least one captured skill, **when** the user requests recommendations, **then** the system returns exactly five occupations ordered by descending similarity score, each displaying its score to two decimal places. |
| **FR-07** | Must | The system shall compare a user's captured skills against the skills required for their target occupation and shall display each missing skill classified as either essential or desirable. | **Given** a profile with captured skills and a target occupation, **when** the user views the skills gap, **then** the system lists every skill the target requires that the profile does not hold, each labelled *essential* where its O\*NET importance rating is 3.5 or above and *desirable* where it is below 3.5. |
| **FR-08** | Must | The system shall generate an ordered pathway of no fewer than three intermediate steps between the user's current profile and their target occupation, each step naming the skills to be acquired at that step. | **Given** a profile with a target occupation, **when** the user requests a pathway, **then** the system displays at least three ordered steps, each identifying a named occupation and listing at least one skill to acquire. |
| **FR-09** | Should | The system shall display the source dataset and publication date for every occupation and skill record presented to the user. | **Given** any occupation or skill shown on screen, **when** the user views it, **then** the source dataset name and that record's publication date are visible without further navigation. |
| **FR-10** | Must | The system shall rebuild its occupation database from the O\*NET source files on demand, and shall abort the load if any source file's row count differs from the published reference count. | **Given** the O\*NET source files are present and intact, **when** the load command is run, **then** the system builds a database of 879 occupations, 35 skills and 27,463 importance ratings. **Given** any source file has an unexpected row count, **when** the load is run, **then** it aborts and names the offending file. |

---

# Non-functional requirements (Question 2.2)

Four measurable requirements across FURPS+ categories. Every target below has
been measured against the running system, so none is aspirational.

| ID | Category | Priority | Requirement | Acceptance criterion |
|---|---|---|---|---|
| **NFR-01** | Performance | Must | The system shall return any screen on the demo path within 2 seconds of the request. | Measured response time is 2 seconds or less for 95% of requests across all 879 occupations. |
| **NFR-02** | Usability | Must | The system shall allow a first-time user to complete the journey from profile creation to displayed pathway in no more than five screens and without written instructions. | An unassisted first-time user reaches a displayed pathway in 5 screens or fewer. |
| **NFR-03** | Reliability | Must | The system shall refuse to start when its database is absent or fails its row-count check, rather than serving partial data. | Given a missing or incomplete database, when the service starts, then it exits with a named error and serves no requests. |
| **NFR-04** | Supportability | Should | The system shall rebuild its entire database from the O\*NET source files with a single command in under 60 seconds. | Measured wall-clock time of the rebuild command is 60 seconds or less. *(Currently 1.1 seconds.)* |

**On the "+" in FURPS+.** This project's binding constraint is a data constraint,
not a technical one: all system data must originate from Kaggle-sourced datasets,
with anything else requiring the lecturer's approval in person. It is recorded as
ADR-0002 and it is the reason the original South African job-data route was
abandoned. Worth stating explicitly in the submission — it shaped more of this
design than any performance target did.

---

# Emerging-technology requirements (Question 2.3)

The emerging technology is **content-based occupation recommendation using
mean-centred cosine similarity** over 35-dimensional O\*NET skill-importance
vectors, implemented in `backend/recommend.py`.

These three requirements were measured on the running engine, not estimated.

| ID | Metric | Priority | Requirement | Acceptance criterion |
|---|---|---|---|---|
| **TR-01** | Model accuracy | Must | The recommendation engine shall place at least one occupation from the user's own occupational family in the top five results for no fewer than 55% of test profiles. | Measured over at least 100 test profiles built from occupations' essential skill sets, at least one top-five result shares the target's SOC major group in 55% or more of cases, against a random baseline of 6.9%. *(Measured: 59.7%.)* |
| **TR-02** | Inference latency | Must | The recommendation engine shall rank the full catalogue of 879 occupations and return the top five within 100 milliseconds. | Measured 95th-percentile inference latency is 100 ms or less. *(Measured: 8.8 ms p95, 6.9 ms median.)* |
| **TR-03** | Determinism and robustness | Must | The recommendation engine shall return exactly five ranked occupations, each with its similarity score, for any profile holding at least one skill, and shall return an explicit empty result for a profile holding none. | Given a profile with one or more skills, five scored results are returned. Given a profile with no skills, an empty result and an explanatory message are returned rather than an arbitrary ranking. |

## Why the accuracy bar is 55% and not 90%

This is the question the emerging-technology section invites, and the honest
answer is the strong one.

O\*NET's 35 skills are deliberately generic — Reading Comprehension, Active
Listening, Critical Thinking — and almost every occupation requires most of them
to some degree. Measured on the loaded catalogue, **the mean cosine similarity
between an occupation and its nearest neighbour is 0.994.** In raw skill space
the occupations are near-duplicates.

That has two consequences worth owning:

**Exact-occupation recall is the wrong metric.** Asking the engine to rank one
specific occupation first, when a dozen others have near-identical skill profiles,
measures nothing useful. Motorboat Mechanics, Small Engine Mechanics and Rail Car
Repairers *should* score alike, because they genuinely are alike. Occupational
family agreement measures whether the recommendation lands in the right area of
work, which is what career guidance actually requires.

**Mean-centring is what makes it work at all.** Subtracting each skill's mean
importance across occupations re-expresses an occupation by how it *deviates* from
the average occupation, which is where the discriminating signal lives. Measured
improvement in top-five family agreement: **19.4% to 32.4%**, against a 6.9%
random baseline. Plain cosine was 2.8 times better than chance; mean-centred is
4.7 times better.

A stated target of 90% would be a claim the data cannot support, and it would fail
the first time anyone tested it.

---

## Supporting notes

Not for submission — this is your preparation for the questions each requirement
invites, and the evidence that each is traceable to real data.

**FR-01 / FR-04 / FR-05 — the two profile types.**
*Data behind it:* `Job Zones.txt`, 923 occupations graded 1–5; 879 in the loaded
catalogue (Zone 1: 31, Zone 2: 285, Zone 3: 209, Zone 4: 204, Zone 5: 150).
*Invites:* "Why do the two profiles need different routes?" — Because a
school-leaver has no qualification to aim from and needs to discover what is
reachable without a degree; Job Zones 1–3 are 525 of the 879 catalogued
occupations, so that is a
substantial answer rather than a token one. An enrolled student already has
direction and needs a target. Note that both capture skills identically — see
ADR-0004 for why inferring skills from a qualification would have meant inventing
data O\*NET does not contain.

**FR-02 — skill capture.**
*Data behind it:* O\*NET's skills taxonomy, 35 entries.
*Invites:* "Why self-assessment?" — Because nothing in the dataset maps a person
to their skills; only occupations to skills. Self-assessment is the honest input
and it keeps the system's claims inside what the data supports.

**FR-06 — the emerging technology.**
*Data behind it:* 27,463 importance ratings across 879 occupations, giving each
occupation a 35-dimensional vector.
*Invites:* "Why cosine similarity and not a neural model?" — Because the feature
space is 35 dimensions of already-curated survey data, there is no labelled
training set to learn from, and cosine similarity on normalised vectors is the
standard content-based recommendation approach for exactly this shape of problem.
It is also fully explainable, which matters when a user asks why an occupation was
suggested.

**FR-07 — the threshold.**
*Data behind it:* O\*NET Importance scale, 1–5.
*Invites:* "Why 3.5?" — **This is the design decision you own, and 3.5 is a
placeholder until you confirm it.** The argument for it: importance ratings cluster
hard on whole numbers, and 3.0 alone holds 32.5% of all ratings, so a cut at 3.0
would flip a third of the dataset depending on whether you write ≥ or >. 3.5 sits
in the sparse gap between the 3.0 and 4.0 clusters. It also yields about 7.3
essential skills per occupation, where a cut at 3.0 gives 14.4 — and fourteen
"essential" skills is not a gap a user can act on.

**FR-08 — the three-step minimum.**
*Data behind it:* `Related Occupations.txt`, 18,460 links ordered by O\*NET's
expert review. Verified: all 879 occupations have three or more reachable primary
neighbours, so this requirement is satisfiable across the whole catalogue.
*Invites:* "Where does the step order come from?" — From O\*NET's expert-review
ordering, not a similarity heuristic of our own. That is a stronger answer than
anything we could have derived.

**FR-09 — provenance.**
*Data behind it:* `source_dataset` on occupations and skills, `source_date` on
each importance rating — real dates spanning June 2010 to August 2024.
*Invites:* Nothing hostile. This requirement exists to create a good moment rather
than survive a bad one: it answers the data-origin question before it is asked.

**FR-10 — the loader.**
*Data behind it:* O\*NET's published row counts — 1,016 / 61,530 / 923 / 18,460.
*Invites:* "Why does a data load need to be a requirement?" — Because a partially
downloaded file loads cleanly and produces a database that looks right and is
quietly wrong. Failing loudly is the requirement.

---

## Renumbering from the earlier draft

The earlier four requirements are preserved in substance and renumbered so that
requirement IDs match the use cases in `docs/uml/01-use-case.puml`.

| Was | Now |
|---|---|
| FR-1 Career Pathway Builder | **FR-08** |
| FR-2 Skills gap analyser | **FR-07** |
| FR-3 User profiles | **FR-01**, **FR-04**, **FR-05** |
| FR-4 Data provenance | **FR-09** |

New from the use-case model: FR-02, FR-03, FR-06, FR-10.

---

## What makes a requirement defensible

A functional requirement says what the system must **do**. "Fast", "secure",
"user-friendly" are non-functional and belong in Question 2.2.

**Countable.** "No fewer than three intermediate steps" can be checked on screen.
"A useful pathway" cannot.

**Traceable to data.** You must be able to say which dataset makes it possible. A
requirement the data cannot support is the one that collapses when he asks where
the numbers come from.

**Demonstrable, or explicitly not.** Mark each as built or designed. Claiming
something works when it does not is worse than saying it is specified but not
implemented.

**Owns its design decision.** Every requirement hides a choice — a threshold, an
ordering, a classification. Know what yours is and why.

## Build status — say this plainly in the presentation

**As of 26 September, all ten are built and demonstrable** — FR-10 in the loader,
FR-01 to FR-09 in the API and the five-screen journey, walked end to end in a
browser against the real database. Run the app with `?presenter` and each screen
shows the requirements it satisfies.

Two things to say plainly rather than let be discovered. FR-03 needed an endpoint
the proposal does not list, `PUT /profiles/{id}/target`. And the three modules
outside the demo — CV scorer, opportunity matching, interview chatbot — are
specified, not built.

*19 November:* a student's field of study (ADR-0029) is built, but **has no
FR yet**. Its wording is the project owner's to write.

## Keep in sync

These must agree with the UML diagrams in `docs/uml/`, with proposal section 2.3,
and with whatever is actually running on demo day. One story told consistently is
most of the mark.
