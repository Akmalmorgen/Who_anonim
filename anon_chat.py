"""
handlers/anon_chat.py — логика анонимного общения через ссылку.

✓ Подключение к чату по ссылке
✓ Передача сообщений владельцу
✓ Назначение каждому анониму своего anon_id (#1234)
✓ Ответ владельца через inline «Ответить»
✓ Жалоба через inline «⚠ Пожаловаться»
✓ Меню причин жалобы
"""

from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import (
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters
)

from db.anon_chat import (
    start_anon_session,
    get_owner_by_link,
    get_or_create_anon_id,
    get_session_partner,
    add_complaint
)

from keyboards.keyboards import kb
from states import UserStates
from db.users import set_user_state
from config.settings import ADMINS


# -----------------------------------------------------------
# Генерация inline кнопок: Ответить + Пожаловаться
# -----------------------------------------------------------
def inline_message_actions(session_id: int, anon_id: int):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💬 Ответить", callback_data=f"reply:{session_id}:{anon_id}"),
            InlineKeyboardButton("⚠ Пожаловаться", callback_data=f"report:{session_id}:{anon_id}")
        ]
    ])


# -----------------------------------------------------------
# Меню причин жалобы
# -----------------------------------------------------------
def report_reasons_keyboard(session_id: int, anon_id: int):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🗯 Мат", callback_data=f"reason:{session_id}:{anon_id}:mat")],
        [InlineKeyboardButton("📛 Спам", callback_data=f"reason:{session_id}:{anon_id}:spam")],
        [InlineKeyboardButton("🔞 18+", callback_data=f"reason:{session_id}:{anon_id}:18")],
        [InlineKeyboardButton("☠ Угроза", callback_data=f"reason:{session_id}:{anon_id}:threat")],
    ])


# -----------------------------------------------------------
# 1) Подключение к анонимному чату по ссылке
# -----------------------------------------------------------
async def join_anon_chat(update: Update, context: ContextTypes.DEFAULT_TYPE, link_id: str):
    anon_user = update.effective_user
    anon_id = anon_user.id

    # Находим владельца ссылки
    owner_id = get_owner_by_link(link_id)
    if not owner_id:
        await update.message.reply_text(
            "❌ Эта ссылка недействительна.",
            reply_markup=kb.reply.main_menu(False)
        )
        return

    if owner_id == anon_id:
        await update.message.reply_text(
            "❌ Это ваша собственная ссылка!",
            reply_markup=kb.reply.main_menu(False)
        )
        return

    # Назначить этому анониму персональный анон-ID (#1234)
    personal_anon_id = get_or_create_anon_id(owner_id, anon_id)

    # Создать или получить сессию
    session_id = start_anon_session(owner_id, anon_id)

    # Анониму — обычное минимальное меню
    set_user_state(anon_id, UserStates.ANON_CHATTING)

    await update.message.reply_text(
        "💬 <b>Анонимный чат открыт!</b>\n"
        "Пишите ваши сообщения.",
        parse_mode="HTML",
        reply_markup=kb.reply.anon_minimal()
    )

    # Уведомляем владельца
    await context.bot.send_message(
        owner_id,
        f"📨 <b>Новое сообщение от Аноним #{personal_anon_id}</b>",
        parse_mode="HTML"
    )


# -----------------------------------------------------------
# 2) Аноним отправляет сообщение владельцу
# -----------------------------------------------------------
async def anon_send_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    # Находим владельца
    owner_id = get_session_partner(user_id)
    if not owner_id:
        await update.message.reply_text("❌ Сессия не активна.")
        return

    # узнаём его персональный anon_id
    anon_id = get_or_create_anon_id(owner_id, user_id)
    session_id = start_anon_session(owner_id, user_id)

    # отправляем владельцу
    await context.bot.send_message(
        owner_id,
        f"🕶 Сообщение от Аноним #{anon_id}\n"
        "━━━━━━━━━━━\n"
        f"{text}\n"
        "━━━━━━━━━━━",
        reply_markup=inline_message_actions(session_id, anon_id)
    )

    await update.message.reply_text("✅ Сообщение отправлено.")


# -----------------------------------------------------------
# 3) Callback: владелец нажал «Ответить»
# -----------------------------------------------------------
async def cb_reply_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    session_id, anon_id = map(int, q.data.split(":")[1:3])

    # сохранение в state id анонима, которому отвечает владелец
    owner_id = q.from_user.id

    context.user_data["reply_to"] = {
        "session_id": session_id,
        "anon_id": anon_id
    }

    await q.message.reply_text(
        f"💬 Введите сообщение для Аноним #{anon_id}",
        reply_markup=kb.reply.back_only()
    )

    set_user_state(owner_id, UserStates.REPLYING)


# -----------------------------------------------------------
# 4) Владелец написал ответ
# -----------------------------------------------------------
async def owner_send_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    owner_id = update.effective_user.id
    data = context.user_data.get("reply_to")

    if not data:
        return

    session_id = data["session_id"]
    anon_id_value = data["anon_id"]

    # получаем настоящего user_id анонима
    anon_user_id = get_session_partner(owner_id, reverse=True)

    if not anon_user_id:
        await update.message.reply_text("❌ Аноним уже вышел.")
        return

    await context.bot.send_message(
        anon_user_id,
        f"💬 Ответ от владельца ссылки:\n\n{update.message.text}"
    )

    await update.message.reply_text("✅ Ответ отправлен.", reply_markup=kb.reply.my_link_menu())

    set_user_state(owner_id, UserStates.MY_LINK)
    context.user_data["reply_to"] = None


# -----------------------------------------------------------
# 5) Callback: владелец нажал «Пожаловаться»
# -----------------------------------------------------------
async def cb_report_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    session_id, anon_id = map(int, q.data.split(":")[1:3])

    await q.message.reply_text(
        f"⚠ Выберите причину жалобы на Аноним #{anon_id}",
        reply_markup=report_reasons_keyboard(session_id, anon_id)
    )


# -----------------------------------------------------------
# 6) Callback: причина жалобы выбрана
# -----------------------------------------------------------
async def cb_report_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    _, session_id, anon_id, reason = q.data.split(":")
    session_id = int(session_id)
    anon_id = int(anon_id)

    # записать жалобу в БД
    add_complaint(session_id, anon_id, reason)

    # отправить админу
    for admin in ADMINS:
        try:
            await context.bot.send_message(
                admin,
                f"⚠ <b>Жалоба!</b>\n"
                f"На Аноним #{anon_id}\n"
                f"Причина: <code>{reason}</code>",
                parse_mode="HTML"
            )
        except:
            pass

    await q.message.reply_text(
        "✅ Жалоба отправлена.",
        reply_markup=kb.reply.my_link_menu()
    )


# -----------------------------------------------------------
# РЕГИСТРАЦИЯ ХЕНДЛЕРОВ
# -----------------------------------------------------------
def register_anon_chat_handlers(app):

    # callback — ответ
    app.add_handler(CallbackQueryHandler(cb_reply_button, pattern=r"^reply:"))

    # callback — жалоба
    app.add_handler(CallbackQueryHandler(cb_report_button, pattern=r"^report:"))

    # callback — причина жалобы
    app.add_handler(CallbackQueryHandler(cb_report_reason, pattern=r"^reason:"))

    # аноним пишет владельцу
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex("^(?!/).+") & filters.ChatType.PRIVATE,
        anon_send_message
    ))