"""
db/users.py — работа с пользователями
"""

from .database import db, lock


def add_user(user_id: int):
    with lock:
        conn = db.get_connection()
        cur = conn.cursor()

        cur.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        exists = cur.fetchone()

        if not exists:
            cur.execute(
                "INSERT INTO users (user_id, banned, state, gender) VALUES (?, 0, 'MAIN_MENU', NULL)",
                (user_id,),
            )

        conn.commit()
        conn.close()


def set_state(user_id: int, state: str):
    with lock:
        conn = db.get_connection()
        cur = conn.cursor()

        cur.execute("UPDATE users SET state = ? WHERE user_id = ?", (state, user_id))

        conn.commit()
        conn.close()


def get_state(user_id: int) -> str:
    conn = db.get_connection()
    cur = conn.cursor()

    cur.execute("SELECT state FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()

    conn.close()
    return row[0] if row else "MAIN_MENU"


def set_gender(user_id: int, gender: str):
    with lock:
        conn = db.get_connection()
        cur = conn.cursor()

        cur.execute("UPDATE users SET gender = ? WHERE user_id = ?", (gender, user_id))

        conn.commit()
        conn.close()


def get_gender(user_id: int):
    conn = db.get_connection()
    cur = conn.cursor()

    cur.execute("SELECT gender FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()

    conn.close()
    return row[0] if row else None


def ban_user(user_id: int):
    with lock:
        conn = db.get_connection()
        cur = conn.cursor()

        cur.execute("UPDATE users SET banned = 1 WHERE user_id = ?", (user_id,))

        conn.commit()
        conn.close()


def unban_user(user_id: int):
    with lock:
        conn = db.get_connection()
        cur = conn.cursor()

        cur.execute("UPDATE users SET banned = 0 WHERE user_id = ?", (user_id,))

        conn.commit()
        conn.close()


def is_banned(user_id: int) -> bool:
    conn = db.get_connection()
    cur = conn.cursor()

    cur.execute("SELECT banned FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()

    conn.close()
    return bool(row[0]) if row else False


def get_all_users() -> list:
    conn = db.get_connection()
    cur = conn.cursor()

    cur.execute("SELECT user_id FROM users")
    rows = cur.fetchall()

    conn.close()
    return [row[0] for row in rows]