"""Конфигурация приложения"""

# Telegram API настройки для пользовательского аккаунта
TELEGRAM_API_ID = 'ваш id'
TELEGRAM_API_HASH = 'хеш'
TELEGRAM_PHONE = 'номер'

# Telegram Bot API для админки
ADMIN_BOT_TOKEN = 'api тг'

# ID администраторов (замените на свой Telegram ID)
ADMIN_IDS = [436816068,6752272110]  # Добавьте свой ID

# НОВОЕ: Список исключений (username без @)
BLACKLIST_USERNAMES = ["список исключений"
    # Примеры (раскомментируйте и добавьте нужные):
    # "spam_bot",
    # "annoying_user",
    # "test_account",
]

# OpenAI настройки
OPENAI_BASE_URL = "https://openrouter.ai/api/v1"
OPENAI_API_KEY = "api"
AI_MODEL = "модель ИИ"

# Настройки AI
AI_MAX_TOKENS = 500
AI_SYSTEM_PROMPT = (
    "Ты — дружелюбный ассистент, который отвечает на сообщения пользователей в Telegram. "
    "Твои ответы должны быть краткими (до 500 символов), полезными и естественными. "
    "Пиши на русском языке в человеческом стиле, как будто общаешься с другом. "
    "Используй базу знаний для предоставления точной информации."
)

# Настройки базы данных
DATABASE_PATH = 'knowledge_base.db'
