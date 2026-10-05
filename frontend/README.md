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
| `job.js` | `JobDetail` (shared by the panel and the page) and the full job page |
| `welcome.js` | The front door: start, or sign in with a plan code (ADR-0008) |
| `skills.js` | Skills tab, skill pages and the unlock card |
| `saved.js` | Saved jobs and the compare page |
| `interests.js` | The interest quiz (ADR-0011) |
| `history.js` | Progress history (ADR-0012) |
| `me.js` | Me tab and the printable plan |
| `cv.js` | The CV check page and its Home card (ADR-0014) |
| `main.js` | `App`: which screen shows, the tab bar, the page stack. Loaded last; mounts the app |
| `styles.css` | The whole visual system: tokens at the top, one section per part |

Nothing here computes a gap, a recommendation, a pathway or a readiness
figure. Every number comes from the API, so a wrong number is a backend
question.
