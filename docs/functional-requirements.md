# Functional requirements (Assignment 2)

At least 10 required. The October presentation is built on them and questions are drawn from them, so every one has to be something you can explain, defend and preferably point at running on screen.

**How this file is meant to be used.** FR-1 to FR-4 below are worked in full — statement, why it holds up, and the question it invites — to establish the pattern. The rest are yours to draft. That split is deliberate: requirements you reasoned your way to are ones you can defend when he pushes, and requirements handed to you are ones you have to reverse-engineer your own thinking for, in the room, under questioning. Use the four as a template for form and rigour, not as text to pad out.

## What makes a requirement defensible

A functional requirement says what the system must **do**. "Fast", "secure", "user-friendly" are non-functional and don't belong here.

Four tests, all of which the worked examples pass:

**Countable.** "No fewer than three intermediate steps" can be checked on screen. "A useful pathway" cannot.

**Traceable to data.** You must be able to say which dataset makes it possible. A requirement the data can't support is the one that collapses when he asks where the numbers come from.

**Demonstrable, or explicitly not.** Mark each one as built or designed. Claiming something works when it doesn't is worse than saying it's specified but not implemented.

**Owns its design decision.** Every requirement hides a choice — a threshold, an ordering, a classification. Know what yours is and why. That's what the questions will be about.

---

## Worked examples

### FR-1 — Career Pathway Builder *(built)*
> The system shall allow a user to select a target occupation from the occupation catalogue and shall generate an ordered pathway of no fewer than three intermediate steps, each step naming the specific skills to be acquired at that step.

*Holds up because:* countable (three steps), demonstrable, and traceable to the role↔skill mapping dataset.

*Invites the question:* "Where do the intermediate steps come from?" — Answer: from skill-overlap distance between the user's current set and the target's required set, grouped into steps. Have the actual grouping rule ready.

### FR-2 — Skills gap analyser *(built)*
> The system shall compare a user's captured skill set against the skills required for their selected target occupation and shall display each missing skill classified as either essential or desirable.

*Holds up because:* clear input, clear output, visible classification.

*Invites the question:* "How do you decide essential versus desirable?" — This is the design decision you own. A defensible rule: a skill appearing in more than a set percentage of records for that occupation is essential, below it desirable. **Pick the threshold, write it down, and be able to say why that number.**

### FR-3 — User profiles *(built)*
> The system shall support two registration paths — enrolled student and unqualified school-leaver — and shall capture a different initial skill profile for each.

*Holds up because:* ties the code directly to the two user profiles in the proposal, so the design and the build tell the same story.

*Invites the question:* "Why do the two paths need different capture?" — An enrolled student has a qualification to infer skills from; a school-leaver has no qualification, so entry has to be interest- or aptitude-based. That difference is the reason the second profile exists at all.

### FR-4 — Data provenance *(built)*
> The system shall record and display the source dataset and publication date for every occupation and skill record presented to the user.

*Holds up because:* it turns his data rule into a visible feature. Cheap to build — two columns and a label in the UI — and it pre-empts the provenance question instead of waiting to be caught by it.

*Invites the question:* nothing hostile. This one creates a good moment rather than a risk, which is exactly why it's worth including.

---

## Yours to draft (aim for 6+, giving 10+ total)

Draft these against the four tests above. Suggested coverage, though the split is yours:

**Two more on the built modules.** What else must the pathway builder or gap analyser *do* that isn't covered? Saving and resuming a pathway? Changing a target and seeing the gap recalculate? Re-ordering steps? These are the strongest additions because you can demo them.

**Two on the CV builder / scorer.** What must it accept — uploaded file, or pasted text? What must it output — a numeric score, a set number of improvement suggestions, both? Mark as designed unless you actually build it.

**Two on opportunity matching.** What does it match on — skills, location, qualification level? How many results, ranked how? Blocked until the SA job postings dataset is verified (`data-sources.md`), so this may have to be specified rather than built.

**Optional, on the interview chatbot.** How many questions, tied to what, and does it evaluate the answer or just ask?

### Template

```
### FR-n — <module> (built | designed)
> The system shall ...

Holds up because:
Invites the question:
Data behind it:
```

## Keep in sync

These have to agree with proposal section 2.3 (expected solution) and with what's actually running by demo day. Three versions of the same story that don't match is a bad look; one story told consistently is most of the mark.
