# Plan: hosting SAYCEP on Fly.io

*Written 8 October 2026; host chosen 9 October: **Fly.io**. Status: **plan
only, waiting for your go-ahead to build.***

## What has to be true

- **A public HTTPS link** the marker can open on a phone, with no install.
- **Saved plans survive** restarts and deploys. The plan code (ADR-0008) is
  in the demo script, and a marker may come back to it later.
- **The data still comes only from Kaggle** (ADR-0002). The O\*NET database
  is built from the Kaggle download during each deploy, using your token.
  The token never goes in chat or in the repo.
- **It stays as simple as it is now:** one service, one process, SQLite.

## Why Fly.io (decided 9 October)

Options checked on 8–9 October:

| Host | Cost | Saved plans survive? |
|---|---|---|
| Render Free | $0 | No: the disk is wiped every time it sleeps |
| Render Starter + disk | ~$7/month | Yes |
| **Fly.io, Johannesburg** | **~$3/month** | **Yes**, on a volume |
| PythonAnywhere | $0–10 | Yes, but its support for apps like this is still beta |

What Fly gives this project:

- **A Johannesburg region (`jnb`).** The app runs in South Africa, close to
  its users, and saved plans stay in South Africa. That's a clean answer if
  POPIA comes up (the data is an optional first name and a skills list).
- **Cost** (docs.fly.io/about/pricing, 9 October):
  - the smallest machine (shared-cpu-1x, 256 MB) is $2.19 per 30 days in the
    US, and Johannesburg is priced 1.3×, so about **$2.86** running
    continuously;
  - a 1 GB volume is **$0.15/month**;
  - the shared IPv4 address is free, and the data transfer at this size is
    negligible;
  - **it costs less still, because the machine stops when nobody is using
    it.**
- **Memory:** the server peaks at about **93 MB** (measured), so 256 MB is
  enough. If it ever runs out, 512 MB is about $4.80.
- **The catches:**
  - There's no free tier, so a card is needed from the start.
  - The first setup uses Fly's command-line tool, once.
  - After that, deploys can run automatically from GitHub (item 7 below), so
    you don't need the command line again.

## How it will work

```
push to main ──► GitHub Actions: run every test ──► if green: fly deploy
                                                         │
             Docker build (on Fly's builder)             ▼
             1. download O*NET from Kaggle (token = build secret, never in the image)
             2. python backend/load_onet.py  → saycep.db baked into the image
             3. advert counts from backend/seed/ → "What employers ask for"
                                                         │
             Machine in Johannesburg ◄────────────────────┘
             ├── image: app + saycep.db (reference data, rebuilt every deploy)
             └── volume /data: users.db (saved plans — survives deploys, snapshotted daily)
```

## What I'd build

1. **Separate user data from reference data.**
   - Today `load_onet.py` deletes `saycep.db`, and the saved plans are in
     that file. On a host, every deploy would wipe every plan.
   - Saved plans move to `users.db`. Its location comes from the environment
     (`SAYCEP_USER_DB`), so on Fly it lives on the volume.
   - The app opens `users.db` and attaches the O\*NET database read-only. The
     user tables already reference only each other, so no queries change.
   - **This is a schema change:** same tables and columns, in a different
     file. It gets ADR-0018.
   - Your local saved plans get copied across once.
2. **`backend/prepare_data.py`.**
   - It downloads O\*NET from Kaggle using `KAGGLE_API_TOKEN`, unzips it and
     runs `load_onet.py`.
   - It uses only the standard library, so no new dependency, and does
     nothing if the data is already built.
   - Locally it replaces the manual "download and unzip" step.
3. **Ship the advert counts.**
   - The 726 KB `advert_counts.cache.json` is committed under
     `backend/seed/`, so "What employers ask for" works without the 517 MB
     advert file.
   - It holds counts only, no advert text, and keeps its CC BY-SA attribution
     on screen.
   - A test fails if the committed counts don't match the code, so they
     can't go silently stale.
4. **Rate limiting.**
   - At most 10 wrong plan codes per address per 15 minutes, then a plain
     "Too many tries — wait a few minutes".
   - A cap on new plans per address per hour, so the volume can't be filled.
   - Both are kept in memory: a few lines, no dependency. That's correct
     because there is exactly one machine.
   - The address comes from Fly's `Fly-Client-IP` header.
5. **`/health`.** It checks that the reference data is present and that
   `users.db` can be written. Fly uses it to decide whether a deploy
   succeeded.
6. **A `Dockerfile` and `fly.toml`.**
   - The Dockerfile has two stages, so the 93 MB of raw O\*NET files and the
     token never reach the final image; only the 19 MB `saycep.db` does.
   - `fly.toml` sets: region `jnb`, 256 MB, HTTPS only, the `/data` volume,
     the health check, and stop-when-idle with start-on-request.
   - **Exactly one machine.** Fly's setup creates two by default "for
     availability", but with SQLite each would have its own volume, and
     saved plans would split between them. The plan pins it to one and says
     why.
7. **GitHub Actions.**
   - On every push: unit, API and performance tests, the accessibility audit
     and the keyboard walk.
   - The O\*NET download is cached between runs.
   - On a push to `main` with every test green, it deploys to Fly. Pushes to
     other branches only run the tests.
8. **Docs.** ADR-0018 for the user-data split; ADR-0019 for the host; a
   `docs/deploy.md` runbook covering setup, deploy, the presentation
   checklist, restore from snapshot, and how to rotate the token.

## What you'd do (once, about 20 minutes, I'll walk you through it)

1. **Rotate the Kaggle token.** The current one was pasted in chat.
2. **Make a Fly.io account** and add a card.
3. **Install `flyctl`** and run three commands I'll give you exactly:
   - create the app;
   - create the 1 GB volume in Johannesburg;
   - make a deploy token.
4. **In GitHub, add two repository secrets** under *Settings → Secrets →
   Actions*: `KAGGLE_API_TOKEN` and `FLY_API_TOKEN`.
5. **Merge to `main`.** The first deploy then runs by itself, and you get a
   `https://<app-name>.fly.dev` link.

No token is ever pasted into chat. I can't do steps 2–4 for you, because
they need your accounts.

## Before the presentation

- **Keep it awake.** Set it to keep one machine running during the
  presentation week, so the first visitor never waits for a start-up. It's a
  one-line change, and costs about $0.70 for that week.
- **Rehearse on the hosted link,** not localhost, and keep the local version
  ready as a fallback.

## Load-bearing decisions in here

- **Hosting on Fly.io, about $3/month on your card.** Decided 9 October.
- **The schema change in item 1** (ADR-0018).
- **Committing a derived data file (item 3).** Until now, every data file has
  been gitignored.
- **Deploying automatically from `main` (item 7).** You'd merge to deploy.
  The alternative is deploying by hand with `fly deploy`.

## Not verified yet (checked on first deploy)

- **How long a stopped machine takes to start.** Fly's docs say it's fast
  but give no figure. I'll measure it.
- **That the 256 MB machine has enough headroom** under Fly's own overhead.
  The 93 MB peak was measured here, not on Fly.

## Rough size

Items 1–8: about a day, with tests. The first deploy: about 20 minutes with
you.
