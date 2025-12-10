"""
db/anon_chat.py — анонимные диалоги через ссылку
"""

import random
from .database import db, lock


def create_session(anon_user: int, owner_id: int) -> int:
    """ Создать новую анонимную сессию """
    anon_tag = str(random.randint(1000, 9999))

    with lock:
        conn = db.get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO anon_sessions (anon_user_id, owner_id, anon_tag)
            VALUES (?, ?, ?)
            """,
            (anon_user, owner_id, anon_tag),
        )

        session_id = cur.lastrowid
        conn.commit()
        conn.close()

    return session_id


def get_session(session_id: int):
    conn = db.get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT session_id, anon_user_id, owner_id, anon_tag FROM anon_sessions WHERE session_id = ?",
        (session_id,),
    )

    row = cur.fetchone()
    conn.close()
    return row


def get_sessions_for_owner(owner_id: int):
    conn = db.get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT session_id, anon_user_id, anon_tag FROM anon_sessions WHERE owner_id = ? ORDER BY session_id DESC",
        (owner_id,),
    )

    rows = cur.fetchall()
    conn.close()
    return rows


# -------------------------- MAPPING owner_message_id → session_id --------------------------


def save_owner_message(message_id: int, session_id: int, owner_id: int):
    with lock:
        conn = db.get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT OR REPLACE INTO message_map (owner_message_id, session_id, owner_id)
            VALUES (?, ?, ?)
            """,
            (message_id, session_id, owner_id),
        )

        conn.commit()
        conn.close()


def find_session_by_owner_message(message_id: int):
    conn = db.get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT session_id, owner_id FROM message_map WHERE owner_message_id = ?",
        (message_id,),
    )

    row = cur.fetchone()
    conn.close()
    return row