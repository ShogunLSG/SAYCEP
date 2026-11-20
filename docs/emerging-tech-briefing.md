# The emerging technology: a briefing to know and explain

For you, not the app. Every number was measured on 20 November 2026 against the
real data, and Thabo is the running example (his plan is in `docs/thabo/`).

## In one breath

> "Every job is 35 numbers, one for each skill, and so is the person. We subtract
> the average job so only what makes a job different counts, then measure how
> closely the person and the job point the same way. We do it twice, once with how
> much each skill matters and once with the job's must-have list, and average the
> two. There's no language model: it's a recommender built from O\*NET's own
> ratings, and it shows its working."

That is the **skill-matching model**, a content-based recommender: mean-centred
cosine similarity over 35 skills. "Emerging technology" here means machine
learning for recommendation. It is the part of AI that ranks things by how well
they fit, which is not the same as a chatbot.

## The four ideas, each with a picture

**1. A job is a list of 35 numbers.** O\*NET rates how important each skill is to
each job, 1 to 5. Gas Plant Operators rates Operation and Control 3.75 and
Operations Monitoring 4.12. A person is the same 35 slots with a 1 for each skill
they ticked and a 0 for the rest. Thabo has six 1s.

**2. Cosine similarity asks "do these two lists point the same way?"** It ignores
how long the lists are. Same direction scores near 1, unrelated near 0, opposite
below 0. Think of two people walking: cosine ignores how fast, only where to.

**3. Centring stops the generic skills drowning out the signal.** Almost every job
rates listening, speaking and reading highly. Measured: a job's nearest neighbour
scores **0.994 out of 1**, so plain cosine barely tells jobs apart. For Thabo,
plain scores sit between **0.27 and 0.58** across all 879 jobs. After subtracting
each skill's average they spread from **-0.47 to 0.70**.
*Picture:* an exam where everyone gets the easy questions right. Subtract the
class average on each question and only the hard questions separate people.

**4. Two views, averaged.** Thabo's ticks are yes or no, so we also compare them
with each job's yes/no must-have list (skills rated 3.5 or more, or its top five
where none are). For Gas Plant Operators his two scores are **0.641** (ratings)
and **0.763** (must-have list), and (0.641 + 0.763) / 2 = **0.702**.

## Why centring matters, in four skills

A made-up test with four skills, run to check the claim:

| Job | Plain cosine | Centred, both views |
|---|---|---|
| Electrician | 0.75 | **0.98** |
| Welder | **0.80** | 0.38 |
| Receptionist | 0.31 | -0.88 |

A person who ticked Troubleshooting and Repairing. Plain cosine ranks the Welder
above the Electrician, which is wrong, because the Electrician's must-haves are
exactly those two skills. Centring fixes the order.

## The evidence, and what each number means

| Claim | Number | What it means |
|---|---|---|
| Accuracy (PT-01b) | **67.5%** against **25.9%** by chance | For each of 713 jobs we build a person from its must-haves, hide the job, and count a hit if any of the five closest jobs is in the same family. Interval 64.0 to 70.8. |
| Agrees with the experts (PT-05) | **60.6%** against **5.2%** | Its five closest jobs include one O\*NET's own experts list as related, 11.6 times better than chance. |
| Before the improvement | 58.5% | The submitted report. Say "improved since the report" (ADR-0027). |
| With messy users | 53.6% against 46.8% before | Simulated realistic users. The gain shrinks as input gets messier but stays positive. |

## Things we tried that did not work (say these, they show it wasn't a guess)

- **Ten techniques** were tested (standardising, LDA, PCA, smoothing with related
  jobs and more). Only the must-have view helped.
- **Learned weights** scored 68.0% on clean tests and fell apart with realistic
  users: overfitting. Rejected.
- **Hiding the everyday skills.** Hidden from the tick screen but still counted, it
  costs **14 points** (67.5% to 53.4%), because an unticked skill that the average
  job needs counts against everyone. Dropped from the model altogether, five of
  them cost 4 points (63.3%). So we show them last (ADR-0032) instead.

## What not to claim

- It is **not** a language model or a chatbot, and nothing is learned from users.
- It is **not** trained. It uses O\*NET's survey ratings directly, which is why it
  can explain itself.
- The 67.5% is on **simulated** people built from each job's must-haves, not on
  real users. The user test for NFR-02 hasn't been run.
- The data is **US** (the course allowed only Kaggle, and both Kaggle "South
  Africa" sets failed checks).

## Likely questions

**Why this and not machine learning proper?** There's no outcome data to learn
from, only survey ratings. The learned version overfitted. This one is explainable,
and that matters when a young person asks why a job was suggested.

**Why average two views?** Ratings keep how much each skill matters but let many
middling skills dilute what defines a job. The must-have list compares yes/no with
yes/no. Each is weaker alone. Together they took it from 58.5% to 67.5%.

**Why 3.5 for a must-have?** Ratings cluster on whole numbers (32.5% sit at 3.0),
so 3.0 would flip a third of the data on a rounding choice. 3.5 sits in the gap
between the 3.0 and 4.0 clusters and leaves about seven must-haves per job.

**What does 25.9% mean?** The score for picking five jobs at random: about one in
four land in the right family by luck. That's the bar to beat.

**Is it fair?** It ranks by the skills a person says they have (and, for a student
who gives one, a field of study, weighted 0.1). It never uses age, gender, name or
place. Its limit is that the data describes the US labour market.
