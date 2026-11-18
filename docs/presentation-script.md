# What I say: the 5-minute talk, slide by slide

*For the presentation on 6 November 2026. It works off the submitted slides,
which stay as they are. Built from my own report answers (Q1.1, Q3.5, Q4.3).
Read it out loud, change anything that doesn't sound like me, and memorise the
**anchors**, not the words.*

Times are spoken at a normal pace. The whole talk is **about 5 minutes**.

---

## Slide 1: Young South Africans are hit hardest by unemployment (about 40 s)

> Good morning. My name is Lesego Matsimela, and my project is SAYCEP, the
> South African Youth Career and Employment Platform.
>
> While I was making my way through high school and then university, I noticed
> that there is very little career guidance for young people, apart from the
> occasional career fair. If you know what you want to do, there's little help
> getting there. And if you don't know yet, there's even less help choosing.
>
> The numbers show who this hurts most. In the second quarter of this year,
> **62.8%** of South Africans aged 15 to 24 were unemployed. That's almost
> **twice** the national rate of 33.6%.
>
> So the problem I'm solving is this: **young people can't see the route from
> the skills they have today to a job that exists.**

**Anchors:** my own experience → 62.8%, almost twice the national rate → can't
see the route from their skills to a job.

## Slide 2: From your skills to a named job (about 40 s)

> SAYCEP works in four steps.
>
> **One, skills:** you tick what you can already do, out of 35 skills, whether
> you learnt it at school, at home or in a part-time job. **Two, the gap:** you
> pick a job to aim for, and it shows the few skills standing between you and
> that job. **Three, the Pathway:** an ordered route of nearby jobs to get
> there, including jobs that need no degree. **Four, progress:** as you learn a
> skill, you mark it, and the plan updates.
>
> It's built for two people: the **school-leaver**, who has no qualification
> and isn't sure what's open to them, and the **enrolled student**, who already
> has a direction and needs a plan.

**Anchors:** skills → gap → Pathway → progress; two users.

## Slide 3: One service, one database, one app (about 40 s)

> Under the hood there are three parts. *(left to right)* The **data** is the
> O\*NET 29.0 database from Kaggle, as the course requires: 879 jobs, 35 skills
> and about 27,000 ratings of how much each job needs each skill. That's served
> by **one Python service** using FastAPI and an SQLite database, and the user
> sees a **React app** that works offline.
>
> It's a single service on purpose. My proposal describes a multi-service
> design for production, but for a prototype one service is faster to build and
> far less likely to fail in a demo. The five modules are kept separate in the
> code, so the recommendation engine can be split out later without a rewrite.

**Anchors:** Kaggle data → one service → React app; one service on purpose,
modules kept separate.

## Slide 4: Matching skills to jobs (about 45 s)

> The emerging technology is the recommendation engine, a form of machine
> learning called content-based recommendation.
>
> Every job is a list of 35 numbers: how much it needs each skill. Your ticked
> skills are another list of 35. The engine first **subtracts the average
> job**, because nearly every job needs skills like reading and listening, and
> those would make every job look the same. What's left is how each job
> *differs*. Then it ranks jobs by **cosine similarity**: how closely your list
> points the same way as each job's. And it tells you which of your skills
> lifted each job.
>
> I measured it. Given a job's must-have skills, with the job itself removed,
> the engine puts a job from the **same field** in its top five **58.5%** of the
> time, against **25.9%** by chance.

**Anchors:** two lists of 35 → subtract the average → point the same way →
58.5% against 25.9%.

**In the demo, show it:** at the *For you* step, tap **How we matched this**
and walk the four steps on screen (demo step N5 in `presentation.md`). Showing
the numbers beats describing them. A second figure, if asked: the same model
compares jobs with jobs and agrees with O\*NET's experts for 60.6% of jobs,
against 5.2% by chance (PT-05).

## Slide 5: What the prototype does (about 30 s)

> There are five modules. The two at the heart of the project are built in
> full: the **Career Pathway Builder** and the **skills gap analyser**.
>
> The other three are built in reduced forms, and I'll be clear about how. The
> **CV check** reads pasted text using rules. **What employers ask for**
> summarises real job adverts, but they're from the US and have closed,
> because Kaggle has no real South African adverts. And **interview practice**
> gives checklist feedback, not a chatbot, because this build deliberately has
> no language model.
>
> Around them: saved plans with progress, saved jobs, an interest quiz, and
> sign-in with a plan code instead of a password.

**Anchors:** two full, three reduced, and say *why* each is reduced.

## Slide 6: Measured results (about 45 s)

> Everything on this slide is reproduced by a test in the repository.
>
> **161** automated tests pass: unit, integration and performance. Responses
> come back in about **100 milliseconds**, against a limit of two seconds. The
> CV check's score agrees with human match scores at **0.27**: that's modest,
> but better than plain word matching at 0.16. And an accessibility audit went
> from **169** failures to **zero** across 23 screens.

**If short of time:** say only the 161 tests and the 169 to zero.

## Slide 7: Limitations, and what comes next (about 50 s)

> I want to name the limitations myself.
>
> **First, the data isn't South African.** The course required Kaggle data,
> and the best skills dataset there is O\*NET, which describes jobs in the
> United States. With the lecturer's approval, the next step is South African
> occupational data, such as the OFO, the framework the SETAs use.
>
> **Second, it does too little for students in the middle of their studies.**
> It gives them a target and a route, but not the internships, certificates or
> learnerships that would build their missing skills. Next, I'd link each
> missing skill to SETA learnerships and TVET short courses.
>
> The skills are also broad and self-reported, and no first-time user has
> tested it yet, so a user test with school-leavers comes next, along with CV
> file upload.

**Don't cut this slide**, even if you're running long. Saying the limits
yourself is worth more than any statistic.

## Slide 8: Live demonstration (switch to the app)

> Let me show you. I'll follow one person, Thabo, a school-leaver, all the way
> through.

Then follow the 10-minute demo path in `docs/presentation.md` §3. What to say at
each step is in the right-hand column there.

## Slide 9: Questions

> That's SAYCEP. Thank you, I'm happy to take questions.

The likely questions and short answers are in `docs/presentation.md` §5.

---

## If you're asked to explain the maths (slide 4)

The simplest true version, in four sentences:

> Each job is a list of 35 numbers, and so is the user. Because almost every
> job needs reading and listening, I subtract the average job first, so I'm
> comparing what makes each job *different*. Cosine similarity then measures
> whether the user's list and the job's list point in the same direction, from
> 1 for the same to minus 1 for opposite. The skills that contributed most to
> that score are the ones the app shows as the reason.
