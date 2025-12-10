"""
states.py — единая система управления состояниями пользователей.

Используется в:
- анонимная ссылка
- рулетка
- админ-панель
- рассылка
- баны
- анонимные сессии
"""

import sqlite3
from typing import Optional

# Путь к базе
DB_PATH = "bot/db/storage.db"


# ============================================================
# 🧩 КАТАЛОГ СОСТОЯНИЙ (движок понимает ВСЁ отсюда)
# ============================================================

class States:
    MAIN_MENU = "main_menu"

    # анонимное общение по ссылке
    MY_LINK = "my_link"
    CHANGE_LINK = "change_link"
    ANON_CONNECTED = "anon_connected"   # anon_connected:<session_id>

    # рулетка
    CHOOSING_GENDER = "choosing_gender"
    SEARCHING = "searching_roulette"
    IN_ROULETTE = "in_roulette"

    # inline reply на анонимного пользователя
    WAITING_REPLY = "waiting_reply"     # waiting_reply:<session_id>

    # админ
    ADMIN = "admin_panel"
    ADMIN_BAN = "admin_ban"
    ADMIN_UNBAN = "admin_unban"
    ADMIN_BROADCAST = "admin_broadcast"
    ADMIN_BROADCAST_MEDIA = "admin_broadcast_media"

    # технические
    UNKNOWN = "unknown"


# ============================================================
# 🔌 РАБОТА СО STATE
# ============================================================

def _connect():
    return sqlite3.connect(DB_PATH)


def set_state(user_id: int, state: str):
    """Устанавливает состояние пользователя"""
    conn = _connect()
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO states(user_id, state)
        VALUES (?, ?)
    """, (user_id, state))
    conn.commit()
    conn.close()


def get_state(user_id: int) -> str:
    """Возвращает состояние пользователя или main_menu"""
    conn = _connect()
    cur = conn.cursor()
    cur.execute("SELECT state FROM states WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return States.MAIN_MENU
    return row[0]


def reset_state(user_id: int):
    """Сбрасывает состояние в main_menu"""
    set_state(user_id, States.MAIN_MENU)


# ============================================================
# 🧱 ИНИЦИАЛИЗАЦИЯ ТАБЛИЦЫ
# ============================================================

def init_states_table():
    """Создаёт таблицу состояний, если её нет"""
    conn = _connect()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS states (
            user_id INTEGER PRIMARY KEY,
            state TEXT DEFAULT 'main_menu'
        )
    """)
    conn.commit()
    conn.close()