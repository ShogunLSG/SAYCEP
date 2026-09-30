# Plan: from a five-screen journey to an app you live in

*Written 30 September 2026. Status: **built 30 September** — all six slices plus the plan-code sign-in; 98 tests pass; screenshots in `docs/screenshots/v3/`.*

**Decisions (30 September):** Assignment 3 is submitted as it stands. All six
slices are built, in order. The interest quiz is our own short questions,
labelled as a simplified version of O\*NET's Interest Profiler. The demo date
isn't known yet, so every slice is pushed demoable.

**One structural change to the frontend, said up front:** `app.js` is 774
lines and would pass 2,000. It is split into plain script files that share
globals (`app.js` for shared pieces and the journey, one file per tab, and
`main.js` last to mount). There's still no build step and no new dependency.

## The problem

The build already has more than five screens: the journey, the job panel and
the *My plan* dashboard. It still **feels** like a five-page wizard with a
page at the end, because:

- There is no navigation. You can only go forward and back.
- Everything outside the journey is reachable only from inside it. You can't
  just go and explore jobs, or look at your skills.
- Things are shallow. A job is a panel, and a skill is a chip.
- Nothing accumulates. There's no history, no saved jobs and no comparison.

An app feels like an app when it has **places** (tabs you move between),
**things with depth** (a job page, a skill page), and **state that grows**
(saved jobs, a progress history). This plan adds those, and every piece of it
uses data we already have or can load from the same Kaggle O\*NET download.

## Shape of the app

```
First visit ──► the five-screen journey (unchanged; NFR-02 holds)
                    │ Save as my plan
                    ▼
     ┌───────────── bottom tab bar ─────────────┐
     │  Home    │  Explore   │  Skills  │   Me   │
     └──────────────────────────────────────────┘
 Home     My plan dashboard (built), plus a progress history
 Explore  search · browse · for you · interest quiz → job pages → compare
 Skills   my skills (have / learning / not yet) → skill pages
 Me       profile type, goal, printable plan, start over
```

The journey stays exactly as it is, and it becomes the onboarding. That keeps
NFR-02 true and the demo script intact. The tabs appear once a plan is saved.

## Sign-in: a welcome screen and a plan code *(added 30 September, built with slice 1)*

You asked for a login page. Real accounts were weighed and rejected for now.
Assignment 3 lists accounts as out of scope and argues that no login is needed
because nothing personal is held. Passwords would also bring hashing, sessions
and POPIA into the demo.

What we're building instead:

- **A welcome screen** as the app's front door, with two options:
  - *Start my plan.* An optional first name, then the journey.
  - *I have a plan code.* Type the code to reopen your plan.
- **A plan code** for every saved plan, such as `K7M-2QX`. It's six characters
  from an alphabet without look-alikes (no 0/O, 1/I), which gives about 887
  million codes. It's shown on the dashboard and on the Me tab. Typing it on
  any device reopens that plan.
- **What the code is not:** a password. Anyone with the code can open that
  plan. That's acceptable only because a plan holds no personal data beyond an
  optional first name, and the screen says so.

*Schema:* `users` gains `display_name` and `plan_code` (unique). This is
ADR-0008, which extends ADR-0006.

## The features, as vertical slices, in build order

Each slice is usable and demoable on its own, so we can stop after any of them.

### 1. App shell and the Explore tab with full job pages *(medium)*

- Bottom tab bar, with the dashboard as Home.
- Explore holds For you, Browse and Search, so they're always reachable and not
  just inside step 3.
- **The job page** replaces the panel with a full screen:
  - What it is, and *A day in this job* (built).
  - Your skills against it, with ticks (built).
  - **Jobs like this.** O\*NET's expert-reviewed related occupations, which are
    already loaded and currently used only for pathways. It's one tap to walk
    the graph.
  - **Technology you'd use.** Examples from `Technology Skills.txt`, which
    covers all 879 jobs, flagged where O\*NET marks them "hot technology".
  - **Save** (slice 3) and **Make this my goal**.
- **Search that understands real job names.** `Alternate Titles.txt` has 45,963
  titles covering all 879 jobs, for example "Construction Electrician" and
  "Conduit Installer" for Electricians. Today search only matches the 879
  official titles.

*Schema:* `occupation_technology` and `occupation_alt_titles` tables (ADR).

### 2. The Skills tab and skill pages: "what does this skill unlock?" *(medium)*

- **My skills:** have, learning and not yet, all editable here instead of only
  through the journey.
- **A skill page** for each of the 35 skills. It shows what the skill is, the
  jobs where it matters most (from `occupation_skills`), and where it sits in
  your plan.
- **The unlock moment.** When you mark a skill *I can do this now*, the app
  shows what changed, for example "Troubleshooting: you now have every
  must-have for Electrical Power-Line Installers". This is computed, not
  invented: a job's readiness before versus after. It's the strongest live
  demo moment in the plan.

*Schema:* none.

### 3. Shortlist and compare *(small–medium)*

- Save jobs from anywhere, and see them on the Home tab with each one's
  readiness bar.
- Compare two or three saved jobs side by side: training needed, must-haves
  held, and shared and different skills.
- Answers the question a school-leaver actually has: "which of these is closest
  for me?"

*Schema:* `saved_occupations (profile_id, soc_code, saved_at)` (ADR).

### 4. Interest quiz, for discovery without knowing job names *(medium)*

- Around 12 quick "would you enjoy…" questions mapped to O\*NET's six interest
  areas (RIASEC). The interest scores in `Interests.txt` cover **all 879**
  jobs.
- "Jobs that fit your interests" becomes a fourth way into Explore, and it
  combines with the skill match.
- This closes a gap the project has admitted since 17 September. ADR-0004 and
  the backlog both say the school-leaver should start from interests, and
  RIASEC was deferred.
- **Caution:** the question wording is ours. O\*NET's own Interest Profiler is
  60 items. A short version is a simplification and must be labelled as one.

*Schema:* `occupation_interests` table (ADR).

### 5. Progress history *(small)*

- Home gains *Your progress*: a dated timeline ("30 Sep — Troubleshooting: can
  do now") and readiness over time, e.g. 0 of 2 → 1 of 2 → 2 of 2.
- This makes FR-11 visible as a story, not just a bar.

*Schema:* `skill_events (profile_id, element_id, status, at)` (ADR).

### 6. The Me tab and a printable plan *(small)*

- Profile type, goal, start over.
- **Print my plan.** A clean one-page version using the browser's print, to
  take to a teacher, parent or career counsellor. No new dependency.

*Schema:* none.

### Considered and deliberately left out

- **"How people got into this job"** from `Education, Training, and
  Experience.txt`. It covers only 858 of 879 jobs, and its categories are
  American qualifications (Associate's degree, GED). We already translate one
  of those in the preparation labels. Showing US percentages as if they applied
  to a South African school-leaver invites exactly the question we can't
  answer. It stays in the backlog.
- **Accounts or login, CV scorer, opportunity matching, chatbot, TVET/SETA
  links, gamification.** These are out of scope or specified-only (CLAUDE.md,
  ADR-0002, BACKLOG).

## Requirements: yours to write

FR-11 onward are yours (CLAUDE.md). This plan implies roughly these, and each
slice gives you a measurable fact for its criterion:

| Likely FR | Covers | A figure for the criterion |
|---|---|---|
| FR-11 | Progress tracking (built) | Electricians: 2 must-haves missing → 2 after *working on it* → 1 after *I can do this now* |
| FR-12 | Search by alternate titles | "Conduit Installer" returns Electricians |
| FR-13 | Related jobs on a job page | Electricians lists O\*NET's primary related occupations, in expert-review order |
| FR-14 | Shortlist and compare | Two saved jobs show readiness side by side |
| FR-15 | Interest-based discovery | A profile scoring highest on Realistic ranks Realistic-high jobs first |
| FR-16 | Progress history | Each status change is listed with its date |

My suggestion is to write FR-11 now and each of the others as its slice lands,
so no requirement is written against a feature that doesn't exist yet.

## Honest costs

- **Five schema additions**, each a load-bearing decision under CLAUDE.md. All
  are additive and none changes an existing table. Each gets an ADR and tests,
  like ADR-0005 and ADR-0007.
- **Assignment 3 describes today's build.** If it's submitted today, the demo
  will show more than the document. That's normal, and fine: say so in the
  presentation. Don't delay the submission for this.
- **Time.** Slices 1–2 are the biggest step up. Slices 3–6 are each smaller.
  I build and test each slice before starting the next, and every slice is
  pushed separately, so the demo is never in a half-built state.

## Decisions I need

1. **Submit Assignment 3 today as it stands?** I recommend yes. It's accurate
   for the system it describes.
2. **Which slices?** I recommend all six, in this order. If time is tight,
   slices 1–3 alone make it feel like an app.
3. **The demo date.** Is it known yet? It decides how far down this list we go.
4. **Interest quiz wording.** Is it acceptable to write our own short
   questions, labelled as a simplified version of O\*NET's Interest Profiler?
   The alternative is to skip slice 4.
