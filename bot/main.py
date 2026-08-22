import os
import json
import logging
from http.server import BaseHTTPRequestHandler
from anthropic import Anthropic
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

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
6. Поощряй даже маленький прогресс

ФОРМАТ ПРОВЕРКИ:
✅ Что хорошо
❌ Ошибки (каждую объясни по-русски)
💡 Совет на сегодня
⭐ Оценка A/B/C"""


def call_claude(messages, system=None):
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1200,
        system=system or SYSTEM_PROMPT,
        messages=messages
    )
    return response.content[0].text


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = [[InlineKeyboardButton(
        "📚 Открыть план обучения",
        web_app=WebAppInfo(url=WEBAPP_URL)
    )]]
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n\n"
        "Я твой учитель английского 🇬🇧\n\n"
        "• Пиши по-английски — проверю ошибки\n"
        "• Пиши по-русски — отвечу и дам упражнение\n"
        "• Отправь голосовое — дам совет\n\n"
        "Или открой план обучения 👇",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.effective_message.web_app_data.data
    logger.info(f"WebApp data: {data[:80]}")
    await update.effective_message.reply_text("⏳ Проверяю...")
    try:
        answer = call_claude([{"role": "user", "content": data}])
        await update.effective_message.reply_text(answer)
    except Exception as e:
        logger.error(f"Claude error: {e}")
        await update.effective_message.reply_text("⚠️ Ошибка. Напиши мне в чат напрямую.")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text
    eng = sum(1 for c in msg if c.isascii() and c.isalpha())
    total = sum(1 for c in msg if c.isalpha())
    is_eng = total > 3 and (eng / total) > 0.6 if total else False

    prompt = (
        f'Ученик написал по-английски:\n\n"{msg}"\n\nПроверь. Формат:\n✅ Что хорошо\n❌ Ошибки\n💡 Совет\n⭐ Оценка'
        if is_eng else
        f'Ученик написал по-русски:\n\n"{msg}"\n\nОтветь и дай практическое упражнение.'
    )
    await update.message.chat.send_action("typing")
    try:
        answer = call_claude([{"role": "user", "content": prompt}])
        await update.message.reply_text(answer)
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("⚠️ Ошибка. Попробуй ещё раз.")


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎤 Получил голосовое!\n\n"
        "Напиши текстом что ты сказал — проверю грамматику и дам совет по произношению 👇"
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
