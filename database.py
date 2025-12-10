"""
db/database.py — подключение к SQLite и создание таблиц.
"""

import sqlite3
import threading

DB_PATH = "database.sqlite"

lock = threading.Lock()


class Database:
    def __init__(self, path):
        self.path = path
        self._init_db()

    def _init_db(self):
        with self.get_connection() as conn:
            cur = conn.cursor()

            # USERS
            cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                banned INTEGER DEFAULT 0,
                state TEXT DEFAULT 'MAIN_MENU',
                gender TEXT DEFAULT NULL
            )
            """)

            # LINKS
            cur.execute("""
            CREATE TABLE IF NOT EXISTS links (
                link_id TEXT PRIMARY KEY,
                owner_id INTEGER
            )
            """)

            # ANON_CHAT_SESSIONS
            cur.execute("""
            CREATE TABLE IF NOT EXISTS anon_sessions (
                session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER,
                anon_user_id INTEGER
            )
            """)

            # ANON_USER_IDS (Аноним #1234 у каждого владельца свои)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS anon_ids (
                owner_id INTEGER,
                anon_user_id INTEGER,
                anon_id INTEGER,
                PRIMARY KEY (owner_id, anon_user_id)
            )
            """)

            # ROULETTE_QUEUE
            cur.execute("""
            CREATE TABLE IF NOT EXISTS roulette_queue (
                user_id INTEGER PRIMARY KEY,
                gender TEXT
            )
            """)

            # ACTIVE_ROULETTE_CHATS
            cur.execute("""
            CREATE TABLE IF NOT EXISTS roulette_chats (
                user_id INTEGER PRIMARY KEY,
                partner_id INTEGER
            )
            """)

            # COMPLAINTS
            cur.execute("""
            CREATE TABLE IF NOT EXISTS complaints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT,
                from_user INTEGER,
                to_user INTEGER
            )
            """)

            conn.commit()

    def get_connection(self):
        return sqlite3.connect(self.path, check_same_thread=False)


db = Database(DB_PATH)