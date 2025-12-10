"""
keyboards.py — агрегатор всех клавиатур бота
Используется там, где нужен единый импорт.

Пример:
from keyboards.keyboards import kb
kb.reply.main_menu()
kb.inline.owner_message(session_id)
"""

from .reply import ReplyKB
from .inline import InlineKB


class Keyboards:
    reply = ReplyKB
    inline = InlineKB


kb = Keyboards()