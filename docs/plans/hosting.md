# Plan: hosting SAYCEP

*Written 8 October 2026. Status: **draft, waiting on the host decision.***

## What has to be true

- **A public HTTPS link** the marker can open on a phone, with no install.
- **Saved plans survive.** The plan code (ADR-0008) is a feature in the demo
  script, and a marker may come back to it later.
- **The data still comes only from Kaggle** (ADR-0002). The host downloads
  O\*NET from Kaggle itself, using a token you enter in the host's settings,
  never in chat or in the repo.
- **Nothing gets more complicated than it needs to be.** It stays one
  service, one process and SQLite, as now.

## Facts checked today (8 October)

| Host | Cost | Saved plans survive? | Catch |
|---|---|---|---|
| Render **Free** | $0 | **No.** Its disk is wiped whenever it sleeps (after 15 minutes idle), restarts or redeploys. | About a minute to wake up; persistent disks aren't available. |
| Render **Starter** + 1 GB disk | ~$7/month, billed per second | Yes | Card needed. The price is from third-party listings; Render's pricing page didn't load. |
| Fly.io | ~$2–4/month + $0.15/GB storage | Yes | No free tier; card needed. Deploys from a command line with a Dockerfile. |
| PythonAnywhere | $0–10 | Yes | Support for apps like this one is **beta**, and whether it's free is undecided. |

Sources: render.com/docs/free, docs.render.com/disks, docs.fly.io/about/pricing,
help.pythonanywhere.com/pages/ASGICommandLine, pythonanywhere.com/pricing.

The server peaks at about **93 MB of memory** (measured after the full API test
run), so the smallest instance on any of these is enough.

## Recommendation: Render, free while building, Starter for the presentation

- It's set up from a dashboard, with no command line or Docker to learn.
- Build on **Free** first, at $0 with no card, and get every piece working.
- Switch to **Starter + a 1 GB disk** for the weeks around the presentation.
  It's one setting, and you're billed only for the days it runs (roughly
  $7 for a month).
- Choose the **Frankfurt** region, the closest Render has to South Africa.
- **Until the switch, saved plans reset whenever the site sleeps.** The
  welcome screen will say so while on Free.

## What I'd build (host-independent, except item 5)

1. **Separate user data from reference data.**
   - Today `load_onet.py` deletes `saycep.db`, which holds the saved plans
     too. On a host, every deploy would wipe every plan.
   - Saved plans move to their own file, `users.db`. Its location comes from
     the environment, so on Render it can sit on the persistent disk.
   - The app opens `users.db` and attaches the O\*NET database read-only. The
     user tables already reference only each other, so no query changes.
   - **This is a schema change:** same tables and columns, in a different
     file. It gets ADR-0018.
2. **`backend/prepare_data.py`.**
   - It downloads the O\*NET dataset from Kaggle using `KAGGLE_API_TOKEN`
     from the environment, unzips it and runs `load_onet.py`.
   - It uses only the standard library, with no new dependency. It does
     nothing if the data is already built.
   - It runs during the host's build. *Unverified:* Render's docs don't say
     whether settings are available during the build. If they aren't, the
     same script runs at start-up instead.
3. **Ship the advert counts.** The 726 KB `advert_counts.cache.json` gets
   committed under `backend/seed/`, so "What employers ask for" works on the
   host without the 517 MB advert file. It holds counts only, no advert text,
   and gives the CC BY-SA attribution on screen. A test fails if the
   committed counts no longer match the code.
4. **Rate limiting.**
   - At most 10 wrong plan codes per address per 15 minutes; after that, a
     plain "Too many tries, wait a few minutes".
   - A cap on new plans per address per hour, so the disk can't be filled.
   - Both are kept in memory, a few lines with no dependency. That's enough
     for a single instance.
5. **`render.yaml`, plus a `/health` check.** The whole service is described
   in one file in the repo: Python version, build, start, region, health
   check, disk and the token setting (entered in the dashboard).
6. **Run the tests automatically on every push (GitHub Actions).**
   - Unit, API and performance tests, plus the accessibility audit and
     keyboard walk.
   - The O\*NET download is cached between runs.
   - This needs `KAGGLE_API_TOKEN` added as a GitHub repository secret.

## What you'd do (I can't)

- **Rotate the Kaggle token first.** The current one was pasted in chat.
- **Render:** sign up, choose *New → Blueprint*, pick `ShogunLSG/SAYCEP`,
  and paste the new token when it asks for `KAGGLE_API_TOKEN`.
- **GitHub:** add the same token under *Settings → Secrets → Actions*.
- **Near the presentation:** switch the plan to Starter and add the disk, or
  tell me and I'll change `render.yaml`. Open the site a few minutes before
  presenting.

## Load-bearing decisions in here

- Which host, and whether you'll spend about $7 for the presentation month.
- The schema change in item 1, recorded as ADR-0018.
- Committing a derived data file (item 3). Until now, every data file has
  been gitignored.

## Rough size

Items 1–4 and 6: about a day, with tests. Item 5 and the first deploy: an
hour with you, because it needs your accounts.
