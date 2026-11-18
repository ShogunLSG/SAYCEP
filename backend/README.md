# Backend

A single FastAPI service that serves both the API and the app. Run it from the
repo root with `python -m uvicorn app:app --app-dir backend --port 8000`; the
API reference is at `/docs`. How it works and why: `../docs/dev-guide.md`.
Schema: `../docs/architecture.md`.

| File | What it holds |
|---|---|
| `load_onet.py` | Builds `saycep.db` from the O*NET 29.0 files (about 5 s), then loads the two advert caches |
| `load_adverts.py`, `load_listings.py` | Advert counts and sample listings from the Kaggle LinkedIn postings, cached and fingerprinted in `seed/` (ADR-0017, 0019, 0022) |
| `app.py` | Routes only (29 endpoints) |
| `repository.py` | Every SQL query |
| `recommend.py` | **The skill-matching model** (FR-06): ranking, reasons, the step-by-step explanation, job-to-job similarity (ADR-0025) |
| `gap.py`, `pathway.py` | The skills gap (FR-07) and the Pathway (FR-08) |
| `cvscan.py`, `cvadvice.py` | The CV check (ADR-0014, measured r = 0.27) and its "what to add" advice (ADR-0024) |
| `interview.py` | Interview questions and checklist feedback (ADR-0015, ADR-0024) |
| `adverts.py`, `listings.py` | What employers ask for, and "Jobs for you" fit (ADR-0017, ADR-0022) |
| `interests.py`, `plain.py`, `config.py` | The interest quiz, plain-language labels, the 3.5 must-have threshold |
| `tests/` | `test_units.py`, `test_api.py` (server running), `test_performance.py`, plus benchmarks and checks |

Deliberately a monolith (see `../docs/architecture.md`). The modules are kept
apart so the model could become its own service later without rework.
