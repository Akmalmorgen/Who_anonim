import asyncio
import logging

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

# ========= CONFIG ==========
from config.settings import TOKEN

# ========= LOGGER ==========
from logger.logger import setup_logger

# ========= DB INIT =========
from db.database import init_database

# ========= HANDLERS ========
from handlers.start.start import start_command, process_start_link
from handlers.menu.menu import handle_main_menu
from handlers.anon_link.anon_link import (
    show_my_link,
    change_link_request,
    execute_change_link,
    cancel_change_link
)
from handlers.anon_chat.anon_chat import (
    callback_query_handler,
    owner_reply_handler
)
from handlers.roulette.roulette import (
    start_roulette,
    handle_roulette_message
)
from handlers.admin.admin import (
    admin_panel,
    handle_admin_commands
)
from handlers.broadcast.broadcast import (
    broadcast_message,
    broadcast_handler
)

# ========= STATES ==========
from config.states import (
    STATE_ANON_LINK_MENU,
    STATE_CHANGE_LINK_CONFIRM,
    STATE_ROULETTE_CHAT,
    STATE_ADMIN_PANEL,
    STATE_ADMIN_BROADCAST
)

from states import get_state


# =====================================================================
#                            MAIN STARTUP
# =====================================================================

def build_application():
    """Создание объекта Application для Telegram API."""
    setup_logger()
    init_database()

    application = Application.builder().token(TOKEN).build()

    # --------------------  /start  --------------------
    application.add_handler(CommandHandler("start", start_command))

    # --------------------  Админ панель  --------------------
    application.add_handler(CommandHandler("admin", admin_panel))

    # --------------------  Callback-кнопки (inline)  --------------------
    application.add_handler(CallbackQueryHandler(callback_query_handler))

    # --------------------  Расслыка (медиа + текст) -------------------
    application.add_handler(MessageHandler(
        filters.ALL & filters.ChatType.PRIVATE,
        broadcast_handler
    ))

    # --------------------  Основной обработчик сообщений  --------------------
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_router))

    return application


# =====================================================================
#                      ГЛОБАЛЬНЫЙ МАРШРУТИЗАТОР
# =====================================================================

async def message_router(update, context):
    """Маршрутизация сообщений по состояниям."""
    user_id = update.effective_user.id
    text = update.message.text

    state = get_state(user_id)

    # ========== ОТВЕТ ВЛАДЕЛЬЦА АНОНИМУ ==========
    # (если владелец нажал "Ответить")
    if await owner_reply_handler(update, context):
        return

    # ========== МЕНЮ АНОНИМНОЙ ССЫЛКИ ==========
    if state == STATE_ANON_LINK_MENU:
        if text == "🔄 Сменить ссылку":
            return await change_link_request(update, context)
        elif text == "⬅️ Назад":
            return await handle_main_menu(update, context)

    # ========== ПОДТВЕРЖДЕНИЕ / ОТМЕНА СМЕНЫ ==========
    if state == STATE_CHANGE_LINK_CONFIRM:
        if text == "🔄 Подтвердить смену":
            return await execute_change_link(update, context)
        elif text == "❌ Отмена":
            return await cancel_change_link(update, context)

    # ========== РУЛЕТКА ==========
    if state == STATE_ROULETTE_CHAT:
        return await handle_roulette_message(update, context)

    # ========== АДМИНСКИЕ РАЗДЕЛЫ ==========
    if state == STATE_ADMIN_PANEL:
        return await handle_admin_commands(update, context)

    if state == STATE_ADMIN_BROADCAST:
        return await broadcast_message(update, context)

    # ========== ГЛАВНОЕ МЕНЮ (текстовые кнопки) ==========
    return await handle_main_menu(update, context)


# =====================================================================
#                        ЗАПУСК БОТА
# =====================================================================

def main():
    application = build_application()
    print("🚀 Who?Anonim Bot запущен!")
    application.run_polling()


if __name__ == "__main__":
    main()