"""
db/links.py — работа с анонимными ссылками
"""

import random
from .database import db, lock


def generate_link_id() -> str:
    return str(random.randint(100000, 999999))


def create_or_get_link(user_id: int) -> str:
    conn = db.get_connection()
    cur = conn.cursor()

    cur.execute("SELECT link_id FROM links WHERE owner_id = ?", (user_id,))
    row = cur.fetchone()

    if row:
        conn.close()
        return row[0]

    # создаём новую
    link_id = generate_link_id()

    with lock:
        cur = conn.cursor()
        cur.execute("INSERT INTO links (link_id, owner_id) VALUES (?, ?)", (link_id, user_id))
        conn.commit()
        conn.close()

    return link_id


def change_link(user_id: int) -> str:
    """Удаляет старую ссылку и создаёт новую"""

    with lock:
        conn = db.get_connection()
        cur = conn.cursor()

        # Удаляем старую, если есть
        cur.execute("DELETE FROM links WHERE owner_id = ?", (user_id,))

        new_id = generate_link_id()

        cur.execute("INSERT INTO links (link_id, owner_id) VALUES (?, ?)", (new_id, user_id))
        conn.commit()
        conn.close()

    return new_id


def get_owner_by_link(link_id: str):
    conn = db.get_connection()
    cur = conn.cursor()

    cur.execute("SELECT owner_id FROM links WHERE link_id = ?", (link_id,))
    row = cur.fetchone()

    conn.close()
    return row[0] if row else None


def delete_link(link_id: str):
    with lock:
        conn = db.get_connection()
        cur = conn.cursor()

        cur.execute("DELETE FROM links WHERE link_id = ?", (link_id,))

        conn.commit()
        conn.close()