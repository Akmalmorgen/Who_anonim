"""
handlers/admin.py — админ-панель

✓ Несколько админов
✓ Статистика
✓ Пользователи
✓ Жалобы
✓ Бан / Разбан
✓ Очистка жалоб
✓ Назад в меню
"""

from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from config.settings import ADMINS
from keyboards.keyboards import kb
from states import UserStates
from db.users import (
    set_user_state,
    get_all_users,
    ban_user,
    unban_user,
    get_banned_users
)
from db.links import count_links
from db.complaints import (
    get_all_complaints,
    clear_complaints
)
from db.roulette import count_active_chats


# ---------------------------------------------------------
# Проверка на админа
# ---------------------------------------------------------
def is_admin(user_id):
    return user_id in ADMINS


# ---------------------------------------------------------
# Вход в админ панель
# ---------------------------------------------------------
async def admin_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_admin(user_id):
        return await update.message.reply_text("❌ У вас нет доступа.")

    set_user_state(user_id, UserStates.ADMIN_PANEL)

    total_users = len(get_all_users())
    total_links = count_links()
    total_complaints = len(get_all_complaints())
    total_banned = len(get_banned_users())
    active_r_chats = count_active_chats()

    text = (
        "👑 <b>Админ-панель</b>\n\n"
        f"👥 Пользователей: <b>{total_users}</b>\n"
        f"🔗 Активных ссылок: <b>{total_links}</b>\n"
        f"⚠ Жалоб: <b>{total_complaints}</b>\n"
        f"🚫 Банов: <b>{total_banned}</b>\n"
        f"🎲 Рулетка чатов: <b>{active_r_chats}</b>\n\n"
        "Выберите действие:"
    )

    await update.message.reply_text(text, parse_mode="HTML", reply_markup=kb.reply.admin_menu())


# ---------------------------------------------------------
# Просмотр пользователей
# ---------------------------------------------------------
async def admin_show_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = get_all_users()

    text = "👥 <b>Все пользователи:</b>\n\n"

    for uid in users[:40]:  # первые 40, чтобы не перегрузить
        text += f"• <code>{uid}</code>\n"

    if len(users) > 40:
        text += f"\n... и ещё {len(users) - 40}"

    await update.message.reply_text(text, parse_mode="HTML")


# ---------------------------------------------------------
# Просмотр жалоб
# ---------------------------------------------------------
async def admin_show_complaints(update: Update, context: ContextTypes.DEFAULT_TYPE):
    complaints = get_all_complaints()

    if not complaints:
        return await update.message.reply_text("✔ Жалоб нет.")

    text = "⚠ <b>Жалобы:</b>\n\n"

    for c in complaints[-50:]:
        text += f"От: <code>{c['from']}</code> → На: <code>{c['to']}</code> ({c['type']})\n"

    await update.message.reply_text(text, parse_mode="HTML")


# ---------------------------------------------------------
# Очистка жалоб
# ---------------------------------------------------------
async def admin_clear_complaints(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_complaints()

    await update.message.reply_text("🧹 Жалобы очищены.")


# ---------------------------------------------------------
# Забанить
# ---------------------------------------------------------
async def admin_ban_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    set_user_state(update.effective_user.id, UserStates.ADMIN_BAN_INPUT)

    await update.message.reply_text(
        "Введите ID пользователя для бана:",
        reply_markup=kb.reply.back_only()
    )


async def admin_ban_execute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        target = int(update.message.text)
    except:
        return await update.message.reply_text("Введите корректный ID!")

    ban_user(target)

    await update.message.reply_text(f"🚫 Пользователь {target} забанен.")
    set_user_state(update.effective_user.id, UserStates.ADMIN_PANEL)


# ---------------------------------------------------------
# Разбан
# ---------------------------------------------------------
async def admin_unban_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    banned = get_banned_users()

    if not banned:
        return await update.message.reply_text("Нет заблокированных пользователей.")

    text = "🚫 <b>Забаненные пользователи:</b>\n\n"
    for uid in banned[:40]:
        text += f"• <code>{uid}</code>\n"

    await update.message.reply_text(text, parse_mode="HTML")

    set_user_state(update.effective_user.id, UserStates.ADMIN_UNBAN_INPUT)
    await update.message.reply_text("Введите ID для разбана:", reply_markup=kb.reply.back_only())


async def admin_unban_execute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        target = int(update.message.text)
    except:
        return await update.message.reply_text("Введите корректный ID!")

    unban_user(target)

    await update.message.reply_text(f"✅ Пользователь {target} разбанен.")
    set_user_state(update.effective_user.id, UserStates.ADMIN_PANEL)


# ---------------------------------------------------------
# РЕГИСТРАЦИЯ ХЕНДЛЕРОВ
# ---------------------------------------------------------
def register_admin_handlers(app):

    # вход в панель
    app.add_handler(MessageHandler(filters.Regex("^⚙️ Админ-панель$"), admin_entry))

    # просмотр пользователей
    app.add_handler(MessageHandler(filters.Regex("^👥 Пользователи$"), admin_show_users))

    # просмотр жалоб
    app.add_handler(MessageHandler(filters.Regex("^⚠️ Жалобы$"), admin_show_complaints))

    # очистка жалоб
    app.add_handler(MessageHandler(filters.Regex("^🗑 Очистить жалобы$"), admin_clear_complaints))

    # бан
    app.add_handler(MessageHandler(filters.Regex("^🚫 Забанить$"), admin_ban_request))
    app.add_handler(MessageHandler(
        filters.TEXT & filters.ChatType.PRIVATE & filters.Regex("^[0-9]+$"),
        admin_ban_execute
    ))

    # разбан
    app.add_handler(MessageHandler(filters.Regex("^✅ Разбанить$"), admin_unban_request))
    app.add_handler(MessageHandler(
        filters.TEXT & filters.ChatType.PRIVATE & filters.Regex("^[0-9]+$"),
        admin_unban_execute
    ))