# Deploying to Fly.io

The live link for the presentation: **minimal, always on, in Johannesburg**
(ADR-0021). My estimate is **about $4.80 a month** running continuously (512 MB,
shared CPU, from Fly's price table and its Johannesburg rate; Fly doesn't
publish that exact figure), so **about $1.20 for a week**. Fly asks for a card.

**The laptop stays your main path.** The link is the safety net, and the answer
if someone asks to try it themselves.

## What to know first

- **Saved plans don't survive a redeploy or a restart.** There's no disk for
  them (that's the fuller plan in `plans/hosting.md`, for after the
  presentation). Fly's docs didn't say what survives a restart, so assume
  nothing does. A plan code from yesterday may not work today. Within one
  session, including the sign-out and sign-back-in in the demo, everything
  works.
- **There's no rate limiting.** Don't publish the link widely, and destroy the
  app when you're done (step 8).
- **One machine only** (`--ha=false`). Fly's default is two, which with this
  database would split saved plans between them.
- **No Kaggle token is needed.** The build uses the O\*NET files in the folder
  you deploy from. Fly uploads the folder, including files git ignores.

## Before you start

On the laptop, set up as in `presentation.md` §4: the O\*NET files in
`backend/data/onet/`, `python backend/load_onet.py` run once, and
`SHORT=1 node frontend/tests/demo_walk.js` passing. **If the demo doesn't
work locally, don't deploy it.**

## Steps (about 30 minutes, most of it waiting)

**1. Install Fly's command-line tool.**
Windows (PowerShell): `pwsh -Command "iwr https://fly.io/install.ps1 -useb | iex"`
(if `pwsh` isn't found, use `powershell` instead of `pwsh`).
Mac: `brew install flyctl`. Then close and reopen the terminal and run
`fly version`.

**2. Make an account.** `fly auth signup` opens the browser. Fly asks for a
card at sign-up, or under Billing in the dashboard.

**3. Create the app,** from the repo folder:
`fly apps create saycep-demo`
If the name is taken, choose another (for example `saycep-yourname`) and change
the `app = ` line at the top of `fly.toml` to match.

**4. Deploy,** from the repo folder:
`fly deploy --ha=false`
It uploads about 100 MB, builds on Fly's servers (a few minutes), and starts one
machine in Johannesburg. It ends by printing your address:
`https://saycep-demo.fly.dev`.

**5. Check it.** Open the address, then run the demo against it.
- Mac or Linux:
  `BASE=https://saycep-demo.fly.dev SHORT=1 node frontend/tests/demo_walk.js`
- Windows PowerShell:
  `$env:BASE="https://saycep-demo.fly.dev"; $env:SHORT="1"; node frontend/tests/demo_walk.js`

It should end with **DEMO PATH OK**.

**6. Confirm there is one machine:** `fly status`. If it lists two, run
`fly scale count 1`.

**7. On the day:** open the address a few minutes before, in case you need it.
It's always on, so nothing needs waking. If something looks wrong,
`fly logs` shows what the server said.

**8. After the presentation,** to stop the charges: `fly apps destroy saycep-demo`.

## If something fails

| You see | It means | Do this |
|---|---|---|
| `Could not find App` or a name error | The name is taken or doesn't match | Pick another name; make `fly.toml` and the commands agree |
| `Occupation Data.txt` not found during the build | The O\*NET files aren't in the folder you deployed from | Complete `presentation.md` §4 step 1, then deploy again |
| `advert counts missing` during the build | The committed advert counts are stale | Tell me; it's a one-command fix on my side |
| The deploy finishes but the site shows an error | The health check (`/skills`) is failing | `fly logs`, and send me the last 20 lines |
| `fly status` shows two machines | The default high-availability setting | `fly scale count 1` |

## What was tested, and what wasn't

Tested on 21 October: the build steps and the run command, run by hand in a
scratch folder on the same Python version (3.11), serving all 15 steps of the demo
with every check passing. **Not tested: Docker itself and Fly itself.** There's no
Docker engine in the environment I work in, so the first real build will happen on
your deploy. If it fails, the table above covers the likely causes, and I'll
fix the rest from the log.
