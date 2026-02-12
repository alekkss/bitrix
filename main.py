"""Точка входа приложения"""

import asyncio
from services.telegram_service import TelegramService
from services.ai_service import AIService
from handlers.message_handler import MessageHandler
from database.db_service import DatabaseService
from database.knowledge_service import KnowledgeService
from admin_bot.admin_bot import AdminBot
import config


async def run_admin_bot_async(admin_bot):
    """Асинхронный запуск админ-бота"""
    await admin_bot.application.initialize()
    await admin_bot.application.start()
    await admin_bot.application.updater.start_polling()
    print("Админ-бот запущен...")


async def run_user_bot():
    """Запуск пользовательского бота"""
    # Инициализация базы данных
    db_service = DatabaseService(config.DATABASE_PATH)
    knowledge_service = KnowledgeService(db_service)
    
    # Инициализация сервисов
    telegram_service = TelegramService()
    ai_service = AIService(knowledge_service)
    
    # Инициализация обработчика сообщений
    message_handler = MessageHandler(telegram_service, ai_service)
    
    # Запуск Telegram клиента
    async with telegram_service.get_client() as client:
        await telegram_service.start()
        
        # Регистрация обработчиков
        message_handler.register_handlers(client)
        
        print("Автоответчик с AI и базой знаний запущен. Ожидание входящих сообщений...")
        
        # Запуск клиента до отключения
        await client.run_until_disconnected()


async def main():
    """Главная функция - запуск обоих ботов в одном event loop"""
    # Инициализация админ-бота
    admin_bot = AdminBot()
    
    # Создаем задачи для обоих ботов
    admin_task = asyncio.create_task(run_admin_bot_async(admin_bot))
    user_task = asyncio.create_task(run_user_bot())
    
    # Запускаем обе задачи параллельно
    await asyncio.gather(admin_task, user_task)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nОстановка ботов...")
