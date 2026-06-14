import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

TOKEN = "8982672799:AAEooOJWc18EuWif1f2EgZ5Bj0LonvUzJ4M"  # Сюда свой токен от @BotFather
ADMIN_ID = 830076237  # Твой Telegram ID (узнай у @userinfobot)

# --- Хранилище заявок и вопросов ---
applications = {}  # {user_id: [answers]}
questions = {}     # {user_id: "question_text"}

# --- Кнопки ---
def main_menu():
    keyboard = [
        [InlineKeyboardButton("📝 Подать заявку", callback_data="apply")],
        [InlineKeyboardButton("❓ Написать вопрос", callback_data="ask")],
    ]
    return InlineKeyboardMarkup(keyboard)

# --- /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Это бот-рекрутер команды **Rigid Force**.\n"
        "Если хочешь вступить в команду — нажми 'Подать заявку'.\n"
        "Если у тебя вопрос — напиши его через 'Написать вопрос'.",
        reply_markup=main_menu()
    )

# --- Обработка кнопок ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "apply":
        # Начинаем опрос
        applications[user_id] = []
        await query.edit_message_text(
            "📋 **Заявка на вступление**\n\n"
            "1️⃣ Какая у тебя роль? (3D-моделлер, аниматор, звукорежиссёр, дизайнер уровней, другое)"
        )
        context.user_data["step"] = "apply_role"

    elif query.data == "ask":
        await query.edit_message_text(
            "❓ Напиши свой вопрос. Я передам его создателю.\n"
            "(Можно текст, ссылку, даже фото)"
        )
        context.user_data["step"] = "ask_question"

# --- Приём сообщений ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    step = context.user_data.get("step")

    # --- Подача заявки (опрос) ---
    if step == "apply_role":
        applications[user_id].append(text)
        await update.message.reply_text("2️⃣ Ссылка на портфолио или примеры работ (можно текстом)")
        context.user_data["step"] = "apply_portfolio"

    elif step == "apply_portfolio":
        applications[user_id].append(text)
        await update.message.reply_text("3️⃣ Расскажи о своём опыте в Unreal Engine 4 (или почему хочешь научиться)")
        context.user_data["step"] = "apply_exp"

    elif step == "apply_exp":
        applications[user_id].append(text)
        await update.message.reply_text("4️⃣ Твой Telegram username (или любой контакт для связи)")
        context.user_data["step"] = "apply_contact"

    elif step == "apply_contact":
        applications[user_id].append(text)
        await update.message.reply_text("✅ Заявка отправлена! Создатель свяжется с тобой, если ты подходишь.")
        # Отправляем заявку админу
        msg = (
            f"📢 **НОВАЯ ЗАЯВКА**\n"
            f"👤 От: @{update.effective_user.username} (ID: {user_id})\n"
            f"🔹 Роль: {applications[user_id][0]}\n"
            f"🔹 Портфолио: {applications[user_id][1]}\n"
            f"🔹 Опыт: {applications[user_id][2]}\n"
            f"🔹 Контакт: {applications[user_id][3]}"
        )
        await context.bot.send_message(chat_id=ADMIN_ID, text=msg)
        # Очищаем шаг
        del context.user_data["step"]
        del applications[user_id]

    # --- Обычный вопрос ---
    elif step == "ask_question":
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"❓ **ВОПРОС ОТ ПОЛЬЗОВАТЕЛЯ**\n👤 @{update.effective_user.username} (ID: {user_id})\n\n{text}"
        )
        await update.message.reply_text("✅ Вопрос отправлен. Создатель ответит, когда сможет.")
        del context.user_data["step"]

    else:
        await update.message.reply_text(
            "Пожалуйста, используй кнопки меню: /start"
        )

# --- Админские команды (только для ADMIN_ID) ---
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    # Здесь нужно передать ID пользователя, которому одобряем
    # Пример: /approve 123456789
    try:
        user_id = int(context.args[0])
        await context.bot.send_message(
            chat_id=user_id,
            text="🎉 Ваша заявка одобрена! Вступайте в команду: https://t.me/ваш_канал_или_чат"
        )
        await update.message.reply_text(f"✅ Пользователь {user_id} одобрен.")
    except:
        await update.message.reply_text("Использование: /approve <user_id>")

async def decline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    # Пример: /decline 123456789 Причина не подходит
    try:
        user_id = int(context.args[0])
        reason = " ".join(context.args[1:]) if len(context.args) > 1 else "не указана"
        await context.bot.send_message(
            chat_id=user_id,
            text=f"❌ Ваша заявка отклонена. Причина: {reason}"
        )
        await update.message.reply_text(f"❌ Пользователь {user_id} отклонён. Причина: {reason}")
    except:
        await update.message.reply_text("Использование: /decline <user_id> причина")

# --- Запуск ---
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(CommandHandler("decline", decline))
    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()