# Plan — the data spine

**Status:** awaiting your approval. Nothing built yet.
**Decision this implements:** hybrid spine — occupation catalogue from
`formatted_jobs.csv`, skills and their importance from `resume_data.csv`.
**Gate it serves:** Week 1 — real data queryable in SQLite.

## Why hybrid

Neither dataset works alone.

`formatted_jobs.csv` has a clean occupation catalogue — title, description,
industry, pay grade — which is what the target-selection screen needs to look
like something. But its skills field has no delimiter and it holds roughly one
row per occupation, so essential-vs-desirable cannot be computed from it.

`resume_data.csv` has 9,544 rows with skills as parseable lists of concrete
competencies. Grouped by role, the share of resumes mentioning a skill *is* the
essential/desirable signal FR-2 needs. But it has no occupation catalogue.

Each supplies what the other lacks. The cost is a join, and the join is the risk.

## Step 0 — get the files (blocked on you)

Kaggle requires a login to download, and signing in is not something I can do on
your behalf. Either sign in at kaggle.com in the browser pane and tell me, or
download both files yourself and drop them in `backend/data/raw/`:

- `formatted_jobs.csv` (177 kB)
- `resume_data.csv` (17 MB)

`.gitignore` gets a `backend/data/raw/` entry — 17 MB of third-party CSV does not
belong in the repo, and the loader rebuilds the database from scratch anyway.

## Step 1 — prove the join, before anything else

Throwaway script, deleted afterwards. It answers one question: **how many
occupations end up with enough resumes behind them to compute a percentage?**

1. Confirm `resume_data.csv` actually has a role/job-title column. I have seen 10
   of its 35 columns and this one is unconfirmed. If it does not exist, this plan
   is dead and we fall back to a resume-only spine.
2. Normalise both title fields — lowercase, strip punctuation and extra
   whitespace, drop seniority prefixes (senior/junior/lead).
3. Exact-match, then count. For each occupation, how many resumes matched?
4. Report the distribution: occupations with ≥50 resumes, ≥20, ≥10, ≥5, 0.

**Go/no-go: at least 30 occupations with 20 or more resumes each.**

That number is the demo, not the dataset. Thirty well-covered occupations is a
catalogue a user can browse and a marker can poke at; an occupation backed by
three resumes produces percentages that mean nothing and will not survive the
question "how confident is that?". If we clear the bar, **the occupation
catalogue is restricted to occupations that cleared it** — a smaller honest
catalogue beats 970 occupations where most are hollow.

If we miss the bar, we stop and reconsider rather than patching with fuzzy
matching. Fuzzy joins are where a day disappears.

## Step 2 — schema

`architecture.md` says to adjust the schema to the real columns rather than force
the data to fit. Concretely:

```
occupations       (id, title, description, industry, pay_grade,
                   source_dataset, source_date)
skills            (id, name, source_dataset, source_date)
occupation_skills (occupation_id, skill_id, resume_count, resume_share,
                   importance)
users             (id, profile_type, target_occupation_id)
user_skills       (user_id, skill_id)
```

Changes from the documented schema, and why:

- `skills.category` dropped — nothing in either dataset provides one. A column we
  would have to invent values for is worse than no column.
- `occupations` gains `industry` and `pay_grade` because the jobs dataset has them
  and the selection screen can use them for filtering.
- `occupation_skills` gains `resume_count` and `resume_share`. `importance` stays
  as the essential/desirable label, but the raw numbers sit beside it so the
  classification can be *shown*, not just asserted. When asked "why is this
  essential?", pointing at 340 of 400 resumes is a better answer than pointing at
  a label.
- `user_skills.level` dropped for now — capture is "do you have this skill",
  which is what the gap needs. Add it back if a requirement asks for it.

**FR-4 gets more interesting here.** In the hybrid, occupation records and skill
records genuinely come from different datasets. The provenance labels stop being
decoration and start being informative — the screen can honestly show that a role
came from one source and its skill profile was derived from another.

## Step 3 — loader

One command, rebuilds `saycep.db` from the two CSVs. Idempotent — drops and
recreates, no migrations, because the source of truth is the CSVs on disk.

Skills are parsed from the resume lists with `ast.literal_eval`, then normalised:
lowercase, trim, collapse obvious duplicates (`Machine Learning` / `machine
learning`). Expect a long tail of near-duplicates; the first pass keeps them and
we look at the actual list before deciding how hard to normalise. Over-merging
skills early is harder to undo than leaving them apart.

## Step 4 — the gap query

The whole point of the pair, and it should be one query: skills for the target
occupation, minus the user's skills, labelled by importance and ordered by
`resume_share` descending. If that query is awkward to write, the schema is wrong
and we fix the schema.

## Open — yours to decide, after Step 1

**The essential/desirable threshold.** `functional-requirements.md` names this as
the design decision you own, and it is the question FR-2 invites, so I am not
picking it. But you should pick it *with the distribution in front of you* rather
than in the abstract — Step 1 gives you that. A threshold you chose because the
data clusters a certain way is defensible; 50% chosen because it is a round
number is the answer that invites a follow-up you cannot win.

## What could go wrong

- **No role column in the resumes.** Plan dies at Step 1.2, fall back to a
  resume-only spine. Cost: half a day.
- **Join too thin.** Fewer than 30 occupations clear the bar. Same fallback.
- **Resume skills are heavily tech-biased.** Likely, looking at the samples. This
  narrows the believable demo to technology occupations, and it collides with the
  school-leaver profile who needs trade routes. Worth knowing early; may need
  saying out loud in the presentation rather than hidden.

## Not in this plan

The React screens, the pathway step-ordering logic, and the demo seed users all
depend on this landing first. Separate plans once the spine is real.
