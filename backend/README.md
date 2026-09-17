# Backend

Single FastAPI service. **The API is not yet built.** What exists is `load_onet.py`,
which builds `saycep.db` from the O*NET files — see `../docs/dev-guide.md`.

Responsibilities for the October demo:
- ~~Load the data into SQLite~~ — done, `load_onet.py`. Schema in `../docs/architecture.md`, reasoning in `../docs/dev-guide.md`
- Profile capture for the two user types
- Skills gap analysis: target occupation's required skills minus the user's captured skills, classified essential/desirable
- Career pathway generation: the gap, ordered into steps
- Return source dataset and date with every occupation/skill record (FR-4)

Deliberately a monolith — see the architecture note on why. Keep the gap-analysis and pathway logic in their own modules so they can be extracted later without rework.
