# Status

**As of 30 September 2026 (night): SAYCEP is a full app.** A welcome screen with plan-code sign-in, the five-screen journey as onboarding, then four tabs — Home, Explore, Skills, Me — with job pages, skill pages, saved jobs and comparison, an interest quiz, progress history and a printable plan. 98 automated tests pass (23 unit, 71 integration and system, 4 performance). Assignment 3 was submitted describing the earlier build; the demo now shows more, which is normal and worth saying.

## Decided

- **Data source rule: Kaggle only.** South African statistics are cited as written background, never loaded. (ADR-0002)
- **Data spine: O*NET 29.0**, from Kaggle — importance-rated skills, job zones, an expert-reviewed related-occupations graph. (ADR-0003)
- **Skill capture is shared; the two profiles diverge at target selection.** O*NET has no qualification-to-skills mapping. (ADR-0004)
- **Emerging technology: mean-centred cosine similarity** over 35-dimensional skill vectors, measured rather than asserted.
- **Demo stack: monolith** — one FastAPI service serving both the API and the app, SQLite, React vendored locally.
- **Scope: two modules built, three specified.**

## Done

- **The journey.** Five screens, one at a time — who you are, your skills, pick a target, the gap, the route. Walked end to end in a browser against the real database. `?presenter` on the URL shows each screen's requirements.
- **The API.** Eight endpoints, module names matching the sequence diagram. One connection per request, verified under 20 concurrent calls.
- **All ten functional requirements are built and demonstrable.** FR-10 in the loader, FR-01 to FR-09 in the API and journey.
- **Recommendation engine** measured at 59.7% occupational-family accuracy against a 6.9% baseline, and 8.8 ms p95 latency.
- **Assignment 2 drafted** — all five questions, four UML diagrams, a formatted `.docx` with your name and verified StatsSA figures.
- **Repo on GitHub**, private, at `ShogunLSG/SAYCEP`.

## Built on 30 September (evening) — `docs/plans/ux-and-dashboard.md`

- **Plain language (Task 1).** Words first, figures behind `?presenter`:
  "Critical for this job" rather than 4.00 / 5, and "Vocational training or an
  apprenticeship" rather than Job Zone 3. Labels come from `backend/plain.py`.
- **"What is this job?" panel (Task 2).** It shows the description, the
  preparation needed, and every skill ticked if you have it. The target is set
  from the panel.
- **"My plan" dashboard (Task 3).** It opens after the route, and again on
  every return visit. It shows the goal, readiness counted in must-haves, the
  route with each step ticked when ready, and the next step. ADR-0006 records
  why this doesn't break NFR-02.
- **Progress (Task 4).** Skills move from *Start learning* to *I can do this
  now*, and only the second closes a gap. This is a schema change (ADR-0005).
- **"A day in this job" (Task 5).** It lists O*NET task statements, most
  important first, from the same Kaggle dataset. New table (ADR-0007).
- New screenshots are in `docs/screenshots/v2/` and new transcripts are in
  `docs/test-results/*-v2.txt`. The originals are untouched, because
  Assignment 3 cites them.

## Not done — in order of what hurts most if left

1. **Write the requirements for what the app now does — yours, not mine.**
   FR-11 (progress), and likely FR-12 onward: alternate-title search, job
   pages, saved jobs and compare, the interest quiz, progress history, the
   plan code. `docs/plans/full-app.md` lists each with a measurable figure.
   Assignment 3 went in without them; the presentation is where they're asked.
2. **Read Assignment 3 before submitting:** `docs/ISJ107V_Assignment_3_SAYCEP.docx`, built from `docs/assignment-3-submission.md`. It's in my words, not yours.
4. **User acceptance test.** NFR-02 is reported as *partial* because no first-time user has walked the journey unassisted. Ten minutes with one person, using the demo script below, would turn it into evidence. The document says plainly that it hasn't been done.
5. **Confirm the new demo date.** Then rehearsal and slides, which are both still not started.
6. **Assignment 2 diagrams are small.** If Assignment 2 isn't submitted yet, its use-case, class and sequence diagrams print with text under 6 px. Assignment 3's are fixed; the same landscape-page approach would fix Assignment 2's.

## Done on 30 September

- 41 automated tests — 12 unit, 23 integration, 2 system, 4 performance — all passing; transcripts in `docs/test-results/`.
- The tests found a real defect: rebuilding the database under a running server dropped the profile tables. Fixed in `load_onet.py`.
- **TR-01's baseline corrected.** Assignment 2 compared 59.7% against 6.9%, which measures something different. Against its own baseline the figure is 59.7% vs 25.8% random (2.3x). Still passes the 55% target; the margin was overstated.
- Nine as-built diagrams in `docs/uml/a3/`. The Assignment 2 sequence diagram was wrong — the Pathway Service never calls the Gap Analyser — and is corrected.
- FR-08 reworded to "new or deeper", closing the old item 5.
- `requirements.txt` added; dead `gap.skills_to_acquire` removed.

## The demo script

Verified end to end on 30 September (night), screenshots in `docs/screenshots/v3/`. About six minutes.

1. **Welcome.** Type a first name (Thabo) → *Start my plan*. Say: no email, no password — a plan code instead.
2. **I left school**, then tick: Operation and Control · Operations Monitoring · Equipment Maintenance · Active Listening · Critical Thinking · Monitoring
3. *For you* shows operator roles with scores, and **why** each one: "Because you have: Operation and Control, Equipment Maintenance…" (FR-06). *Search* "electric", tap **Electricians** — the panel shows what the job is and *A day in this job*. **Aim for this job**.
4. The gap: "You already have **6 of the 34** skills… **2 must-haves**" — Troubleshooting and Repairing.
5. The route: Boilermakers → Power-Line Installers → Electronics Repairers → Electricians. Each step says why it's there ("Closest to you now. Good match with your skills"). **Save as my plan**.
6. **Home.** Troubleshooting → *Start learning* (nothing changes — learning isn't having), then *I can do this now* → **the unlock card**: 1 of 2, Power-Line Installers now ready, 106 jobs with every must-have (up 4).
7. **Explore → Search** "conduit installer" — Electricians, *also called Conduit Installer*. Open it: tools of the trade, software, jobs like this. *Save this job*. Save Power-Line Installers and Boilermakers too.
8. **Explore → Interests.** Answer the twelve; show jobs that fit. Say it's a simplified version of O*NET's profiler.
9. **Skills → Repairing → I can already** → the goal is complete: 2 of 2, 131 jobs.
10. **Home → Saved jobs →** tick three → **Compare**. Then **Your progress**: 0 → 0 → 1 → 2 of 2.
11. **Home → Check my CV → Use an example CV → Check my CV.** Skills it shows, each quoting its line. *Add* Repairing → the unlock card. Then *How it reads for Electricians*: Multimeters and Excel named, Troubleshooting not shown yet. Say: "never saved".
12. **Home → What employers ask for → See what employers ask for.** It opens Electricians at the section: 84 US adverts, 6 in 10 open to beginners, 7 in 10 mention a trade licence; Installation, Repairing and Troubleshooting are the skills they stress. Say: real adverts, American and closed, so it shows what employers ask for, not jobs to apply for.
13. **Home → Practise for an interview.** Question 2 (Troubleshooting): type "I fixed it." → 2 of 7 with tips; paste a full story → 7 of 7. Say: practice with guidance, not a chatbot, and nothing is saved.
14. **Me →** *Print my plan* (one page). Note the plan code, *Sign out*, then *I have a plan code* → the plan comes back.
15. For the marker: add `?presenter` — every SOC code, Job Zone and rating is back.

Questions to expect, with the honest answers:
- *"Why no real login?"* Nothing personal is held beyond an optional first name, so a password would protect nothing a code doesn't. The code is a bearer credential and the screen says so (ADR-0008).
- *"How do you know they can really do it now?"* We don't — progress is self-reported, like the original skill capture (ADR-0005).
- *"Is the quiz validated?"* No. It's twelve statements of ours against O*NET's real interest profiles, labelled as simplified (ADR-0011).
- *"Your accuracy only beats the target by 4.7 points. Can you improve it?"* Measured on 4 October: adding O*NET Knowledge and Abilities to the job vectors moves it from 59.7% to 60.5%, which is noise, because users don't record those. It would only help if users did, and that's a new capture step. Assignment 3 suggested otherwise; measuring showed it was wrong (ADR-0013).
- *"How good is the CV scanner?"* On 172 held-out CVs from a Kaggle benchmark, its goal score tracks human match scores at r = 0.27, against 0.16 for word matching. That's modest, and it's from tech and office CVs, not South African ones. The skill suggestions are rules we wrote, quoted back for the user to confirm, because three smarter text-matching designs did worse than plain word matching (ADR-0014).
- *"Your proposal said interview chatbot. Where is it?"* A chatbot needs a language model, and the project rules out an LLM, so it's interview practice instead: questions from the job's real skills and tasks, and a checklist on each answer. All five modules are now built, three in a reduced form (ADR-0014, ADR-0015, ADR-0017).
- *"Why aren't these South African jobs?"* There are none on Kaggle that are real. The two "South African" sets failed verification: one is mostly Indian and German company scrapes, the other is generated from four templates. So the app shows what 84 real (American, 2024) electrician adverts asked for and says so, rather than inventing local openings. Links are by job title, 44 of 50 checked right (ADR-0017).
- *"Is it accessible?"* Measured on 5 October against WCAG 2.1 AA: an automated audit of all 22 screens went from 169 failures to 0 (light and dark mode, and at 320 px wide), and a keyboard-only walk of the whole demo now passes 19 of 19 checks. It hasn't been tested with a real screen reader or disabled users, and that's the honest gap (ADR-0016).
- *"Why don't recommendations include Electrician?"* The six skills ticked are operator skills; the target was reached by search, which is what search is for.

## Built on 5 October — accessibility (ADR-0016)

- WCAG 2.1 AA pass. Contrast tokens fixed for both themes, focus moves to each new screen and page and back again, the sheets trap focus and close on Escape, and segmented controls have honest roles. Before and after are in `docs/test-results/accessibility-2026-10-05.txt`.
- Rerun with `frontend/tests/a11y_audit.js` and `frontend/tests/keyboard.js`. Both are test-time scripts and not app dependencies.

## Built on 5 October — what employers ask for (ADR-0017)

- Module 4, as the data allows. Real LinkedIn adverts (US, March–April 2024), linked to O*NET by title, summarised per job: beginners' share, requirements, tools named, skills stressed, titles. It's on the job page and in a Home card for the goal.
- Checked: skills agree weakly but really with O*NET (Spearman +0.23 vs +0.09). The requirement rules were hand-checked at 11–12 of 12. See `docs/test-results/adverts-2026-10-05.txt`.
- The advert file (517 MB) is gitignored in `backend/data/linkedin/`. The counts are cached, so rebuilds stay at about 2.5 s.

## Deferred on purpose

- Light gamification polish — `docs/BACKLOG.md`, only if time remains
- RIASEC interest intake, and the three specified-only modules
