from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)

import os

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = int(os.getenv("CHAT_ID", "-1003730582886"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", "8080"))

if not TOKEN:
    raise RuntimeError("Environment variable BOT_TOKEN is required")

VACANCY, NAME, PHONE = range(3)

TEXTS = {
    "ru": {
        "welcome": "👋 Добро пожаловать!\n\nЧерез этот бот вы можете откликнуться на вакансию.",
        "pick_vacancy": "📌 Пожалуйста, выберите вакансию:",
        "ask_name": "✍️ Введите ваше имя и фамилию:",
        "ask_phone": "📞 Введите ваш номер телефона:",
        "new_application": "📩 Новая заявка",
        "vacancy": "📌 Вакансия",
        "name": "👤 Имя",
        "phone": "📞 Телефон",
        "thanks": "✅ Спасибо! Наш менеджер свяжется с вами.",
        "vacancies": [["Бетонщик"], ["Бригадир"]],
    },
    "en": {
        "welcome": "👋 Welcome!\n\nYou can apply for a vacancy through this bot.",
        "pick_vacancy": "📌 Please choose a vacancy:",
        "ask_name": "✍️ Enter your first and last name:",
        "ask_phone": "📞 Enter your phone number:",
        "new_application": "📩 New application",
        "vacancy": "📌 Vacancy",
        "name": "👤 Name",
        "phone": "📞 Phone",
        "thanks": "✅ Thank you! Our manager will contact you.",
        "vacancies": [["Concrete worker"], ["Foreman"]],
    },
}


def detect_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    # Prefer deep-link payload from ads/posts: /start en or /start ru
    if context.args:
        payload = context.args[0].strip().lower()
        if payload in {"en", "eng", "english"}:
            return "en"
        if payload in {"ru", "rus", "russian"}:
            return "ru"

    return "ru"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = detect_language(update, context)
    context.user_data["lang"] = lang
    t = TEXTS[lang]

    await update.message.reply_text(
        t["welcome"]
    )

    await update.message.reply_text(
        t["pick_vacancy"],
        reply_markup=ReplyKeyboardMarkup(t["vacancies"], resize_keyboard=True)
    )

    return VACANCY


async def vacancy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["vacancy"] = update.message.text
    t = TEXTS.get(context.user_data.get("lang", "ru"), TEXTS["ru"])

    await update.message.reply_text(
        t["ask_name"],
        reply_markup=ReplyKeyboardRemove()
    )

    return NAME


async def name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    t = TEXTS.get(context.user_data.get("lang", "ru"), TEXTS["ru"])

    await update.message.reply_text(
        t["ask_phone"]
    )

    return PHONE


async def phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["phone"] = update.message.text

    data = context.user_data
    t = TEXTS.get(data.get("lang", "ru"), TEXTS["ru"])

    message = (
        f"{t['new_application']}\n\n"
        f"{t['vacancy']}: {data['vacancy']}\n"
        f"{t['name']}: {data['name']}\n"
        f"{t['phone']}: {data['phone']}"
    )

    await context.bot.send_message(
        chat_id=CHAT_ID,
        text=message
    )

    await update.message.reply_text(
        t["thanks"]
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
if WEBHOOK_URL:
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK_URL,
        close_loop=False,
    )
else:
    app.run_polling(close_loop=False)
