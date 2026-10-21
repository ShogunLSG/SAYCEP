# ISJ107V Assignment 3 — Project Documentation and UML Design

> **Draft for you to read and adjust before submitting.** Every figure, test
> result and screenshot below comes from the running system and is reproducible
> from the repository — nothing is estimated. Test transcripts are in
> `docs/test-results/*-v2.txt`, diagrams in `docs/uml/a3/`, screenshots in
> `docs/screenshots/v2/`.

---

# Question 1 — Project baseline [6]

## 1.1 Title, purpose, users, emerging technology and executive summary (2)

**Title:** SAYCEP — South African Youth Career and Employment Platform

**Purpose.** To show a young person which specific skills stand between them and
a named occupation and an ordered route of intermediate roles to get there,
including routes that don't require a degree, and to let them track their
progress along it.

**Intended users.** Two profiles. The *unqualified school-leaver* (ages 15–24,
the group with 60.9% unemployment in Q1 2026) needs to discover what is
reachable without a degree. The *enrolled student* has direction and needs a
target and a plan.

**Emerging technology.** Machine learning — content-based occupation
recommendation using **mean-centred cosine similarity** over 35-dimensional
O\*NET skill-importance vectors.

**Executive summary.** SAYCEP is implemented as a single FastAPI service. It
serves an eleven-endpoint REST API and a React interface made of a five-screen
journey followed by a saved *My plan* dashboard. Behind them is an SQLite
database built from the O\*NET 29.0 dataset: 879 occupations, 35 skills, 27,463
importance ratings, 17,580 expert-reviewed related-occupation links and 17,931
task statements.

A user states where they are starting from and ticks the skills they hold. They
then read what candidate jobs involve and pick a target, by recommendation, by
preparation level or by search. They receive a skills gap and a four-step
pathway, written in plain language rather than raw ratings. Saving the plan
opens a dashboard that counts progress in must-have skills held, and it
recalculates the gap and route as the user records skills they've learned.

All ten functional requirements are implemented, and 63 automated tests pass. The recommendation engine places a same-family occupation in its top five
for 59.7% of test profiles, against 25.8% for random selection. It ranks the
full catalogue in 4.7 ms at the 95th percentile.

## 1.2 Final aim, objectives, scope and changes since Assignment 2 (2)

**Aim.** To give South African youth a clear, evidence-based view of the skills
and steps required to reach a specific occupation, including routes that do not
require a degree.

| Objective (from Assignment 2) | Final result |
|---|---|
| Gap analysis for any of 879 occupations, each missing skill classified, within 2 s | Met — p95 45 ms over HTTP (PT-03) |
| Pathway of ≥ 3 intermediate steps for any target, skills named per step | Met — verified for all 879 occupations; TC-I04 |
| ≥ 55% of test profiles get a same-family occupation in the top 5 | Met — 59.7% (PT-01) |

**Scope** covers profile creation for two user types, skill self-assessment,
target selection, gap analysis, pathway generation, recommendation and data
provenance. It now also covers a saved plan with progress tracking (change 4
below). Out of scope remains: employer functionality, job listings,
qualification verification, payments, mobile apps and user accounts. The saved
plan is an identifier held in the browser, not an account. The CV scorer,
opportunity matching and interview chatbot remain specified, not built.

**Changes since Assignment 2.** Four changes were made during the build. The
first three are implementation-level decisions and change nothing a user can
do. The fourth adds user-facing functionality, and it is stated plainly here
rather than folded into the others. It sits inside the Career Pathway Builder
module. Its only new data is two further files from the same Kaggle O\*NET
dataset, and it touches nothing on the out-of-scope list. None of the four
changes the data source or the emerging technology.

1. **An eighth API endpoint:** `PUT /profiles/{id}/target`. FR-03 requires the
   system to record a target and *replace* any previous one. None of the seven
   endpoints listed in Assignment 2 could do this without a GET request that
   modifies data, which would break HTTP semantics. Verified by TC-I02b–e.
2. **FR-08 reworded to match the data.** Assignment 2 said each pathway step
   names skills "to be acquired". Consecutive occupations on a real pathway have
   skill-vector cosine similarity of 0.987 to 0.996 — they need nearly the same
   skills — so a step that lists only *new* skills was frequently empty. Each
   step now lists the skills that matter most in that role, marked **new** to
   the user or **deeper** than the previous step required. The final wording is
   in 2.1.
3. **A correction to how TR-01 was reported.** Assignment 2 stated 59.7%
   accuracy "against a random baseline of 6.9%". Those figures measure different
   things (see 2.3). Measured correctly, the matching random baseline is 25.8%.
   The requirement's 55% threshold still passes; the claimed margin was
   overstated, and this document reports the corrected comparison.
4. **A plain-language interface and a saved plan with progress tracking.**
   Walking the finished journey as a first-time user showed that it spoke to
   the marker, not the user. It showed `3.62 / 5`, `47-2111.00 · Job Zone 3`
   and bare counts that a school-leaver could not read. It also ended at the
   pathway with nothing to return to. Four changes followed:
   - **Words before figures.** Every screen now leads with words, such as
     "Critical for this job" and "Vocational training or an apprenticeship".
     The figures are still returned by the API, and `?presenter` shows them.
   - **An occupation panel (UC-11).** Tapping a job shows O\*NET's description
     and its most important tasks before the user commits to it. The tasks
     come from a new table (ADR-0007).
   - **A My plan dashboard (UC-12).** It opens after the pathway, so the
     journey to a displayed pathway is still five screens and NFR-02 is
     unaffected (ADR-0006).
   - **Two-state progress (UC-13).** A skill can be marked "working on it" or
     "I can do this now", and only the second closes a gap (ADR-0005). This
     behaviour is recorded in ADR-0005 and tested (TC-I07). It was added after
     the requirements were baselined and is not yet written as a functional
     requirement (see 2.2).

   The change added three endpoints, one table and one column, and all 63
   tests pass.

## 1.3 Document control (2)

| Field | Value |
|---|---|
| Document | SAYCEP Project Documentation and UML Design |
| Version | 1.1 |
| Date | 30 September 2026 |
| Author | Lesego Jan Malema Matsimela (219045719) |
| Module | ISJ107V — Integrated Software Project |
| Repository | github.com/ShogunLSG/SAYCEP (private), commit history from 10 September 2026 |

**Revision history**

| Version | Date | Change |
|---|---|---|
| 0.1 | 10 Sep 2026 | Project baseline; five candidate datasets verified; O\*NET 29.0 adopted |
| 0.2 | 19 Sep 2026 | Assignment 2 specification: 10 FRs, 4 NFRs, 3 TRs, four UML diagrams |
| 0.3 | 20 Sep 2026 | API implemented; recommendation engine measured |
| 0.4 | 26 Sep 2026 | Five-screen interface implemented; eighth endpoint added |
| 0.5 | 29 Sep 2026 | Interface libraries bundled locally; no internet needed to run |
| 1.0 | 30 Sep 2026 | Test suites (41 tests), as-built diagrams, loader defect fixed, TR-01 baseline corrected |
| 1.1 | 30 Sep 2026 | Plain-language interface, occupation panel with task statements, *My plan* dashboard and progress tracking (ADR-0005); 11 endpoints; 63 tests; diagrams redrawn |

**Glossary**

| Term | Meaning |
|---|---|
| Occupation | A role in the O\*NET catalogue, identified by an O\*NET-SOC code, e.g. 47-2111.00 Electricians |
| Skill | One of O\*NET's 35 skills, e.g. Troubleshooting |
| Importance rating | O\*NET's 1–5 survey rating of how important a skill is to an occupation |
| Essential / desirable | A missing skill rated 3.5 or above for the target is essential; below 3.5, desirable. The interface calls them *must-have* and *nice to have* |
| Readiness | How many of the target's must-have skills a user holds, e.g. "1 of 2"; for the 166 occupations with no must-have skill, the five most important skills are counted instead |
| My plan | The dashboard a user reaches by saving their pathway; reopened on later visits from an identifier kept in the browser |
| Skill status | *Held* ("I can do this now") or *learning* ("working on it"); only held skills count toward the gap |
| Task statement | O\*NET's plain-English description of one thing a person in the job does |
| Job Zone | O\*NET's 1–5 grade of preparation an occupation needs; Zones 1–3 need no degree |
| Profile | A user's captured skills and chosen target — not an account |
| Pathway | The ordered route of three intermediate occupations plus the target |
| Mean-centred cosine similarity | Similarity between two skill vectors after subtracting each skill's average across all occupations |
| SOC major group | The first two digits of a SOC code — the occupational family, e.g. 47 = construction |
| FR / NFR / TR | Functional / non-functional / emerging-technology requirement |
| UC / TC / PT | Use case / test case / performance test |
| TVET, SETA | Technical and Vocational Education and Training college; Sector Education and Training Authority |

**Referenced artefacts**

| Artefact | Location |
|---|---|
| Assignment 2 proposal and specification | `docs/ISJ107V_Assignment_2_SAYCEP.docx` |
| Architecture decision records | `docs/DECISIONS.md` (ADR-0002 data source, ADR-0003 O\*NET, ADR-0004 profile capture, ADR-0005 progress states, ADR-0006 dashboard and NFR-02, ADR-0007 task statements) |
| As-built UML diagrams (PlantUML source + PNG + SVG) | `docs/uml/a3/` |
| Test suites | `backend/tests/test_units.py`, `test_api.py`, `test_performance.py` |
| Test transcripts | `docs/test-results/*-v2.txt` |
| Interface screenshots | `docs/screenshots/v2/` |
| Developer guide | `docs/dev-guide.md` |

---

# Question 2 — Requirements and traceability [8]

## 2.1 Final prioritised requirements (3)

**Functional requirements**

| ID | Priority | Requirement | Acceptance criterion |
|---|---|---|---|
| FR-01 | Must | The system shall allow a user to create a profile as an enrolled student or a school-leaver. | Given a visitor on step 1, when they choose a type and continue, then a profile of that type is created and an identifier returned. |
| FR-02 | Must | The system shall allow a user to record which of the 35 O\*NET skills they hold. | Given a new profile, when the user submits any subset of the 35 skills, then exactly those skills are stored. |
| FR-03 | Must | The system shall allow a user to select one target occupation from the 879 in the catalogue, replacing any earlier target. | Given a profile, when a target is chosen, then its SOC code is recorded; when a second is chosen, it replaces the first. |
| FR-04 | Should | The system shall allow a user to search occupations by title. | Given a term of two or more characters, then every occupation whose title contains it is returned, or an explicit no-match message. |
| FR-05 | Must | The system shall filter occupations by Job Zone and show that zone's preparation description. | Given Job Zone 3, then only its 209 occupations are listed, with the zone's education description. |
| FR-06 | Must | The system shall rank occupations by mean-centred cosine similarity to the user's skills and show the top five with scores. | Given a profile with at least one skill, then five occupations are returned in descending score order, each with its score. |
| FR-07 | Must | The system shall list each skill the target requires that the user lacks, classified essential or desirable. | Given a profile and target, then every missing skill is listed, essential where its importance is 3.5 or above, desirable below. |
| FR-08 | Must | The system shall generate a pathway of at least three intermediate occupations to the target, each step listing the skills that matter most in that role, marked as new to the user or as needing more depth than the previous step. | Given a profile and target, then at least three intermediate steps and the target are shown, every step names at least one skill, and each skill is marked new, deeper or neither. |
| FR-09 | Should | The system shall show the source dataset and publication date for occupation and skill records. | Given any gap or pathway screen, then the dataset name is visible and every missing skill carries its rating date. |
| FR-10 | Must | The system shall rebuild its database from the O\*NET files on demand and abort if a file's row count differs from O\*NET's published count. | Given intact files, then 879 occupations, 35 skills and 27,463 ratings are built; given a short file, the load aborts naming it. |

**Non-functional requirements (FURPS+)**

| ID | Category | Priority | Requirement | Acceptance criterion |
|---|---|---|---|---|
| NFR-01 | Performance | Must | Every screen on the demo path responds within 2 seconds. | 95% of requests complete in under 2,000 ms. |
| NFR-02 | Usability | Must | A first-time user reaches a pathway in five screens or fewer, without instructions. | An unassisted first-time user reaches step 5 in five screens. |
| NFR-03 | Reliability | Must | The service refuses to start when its database is missing or empty. | Given no reference data, startup exits non-zero with a named error. |
| NFR-04 | Supportability | Should | The database can be rebuilt with one command in under 60 seconds. | Measured rebuild time is 60 seconds or less. |

The three emerging-technology requirements, TR-01 to TR-03, are covered in 2.3.

## 2.2 Requirements traceability matrix (3)

| Requirement | UML reference | Module | Test case | Status |
|---|---|---|---|---|
| FR-01 | UC-01; class Profile | `app.py` POST /profiles; `repository.create_profile` | TC-I02a | Pass |
| FR-02 | UC-02; class Skill | `app.py` GET /skills; `frontend/app.js` StepSkills | TC-I01a, TC-I02a | Pass |
| FR-03 | UC-03; activity "Record target" | `app.py` PUT /profiles/{id}/target; `repository.set_target` | TC-I02b–e | Pass |
| FR-04 | UC-04, UC-11 | `app.py` GET /occupations?q=, GET /occupations/{soc}; `repository.list_occupations` | TC-I01c, TC-I06a–f | Pass |
| FR-05 | UC-05; class JobZone | `app.py` GET /occupations?zone= | TC-I01b | Pass |
| FR-06 | UC-06; class RecommendationEngine; sequence 16–21 | `recommend.py`; GET /recommendations | TC-U02a–d, TC-U06e, TC-I05a, TC-I05c | Pass |
| FR-07 | UC-07; classes GapAnalyser, SkillsGap, PlainLabels | `gap.py`, `plain.py`; GET /profiles/{id}/gap | TC-U01a–c, TC-U06a–b, TC-I03a–d | Pass |
| FR-08 | UC-08; sequence diagram; classes Pathway, PathwayStep, SkillFocus (Fig. 3a) | `pathway.py`; GET /profiles/{id}/pathway | TC-U03a–b, TC-I04a–d, TC-I07d, TC-S01b | Pass |
| FR-09 | UC-09; ERD `source_dataset`, `source_date` | every catalogue response; interface provenance lines | TC-I03e, TC-I06c | Pass |
| FR-10 | UC-10; deployment diagram; ERD | `load_onet.py` | TC-U04a, TC-U08a, PT-04 | Pass |
| ADR-0005 progress tracking *(not yet an FR)* | UC-12, UC-13; class UserSkill, Readiness; activity partition *My plan* | `app.py` GET /profiles/{id}, PUT and DELETE /profiles/{id}/skills/{element_id}; `repository.set_skill_status`; `pathway.step_readiness` | TC-I07a–h, TC-U07a–b | Pass |
| NFR-01 | Deployment diagram | `app.py`, connection per request | PT-03, TC-I05b, TC-N01a | Pass |
| NFR-02 | Activity diagram | `frontend/app.js` | Developer walkthrough (Figures 11–19) | **Partial** — five screens to the pathway confirmed, with the dashboard after them (ADR-0006); unassisted user test not yet run |
| NFR-03 | Activity diagram, exception path | `app.py` startup check | TC-U05a–b | Pass |
| NFR-04 | Deployment diagram | `load_onet.py` | PT-04 | Pass |
| TR-01 | Class RecommendationEngine | `recommend.py` | PT-01 | Pass |
| TR-02 | Sequence 16–21 | `recommend.py` | PT-02 | Pass |
| TR-03 | Activity diagram; class RecommendationEngine | `recommend.py`, `app.py` | TC-U02d, TC-I05d | Pass |

Sixteen of seventeen requirements pass their tests. NFR-02 is partial for the
reason stated in 5.1. The ADR-0005 row traces a feature rather than a requirement.
Progress tracking (UC-13) was added after the requirements were baselined. Its
behaviour is fixed by ADR-0005 and verified by ten tests, but it has not yet
been written as a functional requirement. Doing so is the first item of
future work.

## 2.3 How the emerging-technology requirements are satisfied (2)

The engine represents each of the 879 occupations as a vector of its 35 O\*NET
importance ratings, and the user as a vector of 1s for skills held and 0s
otherwise. Both are **mean-centred** — each skill's average across all
occupations is subtracted — before cosine similarity ranks the catalogue.
Centring matters: raw vectors are near-identical (mean cosine to the nearest
other occupation is 0.994) because O\*NET's skills are generic, and centring
expresses each occupation by how it *differs* from the average one.

**TR-01 — accuracy, target ≥ 55%. Passed: 59.7%.** Over 124 test profiles built
from real occupations' essential skills, at least one of the top five
recommendations shares the occupation's SOC major group 59.7% of the time. The
matching random baseline, from 248,000 random draws, is 25.8% — a 2.3× lift. On
the stricter mean-share measure the engine scores 30.6% against 5.9% random, a
5.2× lift. *Correction:* Assignment 2 compared 59.7% against 6.9%, which is a
mean-share baseline, not the any-of-five baseline; the comparison above is the
correct one.

**TR-02 — latency, target ≤ 100 ms at p95. Passed: 4.7 ms.** Ranking all 879
occupations takes a median 3.6 ms and a 95th percentile of 4.7 ms, on the
standard library alone, with no GPU.

**TR-03 — determinism and robustness. Passed.** A profile with skills always
gets exactly five scored results; the test sample is seeded, so results repeat
exactly. A profile with no skills gets an empty list and an explanatory message
rather than an arbitrary ranking (TC-U02d, TC-I05d).

**How the user sees it.** Each recommendation shows a plain label (*Strong
match*, *Good match* or *Some overlap*) beside its score to two decimal places,
so FR-06's score stays visible. The label cut-points, 0.55 and 0.40, were
measured rather than chosen. Over 300 random 3–12 skill profiles, the top
score has a median of 0.44 and a 90th percentile of 0.56.

---

# Question 3 — Design as implemented [16]

All eight diagrams were authored in PlantUML and drawn against the code, not the
Assignment 2 design. They were redrawn at version 1.1 to include the occupation
panel, the dashboard and progress tracking. Names are consistent across diagrams and match the module
names in the code.

## 3.1 System architecture (2)

*Figure 1.* One FastAPI process serves the interface and the API. Requests pass
from the **SAYCEP API** to three services — **Gap Analyser**, **Pathway Service**
and the **Recommendation Engine** (the emerging-technology component, shaded) —
which read through the **Occupation Repository** from SQLite. **Plain Labels**
attaches a word to every figure the API returns. The browser keeps only one
thing: the saved plan's profile identifier, in `localStorage`. The **O\*NET
Loader** rebuilds the database from files downloaded once from Kaggle.

*Design decision.* No external API is called at request time: every figure the
user sees comes from the local database. This is what makes the 45 ms response
time possible and lets the demonstration run without internet.

*Design decision.* The server decides what a number means and the interface
only displays it. For example, the server decides that 4.0 is "Critical for
this job" and that 3.5 is where must-haves start. This keeps the essential
threshold in one place, and it means an interface label can never disagree
with the classification FR-07 is tested against (TC-U06a–b).

## 3.2 Use-case diagram and detailed description (3)

*Figure 2.* **Changes from Assignment 2:** search, browse and recommendations
are open to both profile types as tabs on one screen, and the profile type only
decides which tab opens first. UC-04, UC-05 and UC-06 therefore *extend* UC-03
rather than belonging to one actor each.

Three use cases were added at version 1.1:
- **UC-11 View Occupation Detail** extends target selection and the pathway.
- **UC-12 Save and View My Plan** includes the gap and the pathway, because the
  dashboard is built from both.
- **UC-13 Track Skill Progress** extends UC-12 and is described in full below
  UC-07.

**UC-07 Analyse Skills Gap**

| | |
|---|---|
| Primary actor | Youth User (Enrolled Student or School-Leaver) |
| Supporting actor | O\*NET Dataset, via `saycep.db` |
| Requirements | FR-07, FR-09 |
| Preconditions | A profile exists (UC-01) with its skills captured (UC-02) and a target recorded (UC-03) |
| Trigger | The user taps *See what's missing* on step 3 |
| Postcondition | The gap is displayed. Nothing is stored — the gap is computed per request |

*Normal flow*

1. The interface sends `GET /profiles/{id}/gap`.
2. The API confirms the profile exists.
3. The API resolves the target — from the request, or the one recorded on the profile.
4. The API confirms the target is in the catalogue.
5. The Gap Analyser reads the skills the user holds and the target's required skills with their importance ratings.
6. Each required skill the user lacks is classified essential (importance ≥ 3.5) or desirable (< 3.5).
7. The missing skills are returned ordered by importance, each with its rating date.
8. The interface shows the held, essential and desirable counts, an importance bar per skill, and the data source.

*Alternative flows*

- **A1 — at step 2, the profile does not exist:** the API returns 404 *No profile*; the interface shows an error banner and stays on the screen.
- **A2 — at step 3, no target is recorded:** 400 *No target occupation*; error banner.
- **A3 — at step 4, the target is not in the catalogue:** 404; error banner.
- **A4 — at step 6, nothing is missing:** the API returns an empty list with the message *"You already hold every skill this occupation requires"*; the interface shows that message and suggests a higher preparation level instead of an empty list.
- **A5 — the user returns to choose another target:** UC-03 records the new target, replacing the old one, and UC-07 runs again from step 1.

**UC-13 Track Skill Progress**

| | |
|---|---|
| Primary actor | Youth User |
| Requirements | ADR-0005 (not yet a functional requirement; see 2.2) |
| Preconditions | A plan has been saved (UC-12): the profile has a target, and its identifier is stored in the browser |
| Trigger | The user taps *Start learning* or *I can do this now* on a skill in the dashboard's *Skills to work on* list |
| Postcondition | The skill's status is stored. If it is now held, the gap, pathway and readiness shown are recalculated |

*Normal flow*

1. The dashboard lists the target's missing skills, must-haves first, each with *Start learning* and *I can already*.
2. The user taps *Start learning* on Troubleshooting.
3. The interface sends `PUT /profiles/{id}/skills/2.B.3.k` with status `learning`.
4. The API confirms the profile and the skill exist, and stores the status.
5. The dashboard refreshes. Troubleshooting moves to *Working on now*. Readiness stays at 0 of 2, because a skill being learned does not close the gap.
6. Later, the user taps *I can do this now*. The status becomes `held`.
7. The API's next gap, pathway and profile reads count Troubleshooting as held.
8. Readiness moves to 1 of 2. The route recalculates, and each step the user now has every must-have for is ticked.

*Alternative flows*

- **A1 — at step 2, the user can already do it:** *I can already* stores `held` directly, and the flow continues at step 7.
- **A2 — the user changes their mind:** *Stop* on a learning skill, or the undo control on a held one, sends `DELETE`. The skill returns to the list, and a held skill's gap reopens.
- **A3 — at step 4, an unknown status is sent:** 422, and nothing is stored.
- **A4 — at step 4, the profile no longer exists (the database was rebuilt):** 404. On the next visit the app forgets the stored identifier and starts the journey fresh.
- **A5 — at step 8, every must-have is held:** the dashboard says so, and points to the remaining nice-to-haves or a higher target.

## 3.3 Class diagram (3)

*Figures 3a and 3b.* Split in two so each stays readable: part A is the
domain model — **persisted** classes (the database tables) and results
**computed per request** — and part B the **services** (the backend modules)
with their operations. **Changes from Assignment 2:** the profile
type is a column with a check constraint rather than two subclasses, because
both types store identical data; each PathwayStep carries up to six
**SkillFocus** items badged new or deeper; and a Pathway has exactly four steps —
three intermediate plus the target — which all 879 occupations were verified to
support.

**Version 1.1 additions:**
- **UserSkill** becomes a class of its own with a *status*, because a held
  skill and one being learned behave differently.
- **OccupationTask** holds O\*NET's task statements.
- **Readiness** is computed per request and never stored.
- Each **PathwayStep** knows whether the user is *ready* for it.
- **PlainLabels** is the service that turns figures into words.

## 3.4 Sequence diagram (3)

*Figure 4.* UC-08 Generate Career Pathway, across the interface (boundary), API
and Pathway Service (control), the Recommendation Engine (emerging technology),
the repository (entity) and the database. **Correction from Assignment 2:** the
earlier diagram showed the Pathway Service calling the Gap Analyser; the
implementation does not. It reads the repository directly and asks the
Recommendation Engine to rank the target's related occupations by similarity to
the user, keeping the three closest. Both error branches — no profile (404) and
no target (400) — are shown. At version 1.1 the service also checks, for each
step, whether the user already holds every essential skill it needs (message
26). That is what lets the dashboard tick steps off. Message 11 now reads held
skills only, so a skill being learned never shortens a route.

## 3.5 Activity diagram (2)

*Figures 5a and 5b.* The full journey, split in two so each part stays readable: part A is the five-screen journey and part B is the *My plan* dashboard. Together they show:
- **Decisions:** a saved plan on arrival, the profile type, whether to aim for
  an opened job, whether anything is missing, the next action, and the action
  taken on a skill.
- **Exceptions:** failed profile creation and an invalid target, each showing
  an error banner.
- **Completion states:** nothing missing, returning to choose another target,
  and the plan kept or its goal reached.

Each screen's Continue button stays disabled until its decision is made, which
the diagram shows as guarded loops. The *My plan* partition is the progress loop
of UC-13. A returning user with a saved plan enters it directly and skips the
journey.

## 3.6 Component and deployment diagrams (3)

*Figure 6 — components.* Frontend, backend and third-party packages, with the
REST interface as the only link between the interface and the backend. The
threshold of 3.5 lives in `config.py` alone. The Gap Analyser, Pathway Service,
Recommendation Engine and Plain Labels all read it.

*Figure 7 — deployment.* The demonstration runs on one Windows laptop: a uvicorn
process on port 8000 serving `backend/` and `frontend/`, the 8.2 MB SQLite file,
and the 97 MB of O\*NET source files. The internet is not needed at runtime —
Google Fonts are optional, and the CDN is only a fallback for the interface
libraries, which are bundled locally.

---

# Question 4 — Technical documentation [10]

## 4.1 Stack, structure and modules (3)

| Layer | Technology | Version |
|---|---|---|
| Interface | React with `htm` templates, no build step, bundled in `frontend/vendor/` | React 18.3.1, htm 3.1.1 |
| API | FastAPI on uvicorn | 0.141.1 / 0.52.4 |
| Language | Python | 3.10 or later; tested on 3.14.0 |
| Database | SQLite (Python standard library) | — |
| Dataset | O\*NET 29.0, via Kaggle, CC BY 4.0 | August 2024 release |

| Module | Lines | Responsibility |
|---|---|---|
| `backend/app.py` | 351 | Eleven REST endpoints; input validation; serves the interface; refuses to start without data |
| `backend/repository.py` | 206 | All SQL; the only module that reads or writes the database directly, apart from the engine's bulk vector load |
| `backend/gap.py` | 50 | Classifies missing skills as essential or desirable |
| `backend/pathway.py` | 171 | Chooses and orders the three intermediate steps; badges skills new or deeper; says whether the user is ready for each step |
| `backend/recommend.py` | 114 | The emerging-technology component — mean-centred cosine similarity |
| `backend/plain.py` | 80 | Plain-language labels for importance, match strength, preparation level and skill groups |
| `backend/load_onet.py` | 251 | Rebuilds the database from O\*NET files; verifies row counts |
| `backend/config.py` | 26 | The essential threshold and pathway length, defined once |
| `frontend/app.js` | 774 | The five-screen journey, the occupation panel and the *My plan* dashboard; computes nothing, displays API results |
| `backend/tests/` | 447 | 63 automated tests across unit, integration, system and performance levels |

*Figure 9 — the recommendation screen, where the emerging technology is visible
to the user as a match label and a similarity score.* *Figure 10 — the API's
generated documentation at /docs, listing all eleven endpoints.*

## 4.2 Database (3)

*Figure 8* is the entity-relationship diagram, read directly from the database's
schema. Solid lines are foreign keys declared in SQL; dashed lines are
references enforced by the API rather than the database.

**Data dictionary**

| Table.column | Type | Constraint | Meaning |
|---|---|---|---|
| occupations.soc_code | TEXT | PK | O\*NET-SOC code, e.g. 47-2111.00 |
| occupations.title | TEXT | NOT NULL | Occupation name |
| occupations.description | TEXT | | O\*NET description |
| occupations.job_zone | INTEGER | NOT NULL; references job_zone_reference.zone (logical) | Preparation level 1–5 |
| occupations.source_dataset | TEXT | NOT NULL | Provenance label (FR-09) |
| skills.element_id | TEXT | PK | O\*NET content-model ID, e.g. 2.B.3.k |
| skills.name | TEXT | NOT NULL | Skill name |
| skills.description | TEXT | | O\*NET definition, shown when the skill is tapped |
| skills.source_dataset | TEXT | NOT NULL | Provenance label |
| occupation_skills.soc_code | TEXT | PK, FK → occupations | |
| occupation_skills.element_id | TEXT | PK, FK → skills | |
| occupation_skills.importance | REAL | NOT NULL | O\*NET importance rating, 1–5 |
| occupation_skills.importance_scale_max | REAL | NOT NULL | Scale ceiling (5), stored so the interface never hard-codes it |
| occupation_skills.source_date | TEXT | | Date O\*NET collected the rating, e.g. 08/2022 |
| related_occupations.soc_code | TEXT | PK, FK → occupations | |
| related_occupations.related_soc_code | TEXT | PK | Related occupation; not a foreign key because 6.8% point outside the usable catalogue and are filtered at query time |
| related_occupations.tier | TEXT | NOT NULL | Primary-Short, Primary-Long or Supplemental |
| related_occupations.sort_index | INTEGER | NOT NULL | O\*NET's expert-review order |
| job_zone_reference.zone | INTEGER | PK | 1–5 |
| job_zone_reference.name, experience, education, training, examples, svp_range | TEXT | name NOT NULL | Zone descriptions; the original O\*NET text travels with the plain-language label |
| occupation_tasks.soc_code | TEXT | PK, FK → occupations | |
| occupation_tasks.task_id | INTEGER | PK | O\*NET task identifier |
| occupation_tasks.task | TEXT | NOT NULL | One thing a person in the job does, in O\*NET's words |
| occupation_tasks.task_type | TEXT | | Core or Supplemental; null where O\*NET gives neither |
| occupation_tasks.importance | REAL | | O\*NET task importance, 1–5, used only for ordering; null for the 298 tasks without a usable rating |
| occupation_tasks.source_date | TEXT | | Date O\*NET collected the statement |
| users.profile_id | TEXT | PK | Random 12-character hex identifier |
| users.profile_type | TEXT | NOT NULL; CHECK in (student, school_leaver) | |
| users.target_soc_code | TEXT | references occupations (validated by the API) | The chosen target |
| users.created_at | TEXT | NOT NULL, default now | |
| user_skills.profile_id | TEXT | PK, FK → users ON DELETE CASCADE | |
| user_skills.element_id | TEXT | PK; references skills (validated by the API) | A skill the user holds or is learning |
| user_skills.status | TEXT | NOT NULL, default `held`; CHECK in (held, learning) | Only `held` is read by the gap, pathway and recommendations (ADR-0005) |
| user_skills.updated_at | TEXT | NOT NULL, default now | When the status last changed |

**Validation rules.** At load: each O\*NET file's row count must equal O\*NET's
published count or the load aborts; ratings O\*NET flags *Not Relevant* are excluded
(3,302 ratings; none were flagged *Recommend Suppress*); occupations missing skills, a job
zone or related occupations are excluded (137 of 1,016). Task ratings O\*NET
marks *Recommend Suppress* are not used for ordering. At request: profile type
must match the check constraint; every skill ID must exist; every SOC code must
exist; zone must be 1–5; search terms need two characters; a skill status must
be `held` or `learning`. All SQL is parameterised.

**Upgrading a database in place.** A database built before version 1.1 has no
`status` column. The API adds it at startup, and existing rows default to
`held`, so no user's gap changes on upgrade (TC-U07a–b).

**Privacy controls.** The system collects no personal information — no name,
email, age, location or contact detail. A profile is a random identifier, a set
of skills and a target. With nothing identifying a person, there is nothing to
protect, disclose or lose, which is why the design needs no login. The saved
plan stores only that random identifier in the browser's `localStorage`. It
identifies a browser, not a person, and clearing the browser's data removes it.

**Backup approach.** The reference data is not backed up because it does not
need to be: it is rebuilt from the source files in 1.74 seconds (PT-04), and the
source files can be downloaded again from Kaggle. The code and documentation are
backed up in a private GitHub repository. Profiles are deliberately not backed
up. They hold nothing identifying, and a rebuild clears them, which 5.4 lists
as a limitation of the saved plan.

## 4.3 API (2)

Base URL `http://127.0.0.1:8000`. All responses are JSON. **Authentication:**
none, by design — no endpoint reads or returns personal data (4.2). Errors return
`{"detail": "..."}` with the status below; the interface shows the detail in an
error banner.

| Method and path | Input | Output | Validation and errors |
|---|---|---|---|
| GET /skills | — | All 35 skills, each with its plain-language group | — |
| GET /occupations | `zone` 1–5, `q` search, `limit` 1–1000 | Matching occupations with preparation label, total, zone description | 422 if zone is out of range or `q` is under two characters |
| GET /occupations/{soc} | SOC code, optional `profile_id` | Occupation, preparation, top 8 task statements, required skills classified; with a profile, which skills it holds | 404 if not in the catalogue, or for an unknown profile |
| POST /profiles | `profile_type`, `skills[]`, optional `target_soc_code` | `profile_id`, skills captured | 422 for an invalid type or unknown skill ID; 404 for an unknown target |
| GET /profiles/{id} | — | Profile type, target, skills with status, readiness counts | 404 unknown profile |
| PUT /profiles/{id}/skills/{element_id} | `status`: `held` or `learning` | Profile, skill and new status | 422 invalid status; 404 unknown profile or skill |
| DELETE /profiles/{id}/skills/{element_id} | — | Profile and skill, status now null | 404 unknown profile |
| PUT /profiles/{id}/target | `soc_code` | Profile ID and new target | 404 for an unknown profile or SOC code |
| GET /profiles/{id}/gap | optional `soc_code` | Classified missing skills with plain labels, counts, threshold, message | 404 unknown profile; 400 no target; 404 unknown SOC |
| GET /profiles/{id}/pathway | optional `soc_code` | Four steps, each with badged skills and whether the user is ready for it | As for the gap |
| GET /recommendations | `profile_id`, `limit` 1–20, `max_job_zone` 1–5 | Ranked occupations with score, match label and zone | 422 if `profile_id` is missing; 404 unknown profile; empty list and message for an empty profile |

Every status in this table was checked against the running API.

## 4.4 Installation, configuration and deployment (2)

**Software:** Python 3.10 or later, a modern browser. **Hardware:** minimum a
dual-core 2 GHz processor, 4 GB RAM and 500 MB free disk; recommended quad-core,
8 GB RAM, SSD. No GPU. Internet is needed once, for the dataset.

1. Clone the repository and install the two packages:
   `pip install -r requirements.txt`
2. Download the O\*NET 29.0 Database from Kaggle
   (`emarkhauser/onet-29-0-database`, login required) and unzip the `.txt` files
   into `backend/data/onet/`.
3. Build the database: `python backend/load_onet.py` — prints 879 occupations,
   35 skills, 27,463 ratings and 17,931 tasks.
4. Start the service from the repository root:
   `python -m uvicorn app:app --app-dir backend --port 8000`
5. Open `http://127.0.0.1:8000`. Add `?presenter` to show each screen's
   requirement IDs and the raw figures behind every label.

**Configuration** lives in `backend/config.py`: the essential threshold (3.5)
and the number of intermediate pathway steps (3). The plain-language cut-points
are in `backend/plain.py`. The port is set on the command line.

**Verification:** with the service running,
`python backend/tests/test_api.py` should report 39 passed.

---

# Question 5 — Evaluation and responsible use [10]

## 5.1 Test summary (4)

63 automated tests, all passing on 30 September 2026 (version 1.1).
Transcripts: `docs/test-results/*-v2.txt`. Version 1.0 had 41 tests. The 22 new
ones cover the plain-language labels, the occupation panel, the task
statements, progress tracking and the in-place database upgrade.

| Level | Tests | Result |
|---|---|---|
| Unit — functions tested directly, no server | 20 | 20 pass |
| Integration — each endpoint over HTTP, plus concurrency | 37 | 37 pass |
| System — the whole demo journey end to end | 2 | 2 pass |
| Performance — requirement targets measured | 4 | 4 pass |
| Browser — the demo script driven in Chromium, screenshot per screen | 1 walkthrough | No console errors (Figures 11–19) |
| User acceptance | — | Partial — see below |

**Representative tests**

| Test | Expected | Actual | Status |
|---|---|---|---|
| TC-U01a — Troubleshooting (4.00) for Electricians | Classified essential | Essential | Pass |
| TC-U02d — recommend with no skills | Empty result, no error | Empty list | Pass |
| TC-U05a — start the API with no reference data | Exits non-zero | Exit code 1, message names `load_onet.py` | Pass |
| TC-I02c — set a second target | Replaces the first | Gap now reports Carpenters | Pass |
| TC-I02d — target an unknown SOC code | 404 | 404 | Pass |
| TC-I03b–d — demo profile against Electricians | 6 held, 2 essential, 26 desirable | 6, 2, 26 | Pass |
| TC-I04b — pathway length | ≥ 3 intermediate steps | 3 | Pass |
| TC-N01a — 20 concurrent requests | All succeed | 20 of 20 | Pass |
| TC-S01a–b — full demo journey on a fresh profile | Reproduces 6/2/26 and a 3-step route to Electricians | Reproduced | Pass |
| TC-U06a — label for any essential importance | "Very important" or "Critical", never lower | As expected at 3.5, 3.75, 4.0, 5.0 | Pass |
| TC-I07b — mark Troubleshooting *working on it* | Recorded, gap unchanged at 2 must-haves | Learning 1, missing 2 | Pass |
| TC-I07c — mark it *I can do this now* | Gap falls to 1, readiness 1 of 2 | 1 and 1 | Pass |
| TC-U07b — open a pre-1.1 database | Existing skills count as held | Held | Pass |

**Two defects found by testing.**

*The first was found by the automated tests.* The first integration run after a database rebuild
failed: every profile request returned HTTP 500. The loader deleted the database
file and recreated only the reference tables, while the API created the profile
tables once at startup — so rebuilding the data under a running server broke
profiles until a restart. The loader now creates the empty profile tables too.
The failing scenario was re-run — rebuild under the live server, no restart —
and all tests pass.

*The second was found by reviewing the build against its requirements.* The
plain-language change first hid the recommendation scores behind presenter
mode, which fails FR-06's criterion "each with its score". The scores were
restored beside the labels before release.

**User acceptance testing.** Assignment 2 planned four participants, two per
profile, reaching a pathway unassisted. That has not yet been run. What has been
done is a developer walkthrough against the same script, recorded in Figures
11–19, confirming the journey to a pathway takes exactly five screens. NFR-02 is
therefore reported as partial: the five-screen structure is verified, but that a
first-time user completes it without help is not yet. The walkthrough itself
changed the design. It is what showed that the screens spoke in figures a
school-leaver could not read (change 4 in 1.2).

## 5.2 Quantitative evaluation (2)

| Requirement | Measure | Target | Result | Margin |
|---|---|---|---|---|
| NFR-01 Performance | HTTP response time, 60 requests across all demo endpoints (PT-03) | 95% under 2,000 ms | p95 45 ms, max 71 ms | 44× under target |
| NFR-04 Supportability | Full database rebuild, now including 158,751 task ratings (PT-04) | ≤ 60 s | 1.74 s | ~34× under target |
| TR-01 Recommendation accuracy | Same family in top 5, 124 profiles (PT-01) | ≥ 55% | 59.7% vs 25.8% random | Passes by 4.7 points; 2.3× random |
| TR-02 Inference latency | Rank 879 occupations (PT-02) | p95 ≤ 100 ms | p95 4.7 ms | 21× under target |

The two performance NFRs pass by wide margins because the design avoids network
calls and keeps the data local. Loading the task statements roughly tripled the
rebuild time, from 0.62 s to 1.74 s. That's still well inside the target. TR-01 is the tightest result: it passes, but by
4.7 points. The engine is clearly better than chance — 2.3× on this measure, 5.2×
on mean share — but not by as much as Assignment 2 suggested. That is the
honest reading, and it points to the first improvement in 5.4.

## 5.3 User guide (2)

**Starting SAYCEP.** With the service running (4.4), open
`http://127.0.0.1:8000` in a browser. The bar at the top shows your progress
through five steps, and the back arrow returns to the previous one. If you've
saved a plan in this browser before, SAYCEP opens straight onto it.

**1. Where are you starting from?** *(Figure 11)* Choose *I'm studying* or *I
left school*. Continue stays greyed out until you choose.

**2. What can you already do?** *(Figure 12)* The skills are grouped under
headings such as *Working with people*. Tap every skill that's genuinely
true of you, and it turns dark blue. The box at the bottom explains the last
skill you tapped. Type in the search box to narrow the list, for example
"fix" or "numbers".

**3. Pick something to aim for.** *(Figures 9, 13 and 14)* There are three tabs:
- *For you* ranks jobs by how closely your skills match. Each shows a label
  (*Strong match*, *Good match*, *Some overlap*) and a score, where 1.00
  would be identical.
- *Browse* groups jobs by how much training they take to start: none,
  matric, trade, degree or postgrad.
- *Search* finds a job by name.

Tap a job to open its panel. It shows what the job is, *A day in this job*,
the training it usually needs, and which of its skills you already have.
Tap **Aim for this job** to make it your target.

**4. What's missing?** *(Figure 15)* One sentence tells you how many of the
job's skills you have and how many must-haves you still need. *Must-haves*
come first, in amber, each with a short explanation. *Nice to have* skills
follow. Tap *How do we decide what's a must-have?* for the rule.

**5. How do you get there?** *(Figure 16)* Three related jobs lead to your
goal, the closest to you first. *New to you* means you don't have that
skill yet. *Use it more* means you have it, but this job needs more of it.
Tap a job's name to open its panel. **Save as my plan** opens your
dashboard. *Try a different target* returns to step 3.

**6. My plan.** *(Figures 17–19)* Your goal and a bar showing how many
must-have skills you hold, then your route with each step ticked once
you're ready for it, and your next step.
- Under *Skills to work on*, tap **Start learning** for a skill you're
  working on. That doesn't change your bar, because learning a skill isn't
  the same as having it.
- Tap **I can do this now** once you can. The bar moves and the route
  updates.
- Changed your mind? *Stop*, or the undo arrow under *Skills you have*,
  reverses it.
- *Change my goal* and *Update my skills* take you back into the journey
  without losing your plan.

**Troubleshooting**

| Problem | Cause and fix |
|---|---|
| The service stops at once with *saycep.db is missing or empty* | The database has not been built. Run `python backend/load_onet.py`. |
| *Address already in use* when starting | Another program holds port 8000. Close it, or start with `--port 8001` and open that port. |
| The page says it could not load its interface libraries | A file is missing from `frontend/vendor/`. Restore it from the repository. |
| A red banner appears on a step | The service stopped or was restarted. Check the terminal, restart it, and reload the page. |
| The page shows an older version after an update | The browser cached it. Reload with Ctrl+F5. |
| Continue stays greyed out | That step needs a choice first — a starting point, at least one skill, or a target. |
| The app starts at step 1 although I saved a plan | The plan is kept in this browser only. A different browser, a private window or cleared site data won't have it. Rebuilding the database also clears saved plans. |
| *Couldn't save that* appears on the dashboard | The service was restarted with a rebuilt database. Reload the page and walk the journey again. |

## 5.4 Limitations, risks, ethics, maintenance and improvements (2)

**Limitations.**
- **United States data.** O\*NET describes the US labour market. The South
  African framing lives in the problem statement; the data has no SA
  qualifications, wages, or TVET and SETA programmes.
- **Coarse skills.** Skills are self-assessed as held or not held, with no level,
  across only 35 generic skills — the reason TR-01 passes by 4.7 points rather
  than a wide margin.
- **Pathway steps are occupations, not training.** The route names roles to work
  through, not the courses that lead to them.
- **Plans live in one browser.** There are no accounts, so a saved plan exists
  only in the browser that saved it, and a database rebuild clears it.
- **Progress is self-reported.** SAYCEP cannot check that someone can now
  troubleshoot. Marking a skill held rests on the same trust as the original
  skill capture (FR-02, ADR-0005).
- **The route moves.** FR-08 orders steps by closeness to the user's current
  skills, so the dashboard's route re-sequences as skills are added. The
  screen says so. Freezing it at save time would need a stored route, and it
  is deferred.
- **Single process, single file.** SQLite on one machine suits a demonstration,
  not many concurrent users in production.

**Unresolved risks.** User acceptance testing has not been run (5.1). Progress
tracking has no functional requirement yet (2.2). A new
O\*NET release will change row counts and the loader will refuse it — deliberate,
but it needs the expected counts updated by hand.

**Ethical concerns and the mitigations built in response.**
- **A similarity score can read as advice about what a young person should
  do.** It could steer someone away from a career they would suit. Mitigation:
  recommendations are one tab of three and are presented as options with the
  reasoning visible. Search and browse carry equal weight.
- **US occupational structures may mislead where South African licensing and
  pay differ.** Mitigation: provenance is shown on every screen. The
  preparation labels translate O\*NET's US education terms (for example,
  "matric" for "high school diploma"), and the original text still travels
  with every response.
- **Labelling a skill "essential" may discourage rather than motivate.**
  Version 1.0 named this risk. Version 1.1 acts on it: the interface says
  *must-have* and *nice to have* ("you can start without them"), leads with
  what the user already has ("You already have 6 of the 34 skills"), and
  counts progress in skills gained rather than skills lacking.
- **Gamification was considered and deliberately rejected.** Streaks, points,
  badges and leaderboards all push engagement. The school-leaver profile is
  making a high-stakes decision in an age group with 60.9% unemployment, and
  a mechanic that rewards returning to the app isn't the same as one that
  helps someone reach a job. Progress is counted only toward the user's own
  goal.
- **No personal data is collected.**

Before real use, the scoring and the wording should be reviewed with career
counsellors.

**Security.** There is no login because no personal data is held. Profile IDs
are random 48-bit values, so they cannot practically be guessed. Since version
1.1 an identifier can also *change* a plan's skills. The random identifier is
therefore the only thing protecting a plan, which is acceptable while a plan
holds nothing personal but should be revisited before public use. Input is
validated and all SQL is parameterised. There is no rate limiting — acceptable
on a laptop, but needed before public deployment.

**Maintenance.** Annually, update to the new O\*NET release and its expected row
counts in `load_onet.py`, then rerun the three test suites. The threshold and
pathway length are single values in `config.py`. The bundled interface libraries
should be updated for security fixes.

**Two realistic improvements.**
1. **Richer skill vectors.** O\*NET's Knowledge (33 elements), Abilities (52) and
   Work Activities (41) files are already downloaded and share the same
   structure. Adding them extends each vector from 35 to 161 dimensions with no
   new data source and no algorithm change — the most direct way to raise TR-01
   above its narrow margin.
2. **South African localisation.** Map O\*NET-SOC codes to South Africa's
   Organising Framework for Occupations (OFO) and link pathway steps to TVET and
   SETA programmes, so a route ends in a named institution. This needs
   non-Kaggle data, so it requires the lecturer's approval first.

---

## Figures

| Figure | Content | File |
|---|---|---|
| 1 | System architecture | `docs/uml/a3/01-architecture.png` |
| 2 | Use-case diagram | `docs/uml/a3/02-use-case.png` |
| 3a | Class diagram, domain model | `docs/uml/a3/03a-class-domain.png` |
| 3b | Class diagram, services | `docs/uml/a3/03b-class-services.png` |
| 4 | Sequence diagram, UC-08 | `docs/uml/a3/04-sequence.png` |
| 5a | Activity diagram, the journey | `docs/uml/a3/05-activity.png` |
| 5b | Activity diagram, My plan dashboard | `docs/uml/a3/05b-activity-plan.png` |
| 6 | Component diagram | `docs/uml/a3/06-component.png` |
| 7 | Deployment diagram | `docs/uml/a3/07-deployment.png` |
| 8 | Entity-relationship diagram | `docs/uml/a3/08-erd.png` |
| 9 | Recommendations — match label and score | `docs/screenshots/v2/03a-for-you.jpg` |
| 10 | API documentation at /docs, eleven endpoints | `docs/screenshots/v2/08-api-docs.jpg` |
| 11 | Step 1 — starting point | `docs/screenshots/v2/01-start.jpg` |
| 12 | Step 2 — skills, grouped and explained | `docs/screenshots/v2/02-skills.jpg` |
| 13 | Step 3 — browse by training needed | `docs/screenshots/v2/03b-browse.jpg` |
| 14 | Step 3 — the occupation panel | `docs/screenshots/v2/03c-job-panel.jpg` |
| 15 | Step 4 — the gap | `docs/screenshots/v2/04-gap.jpg` |
| 16 | Step 5 — the pathway | `docs/screenshots/v2/05-route.jpg` |
| 17 | My plan — readiness and route | `docs/screenshots/v2/06a-plan.jpg` |
| 18 | My plan — a skill being learned | `docs/screenshots/v2/06b-plan-learning.jpg` |
| 19 | My plan — after *I can do this now* | `docs/screenshots/v2/06c-plan-progress.jpg` |
