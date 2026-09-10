# Backend

Single FastAPI service. Not yet built.

Responsibilities for the October demo:
- Load the verified Kaggle CSVs into SQLite at startup (schema in `../docs/architecture.md`)
- Profile capture for the two user types
- Skills gap analysis: target occupation's required skills minus the user's captured skills, classified essential/desirable
- Career pathway generation: the gap, ordered into steps
- Return source dataset and date with every occupation/skill record (FR-4)

Deliberately a monolith — see the architecture note on why. Keep the gap-analysis and pathway logic in their own modules so they can be extracted later without rework.
