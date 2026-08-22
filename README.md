# 🇬🇧 English Learning Telegram Bot

Telegram бот + Mini App для изучения английского с нуля за 6 месяцев.

## Деплой на Railway (бесплатно) — 10 минут

### Шаг 1 — GitHub
1. Зайди на github.com → New repository → назови `english-bot` → Create
2. Загрузи все файлы этой папки в репозиторий

### Шаг 2 — Railway
1. Зайди на railway.app → Login with GitHub
2. New Project → Deploy from GitHub repo → выбери `english-bot`
3. Railway автоматически задетектит Python и задеплоит

### Шаг 3 — Переменные окружения
В Railway → твой проект → Variables → добавь:
```
BOT_TOKEN = твой_токен_от_botfather
ANTHROPIC_API_KEY = твой_ключ_от_console.anthropic.com
WEBAPP_URL = https://твой-проект.railway.app
```

### Шаг 4 — Получить Anthropic API Key
1. Зайди на console.anthropic.com
2. Зарегистрируйся (бесплатно)
3. API Keys → Create Key → скопируй

### Шаг 5 — Настроить Mini App в BotFather
1. Откройте @BotFather
2. /mybots → твой бот → Bot Settings → Menu Button
3. Вставь URL: `https://твой-проект.railway.app`

### Шаг 6 — Готово!
Открой бота в Telegram → /start → нажми кнопку "Открыть план обучения"

## Структура файлов
```
english_bot/
├── bot/
│   └── main.py          # Telegram бот
├── webapp/
│   ├── index.html       # Mini App (план обучения)
│   └── server.py        # Статический сервер
├── start.py             # Запускает бот + сервер
├── requirements.txt
├── railway.json
└── Procfile
```
