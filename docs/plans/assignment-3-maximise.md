# Plan: bring Assignment 3 up to the built system and push each section's marks

*Written 30 September 2026. Status: **done 30 September**, except FR-11 (the author's) and the user acceptance test.*

Assignment 3 is marked out of **50**: Q1 baseline 6, Q2 requirements 8, **Q3 design
16**, Q4 technical 10, Q5 evaluation 10. The draft in `assignment-3-submission.md`
is thorough, but it describes the system as it was **this morning**. A marker who
opens the app will now see a job panel, a dashboard and progress tracking that
the document never mentions. Every stale count is a small consistency loss, and
the new features themselves are unclaimed marks.

## Where the marks are, section by section

| § | Marks | What's stale now | What would raise it | Who |
|---|---|---|---|---|
| 1.1 | 2 | "eight endpoints", "five-screen interface", "41 tests" | Mention the plan dashboard and plain-language design in the summary | me |
| 1.2 | 2 | "Changes since A2" lists three changes | Add the UX pass as change 4, framed honestly (see decision 1) | me |
| 1.3 | 2 | Revision history stops at 1.0 | v1.1 row; glossary gains *Must-have*, *Readiness*, *My plan* | me |
| 2.1 | 3 | FR-06 criterion "each with its score" is now **failed** by the build | Fix the build (decision 2). **Add FR-11** | FR-11 wording: **you** |
| 2.2 | 3 | Matrix has no row for the new behaviour | Rows for FR-11 and the ADRs, with new test IDs (TC-I06, TC-I07, TC-U06–08) | me, once FR-11 exists |
| 2.3 | 2 | TR-02 latency figure (5.5 ms) is from this morning | Rerun gives p95 3.8 ms; update | me |
| 3.1 | 2 | Architecture lacks `plain.py` | Redraw with the label module | me |
| 3.2 | 3 | Use cases stop at UC-10 | Add **UC-11 Track skill progress**, **UC-12 View my plan**, **UC-13 View occupation detail**. UC-11 has good alternative flows (undo, "working on it" doesn't count) | me |
| 3.3 | 3 | No `status` on UserSkill, no readiness, no tasks | Redraw both class diagrams | me |
| 3.4 | 3 | Pathway Service now also computes step readiness | Add that call to the sequence | me |
| 3.5 | 2 | Journey ends at "finished" | Add save → dashboard → progress loop, with a return-visit start | me |
| 3.6 | 3 | Component diagram lacks `plain.py`; deployment is fine | Redraw component | me |
| 4.1 | 3 | Line counts and module list | Recount; add `plain.py` | me |
| 4.2 | 3 | ERD and data dictionary lack `occupation_tasks`, `status`, `updated_at` | Redraw ERD; add rows; mention the in-place upgrade (TC-U07) | me |
| 4.3 | 2 | 8 endpoints in the table | 11 endpoints, plus `profile_id` on GET /occupations/{soc} | me |
| 4.4 | 2 | "25 passed", loader output | 39 passed; loader prints `occupation_tasks` | me |
| 5.1 | 4 | 41 tests | 63 tests. **User acceptance test is the single biggest free gain** | UAT: **you** |
| 5.2 | 2 | Rebuild 0.62 s | 1.1–2.0 s after tasks; still 30× under target | me |
| 5.3 | 2 | User guide describes the old screens | Rewrite against the v2 screenshots, including the dashboard | me |
| 5.4 | 2 | "Temporary profiles" limitation half-addressed | Strongest new material is here (below) | me |

### Why 5.4 and 3.2 are where the new work earns most

- **Ethics.** The draft already names "labelling a skill 'essential' may
  discourage". The build now *mitigates* it: "Must-have / Nice to have",
  sentences before numbers, and the deliberate **rejection of streaks, XP and
  badges** for a user facing 60.9% unemployment (BACKLOG, 26 September). A
  concern with an implemented mitigation beats a concern alone.
- **New honest limitations.** Progress is self-reported (ADR-0005). The route
  re-sequences as skills change (ADR-0006). The plan lives in one browser.
  Stating these yourself pre-empts the questions.
- **UC-11** is a better showcase of alternative flows than UC-07. Keep UC-07 as
  the detailed description and add UC-11 as a second, if length allows.

## Things only you can do (and they're worth the most per minute)

1. **Write FR-11**, and FR-12 if you split out the dashboard. See my last
   message for what it has to cover. Q2's 8 marks depend on the build matching
   the requirements table.
2. **Run the user acceptance test.** One or two people, the demo script in
   `STATUS.md`, you silent, note where they hesitate. It moves NFR-02 from
   *Partial* to *Pass* and gives 5.1 real evidence. That's 10–15 minutes for
   marks in two sections.
3. **Read the final document.** It's in my words. Change anything that doesn't
   sound like you, because you'll be questioned on it.

## Decisions I need

1. **How to present the new features under "Changes since Assignment 2".**
   The draft says no scope change was requested. The dashboard and progress
   tracking are new behaviour. They stay inside the Career Pathway Builder
   module, use no new data source, and add no accounts, so nothing on the
   out-of-scope list is touched. **I recommend** stating them plainly as a
   usability enhancement within the existing module, citing ADR-0005 to 0007,
   rather than playing them down. If you'd rather check with the lecturer first,
   I'll leave 1.2 until you have.
2. **FR-06.** **I recommend** showing the score in small text beside the label
   ("Strong match · 0.64"). It's a five-minute build change, and FR-06 stays
   true as written. The alternative is rewording FR-06 yourself.
3. **Old screenshots.** Replace Figures 9–16 with the v2 set, and add figures
   for the job panel and dashboard. **I recommend yes.** The old ones would
   contradict the live demo.

## Order of work once you say go

1. The FR-06 build fix and test.
2. Diagrams (Q3, 16 marks): use case, both class diagrams, sequence, activity,
   component, ERD, architecture. Each is regenerated from PlantUML, and I'll
   check the rendering.
3. Q4 and Q5 facts, the user guide and 5.4.
4. Q1 and Q2, leaving a clearly marked slot for your FR-11 text.
5. Rebuild the `.docx` with `node docs/build-assignment-3.js` and check the page
   render.

**Not in scope here:** the presentation. There's no rubric for it in the repo.
If you have one, share it and we'll plan it the same way.
