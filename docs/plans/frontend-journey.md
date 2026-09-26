# Plan — the frontend journey

**Status:** building, 26 September. Design approved via the click-through
mockup; the decisions below are the ones the mockup did not settle, recorded
rather than re-asked.
**Depends on:** the API (`backend/app.py`), built 20 September.
**Gate it serves:** the demo path runs end to end.

## The journey

Five screens, one at a time, a segmented progress bar and a single button at
the bottom — the pattern modern career and learning apps share. Five is the
cap NFR-02 sets.

| Step | Screen | Requirements |
|---|---|---|
| 1 | Where are you starting from? | FR-01 |
| 2 | What can you already do? — all 35 skills | FR-02 |
| 3 | Pick a target — tabs: For you · Browse · Search | FR-03, FR-04, FR-05, FR-06 |
| 4 | What's missing? | FR-07, FR-09 |
| 5 | How do you get there? | FR-08 |

## Decisions the mockup did not settle

**Target selection is real.** The mockup hardcoded Electricians. FR-03 is a
Must, so step 3 lets the user pick, three ways, on one screen so NFR-02 holds.
*For you* is the default for a school-leaver and is limited to Job Zones 1–3;
*Search* is the default for a student and is not limited.

**One endpoint is added: `PUT /profiles/{id}/target`.** FR-03's acceptance
criterion says the system records the target and replaces any previous one.
None of the seven specified endpoints can do that without a GET that writes,
which is worse than an honest eighth endpoint.

**The profile is created when the user leaves step 2.** Going back and changing
skills creates a fresh profile rather than mutating the old one. Profiles are
ephemeral in the demo, as the proposal already states.

**One database connection per request.** The API shared a single SQLite
connection across FastAPI's worker threads. Harmless under a scripted test,
unsafe when a browser fires two requests at once — which step 3 does.

**Served by FastAPI, same origin.** `/` returns the app; the API keeps the
paths the proposal documents. No CORS, no second server to start.

**React from CDN, no build step,** as the proposal's Q3.1 describes. JSX is
replaced by `htm` tagged templates so nothing needs compiling.

## Known risk

**The CDN needs internet on demo day.** If the room has no connection the page
loads blank. Mitigation, not yet done: vendor the three library files (~150 KB)
into `frontend/vendor/`. Worth doing before the presentation.

## Not in this plan

Gamification polish (see `BACKLOG.md`), RIASEC intake, the three specified-only
modules.
