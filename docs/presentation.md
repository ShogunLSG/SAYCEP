# Presentation: Friday 6 November 2026

The script, the demo path, what to do if it breaks, and the questions to
expect. **The words are suggestions: put them in your own voice.** You're
questioned on this work directly, so anything you say should be something you
can defend without this page.

**The brief sets the shape** (Assignment 4, `ISJ107V_Assignment_4_Prototype_Presentation.pdf`,
Q5, 10 of the 50 marks):

| Mark | What it asks for | Where it's covered here |
|---|---|---|
| **5.1** (3) | A structured **5-minute** presentation: problem, solution, architecture, emerging technology, prototype features, results, limitations | §2 |
| **5.2** (4) | A reliable **10-minute** live demo of the main workflow and the emerging-technology integration, using prepared sample data **and a fallback plan** | §3, §4 |
| **5.3** (1) | Clear, readable slides; professional; **on time** | §2 |
| **5.4** (2) | Technical questions answered accurately, **explaining your own design, implementation and testing decisions** | §5, especially §5.8 |

The rubric's top band (9–10) is: *focused and professional, a convincing live demo,
and technical answers that show strong individual understanding.*

**The brief also asks for a written report** (8–12 pages, one searchable PDF named
`ISJ107V_Assignment4_StudentNumber.pdf`) and the slides, both uploaded to
Brightspace. See **§9**, because that's a separate piece of work.

---

## 0. Three things to know before you start

**1. Present from the laptop; the web link is the safety net.** The app runs on
the machine you present from. On 21 October a minimal Fly.io deploy was added
(`docs/deploy.md`, ADR-0021) so there's a link too. **Saved plans on the link
reset whenever it's redeployed or restarts**, so don't rely on an old plan code
there. §4 is the
setup, and `frontend/tests/demo_walk.js` checks the whole demo in under a
minute, so you'll know it works before you stand up.

**2. The accuracy figure has a footnote you should know.** The 59.7% in
Assignment 3 counts the target job itself as a hit if it appears in its own top
five (it does for 20% of targets). A stricter reading, over every job and with
the target removed, gives **58.5% (95% interval 54.6–62.1), against 25.9% by
chance**. It still clears the 55% threshold, but the interval touches it. I
added this as a test (PT-01b). **Say the strict figure if asked.** It's in the
Q&A (Q3.2). The submitted document is accurate for what it measured, and
nothing in it needs withdrawing.

**3. Use the newer unemployment figures.** Assignment 2 quotes Q1 2026 (60.9%
for ages 15–24). StatsSA has since published Q2 2026 (released 11 August):
**62.8%** for 15–24, **41.8%** for 25–34, **33.6%** overall, and **47.4%** for
ages 15–34. I checked these in StatsSA's own release and presentation, not a
news report. A marker may ask "is that the latest?", so quote Q2 and say the
written work used Q1.

---

## 1. The story in one breath

> A young South African who didn't go to university can't see the route from
> where they are to a job that exists. SAYCEP takes the skills they already
> have, shows which skills stand between them and a named job, and gives them an
> ordered route of nearby jobs to get there, including routes that don't need a
> degree. It tracks their progress, and checks their CV and interview answers
> against the job they chose.

**What you claim:** a working prototype that goes from skills to a target job to
a gap to an ordered route, with every number measured and every limit stated.

**What you don't claim:** that it helps people get jobs (nothing here measures
that), that its data is South African (it isn't), or that the CV and interview
modules are AI. They're rules, deliberately.

---

## 2. Running order: 5 minutes of talk, then a 10-minute demo

The brief gives you **five minutes** for seven things, so each gets about 40
seconds. That's tight: **one idea per slide, and practise it against a timer.**

| Time | What | Slide | Say, in one breath |
|---|---|---|---|
| 0:00 | **Problem** | 1 | 62.8% of 15–24-year-olds are unemployed, against 33.6% overall (StatsSA, Q2 2026). The worst-hit group has the least guidance. |
| 0:40 | **Solution and users** | 2 | SAYCEP shows the skills between a young person and a named job, and an ordered route of nearby jobs to get there: the **Pathway**. Two users: the school-leaver and the enrolled student. |
| 1:20 | **Architecture** | 3 | One FastAPI service, SQLite and a React app. Data is O\*NET 29.0 from Kaggle: 879 jobs and 35 skills. |
| 2:00 | **Emerging technology** | 4 | Each job is a 35-number skill vector; your skills are another. Ranking is mean-centred cosine similarity. It's measured: **58.5% against 25.9% by chance**. |
| 2:45 | **Prototype features** | 5 | Five modules. Two built in full (pathway, gap); three in reduced forms I'll name: CV check, interview practice, what employers ask for. |
| 3:15 | **Results** | 6 | 161 automated tests pass. Response about 98 ms at p95. CV score r = 0.27. Accessibility: 169 failures to 0. |
| 4:05 | **Limitations** | 7 | The data isn't South African (O\*NET is American; the course required Kaggle). Too little for students mid-study: no internships, certificates or learnerships. Next: South African occupational data (OFO) with approval, linking skills to SETA learnerships and TVET courses, a user test. |
| **5:00** | **Live demo** | 8 | §3, **10 minutes**. A "DEMO" slide, so you can click away from it cleanly. |
| 15:00 | **Questions** | 9 | |

**If you run long, cut Results to two numbers.** Don't cut Limitations: saying them
yourself before you're asked is worth more than one more statistic.

### Slide outline (the slides are yours; this is a suggestion)

1. **The problem.** Three numbers in a row: 62.8% (15–24), 41.8% (25–34), 33.6%
   (all). Source line: *StatsSA, Quarterly Labour Force Survey, Q2 2026.* Put the
   title (SAYCEP: South African Youth Career and Employment Platform) as the
   slide header, so you need no separate title slide.
2. **The solution.** The route screen (`docs/screenshots/v4/05-route.png`) and
   one line on each user.
3. **Architecture.** `docs/uml/a3/01-architecture.png`, or three boxes: *Kaggle
   O\*NET 29.0 → one FastAPI service + SQLite → React app*.
4. **Emerging technology.** A picture of two vectors and the words *mean-centred
   cosine similarity*, plus the measured result.
5. **Prototype features.** A table: module · what it is · how far it goes.

   | Module | What it is | Built as |
   |---|---|---|
   | Career Pathway Builder | skills → ordered route | full |
   | Skills gap analyser | must-have and desirable gaps | full |
   | CV scanner | skills a CV shows, a measured goal score | reduced: pasted text, rules |
   | What employers ask for | real adverts, summarised | reduced: US adverts, not openings |
   | Interview practice | questions and a checklist | reduced: not a chatbot |
6. **Results.** The numbers in §6, large, with the source of each.
7. **Limitations and next.** Three limits and three next steps.
8. **Demo.** One word.
9. **Questions.**

---

## 3. The demo path

I ran this with a browser walk that clicks every step of this 10-minute path
and checks every number below (and a second run that clicks all 15 steps).
It's built to fit the brief's **10-minute demo slot**: the times are my
estimates, so time it yourself. **Everything marked ✔ is what the app shows.** If a number
on screen ever differs from this page, run the check in §4 and tell me.

Use a first name of your choice at step 1. The walk uses *Thabo*.

### The 10-minute path (about 9½ minutes if it runs smoothly)

| # | Do this | What appears ✔ | Say |
|---|---|---|---|
| **1** *(about 50 s)* | Open the app. Tap **I have a plan code**: the button stays greyed. Type *ZZZZZZ* and tap it. Then tap **I'm new**, type a first name, tap *Start my plan*. | "Find a career you can actually reach." "No email, no password." The wrong code gets: **"No plan matches that code. Check it and try again."** | "Bad input gets a plain message, and the button won't work until a full code is typed. There's no account: a plan code brings you back, and nothing personal is held." *(This is brief 2.1 and 2.4: validation, error feedback, protection of personal data.)* |
| **2** | Tap **I left school**, then tick six skills: *Operation and Control, Operations Monitoring, Equipment Maintenance, Active Listening, Critical Thinking, Monitoring*. | Six skills ticked. | "This is self-reported, the same as a CV: you say what you can do." |
| **3** | **For you**: five operator jobs, each with **why**. Then **Search**, type *electric*, open **Electricians**, tap **Aim for this job**. | Gas Plant Operators, Chemical Equipment Operators… each "Because you have: Operation and Control, Equipment Maintenance…". The job panel has *A day in this job*. | "**This is the emerging-technology step.** Your six skills go in as a 35-number vector; a ranked list comes out, and it's used: it picks the target and orders the route. It says why. Search works on other names too." *(Brief 2.2: valid input, observable result used by the system.)* |
| **4** | Continue. **The gap.** | "You already have **6 of the 34** skills." **2 must-haves**: Troubleshooting and Repairing. | "Two skills stand between this person and the job. Not a long list: the two that the job depends on." |
| **5** | Continue. **The route.** Then *Save as my plan*. | Boilermakers → Electrical Power-Line Installers and Repairers → Electrical and Electronics Repairers → **Electricians**. Each says how close it is to you now. | "This is the Pathway: nearby jobs that need nearly the same skills, ordered so the next step is the most achievable." |
| **6** | **Home.** On *Troubleshooting* tap **Start learning**; then **I can do this now**. | Learning changes nothing. Then the card: **1 of 2** must-haves; *Electrical Power-Line Installers* now ready; "every must-have for **106 jobs**, 4 more than before". | "Only 'I can do this now' closes a gap. 'Learning' doesn't. That's a deliberate rule, so progress isn't flattering." |
| **7** | **Home → Check my CV.** Type *hi*: *Check my CV* stays greyed. Then **Use an example CV → Check my CV.** Add *Repairing*. | Skills with the line that triggered each. After adding: the card again, now **2 of 2** ("You now have everything this job depends on"). "How it reads for Electricians": *Microsoft Excel* and *Multimeters* named; "Troubleshooting: not shown yet". "…read and forgotten, never saved." | "It points at the evidence in your own words, and you confirm each one. Nothing is added automatically." |
| **8** | **Home → What employers ask for → See what employers ask for.** | "**84** real adverts… **United States**, listed in **April 2024**. They've closed." Of the 73 that said a level, **7 in 10** open to beginners; **7 in 10** mention a trade licence; **3 in 10** a driver's licence; skills: Installation, Repairing, Troubleshooting. | "Real adverts, but American and expired, so this shows what employers asked for, not jobs to apply for. I looked for South African data twice. Both sets failed verification." |
| **9** | **Home → Practise for an interview.** Question 2. Type *I fixed it.* → **Get feedback**. Paste the full story → **Get feedback**. | **2 of 7** with tips. Then **7 of 7**. | "It's guidance, not a chatbot. There's no language model in this build. The feedback is a checklist: situation, action, result, your own part." |
| **10** | **Me → Print my plan.** Note the plan code. **Sign out**, then **I have a plan code**. | A one-page plan. The plan comes back, Electricians still the goal. | "That's the whole 'login': a six-character code, and the screen says it's the only key. Nothing from the CV or the interview answers is saved. Saved data is a first name and a skills list." *(Brief 2.4: access control, protection of personal data.)* |

**Full story to paste at step 9** (also in `frontend/tests/demo_walk.js`):

> Last year at my uncle's house the kitchen lights stopped working. I checked the
> plug points with a multimeter and found a loose wire in the switch. I switched
> off the power at the board, tightened the wire and tested it again. In the end
> the lights worked and my uncle saved paying an electrician R450. I learned to
> always test before and after.

### New since the report (6 November): show these if time allows

Both are on `main-7rly7s`. Say **"added since the report"**: the submitted
report and slides describe pasted text and adverts summarised.

| # | Do this | What appears | Say |
|---|---|---|---|
| **N1** *(at step 7)* | On *Check my CV*, use **Upload a CV** and choose a PDF or Word CV. Tap *Check my CV*. | The text appears in the box: "Read … Check the text below". Then the skills it shows. | "You can upload a PDF or Word file now. It's read in the browser, so the file never leaves your device; only the text is checked." |
| **N2** *(after step 6, on Home)* | Scroll to **Jobs for you**. Tap **Apply** on a card, then **See all … jobs for you**. | Job cards marked "Sample listings": "You have 3 of the 8 skills it mentions", "Open to beginners". Apply says it's a demo listing. | "These are real adverts, ranked by how well you fit. They're American and from 2024, so they're labelled as sample listings, not openings. Live South African adverts would come from Adzuna's South Africa API, with approval." |

### Add these if you have the time (to the 15-step version)

| # | Do this | What appears ✔ | Say |
|---|---|---|---|
| **a** | **Explore → Search** *conduit installer* | Electricians, "also called Conduit Installer". Its page: tools of the trade, software, jobs like this. *Save this job*; save two more. | "Search covers the names people actually use." |
| **b** | **Explore → Interests**, answer the 12 | "You lean towards…", jobs that fit. "Simplified." | "For someone who doesn't know job names yet. It's twelve statements of mine matched to O\*NET's interest profiles, labelled as simplified." |
| **c** | **Skills → Repairing → I can already** | **2 of 2**: "You now have everything this job depends on." About **131 jobs** with every must-have. | "That's the goal done. And it opens the door to more jobs." |
| **d** | **Home → Saved jobs →** tick three → **Compare**. Then *Your progress*. | Three columns side by side. Progress **0 → 0 → 1 → 2**. | "Compare, and a record of how the plan moved." |
| **e** | Add `?presenter` to the address. | Job codes, Job Zones and ratings appear. | "The figures stay behind a switch for the marker. Users never see a rating of 4.00." |

Screenshots of each step are in `docs/screenshots/v4/`: use them on slides, and
as your backup if the live demo fails.

### Things that go wrong and how to talk through them

- **A click doesn't respond.** Wait two seconds, then reload the page. The plan
  survives a reload.
- **You lose your place.** Go to *Me*, note the plan code, sign out and back
  in. This is itself a feature you can show.
- **A number differs from this page.** Say what's on screen. Don't read from
  the page. Run §4's check afterwards.

---

## 4. The laptop: setup and the day

**The app and its data don't travel with the repo.** The O\*NET files, the
database and the 517 MB advert file are all kept out of git. A fresh checkout
has none of them, and I found this while preparing this page. The steps below
are the tested path. **Do them on the laptop you'll present from, tonight.**

### Setup (once, about 10 minutes)

```
git clone -b main-7rly7s https://github.com/ShogunLSG/SAYCEP.git     # or main, once merged
cd SAYCEP
pip install -r requirements.txt            # fastapi and uvicorn: the only two
```

1. **Get the O\*NET files.** On Kaggle, open the dataset **O\*NET 29.0 Database**
   (`emarkhauser/onet-29-0-database`), download it, and unzip it so the `.txt`
   files sit directly in **`backend/data/onet/`** (41 files, including
   `Occupation Data.txt`). Don't paste a Kaggle token into chat; the website
   download needs only your Kaggle login.
2. **Build the database:** `python backend/load_onet.py`. It takes a few
   seconds. It should end with two `Adverts:` lines saying *from cache*. If it
   says *skipped*, tell me.
3. **Start the app** from the repo folder:
   `python -m uvicorn app:app --app-dir backend --port 8000`
4. Open **http://127.0.0.1:8000**.

### Check that the demo works (40 seconds)

Needs Node, and Playwright with its browser (test-time only; the app doesn't
use them). From the repo folder: `npm i --no-save playwright`, then
`npx playwright install chromium`.

```
SHORT=1 node frontend/tests/demo_walk.js     # the 10-minute path, about 15 seconds
node frontend/tests/demo_walk.js             # all 15 steps
```

It prints PASS or FAIL for each check and ends with **DEMO PATH OK** if every
number matches this page. (With the server on another port:
`BASE=http://127.0.0.1:8001 node ...`.) **Run it tonight and again tomorrow
morning.** If you'd rather not install Node, just walk the demo by
hand and use §3 as the checklist; the numbers are all there.

### Showing it to a room

- **The app is phone-shaped.** On a laptop screen it shows as a narrow card in
  the middle. **Zoom the browser to 150–175%** (Ctrl and +) and test it on the
  actual projector, as the card can end up too tall.
- **Use a light theme** if the projector washes out dark mode. Dark mode follows
  the operating system.
- **Close the other tabs and turn off notifications.**
- **Start from a clean state:** open the site in a **private window**, so no old
  plan is loaded, or use *Me → Start over from scratch*.
- **Start the app 15 minutes before,** and run the walk once.
- **Wi-Fi doesn't matter.** React is bundled in the repo, and nothing in the demo
  calls out. The text font comes from Google when online and falls back to a
  system font when not, so it may look slightly different but works the same.

### Presenting on Microsoft Teams (6 November: Room 2, 18:00)

- **Share your entire screen, not one window.** Then switching between the
  slides and the browser with Alt+Tab shows up for the markers. Don't use
  "PowerPoint Live": you can't switch to the app from it.
- **Turn on Do not disturb** in Windows, and set Teams itself to Do not
  disturb, so no chat or email pop-ups appear on the shared screen. Close
  WhatsApp, email and other browser tabs.
- **The app runs on the laptop, so Wi-Fi only affects the call.** Keep a phone
  hotspot ready in case the connection drops.
- **Zoom the browser to about 175%.** Shared video is compressed, so small text
  blurs.
- **Join 10–15 minutes early,** test sharing once, and check your microphone.
  Use headphones if you can. Keep the laptop plugged in.
- **The markers can't open your app themselves.** It runs on your laptop, and
  the live link isn't deployed. If sharing fails, post the screenshots from
  `docs/screenshots/demo-2026-11-06/` in the meeting chat and talk through them.

### The live link (safety net)

If you've deployed it (`docs/deploy.md`), the link is `https://<your-app>.fly.dev`.
It's always on, in Johannesburg. Check it with
`BASE=<the link> SHORT=1 node frontend/tests/demo_walk.js` tonight and tomorrow
morning. **Rehearse on the laptop and use the link only if
the laptop fails,** or to let someone try it on their own phone.

### If it breaks on the day

| Problem | Do this |
|---|---|
| Server won't start | Read the last line. "saycep.db is missing" means step 2 wasn't run: `python backend/load_onet.py`. |
| "Address already in use" | Another copy is running. Use `--port 8001` and open that address. |
| Page loads but data is empty | Reload. If it persists, restart the server. |
| The whole laptop fails | Open the live link on any other device. If that fails too, use `docs/screenshots/v4/` as a slideshow and talk through the steps. **Record the demo tonight** with the screen recorder (about 7 minutes) and keep the file on a USB stick and your phone. |

---

## 5. Questions to expect

Grouped by who is likely to ask. Each has a short answer you can say in
20–30 seconds and a pointer to the evidence. **Answers marked ◆ are ones only
you can finish.**

### 5.1 The problem and the users

**Q1.1 Why youth, and why these numbers?**
The gradient is the story: 62.8% unemployment for 15–24, 41.8% for 25–34, 33.6%
overall (StatsSA QLFS Q2 2026). The school-leaver is the worst affected and has
the least guidance. Written work used Q1 (60.9%); Q2 is the latest.

**Q1.2 Who is the user, and did you test it with one?**
Two: the school-leaver (15–24) and the enrolled student. **No, not with a real
first-time user yet**, so NFR-02 (a first-time user reaches a route in five
screens, unassisted) is reported as *partial*. ◆ *If you run the ten-minute
test before the presentation, say what happened, in your own words.*

**Q1.3 Does it help anyone get a job?**
Not measured, and I don't claim it. It's a guidance tool: it makes the gap and
the route visible. Whether that leads to work needs a real follow-up, which is
the next step.

### 5.2 The data

**Q2.1 Why American data (O\*NET) for South African youth?**
Two reasons. The course rule is that all system data comes from Kaggle, and
O\*NET was the best of the five Kaggle datasets I compared: curated expert
ratings of 879 occupations on 35 skills. And skills ratings describe the work, so much of
it transfers; job titles and the labour market don't, and I say so. South
African statistics appear only as written background (ADR-0002, ADR-0003).

**Q2.2 What happened to South African data, TVET and SETA?**
The original plan used ESSA and live job feeds. The Kaggle-only rule removed
them (ADR-0002). TVET and SETA stay in the vocabulary and the written work, but
no longer name data sources.

**Q2.3 Why aren't the adverts South African?**
I looked twice. One Kaggle "South Africa" dataset turned out to be career pages
of two German companies, with most locations elsewhere. The other, newer one is
generated from four templates. The real adverts I could verify are American. So the screen shows
what 84 real electrician adverts asked for, labelled American and closed,
rather than inventing local openings (ADR-0017, `data-sources.md`).

**Q2.4 How current is the data?**
O\*NET 29.0, August 2024. Its ratings are dated between 2010 and 2024, and every
screen that shows a record shows its date (FR-09).

**Q2.5 Why only 35 skills?**
That's the set O\*NET rates for every occupation. A finer set would need data I
don't have. One consequence: Software Developers and Data Scientists aren't
available as goals, because O\*NET 29.0 has no skill ratings for them yet.
Computer Programmers and Web Developers are (`BACKLOG.md`).

**Q2.6 How were the adverts linked to jobs?**
By title only, strictly: one matching O\*NET occupation, with vague titles like
"manager" dropped. That links 21% of the 123,849 adverts, and 438 of 879 jobs
have five or more. On my own check of 50, 44 were clearly right (ADR-0017).

### 5.3 The recommendation engine

**Q3.1 What's the emerging technology, and is it really machine learning?**
It's **content-based recommendation**: each job is a 35-number vector of O\*NET
importance ratings, the user's skills are a vector over the same 35, and jobs are
ranked by **mean-centred cosine similarity**. There's no training: O\*NET has no
outcome labels to learn from, and it stays explainable, because "Because you
have: Operation and Control…" *is* the calculation. It's a classical
information-retrieval technique, and I measured it rather than assumed it.

**Q3.2 How accurate is it?** *(◆ know this one well)*
The measure: for each job, give the engine only that job's must-have skills and
see whether any of its top five recommendations is in the **same occupational
family**. Against a random baseline of 25.9%, it gets **58.5%** over all 713
jobs that have must-haves (95% interval 54.6–62.1) with the job itself *not*
allowed to count. Assignment 3's 59.7% was a sample of 124 that did allow the
job itself, and it still passes the 55% threshold. Honest reading: about twice
chance, on a generous measure of "right". It's a proxy, not proof that people
would take the advice.

**Q3.3 That's only a few points above your threshold. Can you improve it?**
I tried. Adding O\*NET's Knowledge and Abilities to the vectors moves it from
59.7% to 60.5%, which is noise, because users don't record those. It would only
help if users did, and that's a new capture step (ADR-0013).

**Q3.4 Why mean-centred? Why not plain cosine?**
O\*NET's 35 skills are generic, and nearly every job needs most of them, so the
raw vectors all point the same way: a job's nearest neighbour has cosine 0.994.
Subtracting the average job leaves how each job *differs*, which is the signal.
Measured at the time: the share of the top five in the right family rose from
19.4% to 32.4%, against 6.9% by chance.

**Q3.5 Why is "essential" 3.5?**
O\*NET importance ratings cluster on whole numbers, and 3.0 alone holds a third
of them. A cut at 3.0 would flip a third of the data on `>=` versus `>`. 3.5
sits in the gap, and gives about 7 must-haves per job; 3.0 would give 14, which
nobody can act on.

**Q3.6 What if someone over-claims skills?**
Then the gap looks smaller and the recommendations drift. Everything is
self-reported, like a CV, and the screen says so. Progress follows the same
rule: "learning" never closes a gap (ADR-0005).

### 5.4 The modules

**Q4.1 Your proposal said CV scorer, opportunity matching and interview chatbot.
Where are they?**
All three are built, each in a reduced form I can state plainly. The CV scanner
reads pasted text, not files. Opportunity matching became "what employers ask
for", because no South African adverts exist to match against. And the chatbot
is interview *practice*, because a chatbot needs a language model and this build
has none (ADR-0014, 0015, 0017).

**Q4.2 Why no language model?**
It's a project rule, and the CV work is why I'd hold to it anyway. I tried three
smarter text-matching designs, and all did worse than plain word matching: they
suggested "Writing" for "fixed bicycles". Rules are testable, free and
deterministic, and they keep a CV on the user's machine (ADR-0014).

**Q4.3 How good is the CV scanner?**
On 172 held-out CVs from a Kaggle benchmark, its goal score tracks human match
scores at **r = 0.27** (95% interval 0.20–0.33), against 0.16 for word
matching. That's modest, and it's from tech and office CVs, not South African
ones. The skill suggestions are rules I wrote and quote back for the user to
confirm, and I make no accuracy claim for them (ADR-0014, ADR-0018).

**Q4.4 What happens to a CV pasted in?**
It's read and forgotten. It's never stored, and the server doesn't log request
bodies. Only skills the user confirms are saved. That keeps POPIA out of it: a
CV holds names, numbers and addresses.

**Q4.5 Why paste a CV? Why not upload a file?**
Reading PDF and Word files needs a new dependency, and the backend has exactly
two. Paste works now. Upload is a sensible next step.

**Q4.6 How do you know the interview feedback is any good?**
I don't, and I don't claim to. There's no ground truth for answer quality. The
rules are the standard situation-action-result structure plus a few checks,
each unit-tested on worked examples, and the screen calls it guidance.

**Q4.7 Why is "What employers ask for" worth showing if it's American and old?**
It's the only real advert data I could verify. It's useful for what employers
ask for (licences, beginners, tools), less for where to apply. The screen says
so, and I'd rather show verified American data than invent South African data.

### 5.5 The engineering

**Q5.1 Why one service and SQLite? The proposal described several services.**
Deliberately. The proposal documents a multi-service production design; the
prototype is a monolith so it's demonstrable in three weeks. The module
boundaries are kept clean in code, so the recommendation engine could be lifted
out later. (This isn't recorded as an ADR; `architecture.md` has the
reasoning.)

**Q5.2 How was it tested?** *(figures in §6)*
Automated: unit tests, integration and system tests over HTTP, and performance
measurements. Plus an accessibility audit, a keyboard-only walk, and a script
that runs this demo and checks every number. Every figure in my documents is
reproduced by a test, not typed in.

**Q5.3 What about security and privacy?**
There's no account and no password. The only personal data is an optional
first name and a skills list, held under a random six-character plan code. The
code is a bearer credential, and the screen says so. There are about 887
million possible codes, but **there's no rate limiting yet**, which is on the
backlog and would be built before any public hosting (ADR-0008). CVs and
interview answers are never stored.

**Q5.4 Does it scale?**
Not as built, and a prototype doesn't need to. The server uses about 93 MB,
ranks 879 jobs in about 7 ms, and answers every demo-path request in about 120
ms at the 95th percentile (limit: 2 seconds). I've tested 20 requests at once,
not hundreds of users. Beyond that, the plan is a hosted database and the
recommendation engine split out as its own service.

**Q5.5 Is it accessible?**
Measured against WCAG 2.1 AA: an automated audit across 23 screens went from
169 failures to 0, in light and dark mode and at 320 px wide, and a keyboard-only
walk of the whole demo passes. **It hasn't been tried with a real screen reader
or with disabled users**, and that's the honest gap (ADR-0016).

**Q5.6 Is it hosted?**
Yes, as a demo: one small always-on server in Johannesburg on Fly.io, for about
$5 a month. It isn't a production service. Saved plans there reset when it's
redeployed, and there's no rate limiting yet. The fuller plan (a disk for plans,
rate limiting, automatic tests and deploys) is in `docs/plans/hosting.md`.

### 5.6 Requirements and process

**Q6.1 Which requirement does X satisfy?**
FR-01 to FR-10 are built and demonstrable; FR-10 is the loader that rebuilds
the database and aborts on a wrong row count. ◆ **The features added after the
requirements were written** (progress tracking, saved jobs and compare, the
quiz, the CV check, interview practice, employer adverts, accessibility)
**need your requirements, FR-11 onward.** `docs/plans/full-app.md` lists each
one with a measurable figure to build the acceptance test on. Have each one's
wording ready before the presentation.

**Q6.2 Why did the scope grow beyond two modules?**
The plan was to build two and specify three. The core landed early, so I built
the other three after it, in reduced and stated forms. I'd rather show one
module properly than five badly, which is why each reduced form says what it
isn't.

**Q6.3 Why did you change the accuracy figure's baseline?**
Assignment 2 compared 59.7% against a random baseline of 6.9%, but those
measured different things. The matching random baseline for the same measure is
25.8%. The requirement's 55% threshold still passes; the margin I claimed was
overstated, so I corrected it in Assignment 3.

◆ **Q6.4 How did you build this, and how much is yours?**
*This one is only yours to answer, and a marker may ask it.* The repo is open
about it: `CLAUDE.md` sets the rules I gave the AI assistant, `DECISIONS.md`
records each decision and why, and the commit messages credit Claude as
co-author. Be ready to say, in your own words, which decisions were yours (the
Kaggle rule, scope, the plan code, the requirements) and what you can explain
without help (§5.3 to 5.5 above).

### 5.7 The hard ones

**Q7.1 What's the biggest weakness?**
Three, in this order: the data is American, so job titles and the labour market
don't match what a South African user will find; skills are self-reported;
and nobody outside the project has used it yet. All three are stated on the
screens or in the documents.

**Q7.2 What would you do with another month?**
Run the user test properly with school-leavers. Replace or supplement O\*NET
with South African occupational data, if approved. Host it, with rate limiting.
Add file upload for CVs. Measure whether the route changes what people do.

**Q7.3 Is "Electricians" realistic for a school-leaver in South Africa?**
The system shows O\*NET's preparation level ("vocational training or an
apprenticeship"), not South African qualification routes. In practice that
means a trade test through a TVET college or an employer, which is outside the
data I'm allowed to use. It's a limit I'd name, not hide.

**Q7.4 Why should anyone trust a score you made up?**
They shouldn't take it on faith, which is why each figure has a stated
measure, a baseline and a confidence interval, and why the limits are on the
slides. The ranking score is the cosine itself, not a made-up index.

**Q7.5 What if I find a bug right now?**
Fair. The demo path is checked by a script, but not everything is. I'd note it
and fix it. The `BACKLOG.md` lists the ones I already know.

---

### 5.8 "Explain your own design, implementation and testing decisions" (brief 5.4)

This is worth 2 marks and the rubric's top band says *strong individual
understanding*. **Pick three decisions you can explain from start to finish,** one
each for design, implementation and testing. For each, be ready to say in two
sentences: *what I decided, why, and what I rejected*. These are candidates from
the decision log (`docs/DECISIONS.md`); **use only the ones that are true of you and
that you can defend without this page.**

| Kind | Decision | The reason | What was rejected | Evidence |
|---|---|---|---|---|
| Design | Progress has two states: only "I can do this now" closes a gap (ADR-0005) | Self-reported "learning" shouldn't make a plan look finished | One tick box | Unlock card: 1 of 2 only after "can do it now" |
| Design | Sign-in is a six-character plan code, not an account (ADR-0008) | Nothing personal is held, so a password protects nothing a code doesn't | Email and password | `test_api.py`; 887 million possible codes |
| Design | Everything from Kaggle; no South African data (ADR-0002) | The course rule | Live job feeds (ESSA, Adzuna) | Two "South African" datasets failed verification |
| Implementation | Mean-centred cosine over 35 skills, not a trained model (`recommend.py`) | O\*NET vectors all point the same way; no outcome labels to train on; explainable | Plain cosine (nearest neighbour is 0.994 similar); a learned model | 58.5% vs 25.9% by chance (PT-01b) |
| Implementation | CV skills come from rules, not text matching (ADR-0014) | Three smarter designs did worse than plain word matching | TF-IDF, task statements, nearest sentence | r = 0.27 vs 0.16 on 172 held-out CVs |
| Testing | Measure before building, and report limits (ADR-0013, 0020) | Richer vectors moved accuracy by 0.8 points (noise); the first accuracy figure was flattering | Building what sounded better | `performance-2026-10-20.txt` |
| Testing | The demo is run by a script that checks every number (`demo_walk.js`) | A number on a slide that the app doesn't show is the worst thing to find live | Checking by eye | 50 checks, all 15 steps |

◆ **"How much of this is yours?"** may come up (see Q6.4). Your repo is open about
using an AI assistant. Know which of the decisions above you made yourself.

---

## 6. The numbers, in one place

All reproduced by a command or a document in the repo. **Quote only these.**

| Claim | Figure | Where it comes from |
|---|---|---|
| Youth unemployment, Q2 2026 | 62.8% (15–24) · 41.8% (25–34) · 33.6% (all) · 47.4% (15–34) | StatsSA QLFS Q2 2026, released 11 Aug 2026 |
| The data | 879 jobs · 35 skills · 27,463 ratings · O\*NET 29.0 | `load_onet.py`; `test_units.py` |
| Recommendation, as submitted | 59.7% vs 25.8% random, n = 124 | `test_performance.py` PT-01 |
| Recommendation, stricter | **58.5%** vs 25.9% random, 713 jobs, interval 54.6–62.1, target removed | PT-01b |
| Ranking speed | about 5 ms at p95 (limit 100 ms) | PT-02 |
| Response time over HTTP | about 98 ms at p95 (limit 2,000 ms); runs vary, 98–120 ms | PT-03 |
| Rebuild from source | a few seconds (limit 60 s) | PT-04 |
| CV scanner | r = **0.27** on 172 held-out CVs, vs 0.16 word matching | `benchmark-cv-2026-10-09.txt` |
| Employer adverts | 123,849 read · 26,472 linked · 438 jobs with 5+ · Electricians 84 | `adverts-2026-10-05.txt` |
| Advert linking precision | 44 of 50 right (my own check) | `job-postings-step0-2026-10-05.txt` |
| Accessibility | 169 failures to 0 · 23 screens · light, dark, 320 px | `accessibility-2026-10-05.txt` |
| Automated tests | **161**, plus the accessibility, keyboard and demo walks | §7 |
| Dependencies | 2 (FastAPI, uvicorn); the app loads React from files in the repo | `requirements.txt` |

---

## 7. Test counts, checked 5 November on a fresh build

| Check | Result |
|---|---|
| Unit tests (`backend/tests/test_units.py`) | **56** passed |
| Integration and system tests over HTTP (`test_api.py`) | **100** passed |
| Performance and accuracy measurements (`test_performance.py`) | **5** passed |
| **Automated tests in all** | **161** |
| Accessibility audit (axe, WCAG 2.1 A and AA) | **0** failing elements on **23** screens, in light mode, dark mode, and at 320 px wide |
| Keyboard-only walk of the demo | **21** of 21 checks |
| Demo walk (this page's script) | **50** checks over all 15 steps; **40** over the 10-minute path |

Run any of them with `python backend/tests/test_<name>.py` (the server running
for the API and performance ones), or the `node frontend/tests/...` scripts.
The accessibility and keyboard scripts need `axe-core` and Playwright; see the
header of each file.

---

## 8. Open items before you present

- ◆ **Set up the presenting laptop from a fresh copy** (§4) and run `demo_walk.js` on it. Tonight, then again tomorrow morning.
- ◆ **Rehearse against a timer:** 5 minutes of slides, then the 10-minute path (§3), twice.
- ◆ **Record the demo tonight** as the fallback (§4), and keep the screenshots in `docs/screenshots/v4/` to hand.
- ◆ §5.8: choose your three decisions, and §5.3: be able to explain the recommendation maths in your own words.
- The live link is **not deployed** (checked 5 November). Either deploy it tonight (`docs/deploy.md`) or rely on the laptop, recording and screenshots.
- Requirements FR-11 onward (yours), if you're asked about them.
- Rotate the Kaggle token that was pasted into this project's chat.

---

## 9. The written report and slides (brief Q1–Q4)

Besides the presentation, the brief asks for **one searchable PDF, 8–12 pages
(excluding the cover, references and appendices),** named
`ISJ107V_Assignment4_StudentNumber.pdf`, **plus the slides**, both uploaded to
Brightspace. It must carry captions, references, and **declarations of original
work and of permitted AI-tool use**. **A draft was built on 24 October:** `docs/ISJ107V_Assignment4_219045719.pdf` (10 pages of body plus cover, references and two appendices), from `docs/assignment-4-submission.md`, with the diagrams in `docs/uml/a4/`. Rebuild it with `node docs/build-assignment-4.js`, then `soffice --headless --convert-to pdf` on the .docx. **Read it, then fill in and sign the two declarations: they are marked in square brackets.** The table below shows where each question's material came from.

| Brief | Marks | What it asks for | What exists | What's missing |
|---|---|---|---|---|
| **Q1.1** | 2 | Title, problem, users, purpose, emerging technology | Text in `assignment-3-submission.md` | Updating for the current prototype |
| **Q1.2** | 5 | At least 5 functional requirements, split into implemented, partial and deferred | FR-01 to FR-10, all built | The status table; your FR-11 onward |
| **Q1.3** | 2 | Setup and access: software, hardware, sample data, repository location | §4 here; `deploy.md`; repo `github.com/ShogunLSG/SAYCEP` | Pulling it into the report |
| **Q2** | 16 | The working prototype, its workflow, the emerging technology, data and security | **Built** (the demo) | The evidence table (below) |
| **Q3.1–3.5** | 10 | **Five UML diagrams:** use case, activity, class, sequence, component or deployment, plus the differences between design and build | `docs/uml/a3/` has all five types (use case, activity, class, sequence, component and deployment) plus an ERD, drawn in PlantUML on 30 September | **They predate the CV check, interview practice and employer adverts**, so each needs updating |
| **Q4.1** | 4 | At least 5 test cases: expected, actual, status | 161 automated tests with IDs (TC-U, TC-I, PT) | Choosing five and tabulating them |
| **Q4.2** | 2 | At least 2 quantitative measures | Many: p95 response, accuracy, accessibility, CV r | Choosing and presenting |
| **Q4.3** | 2 | Two limitations or risks, each with a corrective action | §5.7 here; `BACKLOG.md` | Writing them up |
| **Declarations** | | Original work, and **permitted AI-tool use** | | **Yours to write and sign** |

**The brief's recommended evidence table** (Requirement · Status · Feature · Test
case · Evidence) is easy to fill from what exists. For example: FR-06 · Completed ·
Recommendations with reasons · PT-01b · "58.5% vs 25.9%".

**Two oddities in the brief.** Q1 is printed as 9 marks but the rubric says 6, so
the total printed would be 53, not 50. And the PDF's own title reads "Assignment 3".
Neither changes what to do, but a marker may notice the same.

**On the AI declaration:** this project used an AI coding assistant throughout, and
the repo records it (`CLAUDE.md`, `DECISIONS.md`, commit co-author lines). The
declaration should say so accurately, and **you need to check that the module's
rules permit it.** I can give you a factual list of what the assistant did, but the
declaration is yours.

**What I can draft for you, in the same pipeline that built Assignment 3** (the
markdown becomes a Word file, then a PDF): the updated diagrams, the setup text,
the test-case and measures tables, and the limitations. The requirements wording
and the declarations stay yours.
