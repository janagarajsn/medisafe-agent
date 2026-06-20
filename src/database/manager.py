import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, date

from src.security import encryption

_DEFAULT_DB_DIR = os.path.expanduser("~/.medisafe")
_DB_PATH = os.environ.get(
    "MEDISAFE_DB_PATH",
    os.path.join(_DEFAULT_DB_DIR, "medisafe.db"),
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS medications (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         TEXT    NOT NULL,
    name_enc        TEXT    NOT NULL,
    dosage_enc      TEXT    NOT NULL,
    frequency       TEXT    NOT NULL,
    times_per_day   INTEGER NOT NULL DEFAULT 1,
    schedule_times  TEXT    NOT NULL DEFAULT '08:00',
    start_date      TEXT    NOT NULL,
    end_date        TEXT,
    notes_enc       TEXT,
    active          INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS doses (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    medication_id    INTEGER NOT NULL,
    user_id          TEXT    NOT NULL,
    scheduled_date   TEXT    NOT NULL,
    scheduled_time   TEXT    NOT NULL,
    taken_at         TEXT,
    skipped          INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (medication_id) REFERENCES medications(id)
);
"""


@contextmanager
def _get_conn():
    db_dir = os.path.dirname(_DB_PATH)
    os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with _get_conn() as conn:
        conn.executescript(_SCHEMA)


def add_medication(
    user_id: str,
    name: str,
    dosage: str,
    frequency: str,
    times_per_day: int,
    schedule_times: str,
    start_date: str,
    end_date: str | None = None,
    notes: str | None = None,
) -> int:
    with _get_conn() as conn:
        cursor = conn.execute(
            """INSERT INTO medications
               (user_id, name_enc, dosage_enc, frequency, times_per_day,
                schedule_times, start_date, end_date, notes_enc, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                user_id,
                encryption.encrypt(name),
                encryption.encrypt(dosage),
                frequency,
                times_per_day,
                schedule_times,
                start_date,
                end_date,
                encryption.encrypt(notes) if notes else None,
                datetime.now().isoformat(),
            ),
        )
        return cursor.lastrowid


def _decrypt_row(row: dict) -> dict:
    row["name"] = encryption.decrypt(row.pop("name_enc"))
    row["dosage"] = encryption.decrypt(row.pop("dosage_enc"))
    raw_notes = row.pop("notes_enc", None)
    row["notes"] = encryption.decrypt(raw_notes) if raw_notes else None
    return row


def get_medications(user_id: str) -> list[dict]:
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM medications WHERE user_id = ? AND active = 1 ORDER BY created_at",
            (user_id,),
        ).fetchall()
    return [_decrypt_row(dict(r)) for r in rows]


def deactivate_medication(user_id: str, medication_id: int) -> bool:
    with _get_conn() as conn:
        cursor = conn.execute(
            "UPDATE medications SET active = 0 WHERE id = ? AND user_id = ?",
            (medication_id, user_id),
        )
        return cursor.rowcount > 0


def record_dose(
    user_id: str,
    medication_id: int,
    scheduled_date: str,
    scheduled_time: str,
    taken: bool = True,
) -> int:
    with _get_conn() as conn:
        cursor = conn.execute(
            """INSERT INTO doses
               (medication_id, user_id, scheduled_date, scheduled_time, taken_at, skipped)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                medication_id,
                user_id,
                scheduled_date,
                scheduled_time,
                datetime.now().isoformat() if taken else None,
                0 if taken else 1,
            ),
        )
        return cursor.lastrowid


def get_adherence(user_id: str, days: int = 7) -> list[dict]:
    with _get_conn() as conn:
        rows = conn.execute(
            """SELECT d.medication_id,
                      m.name_enc,
                      COUNT(*)                                              AS total,
                      SUM(CASE WHEN d.taken_at IS NOT NULL THEN 1 ELSE 0 END) AS taken
               FROM doses d
               JOIN medications m ON d.medication_id = m.id
               WHERE d.user_id = ?
                 AND d.scheduled_date >= date('now', ? || ' days')
               GROUP BY d.medication_id, m.name_enc""",
            (user_id, f"-{days}"),
        ).fetchall()

    result = []
    for row in rows:
        r = dict(row)
        r["name"] = encryption.decrypt(r.pop("name_enc"))
        total = r["total"]
        r["adherence_pct"] = round(r["taken"] / total * 100, 1) if total > 0 else 0.0
        result.append(r)
    return result
