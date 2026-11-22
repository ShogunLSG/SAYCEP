# Happy path: Thabo, from first screen to a saved plan

Thabo is a school-leaver in Soweto who wants to be an electrician. Everything
below was run against the app on 21 November 2026 (the browser walk
`frontend/tests/demo_walk.js` passes steps 1 to 11). About 8 to 10 minutes.

**Before you start:** restart the server (`python -m uvicorn app:app --app-dir backend --port 8000`)
and have `Thabo_Mokoena_CV.docx` ready to upload.

| # | You do | The app shows | You say |
|---|---|---|---|
| 1 | Open the app. Tap **I'm new**, type *Thabo*, **Start my plan**. | "Find a career you can actually reach." No email, no password. | "No account. A plan code brings you back and nothing personal is held." |
| 2 | **I left school.** Tick: Installation, Equipment Maintenance, Troubleshooting, Active Listening, Critical Thinking, Coordination. | Six ticks. | "He says what he can do, as he would on a CV." |
| 3 | **For you**, then Search *electric*, open **Electricians**, **Aim for this job**. | Millwrights 0.65, Elevator and Escalator Installers 0.61, **Helpers--Electricians 0.57**, Maintenance and Repair Workers 0.57, Telecommunications Installers 0.57, each with "Because you have…". | "This is the emerging technology. His six skills become a list of 35 numbers, the model ranks 879 jobs, and it says why. He wants the trade itself, so he searches for it." |
| 3b | Tap **How we matched this** under Millwrights. | The two views: ratings 0.615 and must-have list 0.679, averaged to 0.647. Without centring scores sit between 0.25 and 0.51. | "Two views of the job, averaged. Subtracting the average job is what makes jobs tell apart." |
| 4 | **The gap.** | Holds **6 of 34** skills. **2 must-haves, 1 missing: Repairing.** 27 nice-to-have. | "One skill stands between him and the job." |
| 5 | **The route.** Then **Save as my plan**. | **Helpers--Electricians → Electricians.** "Start here", "Leads to the next step… same field of work", and "Also at this level" alternatives. | "One level at a time. The model picks each step: the related job one level down whose skills are closest to the next. If nothing is close enough, it says aim directly." |
| 6 | **Home.** On **Repairing**, tap **Start learning**. | The card stays at **1 of 2**. | "Learning doesn't close a gap. Only 'I can do this now' does, so progress isn't flattering." |
| 7 | **Home → Check my CV.** Upload `Thabo_Mokoena_CV.docx`, **Check my CV**. Add **Repairing**. | Suggests Repairing, quoting "Fixed broken bicycles and small appliances". Names *Microsoft Excel* and *Multimeters* for Electricians. After adding: **2 of 2**, "You now have everything this job depends on". | "It points at the evidence in his own words and he confirms each skill. The CV found the one skill the job was missing. It's read and forgotten, never saved." |
| 8 | **Home → What employers ask for.** | **84** adverts, **United States**, April 2024, closed. 7 in 10 open to beginners, 7 in 10 mention a trade licence. | "Real adverts but American and expired, so it shows what employers ask for, not jobs to apply for." |
| 9 | **Practise for an interview**, question 2. Type *I fixed it.*, then paste a full story. | **2 of 7** with tips, then **7 of 7**. | "A checklist, not a chatbot. There's no language model in this build." |
| 10 | **Me → Print my plan.** Note the code. Sign out, then **I have a plan code**. | A one-page plan. The plan comes back with Electricians as the goal. | "The six-character code is the whole login. Nothing from the CV or interview is saved." |

## If someone asks

- **"Why Helpers--Electricians first?"** The experts list it as related, it is one
  level down, and its skills are close to an electrician's (0.73).
- **"Why is the route only two steps?"** A step has to be a related job one level
  down and similar enough (0.70). There's no good job below it, so it doesn't
  invent one.
- **"Is the data South African?"** No. It's US (O\*NET and LinkedIn adverts via
  Kaggle). Both South African Kaggle sets failed checks.

## Things to know before you click

- The CV check lists *Bicycles* and *Irons* among the tools it found. That is how
  the rule-based scanner reads "fixed bicycles" and "soldering irons". It also says
  Troubleshooting is "not shown yet" in the CV, though Thabo ticked it himself.
  Both are true to the rules; know them in case someone asks.
- The 84 adverts come from the loaded data. If a number on screen differs from
  this page, tell me and I'll re-measure.
