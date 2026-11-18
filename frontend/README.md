# Frontend

The SAYCEP app: a welcome screen, the five-screen journey as onboarding, then
four tabs (Home, Explore, Skills, Me) with pages pushed over them. React with
`htm` tagged templates standing in for JSX, vendored in `vendor/`, so there is
no build step and no internet needed: edit a file, reload the page.

Served by the API, same origin. Run from the repo root:

```bash
python -m uvicorn app:app --app-dir backend --port 8000
```

then open http://127.0.0.1:8000. Add `?presenter` to the URL to show each
screen's requirement IDs and the raw figures behind every label.

Plain scripts that share globals, loaded in this order by `index.html`:

| File | What it holds |
|---|---|
| `app.js` | Shared pieces (API, `useFetch`, icons), the five journey screens, the job panel, the *My plan* dashboard |
| `model.js` | The skill-matching model, made visible: the "Skill-matching model" tag and the "How we matched you" panel (ADR-0025) |
| `job.js` | `JobDetail` (shared by the panel and the page), the full job page, and "Jobs with the closest skills" |
| `welcome.js` | The front door: start, or sign in with a plan code (ADR-0008) |
| `skills.js` | Skills tab, skill pages and the unlock card |
| `saved.js` | Saved jobs and the compare page |
| `interests.js` | The interest quiz (ADR-0011) |
| `history.js` | Progress history (ADR-0012) |
| `me.js` | Me tab and the printable plan |
| `cvfile.js` | Reads an uploaded CV in the browser: PDF (pdf.js, vendored), Word (.docx) and text (ADR-0023) |
| `cv.js` | The CV check page and its Home card: skills found, jobs it points to, what to add (ADR-0014, 0024, 0025) |
| `practice.js` | Interview practice page and its Home card, with retry (ADR-0015, ADR-0024) |
| `employers.js` | What employers ask for: the job-page section and its Home card (ADR-0017) |
| `jobs.js` | "Jobs for you": sample listings as job cards on Home, a Jobs page and job pages (ADR-0022) |
| `main.js` | `App`: which screen shows, the tab bar, the page stack. Loaded last; mounts the app |
| `styles.css` | The whole visual system: tokens at the top, one section per part |

Nothing here computes a gap, a recommendation, a pathway or a readiness
figure. Every number comes from the API, so a wrong number is a backend
question.

## Accessibility (ADR-0016)

The app targets WCAG 2.1 AA. Text colours are tokens. `--muted` and
`--on-fill` were chosen to clear 4.5:1 in both themes, so new text should use a
token rather than a literal colour. `focusWhenReady` and `useDialog` in
`app.js` handle focus on new content and in modal sheets.

`tests/` holds the browser checks. They're test-time only and never loaded by
the app. Install `axe-core` and `playwright` in any scratch folder, put it on
`NODE_PATH`, start the server, then run:

    node frontend/tests/a11y_audit.js          # SCHEME=dark, WIDTH=320 for the other runs
    node frontend/tests/keyboard.js
    node frontend/tests/demo_walk.js           # the presentation demo, all 15 steps; SHORT=1 for the 10-minute path
    node frontend/tests/cv_upload.js           # CV upload with the files in tests/fixtures/
    node frontend/tests/job_cards.js           # Jobs for you
    node frontend/tests/interview_retry.js     # interview retry, the tool question, CV advice
    node frontend/tests/engine_visible.js      # the skill-matching model panel and its tags

`vendor/` holds React, react-dom, htm and pdf.js 3.11.174 (Apache-2.0, with
`isEvalSupported` off as the fix for CVE-2024-4367), so nothing loads from the
internet.
