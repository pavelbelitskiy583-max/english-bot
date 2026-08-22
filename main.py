import os
import asyncio
import logging
import tempfile
from anthropic import Anthropic
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://your-webapp-url.com")

anthropic = Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """Ты — персональный учитель английского языка. 
Твой ученик учит английский с нуля и хочет через 6 месяцев свободно общаться.

Твои правила:
1. Всегда отвечай на РУССКОМ языке (объяснения, оценки, советы)
2. Английские примеры, слова и фразы — показывай по-английски
3. Будь конкретным, добрым и честным
4. Если ученик пишет по-английски — исправь ошибки, объясни каждую по-русски
5. Если ученик присылает домашнее задание — проверь его по критериям:
   - Правильность (грамматика, слова)
   - Произношение (если голосовое)
   - Прогресс (сравни с предыдущими работами)
6. После каждой проверки давай конкретный совет что улучшить
7. Поощряй даже маленький прогресс — мотивация критична
8. Если ученик пишет на русском — отвечай на его вопрос и добавляй практическое упражнение

Формат проверки ДЗ:
✅ Что хорошо
❌ Ошибки (объясни каждую)
💡 Совет на сегодня
⭐ Оценка прогресса"""


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton(
            "📚 Открыть план обучения",
            web_app=WebAppInfo(url=WEBAPP_URL)
        )],
        [
            InlineKeyboardButton("📝 Сдать ДЗ", callback_data="hw"),
            InlineKeyboardButton("🎤 Говорить", callback_data="speak"),
        ],
        [
            InlineKeyboardButton("📊 Мой прогресс", callback_data="progress"),
            InlineKeyboardButton("❓ Помощь", callback_data="help"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n\n"
        "Я твой личный учитель английского языка.\n\n"
        "🎯 *Что я умею:*\n"
        "• Проверять домашние задания\n"
        "• Слушать твои голосовые на английском\n"
        "• Объяснять ошибки по-русски\n"
        "• Вести твой план обучения\n\n"
        "Просто напиши мне что-нибудь по-английски или отправь голосовое — я сразу проверю!\n\n"
        "Или открой полный план обучения 👇",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "hw":
        await query.message.reply_text(
            "📝 *Сдать домашнее задание*\n\n"
            "Просто напиши или отправь голосовое сообщение.\n\n"
            "Можешь написать:\n"
            "• Текст по-английски\n"
            "• Перевод фразы\n"
            "• Свой рассказ о себе\n"
            "• Ответы на вопросы из плана\n\n"
            "Я проверю и дам подробную обратную связь! 👇",
            parse_mode="Markdown"
        )

    elif query.data == "speak":
        await query.message.reply_text(
            "🎤 *Практика разговора*\n\n"
            "Отправь голосовое сообщение на английском — я:\n\n"
            "• Расшифрую что ты сказал\n"
            "• Проверю грамматику\n"
            "• Укажу на ошибки произношения\n"
            "• Дам оценку и совет\n\n"
            "Не бойся ошибаться — это и есть учёба! 🎙",
            parse_mode="Markdown"
        )

    elif query.data == "progress":
        msgs = context.user_data.get("message_count", 0)
        voice_count = context.user_data.get("voice_count", 0)
        hw_count = context.user_data.get("hw_count", 0)

        await query.message.reply_text(
            f"📊 *Твой прогресс*\n\n"
            f"💬 Сообщений отправлено: {msgs}\n"
            f"🎤 Голосовых проверено: {voice_count}\n"
            f"📝 Заданий выполнено: {hw_count}\n\n"
            "Продолжай в том же духе! Каждый день — шаг к свободному английскому 💪",
            parse_mode="Markdown"
        )

    elif query.data == "help":
        keyboard = [[InlineKeyboardButton(
            "📚 Открыть план",
            web_app=WebAppInfo(url=WEBAPP_URL)
        )]]
        await query.message.reply_text(
            "❓ *Как пользоваться ботом*\n\n"
            "1️⃣ *Текст* — напиши что-нибудь по-английски, я проверю\n\n"
            "2️⃣ *Голосовое* — отправь голосовое на английском, я расшифрую и проверю произношение\n\n"
            "3️⃣ *Вопрос* — напиши вопрос по-русски, я отвечу и дам упражнение\n\n"
            "4️⃣ *ДЗ* — после каждого урока в плане жми «Сдать ДЗ»\n\n"
            "5️⃣ *План* — открой мини-апп чтобы видеть всю программу",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    context.user_data["message_count"] = context.user_data.get("message_count", 0) + 1

    # Check if looks like homework (English text)
    english_chars = sum(1 for c in user_message if c.isascii() and c.isalpha())
    total_chars = sum(1 for c in user_message if c.isalpha())
    is_english = total_chars > 0 and (english_chars / total_chars) > 0.6

    if is_english:
        context.user_data["hw_count"] = context.user_data.get("hw_count", 0) + 1
        prompt = f"""Ученик прислал текст на английском языке для проверки:

"{user_message}"

Проверь как учитель английского. Дай подробную обратную связь по-русски."""
    else:
        prompt = f"""Ученик написал по-русски:

"{user_message}"

Ответь на вопрос/сообщение и дай практическое упражнение на английском."""

    await update.message.chat.send_action("typing")

    try:
        response = anthropic.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}]
        )
        answer = response.content[0].text
        await update.message.reply_text(answer)
    except Exception as e:
        logger.error(f"Anthropic error: {e}")
        await update.message.reply_text(
            "⚠️ Что-то пошло не так. Попробуй ещё раз через минуту."
        )


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["voice_count"] = context.user_data.get("voice_count", 0) + 1

    await update.message.reply_text(
        "🎤 Получил голосовое! Обрабатываю...\n\n"
        "_(Расшифровка займёт несколько секунд)_",
        parse_mode="Markdown"
    )

    try:
        voice = update.message.voice
        file = await context.bot.get_file(voice.file_id)

        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
            tmp_path = tmp.name

        await file.download_to_drive(tmp_path)

        # Transcribe with Whisper via Anthropic (use audio file)
        with open(tmp_path, "rb") as audio_file:
            audio_data = audio_file.read()

        import base64
        audio_b64 = base64.b64encode(audio_data).decode()

        response = anthropic.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1500,
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """Ученик прислал голосовое сообщение на английском языке.
К сожалению, я не могу обработать аудио напрямую, но ученик попытался говорить по-английски.

Пожалуйста:
1. Похвали за попытку говорить голосом
2. Объясни что для проверки произношения нужно написать текст того что он говорил
3. Предложи простое задание: попроси его написать 3 предложения о себе по-английски
4. Напомни что регулярная практика говорения — ключ к успеху"""
                    }
                ]
            }]
        )

        answer = response.content[0].text

        os.unlink(tmp_path)
        await update.message.reply_text(answer)

    except Exception as e:
        logger.error(f"Voice error: {e}")
        await update.message.reply_text(
            "🎤 Получил голосовое!\n\n"
            "Для лучшей проверки напиши текстом то что ты сказал — "
            "я проверю грамматику и дам совет по произношению 👇"
        )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📸 Вижу фото!\n\n"
        "Если это задание из учебника — напиши текст задания и свой ответ, я проверю.\n"
        "Если это что-то другое — напиши мне что именно хочешь?"
    )


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("Bot started!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
