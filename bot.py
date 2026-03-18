from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)

import os

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = int(os.getenv("CHAT_ID", "-1003730582886"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/telegram-webhook")
PORT = int(os.getenv("PORT", "8080"))
CONVERSATION_TIMEOUT = int(os.getenv("CONVERSATION_TIMEOUT", "900"))

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
        "incomplete_application": "⚠️ Незавершенная заявка",
        "vacancy": "📌 Вакансия",
        "name": "👤 Имя",
        "phone": "📞 Телефон",
        "telegram_name": "👤 Имя в Telegram",
        "telegram_username": "🔗 Username",
        "telegram_contact": "💬 Связь в Telegram",
        "telegram_id": "🆔 Telegram ID",
        "thanks": "✅ Спасибо! Наш менеджер свяжется с вами.",
        "timed_out": "⌛ Заявка не завершена. Мы сохранили то, что вы уже ввели.",
        "vacancies": [["Бетонщик"], ["Бригадир"], ["Сборщик"], ["Сварщик 136 метод"]],
    },
    "en": {
        "welcome": "👋 Welcome!\n\nYou can apply for a vacancy through this bot.",
        "pick_vacancy": "📌 Please choose a vacancy:",
        "ask_name": "✍️ Enter your first and last name:",
        "ask_phone": "📞 Enter your phone number:",
        "new_application": "📩 New application",
        "incomplete_application": "⚠️ Incomplete application",
        "vacancy": "📌 Vacancy",
        "name": "👤 Name",
        "phone": "📞 Phone",
        "telegram_name": "👤 Telegram name",
        "telegram_username": "🔗 Username",
        "telegram_contact": "💬 Telegram contact",
        "telegram_id": "🆔 Telegram ID",
        "thanks": "✅ Thank you! Our manager will contact you.",
        "timed_out": "⌛ Application not completed. We saved what you entered.",
        "vacancies": [["Concrete worker"], ["Foreman"], ["Assembler"], ["Welder 136 method"]],
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


def has_partial_application(data: dict) -> bool:
    return data.get("started") and not data.get("submitted")


def save_telegram_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return

    full_name = " ".join(part for part in [user.first_name, user.last_name] if part).strip()
    if full_name:
        context.user_data["telegram_name"] = full_name
    if user.username:
        context.user_data["telegram_username"] = user.username
        context.user_data["telegram_contact_url"] = f"https://t.me/{user.username}"
    else:
        context.user_data["telegram_contact_url"] = f"tg://user?id={user.id}"
    context.user_data["telegram_id"] = str(user.id)


async def send_application_to_manager(context: ContextTypes.DEFAULT_TYPE, incomplete: bool = False):
    data = context.user_data
    if not has_partial_application(data):
        return
    if incomplete and data.get("incomplete_sent"):
        return

    t = TEXTS.get(data.get("lang", "ru"), TEXTS["ru"])
    title = t["incomplete_application"] if incomplete else t["new_application"]
    vacancy = data.get("vacancy", "—")
    name_value = data.get("name", "—")
    phone_value = data.get("phone", "—")
    telegram_name = data.get("telegram_name", "—")
    telegram_username = f"@{data['telegram_username']}" if data.get("telegram_username") else "—"
    telegram_id = data.get("telegram_id", "—")
    telegram_contact_url = data.get("telegram_contact_url")
    telegram_contact = (
        f'<a href="{telegram_contact_url}">{t["telegram_contact"]}</a>'
        if telegram_contact_url
        else t["telegram_contact"]
    )

    message = (
        f"{title}\n\n"
        f"{t['vacancy']}: {vacancy}\n"
        f"{t['name']}: {name_value}\n"
        f"{t['phone']}: {phone_value}\n"
        f"{t['telegram_name']}: {telegram_name}\n"
        f"{t['telegram_username']}: {telegram_username}\n"
        f"{t['telegram_id']}: {telegram_id}\n"
        f"{telegram_contact}"
    )

    await context.bot.send_message(chat_id=CHAT_ID, text=message, parse_mode=ParseMode.HTML)
    if incomplete:
        data["incomplete_sent"] = True
    else:
        data["submitted"] = True


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = detect_language(update, context)
    context.user_data.clear()
    context.user_data["lang"] = lang
    context.user_data["started"] = True
    save_telegram_contact(update, context)
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
    save_telegram_contact(update, context)
    context.user_data["vacancy"] = update.message.text
    t = TEXTS.get(context.user_data.get("lang", "ru"), TEXTS["ru"])

    await update.message.reply_text(
        t["ask_name"],
        reply_markup=ReplyKeyboardRemove()
    )

    return NAME


async def name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_telegram_contact(update, context)
    context.user_data["name"] = update.message.text
    t = TEXTS.get(context.user_data.get("lang", "ru"), TEXTS["ru"])

    await update.message.reply_text(
        t["ask_phone"]
    )

    return PHONE


async def phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_telegram_contact(update, context)
    context.user_data["phone"] = update.message.text

    data = context.user_data
    t = TEXTS.get(data.get("lang", "ru"), TEXTS["ru"])
    await send_application_to_manager(context, incomplete=False)

    await update.message.reply_text(
        t["thanks"]
    )
    context.user_data.clear()

    return ConversationHandler.END


async def handle_timeout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_application_to_manager(context, incomplete=True)
    t = TEXTS.get(context.user_data.get("lang", "ru"), TEXTS["ru"])
    if update and update.effective_chat:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=t["timed_out"])
    context.user_data.clear()
    return ConversationHandler.END


app = ApplicationBuilder().token(TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    allow_reentry=True,
    conversation_timeout=CONVERSATION_TIMEOUT,
    states={
        VACANCY: [MessageHandler(filters.TEXT & ~filters.COMMAND, vacancy)],
        NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name)],
        PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, phone)],
        ConversationHandler.TIMEOUT: [MessageHandler(filters.ALL, handle_timeout)],
    },
    fallbacks=[]
)

app.add_handler(conv_handler)

print("Bot started...")
if WEBHOOK_URL:
    webhook_path = WEBHOOK_PATH if WEBHOOK_PATH.startswith("/") else f"/{WEBHOOK_PATH}"
    full_webhook_url = f"{WEBHOOK_URL.rstrip('/')}{webhook_path}"
    print(f"Running in webhook mode on port {PORT}, path {webhook_path}")
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=webhook_path.lstrip("/"),
        webhook_url=full_webhook_url,
        drop_pending_updates=True,
        close_loop=False,
    )
else:
    print("Running in polling mode")
    app.run_polling(close_loop=False)
