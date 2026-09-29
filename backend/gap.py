"""Gap Analyser -- FR-07.

Compares a profile's captured skills against a target occupation's requirements
and classifies each missing skill as essential or desirable.

The raw importance rating travels with every result. The screen shows it beside
the label, so "why is this essential?" is answered by the number on screen
rather than by a rule the user has to be told about.
"""

from config import ESSENTIAL_THRESHOLD
import repository


def compute_gap(con, profile_id, soc_code):
    held = set(repository.profile_skill_ids(con, profile_id))
    required = repository.required_skills(con, soc_code)

    missing, already_held = [], []
    for row in required:
        entry = {
            "element_id": row["element_id"],
            "name": row["name"],
            "importance": round(row["importance"], 2),
            "importance_scale_max": row["importance_scale_max"],
            "classification": ("essential" if row["importance"] >= ESSENTIAL_THRESHOLD
                               else "desirable"),
            "source_date": row["source_date"],
        }
        (already_held if row["element_id"] in held else missing).append(entry)

    essential = [m for m in missing if m["classification"] == "essential"]

    return {
        "profile_id": profile_id,
        "target": dict(repository.get_occupation(con, soc_code)),
        "threshold": ESSENTIAL_THRESHOLD,
        "missing": missing,
        "missing_essential_count": len(essential),
        "missing_desirable_count": len(missing) - len(essential),
        "already_held_count": len(already_held),
        "required_total": len(required),
        # The plan flagged this: a user who ticks most of the 35 can produce an
        # empty gap, and a blank list reads as a broken screen rather than as
        # good news. Say something instead.
        "message": (None if missing else
                    "You already hold every skill this occupation requires. "
                    "Try a target in a higher preparation level."),
    }
