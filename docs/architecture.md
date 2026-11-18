# Architecture

There are two architectures in this project and keeping them distinct matters: the one being **built for the October demo**, and the one **documented as the production design**. They are deliberately different, and being able to explain why is worth marks.

## Demo architecture (what gets built)

One service. One database file. One frontend.

| Layer | Choice |
|---|---|
| Backend | Python (FastAPI) — single service |
| Database | SQLite (file-based, no server to run) |
| Frontend | React with `htm`, vendored, no build step |
| Emerging technology | The **skill-matching model**: mean-centred cosine similarity over 35 O\*NET skill ratings (`backend/recommend.py`), measured by PT-01b and PT-05. **No LLM** |
| Data | O*NET 29.0 text files, loaded into SQLite by `backend/load_onet.py`; LinkedIn advert counts and sample listings from committed caches (see `data-sources.md`) |

**Why this and not the original stack.** The proposal named Node.js plus a separate Python ML microservice plus React. That's three deployable services to wire, configure and debug. With a working demo due in roughly three weeks and one developer, three services is where the time goes — into plumbing rather than into anything demonstrable. Python is the better single choice because the Kaggle data work (loading CSVs, similarity scoring) is native to it, and SQLite removes a whole class of setup problems.

**If asked why the demo is a monolith:** because iteration speed matters more than separation at this stage, and the module boundaries are preserved in code so the ML component can be extracted into its own service without rework. That's a real answer, not an excuse — keep the boundaries clean enough that it stays true.

## Production architecture (what gets documented)

The original design stands as the target: Node.js or Python API, React frontend, a separate Python ML microservice that can scale independently of the request path, and an external job/opportunity data feed. Document it in the proposal; don't build it by October.

## The data spine

Both built modules run off one structure, which is why they're the right pair to build:

**This is the schema as built** (17 September). It differs from the sketch this
file originally carried, because the sketch predated knowing what was in the data:

```sql
occupations         (soc_code PK, title, description, job_zone, source_dataset)
skills              (element_id PK, name, description, source_dataset)
occupation_skills   (soc_code, element_id, importance, importance_scale_max,
                     source_date, PK(soc_code, element_id))
related_occupations (soc_code, related_soc_code, tier, sort_index)
job_zone_reference  (zone, name, experience, education, training, examples, svp_range)
occupation_tasks    (soc_code, task_id, task, task_type, importance, source_date,
                     PK(soc_code, task_id))   -- added 30 September, ADR-0007
occupation_alt_titles (soc_code, title, short_title)          -- ADR-0009
occupation_technology (soc_code, example, category, hot, in_demand) -- ADR-0009
occupation_tools    (soc_code, example, category)             -- ADR-0009

-- "What employers ask for" (ADR-0017), from Kaggle LinkedIn job postings.
-- Counts only: no advert text, companies or links are stored.
advert_summary      (soc_code PK, adverts, level_n, entry_level, years_n, years_median,
                     listed_from, listed_to, source_dataset)
                     -- level_n added 8 October: beginners are counted over adverts that state a level
advert_counts       (soc_code, kind, item, n, PK(soc_code, kind, item))
                     -- kind: 'skill' | 'tool' | 'software' | 'req'
advert_titles       (soc_code, title, n)       -- normalised advert titles, acronyms kept
advert_baseline     (kind, item, n)            -- the same counts over all linked adverts

-- "Jobs for you" (ADR-0022): the 20 newest linked adverts per occupation, as
-- features only (no advert text, company, link or pay). Lists are comma-separated.
advert_listings     (advert_id PK, soc_code, title, location, work_type, level, years,
                     reqs, skills, tools, listed)

occupation_interests (soc_code, area, score, source_date, PK(soc_code, area))
                     -- the six RIASEC interest scores per job, for the quiz (ADR-0011)

users               (profile_id PK, profile_type, target_soc_code, created_at,
                     display_name, plan_code UNIQUE)   -- ADR-0008
user_skills         (profile_id, element_id, status, updated_at,
                     PK(profile_id, element_id))  -- status: 'held' | 'learning'
saved_occupations   (profile_id, soc_code, saved_at, PK(profile_id, soc_code))  -- ADR-0010
progress_events     (profile_id, at, kind, element_id, status, soc_code,
                     skill_count, goal_have, goal_total)   -- dated progress, ADR-0012
```

*Checked against the built database on 18 November.* The advert tables and
`advert_listings` are optional: without them, those screens hide or say the data
isn't loaded.

What changed from the sketch, and why — the reasoning is in `dev-guide.md`:

- **Invented integer ids became SOC codes.** O*NET keys everything on them; our own
  ids would have added a mapping layer for nothing.
- **`skills.category` dropped.** No source data supplies one.
- **`user_skills.level` dropped.** Capture is "do you have this skill", which is
  all the gap needs.
- **`user_skills.status` added (30 September, ADR-0005).** It's either `held`
  or `learning`, for the "My plan" dashboard's progress tracking. Only `held`
  counts toward a gap, pathway or recommendation. It is still not a proficiency
  level. It just separates "I can do this" from "I'm working on it".
- **`job_zone` added to occupations**, and `related_occupations` / 
  `job_zone_reference` added outright. Neither existed in the sketch because
  neither dataset behind it had the data. O*NET does, and they are what make FR-1's
  pathway ordering and FR-3's non-degree routes possible.
- **`importance` stores O*NET's raw 1–5 rating** rather than an essential/desirable
  boolean, so the threshold stays a query-time decision.

A gap is `occupation_skills` for the target minus the `held` rows of `user_skills`. A pathway walks
`related_occupations` in its expert-review order. One structure, two modules —
that is the whole reason this pair is cheap to build together.

The `source_dataset` / `source_date` columns exist so the system can show where
every record came from. That directly answers the data-provenance concern behind
the Kaggle rule (see FR-4 in `functional-requirements.md`). Note that `source_date`
sits on `occupation_skills` rather than `skills`: O*NET dates the *rating*, and
those dates genuinely span 2010 to 2024 (checked 4 October; an earlier version of this line said 2019, which was wrong).

## Core modules

### Built for October
1. **Career Pathway Builder** (central) — the declared hub; ties profile, skills and target into an ordered path.
2. **Skills gap analyser** — compares captured skills against the target occupation's required set.

### Built once the core landed (5 October), and extended in November
3. **CV check** (ADR-0014). Rule-based skill suggestions plus a goal score measured on a Kaggle CV benchmark (r = 0.27). Upload of PDF, Word or text is read in the browser (ADR-0023). "What to add" advice draws on the advert counts (ADR-0024), and "Jobs your CV points to" puts the CV's skills through the skill-matching model (ADR-0025). The CV is never stored.
4. **What employers ask for, and Jobs for you** (ADR-0017, ADR-0022). This stands in for *opportunity matching*: the only real advert data on Kaggle is American and expired (March–April 2024). The module summarises what employers asked for and shows real adverts as job cards ranked by fit, always labelled as sample listings, not jobs to apply to.
5. **Interview practice** (ADR-0015, ADR-0024). Skill, tool and task questions with checklist feedback and retry. Not a chatbot, because there's no LLM in the build.

### Where the skill-matching model runs (ADR-0025)
- *For you* recommendations (FR-06), with the reasons for each.
- The order of the Pathway's steps (FR-08).
- "Jobs your CV points to", from the skills a CV shows.
- "Jobs with the closest skills" on a job page, job against job.
- The "How we matched you" panel, which shows its numbers step by step.

Each place carries a "Skill-matching model" tag. The interest quiz uses a
separate, simpler matcher (Pearson correlation over six RIASEC scores).

*As first planned (September):* build two, specify three. Modules 3–5 were added after the core was finished, each in a reduced form that's stated plainly. Say clearly in the presentation what each one is and isn't. Claiming more than is built is the fastest way to lose the room.

## Decisions settled since this file was first written

- **No LLM.** Every feature runs on measured, explainable rules and the skill-matching model.
- **No accounts:** a six-character plan code (ADR-0008). Real auth is production scope.
- **Hosting:** the laptop is the main path. A minimal Fly.io deploy exists as a safety net (`deploy.md`, ADR-0021).
