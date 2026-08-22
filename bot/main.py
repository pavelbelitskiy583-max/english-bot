import os
import logging
import json
from anthropic import Anthropic
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
WEBAPP_URL = os.getenv("WEBAPP_URL", "")

client = Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """Ты — персональный учитель английского языка. Ученик учит английский с нуля.

ПРАВИЛА:
1. Отвечай на РУССКОМ языке (объяснения, советы, оценки)
2. Английские примеры пиши по-английски
3. Будь конкретным, добрым и честным
4. Если ученик пишет по-английски — исправь ошибки, объясни каждую по-русски
5. После проверки всегда давай конкретный совет что улучшить
6. Поощряй даже маленький прогресс — мотивация критична
7. Если ученик пишет на русском — отвечай и добавляй практическое упражнение

ФОРМАТ ПРОВЕРКИ ДЗ:
✅ Что хорошо
❌ Ошибки (каждую объясни по-русски)
💡 Совет на сегодня
⭐ Оценка (A/B/C) и слова поддержки"""


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = [[InlineKeyboardButton(
        "📚 Открыть план обучения",
        web_app=WebAppInfo(url=WEBAPP_URL)
    )]]
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n\n"
        "Я твой личный учитель английского 🇬🇧\n\n"
        "Просто пиши мне:\n"
        "• По-английски — проверю и исправлю ошибки\n"
        "• По-русски — отвечу и дам упражнение\n"
        "• Голосовое — послушаю и дам совет\n\n"
        "Или открой план обучения 👇",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle data sent from Mini App via sendData()"""
    data = update.effective_message.web_app_data.data
    logger.info(f"WebApp data received: {data[:100]}")

    await update.effective_message.reply_text("⏳ Учитель думает...")

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1200,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": data}]
        )
        answer = response.content[0].text
        await update.effective_message.reply_text(answer)
    except Exception as e:
        logger.error(f"Anthropic error: {e}")
        await update.effective_message.reply_text(
            "⚠️ Ошибка. Попробуй написать мне напрямую в чат."
        )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    if not user_message:
        return

    # Count english chars ratio
    eng = sum(1 for c in user_message if c.isascii() and c.isalpha())
    total = sum(1 for c in user_message if c.isalpha())
    is_english = total > 3 and total > 0 and (eng / total) > 0.6

    if is_english:
        prompt = f'Ученик написал по-английски для проверки:\n\n"{user_message}"\n\nПроверь как учитель. Дай подробную обратную связь.'
    else:
        prompt = f'Ученик написал по-русски:\n\n"{user_message}"\n\nОтветь и дай практическое упражнение на английском.'

    await update.message.chat.send_action("typing")

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1200,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}]
        )
        await update.message.reply_text(response.content[0].text)
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("⚠️ Что-то пошло не так. Попробуй ещё раз.")


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎤 Получил голосовое!\n\n"
        "Напиши текстом что ты сказал — я проверю грамматику и дам совет по произношению 👇"
    )


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    logger.info("Bot started!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
