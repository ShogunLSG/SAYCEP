> **Superseded — archived 10 September 2026.**
>
> Written 3 August 2026, when the project was a seven-phase build submitting a
> dissertation on 30 November 2026. That framing is no longer live: the project
> now ends at the October presentation. Replaced by [`docs/timeline.md`](../timeline.md).
>
> Kept because it records how the work was originally scoped, and because some of
> the reasoning inside it still holds — that the curated dataset is the hidden
> critical path, that a benchmark should exist before the logic it measures.

# SAYCEP Build Roadmap

**Current phase:** Phase 0 — not started
**Last updated:** _(update this every session)_

When I ask "what's next", read this file, tell me which phase I am in, what the
next unchecked item is, and what needs to be true before I can start it. Do not
start work from this file without telling me the plan first.

Update the checkboxes and the "Current phase" line as we go. This file is the
single source of truth for progress.

---

## Phase 0 — Spikes (do this before anything else)

Throwaway code. Delete it afterwards. The point is to answer three questions
that could each reshape the whole design. Do not start Phase 1 until all three
are answered.

- [ ] **Can I get job data?** Try ESSA first — look for any documented API,
      feed, or machine-readable endpoint. If nothing exists after a genuine
      look, register for an Adzuna developer account and pull South African
      listings. Record which one won and why in `docs/DECISIONS.md`.
- [ ] **What does one roadmap cost?** Write the roughest possible prompt that
      produces a career roadmap, run it ten times, record tokens and cost.
      Multiply by 30 users × the number of regenerations you expect. If the
      number is uncomfortable, the design has to change now, not in Phase 4.
- [ ] **Can the LLM reliably return structured output?** Run the same roadmap
      prompt 20 times against a strict schema. Count failures. If it fails more
      than occasionally, we need a repair-and-retry layer, and that is a design
      decision not an afterthought.

**Exit condition:** All three answered, written up in `docs/DECISIONS.md`, and
the proposal updated if any assumption changed.

---

## Phase 1 — Initiation (20 days)

- [ ] System Requirements Specification drafted
- [ ] Literature review
- [ ] Scope and both user profiles defined in writing
- [ ] Repo initialised, CLAUDE.md in place, git history started
- [ ] Supervisor sign-off

Ask me: has the ESSA finding been reflected in the proposal document? If the
spike changed the data source, the proposal needs updating before sign-off.

---

## Phase 2 — Planning (20 days)

- [ ] Architecture documented in `docs/DECISIONS.md`
- [ ] Database schema designed and first migration written
- [ ] Job data source integrated end to end (one script, real data, in the DB)
- [ ] Curated dataset started — TVET colleges, SETA programmes, certifications,
      events. This is manual grind work and it always takes longer than
      expected. Start it now, not in Phase 5.
- [ ] `.env.example` complete

**The dataset is the hidden critical path.** Nothing about Criterion 5 works
without real TVET and SETA data. Remind me of this if I try to defer it.

**Exit condition:** I can run one command and get real job listings into a real
database against a real schema.

---

## Phase 3 — Development 1 (45 days)

Build the first vertical slice. Crude but complete.

- [ ] Auth and user accounts
- [ ] Onboarding assessment — questions, storage, profile creation
- [ ] Base dashboard showing the stored profile
- [ ] CV builder
- [ ] CV AI scoring

**Exit condition:** A user can sign up, answer the assessment, and see something
back. Demo it to someone who is not me.

---

## Phase 4 — Development 2 (45 days)

The hardest phase. The Career Pathway Builder is the project.

- [ ] Benchmark set of 50 constructed user profiles — **build this first**,
      before the pathway logic. It is how Goal 2 gets evidenced and how I know
      whether a prompt change helped or hurt.
- [ ] Career Pathway Builder — pathway selection and roadmap assembly
- [ ] Interest and strength assessment engine
- [ ] Skills gap analyser (Python ML service)
- [ ] Model validation against real job data, scored against the benchmark

**Exit condition:** ≥80% relevance on the benchmark set, measured and recorded,
with the measurement runnable as a command.

---

## Phase 5 — Development 3 (35 days)

- [ ] Opportunity matching engine
- [ ] Job API integration with scheduled caching and filtering
- [ ] Interview preparation chatbot
- [ ] Roadmap integrated into the dashboard — all five modules connected
- [ ] Deployed to hosting

**Exit condition:** Both user journeys work end to end on the deployed site.
Specifically: the unqualified-user journey must terminate in a named TVET
college or SETA programme with real entry requirements. That is Criterion 5.

---

## Phase 6 — Testing and UAT (22 days, October 2026)

- [ ] Integration and regression tests passing
- [ ] Recruit 20–30 participants across both profiles — **start recruiting in
      Phase 5**, not now
- [ ] Feedback capture instrument prepared before sessions begin
- [ ] UAT sessions run
- [ ] Feedback logged, triaged, actioned or documented with a reason
- [ ] Zero critical defects, ≤5 medium

Participants must be on campus, which is why this cannot slip past October.

---

## Phase 7 — Closure (20 days, November 2026)

- [ ] Dissertation written up
- [ ] Results evidenced against all five success criteria
- [ ] Retrospective
- [ ] Submitted by 30 November 2026

The git history, the benchmark results, and the UAT log are the evidence. If
they were kept properly along the way this phase is writing, not archaeology.

---

## Standing reminders

- Recruiting UAT participants takes longer than expected. Start early.
- The curated TVET/SETA dataset is manual and unglamorous and blocks Criterion 5.
- If a phase is running more than 10 working days over, that breaks Criterion 1.
  Tell me, and let us cut scope rather than slip.
