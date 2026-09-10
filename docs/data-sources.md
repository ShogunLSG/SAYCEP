# Data sources

## The rule

Project data must come from Kaggle. If no suitable Kaggle dataset exists, the process is: request a consultation with the lecturer (in his office), present the proposed own/simulated data, and he decides whether it's acceptable or which Kaggle dataset to use instead.

## Decision: hybrid

**System data comes from Kaggle. South African context comes from cited statistics, used only as background in the written proposal — never loaded into the system.**

This satisfies the rule without a consultation dependency, and keeps the "for South African youth" framing that makes the project distinctive. The framing lives in the problem statement and the design decisions; the data the system actually processes is Kaggle-sourced.

Be ready to state this distinction clearly if asked — it's the honest answer to "where does your data come from?" and it shows the rule was understood rather than worked around.

## Why the original plan was dropped

The proposal originally named the ESSA public API and a curated TVET/SETA dataset. Neither is on Kaggle. The authoritative South African labour-market data lives with StatsSA and the World Bank, not Kaggle, so building the system on it would have required the consultation route and a decision that couldn't be guaranteed before the October presentation. The hybrid avoids that risk.

## Kaggle shortlist (verify before relying on any of these)

Schemas could not be confirmed without a logged-in session — Kaggle renders dataset previews client-side. **Open each one, check the actual columns and row count, and record them in the table below before building anything on them.**

| Dataset | Intended use | Verified? |
|---|---|---|
| [Jobs and Skills Mapping for Career Analysis](https://www.kaggle.com/datasets/emaadakhter/jobs-and-skills-mapping-for-career-analysis) | The role↔skill spine — feeds both built modules | ☐ |
| [Skill & Career Recommendation Dataset](https://www.kaggle.com/datasets/tea340yashjoshi/skill-and-career-recommendation-dataset) | Pathway recommendation logic | ☐ |
| [Resume Dataset](https://www.kaggle.com/datasets/saugataroyarghya/resume-dataset) | CV scorer, if built | ☐ |
| [Resume and Job Description](https://www.kaggle.com/datasets/sayyedfaizan95/resume-and-job-description) | CV↔role matching, if built | ☐ |
| [Job Posting Data in South Africa](https://www.kaggle.com/datasets/techsalerator/job-posting-data-in-south-africa) | Opportunity matching — **check first**, vendor-published sets are often a small teaser sample for a paid product | ☐ |

Record real column names and row counts here as each is verified. Requirements that promise something the data can't deliver are the ones that fall apart under questioning.

## Background statistics (proposal section 2.1 only)

Cite these in the written background. Do not load them into the system.

- [StatsSA — South Africa's Youth and the Labour Market](https://www.statssa.gov.za/?p=19526)
- [StatsSA — South Africa's Youth in the Labour Market: A Decade in Review](https://www.statssa.gov.za/?p=18398)
- [World Bank — youth unemployment, South Africa](https://data.worldbank.org/indicator/SL.UEM.1524.NE.ZS?locations=ZA)
