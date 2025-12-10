"""
handlers/start.py — обработка /start, приветствие, deep-link
"""

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from config.settings import ADMINS
from states import UserStates
from keyboards.keyboards import kb

from db.users import ensure_user_exists, is_banned, set_user_state
from db.links import check_link_exists, create_anon_session
from handlers.anon_chat import notify_owner_about_new_anon
from handlers.menu import send_main_menu


# -----------------------------------------------------------
# /start командa
# -----------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    first_name = user.first_name or "Аноним"

    # Добавляем в БД (если нет)
    ensure_user_exists(user_id, first_name)

    # Проверяем бан
    if is_banned(user_id) and user_id not in ADMINS:
        await update.message.reply_text("🚫 Вы заблокированы администратором.")
        return

    # --- Проверяем deep link ---
    if context.args:
        link_id = context.args[0]

        if link_id.isdigit():
            exists, owner_id = check_link_exists(link_id)

            if not exists:
                await update.message.reply_text(
                    "❌ Эта ссылка недействительна.",
                    reply_markup=kb.reply.main_menu(is_admin=user_id in ADMINS)
                )
                return

            if owner_id == user_id:
                await update.message.reply_text(
                    "❌ Это ваша собственная ссылка!",
                    reply_markup=kb.reply.main_menu(is_admin=user_id in ADMINS)
                )
                return

            # Создаём анонимную сессию
            session_id, anon_tag = create_anon_session(anon_user_id=user_id, owner_id=owner_id)

            set_user_state(user_id, UserStates.ANON_CONNECTED.format(session_id=session_id))

            # Отправляем анонима в чат
            await update.message.reply_text(
                "✅ Вы подключились к анонимному чату!\n"
                "Пишите любое сообщение — оно уйдёт владельцу ссылки.\n"
                "🔒 Вы полностью скрыты.",
                reply_markup=kb.reply.anon_user_chat()
            )

            # Уведомляем владельца
            await notify_owner_about_new_anon(context, owner_id, session_id, anon_tag)

            return

    # --- Обычный старт ---
    await send_welcome(update, context)


# -----------------------------------------------------------
# Приветствие + меню
# -----------------------------------------------------------
async def send_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    welcome_text = (
        "╔═══════════════════════════╗\n"
        "║   👻 <b>Who?Anonim™</b> Bot   ║\n"
        "╚═══════════════════════════╝\n\n"
        f"Привет, <b>{user.first_name}</b>! 🎭\n\n"
        "🔐 Это бот для <u>анонимного общения</u>.\n"
        "Вот что доступно:\n\n"
        "🔗 Анонимная ссылка — люди пишут вам скрыто\n"
        "🎲 Рулетка — случайный анонимный собеседник\n"
        "💬 Поддержка — @who_mercy\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Выберите действие ниже 👇"
    )

    set_user_state(user_id, UserStates.MAIN_MENU)

    await update.message.reply_text(
        welcome_text,
        parse_mode="HTML",
        reply_markup=kb.reply.main_menu(is_admin=user_id in ADMINS)
    )


# -----------------------------------------------------------
# Регистрация обработчиков
# -----------------------------------------------------------
def register_start_handlers(app):
    app.add_handler(CommandHandler("start", start))