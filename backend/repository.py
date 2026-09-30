"""Occupation Repository -- all database access lives here.

Named to match the component in the sequence diagram (docs/uml/04-sequence).
Keeping every query in one module is what makes the monolith splittable later:
the data service is already a seam, it just isn't a network boundary yet.

Profile tables are created here rather than by the loader, because the loader
rebuilds reference data and knows nothing about users.
"""

import secrets
import sqlite3
import uuid

from config import DB_PATH

PROFILE_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    profile_id      TEXT PRIMARY KEY,
    profile_type    TEXT NOT NULL CHECK (profile_type IN ('student', 'school_leaver')),
    target_soc_code TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    display_name    TEXT,
    plan_code       TEXT
);
-- plan_code reopens a plan on any device (ADR-0008). Its uniqueness is a
-- separate index, created in ensure_profile_tables after any upgrade, so an
-- older database can gain the column in place.

-- status: 'held' is a skill the user can do now, and the only kind the gap,
-- pathway and recommendations count. 'learning' is one they are working on --
-- it shows on the dashboard and never closes a gap. ADR-0005.
CREATE TABLE IF NOT EXISTS user_skills (
    profile_id  TEXT NOT NULL REFERENCES users(profile_id) ON DELETE CASCADE,
    element_id  TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'held' CHECK (status IN ('held', 'learning')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (profile_id, element_id)
);

-- Jobs a user has saved to come back to or compare (slice 3, ADR-0010).
CREATE TABLE IF NOT EXISTS saved_occupations (
    profile_id  TEXT NOT NULL REFERENCES users(profile_id) ON DELETE CASCADE,
    soc_code    TEXT NOT NULL,
    saved_at    TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (profile_id, soc_code)
);
"""

SKILL_STATUSES = ("held", "learning")


def connect():
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def ensure_profile_tables(con):
    con.executescript(PROFILE_SCHEMA)
    # A database built before ADR-0005 has user_skills without status. The
    # loader rebuilds from scratch so this rarely matters, but a server started
    # on an old file must not fail on its first profile call.
    user_cols = {r[1] for r in con.execute("PRAGMA table_info(users)")}
    for col in ("display_name", "plan_code"):
        if col not in user_cols:
            con.execute(f"ALTER TABLE users ADD COLUMN {col} TEXT")
    con.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_plan_code ON users(plan_code)")
    cols = {r[1] for r in con.execute("PRAGMA table_info(user_skills)")}
    if "status" not in cols:
        con.execute("ALTER TABLE user_skills ADD COLUMN status TEXT NOT NULL DEFAULT 'held'"
                    " CHECK (status IN ('held', 'learning'))")
        con.execute("ALTER TABLE user_skills ADD COLUMN updated_at TEXT NOT NULL DEFAULT ''")
    con.commit()


def reference_data_present(con):
    """NFR-03: refuse to serve rather than serve partial data."""
    try:
        return con.execute("SELECT COUNT(*) FROM occupations").fetchone()[0] > 0
    except sqlite3.OperationalError:
        return False


# ---------- catalogue ----------

_ALT_MATCH = ("EXISTS (SELECT 1 FROM occupation_alt_titles a"
              " WHERE a.soc_code = o.soc_code AND LOWER(a.title) LIKE ?)")


def list_occupations(con, zone=None, query=None, limit=100):
    """Title search also matches O*NET's alternate titles (ADR-0009), so
    "conduit installer" finds Electricians. Official-title matches come first;
    an alternate-title match says which name it matched as also_called."""
    if not query:
        sql, args = ["SELECT soc_code, title, job_zone, source_dataset, NULL AS also_called"
                     "  FROM occupations o WHERE 1=1"], []
        if zone is not None:
            sql.append("AND job_zone = ?")
            args.append(zone)
        sql.append("ORDER BY title LIMIT ?")
        args.append(limit)
        return con.execute(" ".join(sql), args).fetchall()
    like = f"%{query.lower()}%"
    sql = ["SELECT o.soc_code, o.title, o.job_zone, o.source_dataset,"
           "  CASE WHEN LOWER(o.title) LIKE ? THEN NULL ELSE"
           "   (SELECT a.title FROM occupation_alt_titles a WHERE a.soc_code = o.soc_code"
           "     AND LOWER(a.title) LIKE ? ORDER BY LENGTH(a.title) LIMIT 1) END AS also_called"
           "  FROM occupations o WHERE (LOWER(o.title) LIKE ? OR " + _ALT_MATCH + ")"]
    args = [like, like, like, like]
    if zone is not None:
        sql.append("AND o.job_zone = ?")
        args.append(zone)
    sql.append("ORDER BY LOWER(o.title) LIKE ? DESC, o.title LIMIT ?")
    args += [like, limit]
    return con.execute(" ".join(sql), args).fetchall()


def count_occupations(con, zone=None, query=None):
    sql = ["SELECT COUNT(*) FROM occupations o WHERE 1=1"]
    args = []
    if zone is not None:
        sql.append("AND o.job_zone = ?")
        args.append(zone)
    if query:
        like = f"%{query.lower()}%"
        sql.append("AND (LOWER(o.title) LIKE ? OR " + _ALT_MATCH + ")")
        args += [like, like]
    return con.execute(" ".join(sql), args).fetchone()[0]


def get_occupation(con, soc_code):
    return con.execute(
        "SELECT o.soc_code, o.title, o.description, o.job_zone, o.source_dataset,"
        "       z.name AS zone_name, z.education, z.experience, z.training"
        "  FROM occupations o JOIN job_zone_reference z ON z.zone = o.job_zone"
        " WHERE o.soc_code = ?", (soc_code,)).fetchone()


def list_skills(con):
    return con.execute(
        "SELECT element_id, name, description, source_dataset"
        "  FROM skills ORDER BY name").fetchall()


def job_zones(con):
    return con.execute(
        "SELECT z.zone, z.name, z.education, z.experience, z.training,"
        "       COUNT(o.soc_code) AS occupation_count"
        "  FROM job_zone_reference z LEFT JOIN occupations o ON o.job_zone = z.zone"
        " GROUP BY z.zone ORDER BY z.zone").fetchall()


def required_skills(con, soc_code):
    return con.execute(
        "SELECT s.element_id, s.name, s.description, os.importance,"
        "       os.importance_scale_max, os.source_date"
        "  FROM occupation_skills os JOIN skills s ON s.element_id = os.element_id"
        " WHERE os.soc_code = ? ORDER BY os.importance DESC", (soc_code,)).fetchall()


def occupation_tasks(con, soc_code, limit=8):
    """Most important first; core tasks before supplemental; unrated last."""
    rows = con.execute(
        "SELECT task, task_type, importance, source_date FROM occupation_tasks"
        " WHERE soc_code = ?"
        " ORDER BY importance IS NULL, task_type = 'Core' DESC, importance DESC, task_id"
        " LIMIT ?", (soc_code, limit)).fetchall()
    total = con.execute("SELECT COUNT(*) FROM occupation_tasks WHERE soc_code = ?",
                        (soc_code,)).fetchone()[0]
    return rows, total


def occupation_technology(con, soc_code, limit=10):
    """Software examples, O*NET's hot technologies first."""
    return con.execute(
        "SELECT example, category, hot, in_demand FROM occupation_technology"
        " WHERE soc_code = ? GROUP BY example"
        " ORDER BY MAX(hot) DESC, MAX(in_demand) DESC, example LIMIT ?",
        (soc_code, limit)).fetchall()


def occupation_tool_groups(con, soc_code, groups=8, per_group=3):
    """Tools grouped by O*NET commodity category, largest groups first.
    O*NET does not rank tools, so group size is the only honest order."""
    rows = con.execute(
        "SELECT category, COUNT(*) AS n, GROUP_CONCAT(example, '|') AS examples"
        "  FROM occupation_tools WHERE soc_code = ?"
        " GROUP BY category ORDER BY n DESC, category LIMIT ?",
        (soc_code, groups)).fetchall()
    total = con.execute("SELECT COUNT(*) FROM occupation_tools WHERE soc_code = ?",
                        (soc_code,)).fetchone()[0]
    return [{"category": r["category"], "count": r["n"],
             "examples": sorted(r["examples"].split("|"))[:per_group]} for r in rows], total


def get_skill(con, element_id):
    return con.execute("SELECT element_id, name, description, source_dataset FROM skills"
                       " WHERE element_id = ?", (element_id,)).fetchone()


def jobs_for_skill(con, element_id, limit=12):
    """Where this skill matters most, by O*NET importance."""
    return con.execute(
        "SELECT o.soc_code, o.title, o.job_zone, os.importance FROM occupation_skills os"
        "  JOIN occupations o ON o.soc_code = os.soc_code"
        " WHERE os.element_id = ? ORDER BY os.importance DESC, o.title LIMIT ?",
        (element_id, limit)).fetchall()


def count_jobs_needing(con, element_id, threshold):
    return con.execute("SELECT COUNT(*) FROM occupation_skills WHERE element_id = ?"
                       " AND importance >= ?", (element_id, threshold)).fetchone()[0]


def readiness_basis_map(con, threshold, top_n):
    """soc -> the skills that decide 'ready' for that job: its essential skills,
    or its top_n most important where it has none. Same rule as
    pathway.step_readiness, for every job at once."""
    rows = con.execute("SELECT soc_code, element_id, importance FROM occupation_skills"
                       " ORDER BY soc_code, importance DESC").fetchall()
    by_soc = {}
    for r in rows:
        by_soc.setdefault(r[0], []).append((r[1], r[2]))
    return {soc: ({e for e, imp in skills if imp >= threshold}
                  or {e for e, _ in skills[:top_n]})
            for soc, skills in by_soc.items()}


def related_occupations(con, soc_code, primary_only=True):
    sql = ("SELECT r.related_soc_code, r.tier, r.sort_index, o.title, o.job_zone"
           "  FROM related_occupations r JOIN occupations o"
           "    ON o.soc_code = r.related_soc_code"
           " WHERE r.soc_code = ?")
    if primary_only:
        sql += " AND r.tier LIKE 'Primary%'"
    sql += " ORDER BY r.sort_index"
    return con.execute(sql, (soc_code,)).fetchall()


# ---------- profiles ----------

# No 0/O, 1/I/L: a code read aloud or copied off a screen must survive it.
PLAN_CODE_ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"


def new_plan_code(con):
    while True:
        code = "".join(secrets.choice(PLAN_CODE_ALPHABET) for _ in range(6))
        if not con.execute("SELECT 1 FROM users WHERE plan_code = ?", (code,)).fetchone():
            return code


def normalise_plan_code(text):
    """'k7m-2qx', 'K7M 2QX' and 'K7M2QX' are the same code."""
    return "".join(ch for ch in (text or "").upper() if ch.isalnum())


def profile_by_plan_code(con, code):
    return con.execute("SELECT * FROM users WHERE plan_code = ?",
                       (normalise_plan_code(code),)).fetchone()


def create_profile(con, profile_type, skill_ids, target_soc_code=None, display_name=None):
    profile_id = uuid.uuid4().hex[:12]
    con.execute("INSERT INTO users (profile_id, profile_type, target_soc_code,"
                " display_name, plan_code) VALUES (?,?,?,?,?)",
                (profile_id, profile_type, target_soc_code, display_name, new_plan_code(con)))
    con.executemany("INSERT INTO user_skills (profile_id, element_id) VALUES (?,?)",
                    [(profile_id, s) for s in set(skill_ids)])
    con.commit()
    return profile_id


def get_profile(con, profile_id):
    return con.execute("SELECT * FROM users WHERE profile_id = ?",
                       (profile_id,)).fetchone()


def profile_skill_ids(con, profile_id):
    """Skills the user holds now. 'learning' is deliberately excluded: every
    gap, pathway and recommendation is measured against this list."""
    return [r[0] for r in con.execute(
        "SELECT element_id FROM user_skills WHERE profile_id = ? AND status = 'held'",
        (profile_id,))]


def profile_skills(con, profile_id):
    return con.execute(
        "SELECT us.element_id, s.name, s.description, us.status, us.updated_at"
        "  FROM user_skills us JOIN skills s ON s.element_id = us.element_id"
        " WHERE us.profile_id = ? ORDER BY s.name", (profile_id,)).fetchall()


def set_skill_status(con, profile_id, element_id, status):
    con.execute(
        "INSERT INTO user_skills (profile_id, element_id, status) VALUES (?,?,?)"
        " ON CONFLICT (profile_id, element_id)"
        " DO UPDATE SET status = excluded.status, updated_at = datetime('now')",
        (profile_id, element_id, status))
    con.commit()


def remove_skill(con, profile_id, element_id):
    con.execute("DELETE FROM user_skills WHERE profile_id = ? AND element_id = ?",
                (profile_id, element_id))
    con.commit()


def saved_socs(con, profile_id):
    return [r[0] for r in con.execute(
        "SELECT soc_code FROM saved_occupations WHERE profile_id = ? ORDER BY saved_at, soc_code",
        (profile_id,))]


def save_occupation(con, profile_id, soc_code):
    con.execute("INSERT OR IGNORE INTO saved_occupations (profile_id, soc_code) VALUES (?,?)",
                (profile_id, soc_code))
    con.commit()


def unsave_occupation(con, profile_id, soc_code):
    con.execute("DELETE FROM saved_occupations WHERE profile_id = ? AND soc_code = ?",
                (profile_id, soc_code))
    con.commit()


def set_display_name(con, profile_id, name):
    con.execute("UPDATE users SET display_name = ? WHERE profile_id = ?", (name, profile_id))
    con.commit()


def set_target(con, profile_id, soc_code):
    con.execute("UPDATE users SET target_soc_code = ? WHERE profile_id = ?",
                (soc_code, profile_id))
    con.commit()


def valid_skill_ids(con):
    return {r[0] for r in con.execute("SELECT element_id FROM skills")}


def occupation_zones(con):
    return dict(con.execute("SELECT soc_code, job_zone FROM occupations"))
