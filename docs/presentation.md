# Presentation: Saturday 24 October 2026

The script, the demo path, what to do if it breaks, and the questions to
expect. **The words are suggestions: put them in your own voice.** You're
questioned on this work directly, so anything you say should be something you
can defend without this page.

**Assumption to confirm:** I don't know how long your slot is. This is built for
**about 15 minutes of talk and demo, then questions**. §2 shows how to cut it
to 10 or stretch it to 20. If your lecturer gave a length or a rubric for the
presentation, tell me and I'll reshape this.

---

## 0. Three things to know before you start

**1. Present from the laptop, not a web link.** Hosting isn't built (the Fly.io
plan is for after). The app runs on the machine you present from. §4 is the
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

## 2. Running order (15 minutes)

| Time | What | Slide | Notes |
|---|---|---|---|
| 0:00 | **The problem** | 1–2 | The gradient is the point: 62.8% for 15–24 against 33.6% overall. |
| 1:30 | **The solution and the two users** | 3 | The school-leaver and the enrolled student. The central artifact is the **Pathway**. |
| 2:30 | **Five modules, and what each really is** | 4 | Say the reduced forms up front; it earns trust. |
| 3:30 | **How it works** | 5 | One diagram. Skills as vectors, cosine similarity, O\*NET from Kaggle, one service. |
| 4:30 | **Live demo** | 6 | §3. About 7 minutes. |
| 11:30 | **Evidence** | 7 | The numbers, §6. Every one reproduced by a test. |
| 13:00 | **Limits and what's next** | 8 | Say them yourself before you're asked. |
| 14:00 | **Questions** | 9 | |

**To cut to 10 minutes:** merge slides 1–2 and 4–5, and use the 6-minute demo
below. **To stretch to 20:** run the full 15-step demo and add the quiz and the
compare page.

### Slide outline (the slides are yours; this is a suggestion)

1. **Title.** SAYCEP: South African Youth Career and Employment Platform. One
   sentence under it: skills → target → gap → route.
2. **The problem.** Three numbers in a row: 62.8% (15–24), 41.8% (25–34), 33.6%
   (all). Source line: *StatsSA, Quarterly Labour Force Survey, Q2 2026.*
3. **The solution.** The route screen (`docs/screenshots/v4/05-route.png`) and
   two lines on the two users.
4. **Five modules.** A table: module · what it is · how far it goes.

   | Module | What it is | Built as |
   |---|---|---|
   | Career Pathway Builder | skills → ordered route | full |
   | Skills gap analyser | must-have and desirable gaps | full |
   | CV scanner | skills a CV shows, a measured goal score | reduced: pasted text, rules |
   | What employers ask for | real adverts, summarised | reduced: US adverts, not openings |
   | Interview practice | questions and a checklist | reduced: not a chatbot |
5. **How it works.** `docs/uml/a3/01-architecture.png`, or three boxes: *Kaggle
   O\*NET 29.0 (879 jobs, 35 skills) → one FastAPI service + SQLite → React app*.
6. **Demo.** A title slide saying DEMO, so you can click away from it cleanly.
7. **Evidence.** The five numbers in §6, large.
8. **Limits and next.** Four bullets: American data, self-reported skills,
   modest CV accuracy, no real-user test yet. Next: hosting, South African data
   with approval, user testing.
9. **Questions.**

---

## 3. The demo path

I ran this on 20 October with a browser walk that clicks every step of this
7-minute path, and a second run that clicks all 15, and checks every number
below. **Everything marked ✔ is what the app shows.** If a number
on screen ever differs from this page, run the check in §4 and tell me.

Use a first name of your choice at step 1. The walk uses *Thabo*.

### The 7-minute path (recommended)

| # | Do this | What appears ✔ | Say |
|---|---|---|---|
| **1** | Open the app. Type a first name, tap *Start my plan*. | "Find a career you can actually reach." "No email, no password." | "There's no account. A plan code brings you back; nothing personal is held." |
| **2** | Tap **I left school**, then tick six skills: *Operation and Control, Operations Monitoring, Equipment Maintenance, Active Listening, Critical Thinking, Monitoring*. | Six skills ticked. | "This is self-reported, the same as a CV: you say what you can do." |
| **3** | **For you**: five operator jobs, each with **why**. Then **Search**, type *electric*, open **Electricians**, tap **Aim for this job**. | Gas Plant Operators, Chemical Equipment Operators… each "Because you have: Operation and Control, Equipment Maintenance…". The job panel has *A day in this job*. | "It recommends by how closely the skills match, and says why. Search works on other names too, which I'll show." |
| **4** | Continue. **The gap.** | "You already have **6 of the 34** skills." **2 must-haves**: Troubleshooting and Repairing. | "Two skills stand between this person and the job. Not a long list: the two that the job depends on." |
| **5** | Continue. **The route.** Then *Save as my plan*. | Boilermakers → Electrical Power-Line Installers and Repairers → Electrical and Electronics Repairers → **Electricians**. Each says how close it is to you now. | "This is the Pathway: nearby jobs that need nearly the same skills, ordered so the next step is the most achievable." |
| **6** | **Home.** On *Troubleshooting* tap **Start learning**; then **I can do this now**. | Learning changes nothing. Then the card: **1 of 2** must-haves; *Electrical Power-Line Installers* now ready; "every must-have for **106 jobs**, 4 more than before". | "Only 'I can do this now' closes a gap. 'Learning' doesn't. That's a deliberate rule, so progress isn't flattering." |
| **7** | **Home → Check my CV → Use an example CV → Check my CV.** Add *Repairing*. | Skills with the line that triggered each. After adding: the card again, now **2 of 2** ("You now have everything this job depends on"). "How it reads for Electricians": *Microsoft Excel* and *Multimeters* named; "Troubleshooting: not shown yet". "…read and forgotten, never saved." | "It points at the evidence in your own words, and you confirm each one. Nothing is added automatically." |
| **8** | **Home → What employers ask for → See what employers ask for.** | "**84** real adverts… **United States**, listed in **April 2024**. They've closed." Of the 73 that said a level, **7 in 10** open to beginners; **7 in 10** mention a trade licence; **3 in 10** a driver's licence; skills: Installation, Repairing, Troubleshooting. | "Real adverts, but American and expired, so this shows what employers asked for, not jobs to apply for. I looked for South African data twice. Both sets failed verification." |
| **9** | **Home → Practise for an interview.** Question 2. Type *I fixed it.* → **Get feedback**. Paste the full story → **Get feedback**. | **2 of 7** with tips. Then **7 of 7**. | "It's guidance, not a chatbot. There's no language model in this build. The feedback is a checklist: situation, action, result, your own part." |
| **10** | **Me → Print my plan.** Note the plan code. **Sign out**, then **I have a plan code**. | A one-page plan. The plan comes back, Electricians still the goal. | "That's the whole 'login': a six-character code. The screen says it's a bearer credential." |

**Full story to paste at step 9** (also in `frontend/tests/demo_walk.js`):

> Last year at my uncle's house the kitchen lights stopped working. I checked the
> plug points with a multimeter and found a loose wire in the switch. I switched
> off the power at the board, tightened the wire and tested it again. In the end
> the lights worked and my uncle saved paying an electrician R450. I learned to
> always test before and after.

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
are the tested path. **Do them on the laptop you'll present from, by Wednesday.**

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
SHORT=1 node frontend/tests/demo_walk.js     # the 7-minute path, about 15 seconds
node frontend/tests/demo_walk.js             # all 15 steps
```

It prints PASS or FAIL for each check and ends with **DEMO PATH OK** if every
number matches this page. (With the server on another port:
`BASE=http://127.0.0.1:8001 node ...`.) **Run it on Wednesday, Thursday, and the
morning of the 24th.** If you'd rather not install Node, just walk the demo by
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

### If it breaks on the day

| Problem | Do this |
|---|---|
| Server won't start | Read the last line. "saycep.db is missing" means step 2 wasn't run: `python backend/load_onet.py`. |
| "Address already in use" | Another copy is running. Use `--port 8001` and open that address. |
| Page loads but data is empty | Reload. If it persists, restart the server. |
| The whole laptop fails | Use `docs/screenshots/v4/` as a slideshow, and talk through the steps. **Record the demo on Friday** with the screen recorder (about 7 minutes) and keep the file on a USB stick and your phone. |

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
test before Saturday, say what happened, in your own words.*

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
Not yet. It runs locally for the prototype. A Fly.io plan exists, about $3 a
month with a Johannesburg region, and `docs/plans/hosting.md` has it.

### 5.6 Requirements and process

**Q6.1 Which requirement does X satisfy?**
FR-01 to FR-10 are built and demonstrable; FR-10 is the loader that rebuilds
the database and aborts on a wrong row count. ◆ **The features added after the
requirements were written** (progress tracking, saved jobs and compare, the
quiz, the CV check, interview practice, employer adverts, accessibility)
**need your requirements, FR-11 onward.** `docs/plans/full-app.md` lists each
one with a measurable figure to build the acceptance test on. Have each one's
wording ready before Saturday.

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

## 6. The numbers, in one place

All reproduced by a command or a document in the repo. **Quote only these.**

| Claim | Figure | Where it comes from |
|---|---|---|
| Youth unemployment, Q2 2026 | 62.8% (15–24) · 41.8% (25–34) · 33.6% (all) · 47.4% (15–34) | StatsSA QLFS Q2 2026, released 11 Aug 2026 |
| The data | 879 jobs · 35 skills · 27,463 ratings · O\*NET 29.0 | `load_onet.py`; `test_units.py` |
| Recommendation, as submitted | 59.7% vs 25.8% random, n = 124 | `test_performance.py` PT-01 |
| Recommendation, stricter | **58.5%** vs 25.9% random, 713 jobs, interval 54.6–62.1, target removed | PT-01b |
| Ranking speed | about 7 ms at p95 (limit 100 ms) | PT-02 |
| Response time over HTTP | about 120 ms at p95 (limit 2,000 ms) | PT-03 |
| Rebuild from source | a few seconds (limit 60 s) | PT-04 |
| CV scanner | r = **0.27** on 172 held-out CVs, vs 0.16 word matching | `benchmark-cv-2026-10-09.txt` |
| Employer adverts | 123,849 read · 26,472 linked · 438 jobs with 5+ · Electricians 84 | `adverts-2026-10-05.txt` |
| Advert linking precision | 44 of 50 right (my own check) | `job-postings-step0-2026-10-05.txt` |
| Accessibility | 169 failures to 0 · 23 screens · light, dark, 320 px | `accessibility-2026-10-05.txt` |
| Automated tests | **161**, plus the accessibility, keyboard and demo walks | §7 |
| Dependencies | 2 (FastAPI, uvicorn); the app loads React from files in the repo | `requirements.txt` |

---

## 7. Test counts, checked 20 October

| Check | Result |
|---|---|
| Unit tests (`backend/tests/test_units.py`) | **56** passed |
| Integration and system tests over HTTP (`test_api.py`) | **100** passed |
| Performance and accuracy measurements (`test_performance.py`) | **5** passed |
| **Automated tests in all** | **161** |
| Accessibility audit (axe, WCAG 2.1 A and AA) | **0** failing elements on **23** screens, in light mode, dark mode, and at 320 px wide |
| Keyboard-only walk of the demo | **21** of 21 checks |
| Demo walk (this page's script) | **47** checks over all 15 steps; **37** over the 7-minute path |

Run any of them with `python backend/tests/test_<name>.py` (the server running
for the API and performance ones), or the `node frontend/tests/...` scripts.
The accessibility and keyboard scripts need `axe-core` and Playwright; see the
header of each file.

---

## 8. Open items before Saturday

- ◆ Requirements FR-11 onward (yours).
- ◆ Your slides, and a timed run-through with them.
- ◆ Q1.2: run the first-time-user test if you can, and add what you find.
- ◆ Q6.4: your own answer on how you built this.
- Set up the laptop (§4), and run `demo_walk.js` on it.
- Record the demo on Friday as a backup.
- Rotate the Kaggle token that was pasted into this project's chat.
