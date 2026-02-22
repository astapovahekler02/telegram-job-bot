from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)

TOKEN = "7956571535:AAHDCyd6AzquBsqjDofo8vUnqDeSRtc0psI"
CHAT_ID = -1003730582886  

VACANCY, NAME, PHONE = range(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Добро пожаловать!\n\n"
        "Через этот бот вы можете откликнуться на вакансию."
    )

    keyboard = [
        ["Бетонщик"],
        ["Бригадир"]
    ]

    await update.message.reply_text(
        "📌 Пожалуйста, выберите вакансию:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

    return VACANCY


async def vacancy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["vacancy"] = update.message.text

    await update.message.reply_text(
        "✍️ Введите ваше имя и фамилию:",
        reply_markup=ReplyKeyboardRemove()
    )

    return NAME


async def name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text

    await update.message.reply_text(
        "📞 Введите ваш номер телефона:"
    )

    return PHONE


async def phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["phone"] = update.message.text

    data = context.user_data

    message = (
        "📩 Новая заявка\n\n"
        f"📌 Вакансия: {data['vacancy']}\n"
        f"👤 Имя: {data['name']}\n"
        f"📞 Телефон: {data['phone']}"
    )

    await context.bot.send_message(
        chat_id=CHAT_ID,
        text=message
    )

    await update.message.reply_text(
        "✅ Спасибо! Наш менеджер свяжется с вами."
    )

    return ConversationHandler.END


app = ApplicationBuilder().token(TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        VACANCY: [MessageHandler(filters.TEXT & ~filters.COMMAND, vacancy)],
        NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name)],
        PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, phone)],
    },
    fallbacks=[]
)

app.add_handler(conv_handler)

print("Bot started...")
app.run_polling(close_loop=False)