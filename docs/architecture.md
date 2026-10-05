# Architecture

There are two architectures in this project and keeping them distinct matters: the one being **built for the October demo**, and the one **documented as the production design**. They are deliberately different, and being able to explain why is worth marks.

## Demo architecture (what gets built)

One service. One database file. One frontend.

| Layer | Choice |
|---|---|
| Backend | Python (FastAPI) — single service |
| Database | SQLite (file-based, no server to run) |
| Frontend | React |
| AI features | LLM API called from the backend |
| Data | O*NET 29.0 text files, loaded into SQLite by `backend/load_onet.py` (see `data-sources.md`) |

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
advert_summary      (soc_code PK, adverts, entry_level, years_n, years_median,
                     listed_from, listed_to, source_dataset)
advert_counts       (soc_code, kind, item, n, PK(soc_code, kind, item))
                     -- kind: 'skill' | 'tool' | 'software' | 'req'
advert_titles       (soc_code, title, n)       -- normalised advert titles
advert_baseline     (kind, item, n)            -- the same counts over all linked adverts

users               (profile_id PK, profile_type, target_soc_code, created_at,
                     display_name, plan_code UNIQUE)   -- ADR-0008
user_skills         (profile_id, element_id, status, updated_at,
                     PK(profile_id, element_id))  -- status: 'held' | 'learning'
```

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

### Built once the core landed (5 October)
3. **CV scanner** (ADR-0014). It's rule-based skill suggestions plus a goal score measured on a Kaggle CV benchmark. The CV is never stored.
4. **What employers ask for** (ADR-0017). This stands in for *opportunity matching*: the only real advert data on Kaggle is American and expired (March–April 2024), so the module summarises what employers asked for, not jobs to apply to.
5. **Interview practice** (ADR-0015). Rule-based feedback, not a chatbot, because there's no LLM in the build.

*As first planned (September):* build two, specify three. Modules 3–5 were added after the core was finished, each in a reduced form that's stated plainly. Say clearly in the presentation what each one is and isn't. Claiming more than is built is the fastest way to lose the room.

## Decisions still open

- Which LLM API/provider (and whether the demo needs it at all — the two built modules may not)
- Auth for the demo: proposed as none — a profile is a row with an id. Reasoning in `plans/api-first-slice.md`. Real auth is production scope.
- Hosting: local for the demo unless he requires a live URL — worth confirming.
