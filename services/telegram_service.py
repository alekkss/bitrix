"""Сервис для работы с Telegram"""

from telethon.sync import TelegramClient
import sys
sys.path.append('..')
import config


class TelegramService:
    """Класс для управления Telegram клиентом"""
    
    def __init__(self):
        """Инициализация Telegram клиента"""
        self.client = TelegramClient(
            'session_name',
            config.TELEGRAM_API_ID,
            config.TELEGRAM_API_HASH
        )
    
    async def start(self):
        """Запуск и авторизация клиента"""
        await self.client.start(phone=config.TELEGRAM_PHONE)
        print("Telegram клиент успешно запущен и авторизован")
    
    async def send_message(self, event, message: str):
        """
        Отправка сообщения в ответ на событие
        
        Args:
            event: Событие Telegram
            message: Текст сообщения для отправки
        """
        try:
            await event.respond(message)
        except Exception as e:
            print(f"Ошибка при отправке сообщения: {e}")
            raise
    
    def get_client(self) -> TelegramClient:
        """Получение экземпляра клиента"""
        return self.client
