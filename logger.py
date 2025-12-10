"""
logger/logger.py — глобальная система логирования для бота
"""

import logging
import os

# Папка для логов
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "bot.log")

# Создаём папку logs если её нет
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Формат логов
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

# Создаём корневой логгер
logger = logging.getLogger("WhoAnonimBot")
logger.setLevel(logging.INFO)

# ---------- Консоль ----------
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter(LOG_FORMAT))

# ---------- Файл ----------
file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter(LOG_FORMAT))

# Добавляем обработчики, чтобы не дублировались
if not logger.handlers:
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)


def get_logger(name: str):
    """
    Получить дочерний логгер для модуля.
    Пример: log = get_logger(__name__)
    """
    return logger.getChild(name)