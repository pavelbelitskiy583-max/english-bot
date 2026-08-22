import os
import logging
import google.generativeai as genai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WEBAPP_URL = os.getenv("WEBAPP_URL", "")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

SYSTEM_PROMPT = """Ты — персональный учитель английского языка. Ученик учит английский с нуля.

ПРАВИЛА:
1. Отвечай на РУССКОМ языке (объяснения, советы, оценки)
2. Английские примеры пиши по-английски
3. Будь конкретным, добрым и честным
4. Если ученик пишет по-английски — исправь ошибки, объясни каждую по-русски
5. После проверки всегда давай совет что улучшить
6. Поощряй даже маленький прогресс — мотивация критична

ФОРМАТ ПРОВЕРКИ:
✅ Что хорошо
❌ Ошибки (каждую объясни по-русски)
💡 Совет на сегодня
⭐ Оценка A/B/C"""


def ask_gemini(user_text, system=None):
    prompt = f"{system or SYSTEM_PROMPT}\n\nУченик: {user_text}"
    response = model.generate_content(prompt)
    return response.text


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
        "• Голосовое — напиши текстом, проверю\n\n"
        "Или открой план обучения 👇",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.effective_message.web_app_data.data
    logger.info(f"WebApp data: {data[:80]}")
    await update.effective_message.reply_text("⏳ Проверяю...")
    try:
        answer = ask_gemini(data)
        await update.effective_message.reply_text(answer)
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        await update.effective_message.reply_text("⚠️ Ошибка. Напиши мне в чат напрямую.")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text
    eng = sum(1 for c in msg if c.isascii() and c.isalpha())
    total = sum(1 for c in msg if c.isalpha())
    is_eng = total > 3 and (eng / total) > 0.6 if total else False

    prompt = (
        f'Ученик написал по-английски:\n\n"{msg}"\n\nПроверь:\n✅ Что хорошо\n❌ Ошибки (объясни по-русски)\n💡 Совет\n⭐ Оценка A/B/C'
        if is_eng else
        f'Ученик написал по-русски:\n\n"{msg}"\n\nОтветь и дай практическое упражнение на английском.'
    )
    await update.message.chat.send_action("typing")
    try:
        answer = ask_gemini(prompt)
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
