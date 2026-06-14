import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ===== НАСТРОЙКИ (ЗАМЕНИ НА СВОИ) =====
TOKEN = "8982672799:AAEooOJWc18EuWif1f2EgZ5Bj0LonvUzJ4M"   # Токен твоего бота
ADMIN_ID = 8430076237                                      # Твой Telegram ID (узнай у @userinfobot)
# ======================================

applications = {}
user_states = {}

def main_menu():
    keyboard = [
        [InlineKeyboardButton("📝 Подать заявку", callback_data="apply")],
        [InlineKeyboardButton("❓ Написать вопрос", callback_data="ask")],
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Это бот-рекрутер команды **Full Force**.\n"
        "Если хочешь вступить в команду — нажми 'Подать заявку'.\n"
        "Если у тебя вопрос — напиши его через 'Написать вопрос'.",
        reply_markup=main_menu()
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "apply":
        applications[user_id] = []
        user_states[user_id] = "apply_role"
        await query.edit_message_text(
            "📋 **Заявка на вступление**\n\n"
            "1️⃣ Какая у тебя роль? (3D-моделлер, аниматор, звукорежиссёр, дизайнер уровней, другое)"
        )
    elif query.data == "ask":
        user_states[user_id] = "ask_question"
        await query.edit_message_text(
            "❓ Напиши свой вопрос. Я передам его создателю.\n"
            "(Можно текст, ссылку, даже фото)"
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    state = user_states.get(user_id)

    # ---- ЗАЯВКА: шаг 1 (роль) ----
    if state == "apply_role":
        applications[user_id].append(text)
        user_states[user_id] = "apply_portfolio"
        await update.message.reply_text("2️⃣ Ссылка на портфолио или примеры работ (можно текстом)")

    # ---- ЗАЯВКА: шаг 2 (портфолио) ----
    elif state == "apply_portfolio":
        applications[user_id].append(text)
        user_states[user_id] = "apply_exp"
        await update.message.reply_text("3️⃣ Расскажи о своём опыте в Unreal Engine 4 (или почему хочешь научиться)")

    # ---- ЗАЯВКА: шаг 3 (опыт) ----
    elif state == "apply_exp":
        applications[user_id].append(text)
        user_states[user_id] = "apply_contact"
        await update.message.reply_text("4️⃣ Твой Telegram username (или любой контакт для связи)")

    # ---- ЗАЯВКА: финал ----
    elif state == "apply_contact":
        applications[user_id].append(text)
        await update.message.reply_text("✅ Заявка отправлена! Создатель свяжется с тобой, если ты подходишь.")

        # Формируем сообщение для админа
        msg = (
            f"📢 **НОВАЯ ЗАЯВКА**\n"
            f"👤 От: @{update.effective_user.username} (ID: {user_id})\n"
            f"🔹 Роль: {applications[user_id][0]}\n"
            f"🔹 Портфолио: {applications[user_id][1]}\n"
            f"🔹 Опыт: {applications[user_id][2]}\n"
            f"🔹 Контакт: {applications[user_id][3]}"
        )
        # Отправляем админу (тебе)
        await context.bot.send_message(chat_id=ADMIN_ID, text=msg)

        # Очищаем данные пользователя
        del user_states[user_id]
        del applications[user_id]

    # ---- ОБЫЧНЫЙ ВОПРОС ----
    elif state == "ask_question":
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"❓ **ВОПРОС ОТ ПОЛЬЗОВАТЕЛЯ**\n👤 @{update.effective_user.username} (ID: {user_id})\n\n{text}"
        )
        await update.message.reply_text("✅ Вопрос отправлен. Создатель ответит, когда сможет.")
        del user_states[user_id]

    # ---- НЕПОНЯТНОЕ СООБЩЕНИЕ ----
    else:
        await update.message.reply_text("Используй /start для начала.")

# ===== АДМИН-КОМАНДЫ =====
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        user_id = int(context.args[0])
        await context.bot.send_message(
            chat_id=user_id,
            text="🎉 Ваша заявка одобрена! Вступайте в команду: https://t.me/+pZ5IV1LmBk5hZTYy"
        )
        await update.message.reply_text(f"✅ Пользователь {user_id} одобрен.")
    except:
        await update.message.reply_text("Использование: /approve <user_id>")

async def decline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        user_id = int(context.args[0])
        reason = " ".join(context.args[1:]) if len(context.args) > 1 else "не указана"
        await context.bot.send_message(
            chat_id=user_id,
            text=f"❌ Ваша заявка отклонена. Причина: {reason}"
        )
        await update.message.reply_text(f"❌ Пользователь {user_id} отклонён.")
    except:
        await update.message.reply_text("Использование: /decline <user_id> причина")

# ===== ЗАПУСК =====
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(CommandHandler("decline", decline))
    print("✅ Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
