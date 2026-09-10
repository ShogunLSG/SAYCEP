# Architecture

There are two architectures in this project and keeping them distinct matters: the one being **built for the October demo**, and the one **documented as the production design**. They are deliberately different, and being able to explain why is worth marks.

## Demo architecture (what gets built)

One service. One database file. One frontend.

| Layer | Choice |
|---|---|
| Backend | Python (FastAPI) — single service |
| Database | SQLite (file-based, no server to run) |
| Frontend | React |
| AI features | LLM API called from the backend |
| Data | Kaggle CSVs loaded into SQLite at startup (see `data-sources.md`) |

**Why this and not the original stack.** The proposal named Node.js plus a separate Python ML microservice plus React. That's three deployable services to wire, configure and debug. With a working demo due in roughly three weeks and one developer, three services is where the time goes — into plumbing rather than into anything demonstrable. Python is the better single choice because the Kaggle data work (loading CSVs, similarity scoring) is native to it, and SQLite removes a whole class of setup problems.

**If asked why the demo is a monolith:** because iteration speed matters more than separation at this stage, and the module boundaries are preserved in code so the ML component can be extracted into its own service without rework. That's a real answer, not an excuse — keep the boundaries clean enough that it stays true.

## Production architecture (what gets documented)

The original design stands as the target: Node.js or Python API, React frontend, a separate Python ML microservice that can scale independently of the request path, and an external job/opportunity data feed. Document it in the proposal; don't build it by October.

## The data spine

Both built modules run off one structure, which is why they're the right pair to build:

```
occupations        (id, title, description, source_dataset, source_date)
skills             (id, name, category, source_dataset, source_date)
occupation_skills  (occupation_id, skill_id, importance)   -- essential vs desirable
users              (id, profile_type, target_occupation_id)
user_skills        (user_id, skill_id, level)
```

A gap is `occupation_skills` for the target minus `user_skills`. A pathway is that gap ordered into steps. One structure, two modules — that's the whole reason this pair is cheap to build together.

The `source_dataset` / `source_date` columns exist so the system can show where every record came from. That directly answers the data-provenance concern behind the Kaggle rule (see FR-4 in `functional-requirements.md`).

## Core modules

### Built for October
1. **Career Pathway Builder** (central) — the declared hub; ties profile, skills and target into an ordered path.
2. **Skills gap analyser** — compares captured skills against the target occupation's required set.

### Designed, not built
3. **CV builder / scorer** — stretch goal if the core lands early; demos well but CV parsing is a time sink.
4. **Opportunity matching engine** — blocked on whether the SA job postings dataset is usable.
5. **Interview prep chatbot** — cheap to build with an LLM but shallow under questioning; low priority.

Specify all five fully in the proposal. Build two properly. Say clearly in the presentation which is which — claiming more than is built is the fastest way to lose the room.

## Decisions still open

- Which LLM API/provider (and whether the demo needs it at all — the two built modules may not)
- Auth for the demo: likely none, or a hardcoded demo user. Real auth is production scope.
- Hosting: local for the demo unless he requires a live URL — worth confirming.
