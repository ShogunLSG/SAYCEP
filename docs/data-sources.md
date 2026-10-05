# Data sources

## The rule

Project data must come from Kaggle. If no suitable Kaggle dataset exists, the process is: request a consultation with the lecturer (in his office), present the proposed own/simulated data, and he decides whether it's acceptable or which Kaggle dataset to use instead.

## Decision: hybrid

**System data comes from Kaggle. South African context comes from cited statistics, used only as background in the written proposal — never loaded into the system.**

This satisfies the rule without a consultation dependency, and keeps the "for South African youth" framing that makes the project distinctive. The framing lives in the problem statement and the design decisions; the data the system actually processes is Kaggle-sourced.

Be ready to state this distinction clearly if asked — it's the honest answer to "where does your data come from?" and it shows the rule was understood rather than worked around.

## Why the original plan was dropped

The proposal originally named the ESSA public API and a curated TVET/SETA dataset. Neither is on Kaggle. The authoritative South African labour-market data lives with StatsSA and the World Bank, not Kaggle, so building the system on it would have required the consultation route and a decision that couldn't be guaranteed before the October presentation. The hybrid avoids that risk.

## The spine: O*NET 29.0 (decided 10 September 2026)

**Source:** [O*NET Database on Kaggle](https://www.kaggle.com/datasets/emarkhauser/onet-29-0-database)
· CC BY 4.0 · usability 10.00 · U.S. Department of Labor, Employment and Training
Administration.

Found by searching Kaggle for trade and artisan coverage, after the original
shortlist left the school-leaver profile with almost nothing to stand on. It
replaces the shortlist as the system's data spine — see ADR-0003 in
`DECISIONS.md` for the reasoning and the full comparison.

Structure confirmed against O*NET's published data dictionary at onetcenter.org.
Reading that documentation is not a second data source; the data itself comes
from the Kaggle copy.

| File | Rows | Gives us |
|---|---|---|
| `Occupation Data.txt` | 1,016 | SOC code, title, description |
| `Skills.txt` | 61,530 | Importance (IM) and Level (LV) ratings per skill per occupation, with confidence intervals |
| `Job Zones.txt` | 923 | Preparation level 1–5 — the degree vs non-degree distinction |
| `Related Occupations.txt` | 18,460 | 10 primary + 10 supplemental related occupations, ordered by expert review |
| `Task Statements.txt` | 18,796 | What people in the job actually do, in plain sentences. Loaded 30 September (ADR-0007) |
| `Task Ratings.txt` | 158,751 | Importance (IM) of each task, used only to put the most important tasks first |
| `Alternate Titles.txt` | 55,120 | Other names for each job, so search finds them (ADR-0009) |
| `Technology Skills.txt` | 32,470 | Software used in each job, with O*NET's "hot technology" flag |
| `Tools Used.txt` | 41,650 | Physical tools used in each job, grouped by category |
| `Interests.txt` | — | RIASEC inventory, for school-leaver intake |

Two flags in `Skills.txt` must be respected on load: `Recommend Suppress` marks
low-precision ratings and `Not Relevant` marks skills that don't apply. Rows
marked `Y` get dropped, or the system will present numbers its own source won't
stand behind.

**It is United States data.** That does not worsen the position ADR-0002 already
took — the South African framing lives in the problem statement, not in what the
system ingests. An authoritative government dataset is easier to defend than an
anonymous synthetic CSV. Be ready to say exactly that.

---

## Original shortlist — verified 10 September 2026, now superseded

Kept because the verification is what led to O*NET, and because "why aren't you
using the South African job postings dataset?" has a specific answer that belongs
on the record.

All five opened and inspected in a browser. Schemas render publicly; no login was
needed. Two are unusable for their intended purpose and the intended spine has a
defect that reaches FR-2. Only the Resume Dataset remains a candidate — for the
CV scorer, if that module is ever built.

| Dataset | Intended use | Verdict |
|---|---|---|
| [Jobs and Skills Mapping for Career Analysis](https://www.kaggle.com/datasets/emaadakhter/jobs-and-skills-mapping-for-career-analysis) | The role↔skill spine | ⚠️ **Usable with a caveat** — skills field has no delimiter, no importance data |
| [Skill & Career Recommendation Dataset](https://www.kaggle.com/datasets/tea340yashjoshi/skill-and-career-recommendation-dataset) | Pathway recommendation logic | ❌ **Not a role↔skill map** — student aptitude scores. Possible fit for school-leaver intake instead |
| [Resume Dataset](https://www.kaggle.com/datasets/saugataroyarghya/resume-dataset) | CV scorer, if built | ✅ **Best of the five** — 9,544 rows, 35 columns, usability 10.00, documented |
| [Resume and Job Description](https://www.kaggle.com/datasets/sayyedfaizan95/resume-and-job-description) | CV↔role matching, if built | ⚠️ Tagged synthetic; **license Unknown** |
| [Job Posting Data in South Africa](https://www.kaggle.com/datasets/techsalerator/job-posting-data-in-south-africa) | Opportunity matching | ❌ **Mislabelled — not South African** |

### 1. Jobs and Skills Mapping for Career Analysis

`formatted_jobs.csv`, 176.59 kB. Six columns, ~970 rows. MIT licence, usability
6.47, last updated a year ago.

| Column | Notes |
|---|---|
| `ID_num` | 1–970 |
| `job_title` | 896 unique across ~970 rows — **roughly one row per occupation** |
| `Short_description` | 930 unique |
| `Skills_required` | 918 unique — see the defect below |
| `Industry` | Technology 20%, Marketing 10%, other 70% across 679 further values |
| `Pay_grade` | Average 56%, High 29%, remainder across 140 further values |

**Defect — the skills field has no delimiter.** The data card documents
`Skills_required` as semicolon-separated. It is not. Across 108 distinct rows
loaded from the preview, **zero** contained a semicolon. Every one looked like:

> `Problem Solving Logical Reasoning Attention to Detail Team Collaboration Critical Thinking`

Five multi-word skills run together with nothing but spaces between them. There is
no reliable way to split that back into skills — a parser cannot know whether
`Problem Solving Logical Reasoning` is two skills or three. The two
semicolon-separated examples on the data card (rows 648 and 970) are not
representative of anything visible in the file.

**Second defect — no importance field.** The schema in `architecture.md` has
`occupation_skills(occupation_id, skill_id, importance)` for essential vs
desirable. Nothing in this dataset carries importance. And because each
occupation appears roughly once, the rule FR-2 suggests — a skill is essential if
it appears in more than X% of records *for that occupation* — has no frequency to
compute. One record per occupation means every skill appears in 100% of them.

**Third — the skills are generic.** What is present is largely soft skills
(Problem Solving, Communication, Attention to Detail) rather than the concrete,
teachable competencies a pathway step would name. Trade and artisan coverage was
not confirmed.

### 2. Skill & Career Recommendation Dataset

`Dataset Project 404.xlsx`, 808 kB, 56 columns. Row count unconfirmed — Kaggle
cannot preview the file ("There are no tables in this selection"). Usability 5.88,
Open Database licence, two years old.

Not a role↔skill mapping. It is one row per *student*: eight
multiple-intelligence scores (Linguistic, Musical, Bodily,
Logical-Mathematical, Spatial-Visualization, Interpersonal, Intrapersonal,
Naturalist), eight performance indicators (P1–P8, valued AVG/POOR/BEST), a
`Course`, and a single recommended `Job Profession`.

It cannot populate `occupation_skills`. It *could* serve the school-leaver intake
path in FR-3, where capture has to be interest- or aptitude-based because there is
no qualification to infer from — this is precisely an aptitude instrument. Being
`.xlsx` it needs `openpyxl`; minor.

### 3. Resume Dataset

`resume_data.csv`, 17 MB. **35 columns, 9,544 rows**, both stated on the data
card. Usability **10.00** — the only well-documented dataset of the five.
Licence: Attribution-NonCommercial 4.0 International (fine for coursework; note
the non-commercial term).

Columns seen: `address`, `career_objective`, `skills`,
`educational_institution_name`, `degree_names`, `passing_years`, and 29 more.

Worth more than its "CV scorer" slot suggests. It carries a real `skills`
vocabulary at volume alongside `degree_names` — the qualification→skills link the
enrolled-student profile needs.

**Verified 5 October 2026 (downloaded and measured, step 0 of `plans/cv-scorer.md`):**

- **9,544 rows are 341 distinct CVs crossed with 28 job adverts.** The effective
  sample is 341 CVs, not 9,544.
- **There is a ground truth:** `matched_score` (0.00–0.97, mean 0.66) for each
  CV–advert pair. The data card doesn't say how it was produced (it's from a
  hackathon, Bitfest 2025), but it behaves sensibly. CVs with machine-learning
  skills average 0.82 for *ML Engineer* and 0.40 for *Civil Engineer*. The
  advert explains 28% of its variance and the CV 22%; the rest depends on the
  pairing, which is what a matcher must capture. Naive word overlap reaches
  only r = 0.16 against it.
- **Defect:** the CV's `responsibilities` column is identical to the advert's
  `responsibilities.1` in all 9,544 rows. The CVs' own experience text is
  missing.
- **Domain:** tech and office work in South Asia (Python, machine learning,
  SQL, Excel; adverts for civil, AI and HR roles). It doesn't resemble a South
  African school-leaver or trades CV.
- **Vocabulary link to O\*NET:** 50.3% of CV skill mentions match an O\*NET
  *Technology Skills* example (Python, SQL, Excel), which links them to
  occupations rather than directly to the 35 skills. 48.4% match nothing
  ("machine learning", "leadership", "budgets"), and under 2% name an O\*NET
  skill or knowledge area directly.

### 4. Resume and Job Description

`resume_dataset_1200.csv`, 507 kB, 14 columns, ~1,200 rows (967 unique names).
Usability 5.29. Tagged **Synthetic** by the uploader. **Licence: Unknown** — worth
avoiding in assessed work where provenance is the thing being examined.

Columns: `Name`, `Age`, `Gender`, `Education_Level`, `Field_of_Study`, `Degrees`,
`Institute_Name`, `Graduation_Year`, `Experience_Years`, `Current_Job_Title`, +4.

### 5. Job Posting Data in South Africa

`Job Posting.csv`, 39.36 MB, 21 columns, ~9,900 unique postings dated March to
September 2024. Apache 2.0, usability 5.29.

**The data is not South African.** The suspicion recorded here was that this would
be a thin teaser for a paid product. The file is substantial, but mislabelled:

- `Location` — the single most common value is **Bangalore, India** (6%). A sample
  row reads `Indiana, United States`. South Africa does not appear among the
  frequent values.
- `Website Domain` — **bosch.com 55%, zf.com 34%**. Two German industrial groups
  account for 89% of every posting in a dataset titled for South Africa.
- `Ticker` — **100% null**. An entirely empty column.

The data card's own text ends by inviting you to email the vendor for a quote. The
Kaggle upload appears to be a global scrape of two companies' career pages with a
country name attached to it.

Unusable for opportunity matching, and worth knowing about for its own sake: it is
a clean example of why the verification step exists.

---

Requirements that promise something the data can't deliver are the ones that fall
apart under questioning. Two of these would have done exactly that.

## Job adverts for "What employers ask for" (5 October 2026, ADR-0017)

Searched again for module 4. Full results are in
`test-results/job-postings-step0-2026-10-05.txt` and
`test-results/adverts-2026-10-05.txt`.

- **`samanthalucywu/2023-2025-mba-jobs-data-south-africa`, rejected as
  synthetic.**
  - It's 786 MB, MIT-licensed and published July 2026.
  - 3,817 sampled rows have only 40 titles, 10 summaries and 4 description
    templates.
  - The company names are invented, and every row claims Adzuna as its
    source.
  - It covers MBA roles only.
  - It's the second Kaggle "South Africa jobs" set to fail verification.
- **`arshkon/linkedin-job-postings`, used.**
  - CC BY-SA 4.0, 123,849 real LinkedIn adverts, US only, listed 24 March –
    20 April 2024.
  - It's linked to O\*NET by **title only**: one candidate occupation, with
    generic titles dropped. That links 21.4% of adverts, and 438 of 879
    occupations have 5 or more adverts. 44 of 50 links were clearly right on
    a hand check.
  - Only counts are stored, never advert text.
  - **ShareAlike:** anything derived from it that's redistributed carries the
    same licence. For coursework that means attribution, which the screen
    gives.

## Background statistics (proposal section 2.1 only)

Cite these in the written background. Do not load them into the system.

- [StatsSA — South Africa's Youth and the Labour Market](https://www.statssa.gov.za/?p=19526)
- [StatsSA — South Africa's Youth in the Labour Market: A Decade in Review](https://www.statssa.gov.za/?p=18398)
- [World Bank — youth unemployment, South Africa](https://data.worldbank.org/indicator/SL.UEM.1524.NE.ZS?locations=ZA)
