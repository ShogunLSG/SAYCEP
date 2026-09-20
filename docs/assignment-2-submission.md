# ISJ107V Assignment 2 — Formal System Proposal and Specification

> **Draft for you to rewrite in your own voice.** This assembles answers to all
> five questions from decisions already made and recorded in this repository. It
> is assessed work and you are questioned on it, so the phrasing should be yours.
>
> **Placeholders marked `[CITE]` need a real referenced statistic.** I have not
> filled those in because I cannot verify South African labour figures from here,
> and an invented number in an assessed document is worse than a gap.
>
> Q2 lives in `functional-requirements.md` and is summarised here. Q4 diagrams are
> in `docs/uml/` as PlantUML source with rendered PNG and SVG.

---

# Question 1 — Project introduction [8]

## 1.1 Project title, description, intended users, emerging technology (2)

**Title:** SAYCEP — South African Youth Career and Employment Platform

**Description.** SAYCEP is a web-based career guidance system that helps young
people identify an achievable target occupation, understand precisely which
skills they are missing to reach it, and follow an ordered pathway of
intermediate steps to get there. It holds a catalogue of 879 occupations, each
described by 35 skills rated for importance, together with the level of
preparation each occupation requires and an expert-reviewed map of which
occupations lead to which others.

**Intended users.** Two profiles, and the system is designed around the
difference between them:

- **The enrolled student** — already studying toward a qualification, with
  direction but not a plan. They need to know what a target role requires beyond
  what their course gives them.
- **The unqualified school-leaver** — no qualification and no direction,
  including those for whom a degree is not the route. They need to discover what
  is reachable at all, which is why the system exposes occupations by preparation
  level rather than assuming a degree.

**Emerging technology.** Machine learning, specifically **content-based
recommendation using mean-centred cosine similarity** over 35-dimensional
skill-importance vectors. Each occupation is represented as a vector of O\*NET
importance ratings; a user's self-assessed skill profile is compared against all
879 to rank them by fit. It is implemented in `backend/recommend.py`.

## 1.2 Problem statement (3)

**The current problem.** South African youth unemployment is among the highest in
the world, at `[CITE]`% for ages 15–34 `[CITE: source and year]`. But
unemployment figures describe the symptom. The underlying problem this system
addresses is narrower and more tractable: young people cannot see the route from
where they are to work that exists. Career guidance is concentrated in
better-resourced schools, it skews heavily toward university pathways, and it
rarely tells a young person which specific, nameable skills stand between them
and a particular job.

**Who is affected.** Two groups, differently. School-leavers without a
qualification are affected most severely: they are frequently steered toward
degree routes they cannot access, while trade and technician occupations that
require apprenticeship or vocational training rather than a degree go
unmentioned. Of the 879 occupations in the system's catalogue, **525 — 59.7% —
require no degree**. That is the majority of the labour market, and it is the
part least visible to the people who most need it. Enrolled students are affected
differently: they have direction but often discover only at graduation that their
qualification alone does not meet what employers ask for.

**Consequences of leaving it unresolved.** Young people continue to make
irreversible decisions — which course to take, whether to continue studying,
which jobs to apply for — on incomplete information. The individual cost is time
and money spent on routes that do not lead anywhere they wanted. The systemic
cost is a labour market where vacancies in skilled trades coexist with high youth
unemployment, because the people who could fill them were never shown the path.

## 1.3 Aim, objectives, scope, success criteria (3)

**Aim.** To give South African youth a clear, evidence-based view of the skills
and steps required to reach a specific occupation, including routes that do not
require a degree.

**Measurable objectives.**

1. Deliver a skills gap analysis that, for any of the 879 catalogued
   occupations, lists every missing skill classified as essential or desirable,
   returning results within 2 seconds.
2. Generate a career pathway of no fewer than three ordered intermediate steps
   for any target occupation in the catalogue, each step naming the skills to
   acquire.
3. Recommend occupations by skill similarity such that at least one of the top
   five results falls in the user's own occupational family in 55% or more of
   test cases, against a 6.9% random baseline.

**Scope boundaries.**

*In scope:* profile creation for two user types; skill self-assessment against 35
skills; occupation search and browsing by preparation level; skills gap analysis;
career pathway generation; similarity-based occupation recommendation; data
provenance display.

*Out of scope:* employer-facing functionality of any kind; job vacancy listing or
application; qualification verification; payment processing; mobile applications;
and any authentication beyond profile identification, which is deliberate — see
3.3.

**Success criteria.**

1. A user with no qualification can, in five screens or fewer and without
   instructions, reach a displayed pathway of at least three steps toward an
   occupation that requires no degree.
2. Every occupation and skill shown to a user displays its source dataset and
   publication date, so that the origin of every claim the system makes is
   visible without being asked for.

---

# Question 2 — Requirements [15]

Full text, with acceptance criteria, in `functional-requirements.md`. Summary:

**2.1 — Ten functional requirements.** FR-01 Create Profile · FR-02 Capture Skill
Profile · FR-03 Select Target Occupation · FR-04 Search Occupation Catalogue ·
FR-05 Browse by Preparation Level · FR-06 Recommend Occupations · FR-07 Analyse
Skills Gap · FR-08 Generate Career Pathway · FR-09 View Data Provenance · FR-10
Load Occupation Data. Each carries a MoSCoW priority and a Given/When/Then
acceptance criterion. IDs match the use cases in the Q4 diagrams.

**2.2 — Four non-functional requirements.** NFR-01 Performance (2 s response) ·
NFR-02 Usability (5 screens, unassisted) · NFR-03 Reliability (refuse to start on
an invalid database) · NFR-04 Supportability (full rebuild under 60 s; measured
at 1.1 s).

**2.3 — Three emerging-technology requirements.** TR-01 accuracy (≥55%
occupational-family agreement; measured 59.7%) · TR-02 latency (≤100 ms p95;
measured 8.8 ms) · TR-03 determinism and robustness.

---

# Question 3 — Technical environment [10]

## 3.1 Technology stack and justification (3)

| Layer | Choice | Justification |
|---|---|---|
| User interface | React, served as a single page | Named in the project proposal; component model suits the four-screen demo path. Loaded from CDN rather than a build toolchain, removing a category of setup failure. |
| Application layer | Python 3.10+ with FastAPI | One language across the API, the data loading and the recommendation engine. FastAPI gives typed request validation and generated API documentation without additional libraries. |
| Dataset | O\*NET 29.0 Database, obtained via Kaggle | CC BY 4.0, published by the U.S. Department of Labor. Supplies importance-rated skills, preparation levels and an expert-reviewed occupation graph — see 5.1. |
| Database | SQLite, single file | No server to install, configure or keep running. The database is a derived artifact rebuilt from source in 1.1 seconds, so durability is not a requirement it has to meet. |
| Emerging technology | Mean-centred cosine similarity, Python standard library | No framework needed: the feature space is 35 dimensions and the whole catalogue ranks in 8.8 ms. Adding a machine-learning framework would add weight without adding capability. |
| APIs | Internal REST over HTTP/JSON | No external API calls at request time. All data is local, which is what makes the 2-second performance requirement easy to meet. |
| Development tools | Git, Python standard library, PlantUML for modelling | The project has no third-party runtime dependencies at all, which is unusual and deliberate. |
| Deployment platform | Local host for the demonstration | Sized in 3.2. Nothing in the design prevents container deployment later. |

**The main justification, stated plainly.** Every choice above optimises for a
system that can be built, demonstrated and explained by one developer. A
multi-service architecture with a separate ML service, a database server and a
frontend build pipeline is the conventional answer and would have consumed the
available time in configuration rather than capability.

## 3.2 Hardware requirements (4)

| Component | Minimum | Recommended |
|---|---|---|
| Processor | Dual-core x86-64, 2.0 GHz | Quad-core x86-64, 2.5 GHz or better |
| Memory | 4 GB RAM | 8 GB RAM |
| Storage | 500 MB free — 97 MB source data, 5 MB database, runtime and interpreter | 2 GB free, SSD |
| Network / connectivity | None at runtime; connection required once to download the dataset | Broadband for the initial 13 MB dataset download |
| Client devices | Any device with a modern browser supporting ES6 — desktop, laptop or tablet | Desktop or laptop, 1366×768 or larger, for the tabular gap and pathway views |
| Specialised hardware | **None** | **None** |

**On specialised hardware.** The emerging technology requires no GPU and no
accelerator. This is a consequence of the design choice, not an accident: the
recommendation operates on 879 vectors of 35 dimensions and completes in under
9 milliseconds on ordinary hardware. A deep learning approach would have required
specialised hardware to train and a dependency to run, for a problem whose entire
feature space is 35 curated survey dimensions. Stating this is worth a mark —
choosing a technology proportionate to the problem is an engineering decision, not
a limitation.

## 3.3 Architecture, communication, scalability, security, backup and recovery (3)

**Architecture.** A single deployable service. The React client issues HTTP/JSON
requests to the FastAPI application layer, which calls two internal modules — the
Gap Analyser and the Recommendation Engine — both of which read through an
Occupation Repository onto SQLite. The sequence diagram in `docs/uml/` shows this
path for the pathway use case.

The production design documented in the proposal separates the ML component into
its own service. The demonstration deliberately does not, and the module
boundaries in code are kept clean so that the separation remains possible without
rework.

**Scalability.** The current load is one user and a 5 MB database, so scaling is a
design property rather than a present need. The relevant properties: the dataset
is read-only at runtime and identical for every user, so it can be replicated
behind a load balancer without coordination; the recommendation engine is
stateless and CPU-bound, so it scales horizontally; and its 8.8 ms latency leaves
ample headroom. The first bottleneck under real load would be the per-request
vector construction, which is cacheable in memory since the occupation vectors
never change between data loads.

**Security.** The system holds no credentials, no payment data and no personal
identifiers — a profile is a set of self-declared skills and a target occupation,
with no name, email or contact details attached. This is the strongest security
posture available: data that is not collected cannot be breached. Input is
constrained to selections from fixed catalogues rather than free text, which
removes injection surface, and all database access uses parameterised queries.

**Backup and recovery.** The database is a derived artifact, not a system of
record. It is rebuilt from the O\*NET source files by a single command in 1.1
seconds, and the loader refuses to complete if any source file's row count
differs from O\*NET's published reference — so a corrupted rebuild fails loudly
rather than producing a database that looks correct and is quietly wrong. User
profiles are the only non-reproducible data and would require conventional
backup in a production deployment; for the demonstration they are ephemeral.

---

# Question 4 — UML models [13]

Four diagrams in `docs/uml/`, authored in PlantUML, rendered to PNG and SVG.
Actor, class, component and requirement names are consistent across all four and
with the Q2 requirements.

| Diagram | File | Shows |
|---|---|---|
| 4.1 Use case | `01-use-case.puml` | System boundary; Youth User generalised into Enrolled Student and School-Leaver; Data Administrator and O\*NET Dataset as supporting actors; ten use cases UC-01 to UC-10 mapping to FR-01 to FR-10; include and extend relationships. |
| 4.2 Activity | `02-activity.puml` | End-to-end workflow from profile creation to displayed pathway, with the decision on profile type, the two alternative paths, the empty-gap alternative, and the Recommendation Engine as the labelled emerging-technology step. |
| 4.3 Class | `03-class.puml` | Domain classes with attributes and operations; Profile generalised into StudentProfile and SchoolLeaverProfile; Pathway composed of PathwayStep with multiplicity `3..*`, which encodes FR-08's three-step minimum as a model constraint. |
| 4.4 Sequence | `04-sequence.puml` | Time-ordered interaction for UC-08 Generate Career Pathway, across Web UI, SAYCEP API, Pathway Service, Gap Analyser, Recommendation Engine, Occupation Repository and SQLite. |

---

# Question 5 — Implementation and evaluation [13]

## 5.1 Dataset, interface, entities, inputs, outputs, validation, privacy (2)

**Dataset.** The O\*NET 29.0 Database, published by the U.S. Department of Labor's
Employment and Training Administration under CC BY 4.0 and obtained through
Kaggle. Loading it produces 879 occupations, 35 skills, 27,463 importance
ratings, 17,580 related-occupation links and 5 preparation levels. It is United
States occupational data; the South African framing of this project lives in the
problem statement and the design decisions rather than in the ingested data, and
that distinction is deliberate and documented.

**Main data entities.** `occupations` (SOC code, title, description, job zone) ·
`skills` (element ID, name, description) · `occupation_skills` (importance rating
on a 1–5 scale, scale maximum, publication date) · `related_occupations` (tier,
expert-review order) · `job_zone_reference` (preparation level descriptions) ·
`users` and `user_skills` (the captured profile).

**Interface.** Internal REST over HTTP/JSON:

```
GET  /occupations?zone=&q=      list and filter the catalogue
GET  /occupations/{soc}         one occupation with provenance
GET  /skills                    all 35, for the capture screen
POST /profiles                  create a profile with captured skills
GET  /profiles/{id}/gap         missing skills, classified, by importance
GET  /profiles/{id}/pathway     ordered steps with skills per step
GET  /recommendations           ranked occupations by similarity
```

**Inputs.** Profile type (one of two fixed values); skill selections (a subset of
35 fixed identifiers); target occupation (one SOC code from the catalogue); job
zone filter (integer 1–5); search term (text).

**Outputs.** Classified skills gap; ordered pathway with skills per step; ranked
occupation recommendations with similarity scores; source dataset and publication
date on every record.

**Validation.** Every input except the search term is a selection from a fixed,
server-known set, so validation is membership checking rather than parsing. SOC
codes are verified against the catalogue; job zones must be 1–5; skill
identifiers must exist in the 35-entry taxonomy. At load time, every source file's
row count is checked against O\*NET's published figures and the load aborts on any
mismatch.

**Privacy.** The system collects no personal identifiers — no name, email,
contact details or demographic data. A profile is a set of self-declared skills
and a target occupation. Nothing collected identifies a person, which means there
is no personal data to protect, disclose or lose.

## 5.2 Emerging-technology integration and interface contract (2)

The Recommendation Engine sits between target selection and pathway generation.
It is invoked when a school-leaver needs candidate occupations and when the
pathway service orders intermediate steps.

**Interface contract:**

```
recommend(connection, held_skill_ids, limit=5, max_job_zone=None)
    -> [(soc_code: str, title: str, score: float), ...]

  Preconditions:
    held_skill_ids ⊆ the 35 O*NET skill element identifiers
    max_job_zone ∈ {1..5} or None
  Postconditions:
    returns exactly `limit` results ordered by descending score,
      where held_skill_ids is non-empty
    returns [] where held_skill_ids is empty        (TR-03)
    every returned soc_code exists in the catalogue
    0.0 ≤ score ≤ 1.0
```

**Pseudocode:**

```
FOR each skill i in the 35-skill taxonomy
    mean[i] ← average importance of skill i across all 879 occupations

FOR each occupation o
    centred[o][i] ← importance[o][i] − mean[i]

profile[i] ← 1 if the user holds skill i, else 0
centred_profile[i] ← profile[i] − (1 if mean[i] ≥ 3.5 else 0)

FOR each occupation o (optionally restricted by job zone)
    score[o] ← cosine(centred_profile, centred[o])

RETURN the 5 occupations with highest score
```

**Why mean-centring, in one sentence you may be asked for.** Measured on the
loaded catalogue, the mean cosine similarity between an occupation and its
nearest neighbour is 0.994 — the raw vectors nearly all point the same way
because O\*NET's skills are generic — so subtracting each skill's mean
re-expresses an occupation by how it deviates from the average occupation, which
is where the discriminating signal actually is. This lifted top-five occupational
family agreement from 19.4% to 32.4%.

## 5.3 Testing and evaluation plan (2)

**Functional testing.** Each of FR-01 to FR-10 has a Given/When/Then acceptance
criterion, written to be executable rather than interpretive. Data-layer
requirements are already verified: FR-10's row counts are asserted by the loader
on every run, and FR-08's three-step minimum was confirmed by checking that all
879 occupations have three or more reachable primary neighbours.

**Emerging-technology metric.** Top-five occupational-family agreement, measured
against a random baseline. Test profiles are constructed by taking an
occupation's essential skills as a stand-in for a person suited to it, then
checking whether the engine returns occupations in the same SOC major group.
Current measurement: **59.7% against a 6.9% baseline**, with the requirement set
at 55%. Exact-occupation recall is deliberately *not* the metric, because
occupations with near-identical skill profiles should legitimately score alike.

**User acceptance testing.** Two participants per user profile, four in total,
each asked to reach a displayed pathway without instruction. Success is measured
against NFR-02: five screens or fewer, unassisted. The school-leaver participants
matter most, since that path involves discovering occupations rather than
searching for a known one.

**Principal technical risk and mitigation.** *The recommendation engine's
discrimination is inherently limited by the generic nature of O\*NET's 35-skill
taxonomy* — a 0.994 mean nearest-neighbour similarity is a property of the data,
not a defect in the implementation. If accuracy proves insufficient under user
testing, the mitigation is available and unused: O\*NET supplies Knowledge (33
elements), Abilities (52) and Work Activities (41) in the same structure and the
same files already downloaded. Extending the feature space from 35 to 161
dimensions requires no new data source, no schema redesign and no change to the
algorithm — only a wider vector. Holding that in reserve is why the risk is
manageable rather than fundamental.
