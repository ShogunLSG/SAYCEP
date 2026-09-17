# Plan — the data spine

**Status:** ✅ executed 17 September. Loader built, run and verified.
**Decision this implements:** ADR-0003 — O*NET 29.0 as the spine.
**Supersedes:** the hybrid plan of earlier today, superseded before any code.
**Gate it serves:** Week 1 — real data queryable in SQLite.

## What we're loading

From `emarkhauser/onet-29-0-database` on Kaggle. Structure confirmed against
O*NET's published data dictionary, so the numbers below are known, not hoped for.

| File | Rows | Used for |
|---|---|---|
| `Occupation Data.txt` | 1,016 | The occupation catalogue |
| `Skills.txt` | 61,530 | Skill importance per occupation — FR-2 |
| `Job Zones.txt` | 923 | Preparation level 1–5 — FR-3 |
| `Related Occupations.txt` | 18,460 | Ordered pathway steps — FR-1 |
| `Content Model Reference.txt` | — | Skill names and IDs |
| `Job Zone Reference.txt` | 5 | Zone descriptions for the UI |

`Interests.txt` (RIASEC) is left for a later plan. It serves school-leaver intake,
which is a screen, not the spine.

## Step 0 — get the files ✅ done 11 September

Downloaded and extracted to `backend/data/onet/` — 41 files, 97 MB uncompressed.
`backend/data/` and `docs/Datasets/` are both gitignored; third-party data doesn't
belong in the repo and the loader rebuilds the database from the files anyway.

## Step 1 — load it, verify the counts

No spike this time. The hybrid needed one because its join was unproven; here
every file keys on the O*NET-SOC code and there is nothing to prove. So Step 1 is
the real loader, not throwaway code.

One command rebuilds `saycep.db`. Idempotent — drops and recreates, no migrations,
because the CSVs on disk are the source of truth.

Two things it must do that are easy to get wrong:

**Handle the quality flags correctly — and they are not where this plan first
assumed.** Checked against the real file:

- `Recommend Suppress` is **never `Y` on an IM row** — 0 of 30,765. All 124
  suppressed rows are LV. Filtering importance rows on this flag is a no-op.
- `Not Relevant` is **`n/a` on every IM row**; it is carried on the LV row of the
  pair. So excluding not-relevant skills means joining to the LV row, not
  filtering the IM row. 3,302 pairs are affected.
- Every one of those 3,302 has an importance of **2.0 or below** — so any
  threshold above 2.0 excludes them anyway. Apply the filter regardless, because
  correctness shouldn't depend on the threshold staying where it is today.

**Keep only `Scale ID = 'IM'` for importance.** Each skill appears twice per
occupation, once as IM (importance) and once as LV (level). They answer different
questions. The gap analyser wants importance.

**Row counts verified 11 September** — all four match the published dictionary
exactly: 1,016 / 61,530 / 923 / 18,460, with IM and LV pairing at 30,765 each.

**The usable catalogue is 879 occupations, not 1,016.** That many are complete
across occupations, skills, job zones and related-occupations. The 137 without
skills data must be excluded from target selection or the gap analyser will have
nothing to say about them.

## Step 2 — schema

```
occupations       (soc_code PK, title, description, job_zone,
                   source_dataset, source_date)
skills            (element_id PK, name,
                   source_dataset, source_date)
occupation_skills (soc_code, element_id, importance, importance_scale_max,
                   PRIMARY KEY (soc_code, element_id))
related_occupations (soc_code, related_soc_code, tier, sort_index)
job_zone_reference  (zone, name, education, experience, training)

users             (id, profile_type, target_soc_code)
user_skills       (user_id, element_id)
```

Deviations from `architecture.md`, and why:

- **The SOC code is the primary key throughout**, replacing invented integer ids.
  It is stable, it is the join key across every O*NET file, and it is citable in
  the UI. Inventing our own ids on top would add a mapping layer that buys
  nothing.
- `skills.category` dropped — as before, nothing supplies one. O*NET's Content
  Model has a hierarchy we could derive one from later if a requirement asks.
- `occupations` gains `job_zone`, denormalised from `Job Zones.txt`. One integer,
  needed on nearly every query that serves the school-leaver profile.
- `occupation_skills.importance` is O*NET's `Data Value` on the IM scale, stored
  raw. `importance_scale_max` stores the scale ceiling alongside it so the UI can
  render "4.2 out of 5" without hardcoding a 5 somewhere it will later be wrong.
- **`importance` is stored, not the essential/desirable label.** The label is
  derived at query time from your threshold. Storing the raw rating means changing
  your mind about the threshold is a config change, not a reload — and it means
  the screen can show the rating next to the label, which is a much better answer
  to "why is this one essential?"
- `related_occupations.sort_index` is O*NET's `Index`, its expert-review ordering.
  Preserved exactly; it is what makes FR-1's step ordering defensible.
- `user_skills.level` dropped. Capture is "do you have this skill", which is what
  the gap needs.

## Step 3 — the gap query

Skills for the target occupation, minus the user's, labelled essential or
desirable by your threshold, ordered by importance descending. One query. If it's
awkward to write, the schema is wrong and the schema changes.

## Step 4 — the pathway query

`Related Occupations.txt` gives ordered neighbours. A pathway from where the user
is to a target is a walk across that graph, and FR-1 promises no fewer than three
intermediate steps, each naming skills to acquire.

**Resolved 17 September — no second pass needed.** The concern was whether a
clean three-step walk exists across the graph. It does, everywhere: **all 879
occupations have three or more reachable primary neighbours**, so FR-1's "no fewer
than three intermediate steps" is satisfiable for every occupation in the
catalogue. The Job Zone fallback is not required.

Two properties worth knowing: 1,189 related-occupation rows (6.8%) point outside
the usable catalogue and are dropped by the join, which is why a pathway's
expert-review indices can start at 2 rather than 1. And 436 of 879 occupations
have at least one primary neighbour in a *higher* job zone — upward progression
exists for about half the catalogue, which matters when the pathway needs a
direction.

## Open — yours to decide, after Step 1

**The essential/desirable threshold, on O*NET's importance scale.** This is still
your design decision and I'm still not making it. What's changed is that you now
get to make it against a published survey instrument rather than a proxy you'd
have to defend from first principles.

Once loaded I'll show you the distribution of importance ratings so you can pick a
cut where the data actually separates. "Above 3.5, because that's where the
distribution splits and O*NET's scale anchors describe it as important to the
occupation" is an answer that survives follow-up. "Above 3.5 because it seemed
reasonable" is not.

## What could go wrong

- **The Kaggle copy is incomplete or an older version.** Row counts in Step 1
  catch it. Fallback: O*NET publishes the database directly, but that's a
  non-Kaggle source and would need raising with your lecturer first — do not
  reach for it without asking.
- **The related-occupations graph doesn't yield three-step paths.** Covered above;
  Job Zone ordering is the fallback.
- **1,016 occupations is a lot to browse.** A target-selection screen listing all
  of them is unusable. Likely needs search or filtering by Job Zone — a UI problem
  for the frontend plan, noted here so it isn't forgotten.

## Not in this plan

React screens, RIASEC intake for the school-leaver profile, and demo seed users.
Each depends on this landing first and gets its own plan.
