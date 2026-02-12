"""Главный файл админ-бота"""

from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import sys
sys.path.append('..')
from admin_bot.admin_handlers import AdminHandlers
from database.db_service import DatabaseService
from database.knowledge_service import KnowledgeService
from services.ai_service import AIService  # ← НОВЫЙ ИМПОРТ
import config


class AdminBot:
    """Класс для управления админ-ботом"""
    
    def __init__(self):
        """Инициализация админ-бота"""
        self.application = Application.builder().token(config.ADMIN_BOT_TOKEN).build()
        
        # Инициализация сервисов
        self.db_service = DatabaseService(config.DATABASE_PATH)
        self.knowledge_service = KnowledgeService(self.db_service)
        
        # НОВОЕ: Инициализация AI сервиса для тестирования
        self.ai_service = AIService(self.knowledge_service)
        
        # Инициализация обработчиков с AI сервисом
        self.handlers = AdminHandlers(self.knowledge_service, self.ai_service)  # ← ИЗМЕНЕНО
        
        # Регистрация обработчиков
        self._register_handlers()
    
    def _register_handlers(self):
        """Регистрация всех обработчиков команд"""
        # Команда /start
        self.application.add_handler(
            CommandHandler("start", self.handlers.start_command)
        )
        
        # Обработчик кнопок
        self.application.add_handler(
            CallbackQueryHandler(self.handlers.button_handler)
        )
        
        # ВАЖНО: Обработчик документов ПЕРЕД текстовым
        self.application.add_handler(
            MessageHandler(filters.Document.ALL, self.handlers.message_handler)
        )
        
        # Обработчик текстовых сообщений
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handlers.message_handler)
        )
