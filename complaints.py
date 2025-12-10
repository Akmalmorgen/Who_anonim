"""
db/complaints.py — жалобы пользователей
"""

from datetime import datetime
from .database import db, lock


def add_complaint(reporter_id: int, reported_id: int, anon_tag: str, reason: str, chat_type: str):
    with lock:
        conn = db.get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO complaints (reporter_id, reported_id, offender_anon_tag, reason, date, chat_type)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (reporter_id, reported_id, anon_tag, reason, datetime.utcnow().isoformat(), chat_type),
        )

        conn.commit()
        conn.close()


def get_last(limit: int = 50):
    conn = db.get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT id, reporter_id, reported_id, offender_anon_tag, reason, date, chat_type "
        "FROM complaints ORDER BY id DESC LIMIT ?",
        (limit,),
    )

    rows = cur.fetchall()
    conn.close()
    return rows


def clear_all():
    with lock:
        conn = db.get_connection()
        cur = conn.cursor()

        cur.execute("DELETE FROM complaints")

        conn.commit()
        conn.close()