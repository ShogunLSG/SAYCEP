# User-test pack (NFR-02)

*Prepared 19 November 2026. This is what you need to run the user test that
Assignment 2 planned and Assignments 3 and 4 report as not yet done.*

NFR-02 says a first-time user reaches a displayed Pathway in **five screens or
fewer, without written instructions**. The test checks exactly that, with
**four participants, two per profile** (two school-leavers and two students),
as Assignment 2 planned.

## The files

| File | What it's for | Who sees it |
|---|---|---|
| `consent.md` | Read it aloud or hand it over, and get a yes before starting | the participant |
| `task-sheet.md` | The one task, plus three follow-up questions and the 10-item SUS | the participant |
| `facilitator.md` | What you say, what you don't say, what you count | you |
| `results.md` | One row per participant, and the summary that goes into a report | you |

## Before you start

- **Ethics:** check whether the module requires ethics clearance for a test
  with people outside the class. If it's unclear, ask the lecturer first: it's
  a one-line question, and it protects the result.
- **Age:** test **adults only (18 to 24).** The target group starts at 15, but
  anyone under 18 needs a parent's or guardian's consent as well, which this
  pack doesn't cover.
- **Anonymity:** record nothing that identifies anyone. Participants are P1 to
  P4. Don't record names, ID numbers, recordings of faces or voices, or screen
  recordings that show their accounts.
- **Setup:** run the app with
  `python -m uvicorn app:app --app-dir backend --port 8000`, open
  `http://127.0.0.1:8000` in a fresh private window for each participant (so
  no earlier plan is remembered), and leave presenter mode **off**.
- **Time:** about 15 minutes per participant: 2 for consent, up to 10 for the
  task, and 3 for the questions.
