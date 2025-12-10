"""
db/roulette.py — логика рулетки
"""

from .database import db, lock


# Очередь в памяти — как ты и хотел
roulette_queue = {
    "M": [],
    "F": []
}


def add_to_queue(user_id: int, gender: str):
    if user_id not in roulette_queue[gender]:
        roulette_queue[gender].append(user_id)


def remove_from_queue(user_id: int):
    for g in ["M", "F"]:
        if user_id in roulette_queue[g]:
            roulette_queue[g].remove(user_id)


def find_partner(gender: str):
    """ Ищем человека противоположного пола """
    opposite = "F" if gender == "M" else "M"

    if roulette_queue[opposite]:
        return roulette_queue[opposite].pop(0)

    return None


# --------------------- Активные пары (в БД) ---------------------

def set_pair(u1: int, u2: int):
    with lock:
        conn = db.get_connection()
        cur = conn.cursor()

        cur.execute(
            "INSERT OR REPLACE INTO active_chats (user_id, partner_id) VALUES (?, ?)",
            (u1, u2)
        )
        cur.execute(
            "INSERT OR REPLACE INTO active_chats (user_id, partner_id) VALUES (?, ?)",
            (u2, u1)
        )

        conn.commit()
        conn.close()


def remove_pair(user_id: int):
    conn = db.get_connection()
    cur = conn.cursor()

    cur.execute("SELECT partner_id FROM active_chats WHERE user_id = ?", (user_id,))
    row = cur.fetchone()

    if row:
        partner = row[0]
        with lock:
            cur.execute("DELETE FROM active_chats WHERE user_id IN (?, ?)", (user_id, partner))
            conn.commit()

        conn.close()
        return partner

    conn.close()
    return None


def get_partner(user_id: int):
    conn = db.get_connection()
    cur = conn.cursor()

    cur.execute("SELECT partner_id FROM active_chats WHERE user_id = ?", (user_id,))
    row = cur.fetchone()

    conn.close()
    return row[0] if row else None