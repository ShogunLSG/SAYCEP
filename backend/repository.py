"""Occupation Repository -- all database access lives here.

Named to match the component in the sequence diagram (docs/uml/04-sequence).
Keeping every query in one module is what makes the monolith splittable later:
the data service is already a seam, it just isn't a network boundary yet.

Profile tables are created here rather than by the loader, because the loader
rebuilds reference data and knows nothing about users.
"""

import sqlite3
import uuid

from config import DB_PATH

PROFILE_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    profile_id      TEXT PRIMARY KEY,
    profile_type    TEXT NOT NULL CHECK (profile_type IN ('student', 'school_leaver')),
    target_soc_code TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS user_skills (
    profile_id  TEXT NOT NULL REFERENCES users(profile_id) ON DELETE CASCADE,
    element_id  TEXT NOT NULL,
    PRIMARY KEY (profile_id, element_id)
);
"""


def connect():
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def ensure_profile_tables(con):
    con.executescript(PROFILE_SCHEMA)
    con.commit()


def reference_data_present(con):
    """NFR-03: refuse to serve rather than serve partial data."""
    try:
        return con.execute("SELECT COUNT(*) FROM occupations").fetchone()[0] > 0
    except sqlite3.OperationalError:
        return False


# ---------- catalogue ----------

def list_occupations(con, zone=None, query=None, limit=100):
    sql = ["SELECT soc_code, title, job_zone, source_dataset FROM occupations WHERE 1=1"]
    args = []
    if zone is not None:
        sql.append("AND job_zone = ?")
        args.append(zone)
    if query:
        sql.append("AND LOWER(title) LIKE ?")
        args.append(f"%{query.lower()}%")
    sql.append("ORDER BY title LIMIT ?")
    args.append(limit)
    return con.execute(" ".join(sql), args).fetchall()


def count_occupations(con, zone=None, query=None):
    sql = ["SELECT COUNT(*) FROM occupations WHERE 1=1"]
    args = []
    if zone is not None:
        sql.append("AND job_zone = ?")
        args.append(zone)
    if query:
        sql.append("AND LOWER(title) LIKE ?")
        args.append(f"%{query.lower()}%")
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
        "SELECT s.element_id, s.name, os.importance, os.importance_scale_max,"
        "       os.source_date"
        "  FROM occupation_skills os JOIN skills s ON s.element_id = os.element_id"
        " WHERE os.soc_code = ? ORDER BY os.importance DESC", (soc_code,)).fetchall()


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

def create_profile(con, profile_type, skill_ids, target_soc_code=None):
    profile_id = uuid.uuid4().hex[:12]
    con.execute("INSERT INTO users (profile_id, profile_type, target_soc_code)"
                " VALUES (?,?,?)", (profile_id, profile_type, target_soc_code))
    con.executemany("INSERT INTO user_skills (profile_id, element_id) VALUES (?,?)",
                    [(profile_id, s) for s in set(skill_ids)])
    con.commit()
    return profile_id


def get_profile(con, profile_id):
    return con.execute("SELECT * FROM users WHERE profile_id = ?",
                       (profile_id,)).fetchone()


def profile_skill_ids(con, profile_id):
    return [r[0] for r in con.execute(
        "SELECT element_id FROM user_skills WHERE profile_id = ?", (profile_id,))]


def set_target(con, profile_id, soc_code):
    con.execute("UPDATE users SET target_soc_code = ? WHERE profile_id = ?",
                (soc_code, profile_id))
    con.commit()


def valid_skill_ids(con):
    return {r[0] for r in con.execute("SELECT element_id FROM skills")}
