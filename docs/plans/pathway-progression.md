# Plan — a Pathway that reads as progression

**Status:** proposed, not built. Written 20 November after the final
presentation's rehearsal, for approval afterwards.
**Depends on:** `pathway.py` (FR-08), `related_occupations`, `Job Zones`.
**Gate it serves:** a route that a marker reads as "junior → target" rather than
"three unrelated jobs".

## The problem

The Pathway is built from O*NET's *primary related occupations* for the target,
ordered by closeness to the user's current skills (`pathway._rank_by_closeness`).
That is defensible — "reachable first" — but on screen it can read as lateral
jumps:

- Industrial Machinery Mechanics → *Millwrights → Mobile Heavy Equipment
  Mechanics → Maintenance Workers, Machinery → Industrial Machinery Mechanics*.
- Install → Electricians → *Helpers--Electricians → Electrical/Electronics
  Repairers (Powerhouse) → Electrical/Electronics Repairers (Commercial) →
  Electricians*. Two of those steps share a near-identical title.

Related occupations have mean cosine 0.987–0.996 to each other, so every step is
genuinely close in skill space. The order is by *the user's* fit, not by
preparation or seniority. O*NET's related list means "similar work", not
"prerequisite work".

## What the data already gives us

O*NET's `Job Zones` grades every occupation 1–5 by preparation required, and it
is already loaded (`occupations.job_zone`). The related lists already contain
lower-zone roles. For Electricians (zone 3):

```
zone 2  Helpers--Electricians
zone 2  Electrical Power-Line Installers and Repairers
zone 2  Electrical and Electronic Equipment Assemblers
zone 3  Electric Motor, Power Tool, and Related Repairers
zone 3  Electrical/Electronics Repairers, Powerhouse, Substation, and Relay
zone 3  Electrical/Electronics Repairers, Commercial and Industrial Equipment
zone 3  Boilermakers
```

So the "junior roles" are present. The missing piece is **ordering by
preparation**, not new data.

## Options

### A. Zone-ascending ordering (recommended)

Sort the candidate related occupations by `job_zone` ascending, then by closeness
to the user; take the first three. The route then climbs from the lowest
preparation level present to the target.

- **Changes:** step order and often step titles for every target; the
  `closeness` values on the screen; `ordering_basis` wording; `docs/presentation.md`
  §3 numbers; `demo_walk.js` (it checks step titles and counts).
- **Keeps:** Kaggle-only data, no schema change, FR-08's membership (still
  O*NET's related occupations).
- **Risk:** Job Zone is *preparation required*, not *seniority*. A zone-2
  machine operator is not necessarily a junior version of a zone-3 mechanic.
  Some routes would climb through a role that is only loosely related.
- **Wording it forces:** "progressively more preparation", not "junior to
  senior". FR-08's acceptance criterion already allows this — it asks for steps,
  not for a promotion ladder.

### B. No-step-down rule

Keep ordering by closeness, but require each step's zone to be ≥ the previous
step's (filter, then fill). Prevents a route that dips in preparation, but does
not force a climb from the bottom; routes can stay lateral at zone 3.

- **Changes:** fewer routes, and only the ones that already happen to climb.
- **Risk:** can leave fewer than three viable candidates; needs a fallback (the
  current behaviour), which reintroduces the lateral case silently.

### C. Curated "junior role" table (not recommended without approval)

A new table mapping each target to named junior roles ("Electrician's mate",
"Apprentice electrician"), written by us.

- **What it would change:** route titles become recognisable; the demo reads
  best.
- **Why it is a problem:** it is invented data, and the course rule is
  Kaggle-only (ADR-0002). It would also break FR-09's provenance claim — the
  screen says every record comes from O*NET with a date, and these would not.
  It needs the lecturer's approval in person, and a visible "curated, not
  O*NET" label if approved.
- **Verification before building:** none possible — there is no source to check
  it against, which is exactly the property that made the TVET/SETA dataset
  unusable.

### D. A Kaggle career-progression dataset

Search Kaggle for role ladders with a real source. If one verifies (columns,
row counts, provenance), it could replace C honestly. Unknown until opened; the
last five datasets were verified before anything was built, and two were
unusable.

## Recommendation

Build **A**, and measure it before shipping:

1. For all 879 targets, compute the route under the current order and under A.
2. Report: share of routes whose zone sequence is non-decreasing (before/after);
   mean closeness of step 1 and of the target; how many routes still have three
   distinct titles.
3. Check the demo profile specifically: Thabo → Electricians must still produce
   three steps, and its gap must be unchanged.
4. Update `presentation.md` §3 and `demo_walk.js` in the same change — the script
   is the contract for the numbers.

If A makes step 1 materially less close to the user (a real trade-off: reachable
first vs. climb first), consider a blend: prefer a rising zone, break ties by
closeness, and never step down more than one zone.

## What this deliberately does not do

- It does not add data. The junior roles are already in O*NET's related lists
  and Job Zones.
- It does not change the gap, readiness, recommendations or the model.
- It does not claim a role "leads to" another. O*NET says they are related; the
  plan's wording must stay inside that.
- It does not relabel routes as training paths. The limitation stands: the route
  names roles, not courses or qualifications.

## Not in this plan

- South African qualification routes (needs non-Kaggle data, approval).
- Salary or demand data.
- Any change to `related_occupations` itself.

---

## Implemented 20 November 2026

The route was producing nonsense: with **Helpers--Electricians** (zone 2) as the
target, it climbed to **Electricians** (zone 3) and came back down to the helper
role. Measured over 879 targets with a neutral profile: **260 routes contained a
step more senior than the target**, and 50 targets had fewer than three related
jobs at or below their own zone.

### The rule now in `pathway._sequence`

1. A step may not be more senior (higher Job Zone) than the target.
2. The first step is the closest related job to the user; each later step must
   be at least as senior as the one before, so the route never steps down.
3. If fewer than three such jobs exist, the rule relaxes one level (then two)
   and `zone_fallback` says so in the API response.

The stricter "all zone 2 before any zone 3" version was measured and rejected:
it replaced the Electricians route's repair roles with an assembler at 0.20.
Closest-first plus no-step-down keeps the good route and still forbids descent.

### After

- **813** of 879 routes: no relaxation, no senior step, no step down.
- **49** targets relax one level, **1** relaxes two, **16** cannot climb and keep
  the closest jobs (`zone_fallback: null`). Those 50 account for the only
  remaining more-senior steps; the 16 for the only step-downs.
- **0** routes have fewer than three steps.
- The demo route is unchanged: Helpers--Electricians (0.57) ? Powerhouse
  Repairers (0.56) ? Commercial Repairers (0.52) ? Electricians (0.48).

### Same-level branches (ADR-0033)

Each level's other related jobs are listed once, under the first step of that
level, as `also_at_level` (max 5, with their zone), and are tappable. They are
alternatives, not part of the ordered climb, so the route no longer presents
same-zone jobs as sequential hops.
