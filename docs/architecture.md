# Architecture

## Tech stack

| Layer | Choice |
|---|---|
| Backend | Node.js |
| Frontend | React |
| ML / scoring | Python microservice |
| AI features | LLM API (provider TBD) |
| External data | ESSA public API |
| Curated data | TVET/SETA dataset |

Nothing has been scaffolded yet beyond placeholder folders (`backend/`, `frontend/`, `ml-service/`).

## Core modules

### 1. Career Pathway Builder (central)
The hub the other four modules feed into. Ties a user's profile, skills, and goals into a recommended path.

### 2. CV builder / scorer
Helps a user build a CV and scores it — likely feeds off the same skills data used by the gap analyser.

### 3. Skills gap analyser
Compares a user's current skills against what a target pathway/role requires.

### 4. Opportunity matching engine
Matches users to opportunities — jobs, learnerships, TVET/SETA programmes — using the curated dataset and ESSA data.

### 5. Interview prep chatbot
LLM-backed chatbot for interview practice, presumably tied to the pathway/role the user is targeting.

## Open questions (not yet decided)

- Which LLM API/provider
- How the Python ML microservice and Node backend talk to each other (REST? message queue?)
- Auth approach
- Hosting/deployment target
