# Frontend

The five-screen journey. React loaded from a CDN, with `htm` tagged templates
standing in for JSX, so there is no build step — edit a file, reload the page.

Served by the API, same origin. Run from the repo root:

```bash
python -m uvicorn app:app --app-dir backend --port 8000
```

then open http://127.0.0.1:8000. Add `?presenter` to the URL to show which
requirement each screen satisfies.

| File | What it holds |
|---|---|
| `index.html` | The shell and the three library script tags |
| `styles.css` | The whole visual system — tokens at the top, one section per screen |
| `app.js` | The journey: one component per screen, plus `App`, which owns the state |

`app.js` never computes a gap, a recommendation or a pathway. Every figure on
screen comes from the API, so a wrong number is a backend question.

**Demo-day risk:** the libraries come from a CDN, so the page needs internet.
If they fail to load the page says so rather than going blank. Bundling them
locally removes the risk — see `docs/plans/frontend-journey.md`.
