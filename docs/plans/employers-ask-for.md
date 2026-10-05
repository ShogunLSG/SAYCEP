# Plan: "What employers ask for" — module 4, as the data allows

*Written 5 October 2026. Status: **built 5 October (ADR-0017).** Step 0 is in `next-three.md` §3.*

## What it is

On a job's page, a section that summarises **real job adverts** for that
occupation. It's always labelled **US adverts, March–April 2024** (Kaggle
`arshkon/linkedin-job-postings`, CC BY-SA 4.0). It isn't a list of jobs to
apply for, and the screen says so.

- **How many adverts**, and how many were open to beginners (entry level or
  internship).
- **What they ask for** (requirements), from rules we write and test:
  - a high-school diploma (the screen says "about the same as matric");
  - a college or degree qualification;
  - a driver's licence;
  - a trade licence or certificate;
  - "no experience needed" or "we'll train you";
  - typical years of experience asked for;
  - physical work (lifting).
- **Tools and software the adverts name**, from this job's O\*NET lists,
  using the CV scanner's measured matching (ADR-0014).
- **Skills the adverts stress.** These use the CV scanner's skill rules,
  shown only where this job's adverts mention a skill noticeably more often
  than adverts in general. That filters out boilerplate like "customers"
  and "teamwork". Each skill is marked *you have this* or *learning*.
- **Example advert titles.** Titles only: advert text can name recruiters,
  so no descriptions are stored or shown.
- **Fewer than 5 linked adverts:** the section says there aren't enough
  rather than showing noise.

## How

- **Linking:** advert title → O\*NET title or alternate title. The strict
  rule from step 0 applies: one candidate occupation only, generic titles
  dropped. Precision on the hand check was 44 of 50 clearly right.
- **`backend/adverts.py`:** title normalising, linking and requirement
  rules. It's pure functions and unit-tested.
- **`backend/load_adverts.py`:** reads `backend/data/linkedin/postings.csv`
  (gitignored) and writes per-occupation counts. `load_onet.py` calls it at
  the end when the file is present; without the file, the section says the
  data isn't loaded.
- **New tables (a schema change):** `advert_summary`, `advert_counts` and
  `advert_titles`, plus `advert_baseline` for the all-adverts rates. Only
  counts are stored, never advert text.
- **API:** `GET /occupations/{soc}/adverts?profile_id=`.
- **Screen:** a section on the job page (not the journey's quick panel, so
  NFR-02's five screens are untouched), plus the goal's figures on Home.

## How it's checked

- **Validity:** for each occupation with 20 or more adverts, does the
  ranking of skills by how much more its adverts mention them agree with
  O\*NET's importance ranking? Report the median Spearman correlation against
  a shuffled baseline. If there's no agreement, skills get dropped from the
  screen and the reason is written down.
- **Requirement rules:** hand-check a sample of matches per rule and report
  the precision.
- **Tests:** unit tests for linking and rules; API tests for shape,
  threshold and held marking. The browser walk and the accessibility audit
  are extended to the new section.
