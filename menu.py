"""
handlers/menu.py — главное меню и обработка пунктов из меню
"""

from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from config.settings import ADMINS
from states import UserStates
from keyboards.keyboards import kb

from db.users import set_user_state, is_banned

# импортируем обработчики других разделов
from handlers.anon_link import send_my_link
from handlers.roulette import start_roulette
from handlers.start import send_welcome


# -----------------------------------------------------------
# Отправка главного меню (можно вызывать из других модулей)
# -----------------------------------------------------------
async def send_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    set_user_state(user_id, UserStates.MAIN_MENU)

    await update.message.reply_text(
        "🔘 Главное меню:",
        reply_markup=kb.reply.main_menu(is_admin=user_id in ADMINS)
    )


# -----------------------------------------------------------
# Обработка кнопок главного меню
# -----------------------------------------------------------
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    text = update.message.text

    # БАН
    if is_banned(user_id) and user_id not in ADMINS:
        await update.message.reply_text("🚫 Вы заблокированы администратором.")
        return

    # 🔗 Моя ссылка
    if text == "🔗 Моя анон-ссылка":
        await send_my_link(update, context)
        return

    # 🎲 Рулетка
    if text == "🎲 Рулетка":
        await start_roulette(update, context)
        return

    # 💬 Помощь
    if text == "💬 Помощь":
        await send_help(update)
        return

    # 🛠 Админ-панель
    if text == "👑 Админ-панель" and user_id in ADMINS:
        from handlers.admin import open_admin_panel
        await open_admin_panel(update, context)
        return

    # Если текст неизвестный → снова показываем меню
    await send_main_menu(update, context)


# -----------------------------------------------------------
# Помощь
# -----------------------------------------------------------
async def send_help(update: Update):
    text = (
        "━━━━━━━━━━━━━━━━━━━━\n"
        "💡 <b>Помощь</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🔗 Создайте анонимную ссылку.\n"
        "🎲 Используйте рулетку.\n"
        "👤 Собеседник не узнает кто вы.\n\n"
        "Если нужна доработка бота:\n"
        "🛠 Разработчик: @who_mercy\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )

    await update.message.reply_text(
        text,
        parse_mode="HTML"
    )


# -----------------------------------------------------------
# Регистрация обработчика
# -----------------------------------------------------------
def register_menu_handlers(app):
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler))