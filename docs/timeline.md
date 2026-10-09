# Timeline

Solo developer. The proposal describes a Feb–Nov 2026 seven-phase plan; that stays in the written document as the project's formal schedule. What follows is the real working plan from today, which is what actually needs executing.

## Fixed point — confirmed 9 October

**Prototype presentation: Saturday 24 October 2026.** That's 15 days from 9
October, worked around a full-time job. The plan for those days is at the end
of this file. *The paragraph below is the original September estimate, kept
for the record.*

**Presentation: beginning of October 2026, with a working demo expected.** From 10 September that is roughly three weeks, worked around a full-time job.

**Confirm first, before anything else:** the exact date, and what "working demo" means to him — a local run on your laptop, or a deployed URL. A demo due 1 October rather than 7 October is a quarter of the available time, and "deployed" adds a workstream that "local" doesn't. This one question changes the plan below more than any other decision, so ask it this week.

## Three-week plan *(superseded 17 September — see the revision below)*

### Week 1 — 10 to 17 September: data and requirements
Nothing gets built on unverified data. This week is about removing that risk and locking the requirements.

- Confirm the presentation date and demo expectations with the lecturer
- Open each shortlisted Kaggle dataset, record real columns and row counts in `data-sources.md`
- Settle on the role↔skill dataset that becomes the spine; discard the rest for now
- Load it into SQLite against the schema in `architecture.md`; adjust the schema to the data rather than forcing the data into the schema
- Draft FR-5 onward and finalise the full list of 10+

Gate: real data queryable in SQLite, and 10+ requirements written. Do not start week 2 without both.

### Week 2 — 18 to 24 September: build the core
- FastAPI service over the SQLite spine
- Skills gap analyser first — it's the simpler of the two and the pathway builder depends on the same queries
- Career Pathway Builder on top of it
- Minimal React UI: profile capture, target selection, gap view, pathway view

Gate: the demo path runs end to end, ugly but working. Ugly and working beats polished and partial.

### Week 3 — 25 September to 1 October: demo-ready
- Seed a believable demo user for each of the two profile types, so the story lands
- Add the source-dataset labels for FR-4 — small, visible, and it pre-empts the provenance question
- Tighten only the screens that appear in the demo; leave the rest
- Build the slides directly from the 10 requirements
- Rehearse the Q&A: for each requirement, say it out loud, then answer the question it invites

Gate: run the whole demo start to finish without touching code. Twice.

## After October

Build-out to November: the CV scorer, then opportunity matching if the job postings data proves usable. Both are specified in the proposal regardless of whether they get built.

## Slippage rule

If week 1 runs over, cut scope, not the gates. One module demoed properly with data you can account for beats two half-modules and a question you can't answer.


---

# Revised plan — 17 September

Week 1 closed with the data gate met and the requirements gate not. Assuming the
presentation falls in the **first week of October, planned against 1 October** —
if it lands later that becomes slack rather than a reason to add scope.

## The real budget

14 calendar days, but the working time is **4 full days (two weekends) plus ten
evenings**. Roughly six to seven effective days. The original plan assumed more
than exists, so this is what fits.

## What gets cut, now rather than later

- **RIASEC interest intake is dropped from the demo.** It is the most interesting
  unbuilt thing here and it is still the right answer for the school-leaver, but
  it is a whole screen plus a matching algorithm. The school-leaver browses by Job
  Zone instead — Zones 1–3 are 59% of the catalogue and that is a real answer.
  Specify RIASEC in the proposal; say plainly it is designed and not built.
- **Target selection is a search box, not a browse experience.** 879 occupations
  with a filter by Job Zone. Nothing clever.
- **No polish on anything off the demo path.**

## Day by day

**Fri 18 — decide.** FR-3 capture approach. One decision, unblocks everything.

**Sat 19 / Sun 20 — the API.** FastAPI over `saycep.db`: occupations, skills,
profiles, gap, pathway. Verified against real rows before any UI exists. This is
the half that must not slip, because the frontend has nothing to show without it.

**Mon 22 – Fri 25, evenings — FR-5 onward.** Six requirements, the other half of
the Week 1 gate. Yours; nothing on the build side unblocks them. Evenings are the
right slot because drafting does not need a long run of time.

**Sat 26 / Sun 27 — the frontend.** Four screens: capture, target, gap, pathway.
Ugly and working. If a screen is not on the demo path it does not get built.

**Mon 28 – Tue 29, evenings — make it demoable.** Two seeded users, one per
profile type, so the story lands. FR-4 provenance labels — cheap, visible, and
they pre-empt the data question.

**Wed 30 / Thu 1 — slides and rehearsal.** Slides built from the ten
requirements, not from the code. Then run the demo start to finish without
touching code. Twice.

## The gate that matters now

There is only one: **on 29 September the demo path runs end to end.** If it does
not, the remaining time goes to making one module demo properly rather than two
half-working. One module demoed well with data you can account for beats two
half-modules and a question you cannot answer.

## Known risk

The frontend is the riskiest item, and it sits on the last weekend. Mitigation:
React from a CDN in a single HTML file served by FastAPI — no npm, no build step,
no toolchain to debug at 11pm on 27 September. Still React, still honest in the
proposal, and it removes a category of problem rather than solving one.

---

## Final run-in — 9 to 24 October *(added 9 October, when the date was confirmed)*

The build is done: five modules, accessibility, 155 tests. What's left is
mostly the project owner's assessed work, plus hosting. **The code freezes on
the evening of Wednesday 21 October.** After that, only fixes to things that
break the demo.

| When | Claude | You |
|---|---|---|
| **Fri 9 – Sun 11** | Build the hosting (`plans/hosting.md`). Fix the CV scanner's "Canes" bug and re-measure, because that figure is quoted. | Rotate the Kaggle token. Make a Fly.io account. The 20-minute setup with me on Sat or Sun. Start drafting FR-11 onward. |
| **Mon 12 – Fri 16** | Pressure-test each requirement as you send it; close any gap between what a requirement promises and what's built. | Finish the requirements for everything after FR-10. Book one first-time user for a ten-minute test. |
| **Sat 17 – Sun 18** | Turn the user test into NFR-02 evidence. | Run the user test. Draft the slides. **Gate:** the demo script runs end to end on the live link, twice, without touching code. |
| **Mon 19 – Wed 21** | Fixes only. **Freeze on Wed evening.** | Rehearse with the slides. |
| **Thu 22** | Keep the site awake from now until after the presentation (one line, about $0.30). | Full dress rehearsal on the live link, timed. |
| **Fri 23** | Check that the live site and the laptop fallback both work. | Rest. Charge the laptop. |
| **Sat 24** | — | Open the site 15 minutes before. Present. |

**If something slips, cut in this order:** hosting goes first (present from
the laptop, which is already rehearsed), then the user test. The requirements
and the rehearsal can't be cut.
