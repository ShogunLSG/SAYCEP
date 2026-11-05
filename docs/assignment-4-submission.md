# ISJ107V Assignment 4 — Functional Prototype and Presentation

> **Draft for you to read and adjust before submitting.** Every figure below comes
> from a test run on 24 October 2026, and each is reproducible from the repository
> (transcripts in `docs/test-results/*-2026-10-24.txt`). The declarations on the
> last numbered page are **yours to confirm**: check them against the module's
> rules before you sign. This note is not printed in the PDF.

---

# Question 1 — Prototype definition and readiness

## 1.1 Project, problem, users, purpose and emerging technology

| Item | Detail |
|---|---|
| Project title | SAYCEP — South African Youth Career and Employment Platform |
| Problem addressed | With unemployment rising in South Africa, I noticed while making my way through high school and tertiary education that there is very little guidance outside of the occasional career fair. Students get little help with a career path they have chosen, or with choosing one if they haven't yet decided. Young South Africans aged 15 to 24 are almost twice as likely to be unemployed as the average South African: 62.8% against 33.6% in Q2 2026 (Statistics South Africa, Quarterly Labour Force Survey, 11 August 2026). Research that followed the same young South Africans for ten years found that many "stagger from education into the labour market, disconnected from jobs or skills training", and that facilities giving access to information about jobs are often hard to reach (Branson, De Lannoy & Brynde, 2019). The longer young people stay unemployed, the harder it becomes to leave unemployment, a scarring effect (Ismail & Kollamparambil, 2015). Helping people early in their careers addresses the problem at its start, and I want to help bridge that gap. |
| Intended users | The *school-leaver*, who has left school with no qualification and is not sure what is open to them, and the *enrolled student*, who is studying and usually already has a direction. Both follow the same journey: they choose their starting point, then tick the skills they already have. After that, a school-leaver is shown recommendations first, limited to jobs that need less preparation. An enrolled student starts by searching for the role they are aiming at. High-school learners are a future extension. |
| Prototype purpose | My prototype lets a young person select the skills they believe they have, and then shows them a set of jobs that match those skills, so they can research what those jobs involve and consider pursuing them. Once they pick a job to aim for, it shows the skills they are missing and an ordered **Pathway** of jobs to get there. They can save that plan and track their progress as they learn the missing skills. |
| Emerging technology | Machine learning: content-based recommendation using **mean-centred cosine similarity**. Each of 879 O\*NET occupations is a list of importance ratings for 35 skills, and the user's ticked skills form a list over the same 35. Because nearly every job needs general skills such as reading and listening, the average occupation is subtracted first, so jobs are compared on what makes them different. The jobs whose lists point most in the same direction as the user's are recommended, with the skills that lifted each one shown as the reason. The model is not trained, because O\*NET provides ratings rather than hiring outcomes. No chatbot or large language model is used: every suggestion can be explained, nothing is invented outside the dataset, and it runs offline at no cost. |

## 1.2 Functional requirements demonstrated, and feature status

The prototype demonstrates ten functional requirements (FR-01 to FR-10), all implemented, plus features added since they were written.

| Requirement | Feature in the prototype | Status |
|---|---|---|
| FR-01 | Create a profile as an enrolled student or a school-leaver | Implemented |
| FR-02 | Record which of the 35 O\*NET skills the user holds | Implemented |
| FR-03 | Select one target occupation from 879 | Implemented |
| FR-04 | Search occupations, including by alternate titles ("conduit installer" finds Electricians) | Implemented |
| FR-05 | Browse by Job Zone, with the preparation level described | Implemented |
| FR-06 | Rank occupations by similarity and show why each was recommended | Implemented |
| FR-07 | Skills gap, split into essential and desirable | Implemented |
| FR-08 | A Pathway of three intermediate steps plus the target | Implemented |
| FR-09 | Source dataset and record dates shown with every record | Implemented |
| FR-10 | Rebuild the database from the O\*NET files, aborting on a wrong row count | Implemented |
| Added: progress, saved jobs and compare, interest quiz, plan-code sign-in, printable plan | Two-state skill progress, side-by-side comparison, a 12-question quiz, a six-character plan code | Implemented (requirements to be written as FR-11 onward) |
| Added: CV check | Skills a pasted CV shows, and a goal score | **Partially implemented:** pasted text only, rule-based |
| Added: interview practice | Questions for the goal job, and a checklist on each answer | **Partially implemented:** not a conversational chatbot |
| Added: what employers ask for | Real adverts linked to a job by title, summarised | **Partially implemented:** US adverts from April 2024, not openings to apply for |
| NFR-02 | A first-time user reaches a Pathway in five screens, unassisted | **Partially implemented:** the five-screen journey exists; no unassisted user test has been run |
| CV file upload, South African job data, saved plans that persist on a hosted copy, rate limiting | | **Deferred** |

## 1.3 Setup and access

| Item | Detail |
|---|---|
| Software | Python 3.10 or newer. `pip install -r requirements.txt` installs the only two packages: FastAPI 0.141.1 and uvicorn 0.52.4. A modern web browser. Node.js and Playwright are optional, for the test scripts only. |
| Hardware | An ordinary laptop. About 200 MB of disk (93 MB of source data and a 19 MB database). No internet is needed at run time. |
| Data | O\*NET 29.0 from Kaggle (`emarkhauser/onet-29-0-database`), unzipped into `backend/data/onet/`. The advert counts are committed in the repository (`backend/seed/`). |
| Build and run | `python backend/load_onet.py` builds the database in about 6 seconds. Then `python -m uvicorn app:app --app-dir backend --port 8000` and open http://127.0.0.1:8000 |
| Test credentials | None. There are no accounts. A plan code is issued when a plan is saved. |
| Sample data | The demonstration user *Thabo*: a school-leaver holding six skills (Operation and Control, Operations Monitoring, Equipment Maintenance, Active Listening, Critical Thinking, Monitoring) and aiming for Electricians. |
| Repository | https://github.com/ShogunLSG/SAYCEP, branch `main` |
| Optional live copy | A minimal Fly.io deployment, in the repository as `Dockerfile` and `fly.toml`, with a runbook in `docs/deploy.md`. Saved plans there reset when it is redeployed. |

# Question 2 — The working prototype

## 2.1 One complete end-to-end workflow

The workflow is *skills → recommendations → target → gap → Pathway → saved plan → progress*. It is a five-screen journey, then a saved dashboard (Appendix B, Figures B1–B6; activity diagram in Appendix A, Figure A2).

| Step | Input | Validation | Output | Error feedback |
|---|---|---|---|---|
| Welcome | A first name (optional), or a plan code | Sign-in is disabled until six characters are typed; a name over 40 characters is rejected | A new journey, or the saved plan | A wrong code: "No plan matches that code. Check it and try again." |
| 1. Starting point | Student or school-leaver | Continue is disabled until one is chosen; the server accepts only those two values | A profile type | Plain error banner |
| 2. Skills | Ticks on the 35 skills | At least one skill is needed; the server rejects unknown skill identifiers (422) | A profile with a plan code | Plain error banner |
| 3. Choose a target | A job found by recommendation, browsing or search | Unknown occupation codes return 404 | A recorded target | Plain error banner |
| 4. The gap | The target | None needed | Skills held, and the essential and desirable skills still missing | A target with every skill held gets a message, not an empty list |
| 5. The Pathway | The profile and the target | None needed | Three intermediate jobs plus the target, each saying why it is there | 404 or 400 if no profile or target |
| Dashboard | "Start learning" or "I can do this now" on a skill | Only the two statuses are accepted | Readiness (for example 1 of 2), what the change unlocked | Unknown skills return 404 |

The same dashboard links to the other modules: a CV check (a text that is too short or too long is refused), interview practice, and what employers ask for.

## 2.2 Emerging-technology integration

**Input.** The user's held skills become a 35-number vector. Invalid input is refused: unknown skill identifiers return 422, and an empty set returns an empty result with the message "Select at least one skill to receive recommendations" rather than an arbitrary ranking (TC-I05d).

**Processing.** Each of the 879 occupations is a vector of O\*NET importance ratings. Because almost every occupation rates most of the 35 skills highly, the raw vectors point nearly the same way (a job's nearest neighbour has cosine 0.994), so the model subtracts the average occupation from every vector and ranks by cosine similarity on what is left.

**Observable result used by the system.** The five highest-scoring occupations are returned with a similarity score, a plain match label and the held skills that lifted each one most ("Because you have: Operation and Control, Equipment Maintenance…"). The result is *used*: it decides which jobs the user can choose as a target, and the Pathway Service uses the same similarity to order the related occupations on the route, most achievable first.

**Measured.** Giving the engine only a job's must-have skills and asking whether any of its five recommendations is in the same occupational family, over all 713 occupations that have must-haves and with the job itself removed, it succeeds **58.5%** of the time (95% interval 54.6–62.1) against 25.9% by chance (PT-01b).

## 2.3 Data

All system data comes from Kaggle. The core is O\*NET 29.0 (August 2024 release): 879 usable occupations, 35 skills and 27,463 importance ratings, plus task statements, alternate titles, software and tools, and interest profiles. It is held in an SQLite database (`saycep.db`, 19 MB) that is rebuilt from the source files, never edited by hand. User data (profiles, skills, saved jobs and progress events) lives in the same database. The advert summaries come from a Kaggle dataset of 123,849 LinkedIn adverts (US, 2024): 26,472 are linked to an occupation by title, and only counts are stored.

## 2.4 Security and reliability

| Control | How it is met |
|---|---|
| Access control | There are no accounts. A plan is reached only with its six-character code, drawn at random from 31 unambiguous characters (about 887 million codes). The screen says the code is the only key. |
| Personal data | The only personal data is an optional first name and the skills a user ticks. **CV text and interview answers are processed and discarded, never stored** (the response says so, and TC-I18d shows scanning changes nothing). |
| Credentials and secrets | None in the code. No LLM or API key is used. A Kaggle token, if needed for downloading data, is held in an environment variable and never committed. |
| Safe error handling | Plain messages for 404 and 422, never a stack trace. Queries use bound parameters for user-supplied values. Input lengths are capped (CV 15,000 characters, interview answer 5,000, name 40). |
| Reliability | The service refuses to start if the database is missing or empty (NFR-03). Twenty concurrent requests all succeeded (TC-N01a). A cached build step keeps a rebuild at about 6 seconds. |
| Known gap | There is no rate limiting on plan-code guesses. It is the first item to add before any public deployment. |

**Evidence against the requirements** (recommended format):

| Requirement | Status | Prototype feature | Test case | Evidence |
|---|---|---|---|---|
| FR-03 | Completed | Select and replace a target | TC-I02b, c, d | Demo, 404 on unknown code |
| FR-06 | Completed | Ranked recommendations with reasons | TC-I05a, TC-I05d | 5 results; empty profile handled |
| FR-07 | Completed | Skills gap | TC-I03b, c, d | 6 held, 2 essential and 26 desirable missing |
| FR-08 | Completed | Pathway | TC-I04b, c, d | 3 steps plus the target |
| FR-09 | Completed | Source and date on records | TC-I03e, TC-I15 | Dates on every missing skill |
| ETR-01 | Completed | Emerging-technology engine | PT-01, PT-01b | 58.5% against 25.9% by chance |
| NFR-01 | Completed | Response time | PT-03 | 98 ms at p95 against a 2,000 ms limit |
| NFR-02 | Partial | Five-screen journey | none yet | Needs an unassisted user test |

# Question 3 — UML: structure and behaviour

All diagrams were drawn in PlantUML (a recognised UML tool) from the code as it is on 24 October. They are in **Appendix A** at full-page size so the labels stay legible.

## 3.1 Use-case diagram (Figure A1)

Actors are the Youth User (with the Enrolled Student and School-Leaver as specialisations), the Data Administrator, and the two Kaggle datasets that the loaders read. Nineteen use cases are shown; UC-14 to UC-19 are the plan-code sign-in, saved jobs and compare, the interest quiz, the CV check, interview practice and employer adverts, all added since Assignment 3. UC-06 *Recommend Occupations* is the emerging-technology function.

## 3.2 Activity diagram (Figure A2)

The demonstrated workflow, with its decisions: a plan-code loop with the disabled-button and wrong-code paths, a skills loop that blocks Continue until one is ticked, a profile-creation failure path, the emerging-technology ranking step, the *Aim for this job* decision, the "any must-have missing?" branch, and the progress loop in which only "can do it now" recalculates readiness.

## 3.3 Class diagram (Figures A3 and A4)

Part A shows the domain: Profile, UserSkill, SavedOccupation and ProgressEvent on the user side, and Occupation, Skill, OccupationSkill, RelatedOccupation, OccupationTask, AdvertSummary and AdvertCount on the reference side, with multiplicities (for example, an Occupation has at least one OccupationSkill and at most one AdvertSummary). Part B shows the service modules and their main operations. The backend is written as Python modules of functions, not as classes, so each "class" in part B is a module, marked with a stereotype giving its file.

## 3.4 Sequence diagram (Figure A5)

UC-06 *Recommend Occupations*, between the web UI, the application logic (`app.py`), the data service (the repository and SQLite) and the Recommendation Engine. It shows the alternative paths: a 422 for invalid input, a 404 for an unknown profile, an empty list with a message when no skills are held, and the normal case in which the engine loads 27,463 ratings, centres the vectors, ranks by cosine, and returns the top five with the skills that lifted each.

## 3.5 Component and deployment diagrams (Figures A6 and A7), and design against implementation

The component diagram groups the twelve front-end scripts and eleven back-end modules, and shows the two loaders. The deployment diagram shows the presenter's laptop as the execution environment, with the optional Fly.io machine beside it.

**Important differences between the design and the prototype:**

The prototype is a layered single service (presentation, API, service modules, data). The design separates these into services; that is planned for the final system, and the module boundaries already allow it. Accounts are replaced by a plan code, because the prototype stores no personal data that needs a password. The CV check accepts pasted text only; CV file upload is planned for the final system. Interview practice gives checklist feedback rather than conversation; a chatbot would need a language model, which this build deliberately excludes.

# Question 4 — Evidence and limitations

## 4.1 Test cases

Run on 24 October 2026: 56 unit tests, 100 integration and system tests and 5 performance tests, all passing (161 in all). Representative cases:

| ID | Covers | Expected result | Actual result | Status |
|---|---|---|---|---|
| TC-S01 | Main workflow | The demonstration profile (6 skills, goal Electricians) gives 6 held, 2 essential and 26 desirable missing, and a 3-step Pathway | 6 / 2 / 26, and 3 steps | Pass |
| TC-I10c | Invalid input | A wrong plan code returns 404 with a plain message | 404 "No plan matches that code. Check it and try again." | Pass |
| TC-I18e | Invalid input | A CV under 20 characters is refused | 422 | Pass |
| TC-I08a | Data interaction | Searching "conduit installer" finds Electricians through an alternate title | Electricians returned | Pass |
| TC-I20a | Data interaction | Electricians' adverts are labelled US, April 2024, closed, with the dataset named | 84 adverts, April 2024, CC BY-SA named | Pass |
| TC-I05a, d | Emerging technology | Five recommendations for six skills; none, with a message, for no skills | 5 results; empty list and message | Pass |
| PT-01b | Emerging technology | Accuracy at least 55%, with the target excluded | 58.5% (95% interval 54.6–62.1) against 25.9% by chance | Pass |
| TC-I18d | Privacy | Scanning a CV changes nothing stored on the profile | Skills, history and counts unchanged | Pass |
| TC-N01a | Reliability | 20 concurrent requests all succeed | 20 of 20 returned 200 | Pass |

## 4.2 Quantitative measures

| Measure | Result | Target | Source |
|---|---|---|---|
| Response time over HTTP, every demo endpoint | **98 ms at p95**, 158 ms maximum | 95% under 2,000 ms | PT-03 |
| Recommendation ranking time (879 occupations) | **4.9 ms at p95** | 100 ms | PT-02 |
| Recommendation accuracy, same-family agreement | **58.5%** against 25.9% by chance | 55% | PT-01b |
| Rebuild of the database from source | **5.7 s** | 60 s | PT-04 |
| CV goal score against human match scores (172 held-out CVs) | **r = 0.27**, against 0.16 for word matching | better than word matching | benchmark, 9 October |
| Accessibility (WCAG 2.1 A and AA, automated) | **169 failures to 0**, on 23 screens, in light and dark mode and at 320 px wide | 0 | axe-core audit |

## 4.3 Limitations and corrective actions

1. **The data is not South African.** The course required all system data to come from Kaggle, and the best occupational skills dataset available there was O\*NET, which describes jobs in the United States. Its job titles, skill ratings and labour market differ from South Africa's, and the skills a user ticks are self-reported. With broader access to South African labour force and job data, or my own surveys of the skills South African jobs need, the recommendations would give a far more accurate picture. **Corrective action:** with the lecturer's approval, add South African occupational data, such as the Organising Framework for Occupations (OFO) used by the SETAs, and map it to the same skills. Then run a short survey of employers and young workers to check the skill ratings for the most common entry-level jobs.
2. **Too little for students in the middle of their studies.** The prototype gives an enrolled student a target and a Pathway of jobs, but not the steps that matter most to them now: internships, short certificates and learnerships that build the missing skills. Its 35 skills are also broad; finer, more specific skills would suit South African youth better. **Corrective action:** link each missing skill to SETA learnerships, TVET short courses and internship programmes, with approval for that data. Use the finer detail already in the database (software, tools and knowledge areas per job) to break the broad skills down further.

*Further risks:* no first-time user has yet completed the journey unassisted, so its ease of use is unproven; plan codes are not rate-limited; and saved plans reset on the optional hosted copy.

# Declarations

**Original work.** [To be confirmed and signed by the student.] The signed TUT Declaration of Originality form is attached separately. I declare that this report and the prototype are my own work, except where sources are acknowledged.

**Use of AI tools.** [To be confirmed by the student: the study guide has no AI rule, so this is disclosed and has been raised with the lecturer in writing.] An AI coding assistant, Claude Code (Anthropic), wrote most of the code, tests and first drafts of the documentation, and produced the first draft of this report from the repository's test results. I set the scope, the data rules and the decisions recorded in `docs/DECISIONS.md`, drafted the functional requirements (FR-5 onward) myself, ran and checked the prototype, rewrote the key sections of this report in my own words (the problem, users and purpose, the design differences, and the limitations), and checked the rest. I am responsible for everything submitted. The repository's commit messages record the assistant's involvement.

# References

- Branson, N., De Lannoy, A. and Brynde, K. (2019). *Review of Youth Labour Market Research: Staggered pathways to employment for youth in South Africa*. National Income Dynamics Study. Cape Town: SALDRU, University of Cape Town. https://opensaldru.uct.ac.za/handle/11090/948
- Ismail, Z. and Kollamparambil, U. (2015). Youth unemployment duration and competing exit states: what hides behind long spells of black youth unemployment in South Africa? *African Development Review*, 27(3), 301–314.
- Statistics South Africa (2026). *Quarterly Labour Force Survey, Q2 2026*, media release, 11 August 2026. https://www.statssa.gov.za
- National Center for O\*NET Development (2024). *O\*NET 29.0 Database* (August 2024 release). Kaggle: emarkhauser/onet-29-0-database.
- Kaggle. *LinkedIn Job Postings (2023–2024)*, arshkon/linkedin-job-postings, CC BY-SA 4.0.
- Kaggle. *Resume Dataset*, saugataroyarghya/resume-dataset, CC BY-NC 4.0 (used to measure the CV scanner).
- FastAPI 0.141.1 and uvicorn 0.52.4; React 18.3.1; htm 3.1.1; PlantUML.
- Project repository: https://github.com/ShogunLSG/SAYCEP, including `docs/DECISIONS.md` (the decision log) and `docs/test-results/`.

# Appendix A — UML diagrams

*Figure A1 — use-case diagram.*

*Figure A2 — activity diagram.*

*Figure A3 — class diagram, part A: domain.*

*Figure A4 — class diagram, part B: services.*

*Figure A5 — sequence diagram.*

*Figure A6 — component diagram.*

*Figure A7 — deployment diagram.*

# Appendix B — Screenshots of the demonstrated workflow

*Figure B1 — welcome.*

*Figure B2 — recommendations, each with its reasons.*

*Figure B3 — the gap for Electricians.*

*Figure B4 — the Pathway.*

*Figure B5 — the unlock card after "I can do this now".*

*Figure B6 — what employers ask for.*
