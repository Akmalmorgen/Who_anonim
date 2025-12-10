"""
handlers/roulette.py — логика чат-рулетки.

✓ Выбор пола
✓ Ожидание собеседника (по очередям)
✓ Отмена поиска
✓ Диалог: Стоп / След / Пожаловаться / Назад
✓ После «Стоп» — быстрый поиск
"""

from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from db.roulette import (
    set_user_gender,
    add_to_queue,
    find_match,
    remove_from_queue,
    set_active_chat,
    get_partner,
    end_chat,
)

from keyboards.keyboards import kb
from states import UserStates
from db.users import set_user_state
from db.complaints import save_roulette_complaint
from config.settings import ADMINS


# ---------------------------------------------------------
# 1) Старт рулетки — показать выбор пола
# ---------------------------------------------------------
async def roulette_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    set_user_state(user.id, UserStates.ROULETTE_GENDER)

    await update.message.reply_text(
        "🎲 <b>Рулетка</b>\n\n"
        "Выбери свой пол:",
        parse_mode="HTML",
        reply_markup=kb.reply.gender_choice()
    )


# ---------------------------------------------------------
# 2) Установка пола и поиск пары
# ---------------------------------------------------------
async def roulette_set_gender(update: Update, context: ContextTypes.DEFAULT_TYPE, gender: str):
    user_id = update.effective_user.id

    set_user_gender(user_id, gender)

    # Ищем пару
    partner = find_match(user_id, gender)

    if partner:
        # Пара найдена
        set_active_chat(user_id, partner)
        set_active_chat(partner, user_id)

        set_user_state(user_id, UserStates.ROULETTE_CHATTING)
        set_user_state(partner, UserStates.ROULETTE_CHATTING)

        await update.message.reply_text(
            "✅ <b>Собеседник найден!</b>\n"
            "Начинайте общаться.",
            parse_mode="HTML",
            reply_markup=kb.reply.roulette_chat()
        )

        await context.bot.send_message(
            partner,
            "✅ <b>Собеседник найден!</b>\n"
            "Начинайте общаться.",
            parse_mode="HTML",
            reply_markup=kb.reply.roulette_chat()
        )
    else:
        # Никого нет — становимся в очередь
        add_to_queue(user_id, gender)

        set_user_state(user_id, UserStates.ROULETTE_SEARCH)

        await update.message.reply_text(
            "🔍 <b>Поиск собеседника...</b>\n"
            "Ожидайте.",
            parse_mode="HTML",
            reply_markup=kb.reply.roulette_search()
        )


# ---------------------------------------------------------
# 3) Отмена поиска
# ---------------------------------------------------------
async def roulette_cancel_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    remove_from_queue(user_id)
    set_user_state(user_id, UserStates.MAIN_MENU)

    await update.message.reply_text(
        "❌ Поиск отменён.",
        reply_markup=kb.reply.main_menu()
    )


# ---------------------------------------------------------
# 4) Пользователь пишет собеседнику
# ---------------------------------------------------------
async def roulette_relay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    partner_id = get_partner(user_id)

    if not partner_id:
        await update.message.reply_text("❌ Ваш чат уже завершён.")
        return

    # Пересылка текста
    await context.bot.send_message(
        partner_id,
        f"💬 {update.message.text}"
    )


# ---------------------------------------------------------
# 5) Следующий собеседник
# ---------------------------------------------------------
async def roulette_next(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    partner_id = get_partner(user_id)

    # Завершаем текущий чат
    if partner_id:
        end_chat(user_id)
        end_chat(partner_id)

        await context.bot.send_message(
            partner_id,
            "👋 Собеседник переключился.",
            reply_markup=kb.reply.main_menu()
        )

    # Ищем нового
    gender = None
    # вытаскиваем из БД (там хранится)
    from db.roulette import get_user_gender
    gender = get_user_gender(user_id)

    await roulette_set_gender(update, context, gender)


# ---------------------------------------------------------
# 6) Стоп — завершить чат
# После стопа → быстрый поиск: М, Ж или любой
# ---------------------------------------------------------
async def roulette_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    partner_id = get_partner(user_id)

    if partner_id:
        end_chat(user_id)
        end_chat(partner_id)

        await context.bot.send_message(
            partner_id,
            "👋 Собеседник завершил чат.",
            reply_markup=kb.reply.main_menu()
        )

    set_user_state(user_id, UserStates.ROULETTE_QUICK_CHOICES)

    await update.message.reply_text(
        "Чат завершён.\n\n"
        "👇 Быстрый поиск:",
        reply_markup=kb.reply.roulette_quick()
    )


# ---------------------------------------------------------
# 7) Жалоба
# ---------------------------------------------------------
async def roulette_complaint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    partner_id = get_partner(user_id)

    if not partner_id:
        await update.message.reply_text("❌ Вы не в чате.")
        return

    save_roulette_complaint(user_id, partner_id)

    await update.message.reply_text("✅ Жалоба отправлена.")

    # уведомить админов
    for admin in ADMINS:
        await context.bot.send_message(
            admin,
            f"⚠ Жалоба (рулетка)\n"
            f"От: {user_id}\n"
            f"На: {partner_id}"
        )


# ---------------------------------------------------------
# 8) Регистрация хендлеров
# ---------------------------------------------------------
def register_roulette_handlers(app):

    # Выбор пола
    app.add_handler(MessageHandler(filters.Regex("^👨 Мужчина$"), lambda u, c: roulette_set_gender(u, c, "M")))
    app.add_handler(MessageHandler(filters.Regex("^👩 Женщина$"), lambda u, c: roulette_set_gender(u, c, "F")))

    # Отмена
    app.add_handler(MessageHandler(filters.Regex("^❌ Отменить$"), roulette_cancel_search))

    # Чат
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^(?!/).+") &
                                   filters.ChatType.PRIVATE,
                                   roulette_relay))

    # Следующий
    app.add_handler(MessageHandler(filters.Regex("^⏭ След\\. собеседник$"), roulette_next))

    # Стоп
    app.add_handler(MessageHandler(filters.Regex("^⛔ Стоп$"), roulette_stop))

    # Жалоба
    app.add_handler(MessageHandler(filters.Regex("^⚠ Пожаловаться$"), roulette_complaint))