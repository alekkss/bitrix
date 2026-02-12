"""Обработчики событий сообщений"""

from telethon import events
import sys
sys.path.append('..')
from services.ai_service import AIService
from services.telegram_service import TelegramService
import config


class MessageHandler:
    """Класс для обработки входящих сообщений"""
    
    def __init__(self, telegram_service: TelegramService, ai_service: AIService):
        """
        Инициализация обработчика
        
        Args:
            telegram_service: Сервис Telegram
            ai_service: Сервис AI
        """
        self.telegram_service = telegram_service
        self.ai_service = ai_service
        self.greeted_users = set()
    
    async def handle_incoming_message(self, event):
        """
        Обработка входящих личных сообщений с AI-ответом
        
        Args:
            event: Событие нового сообщения
        """
        try:
            # Получение информации об отправителе
            sender = await event.get_sender()
            
            # Проверка на бота
            if sender and sender.bot:
                print(f"Игнорируем сообщение от бота: {sender.username or sender.first_name}")
                return
            
            # Проверка черного списка по username
            if sender.username and sender.username.lower() in [u.lower() for u in config.BLACKLIST_USERNAMES]:
                print(f"Игнорируем сообщение от пользователя из черного списка: @{sender.username}")
                return
            
            sender_id = event.sender_id
            sender_name = sender.first_name or "Пользователь"
            sender_username = sender.username if sender.username else None
            user_message = event.message.text
            
            # Проверяем, что сообщение содержит текст
            if not user_message:
                print(f"Получено сообщение без текста от {sender_name}")
                return
            
            print(f"Получено сообщение от {sender_name} (@{sender_username}, ID: {sender_id}): {user_message}")
            
            # Генерируем ответ с передачей username
            ai_response = self.ai_service.generate_response(
                user_message=user_message,
                user_name=sender_name,
                user_id=sender_id,
                username=sender_username  # ← ИСПРАВЛЕНО: передаём username
            )
            
            # Отправка ответа
            await self.telegram_service.send_message(event, ai_response)
            
            print(f"Отправлен AI-ответ пользователю {sender_name}: {ai_response}")
            
        except Exception as e:
            print(f"Ошибка при обработке сообщения: {e}")
    
    def register_handlers(self, client):
        """
        Регистрация обработчиков событий
        
        Args:
            client: Клиент Telegram
        """
        # Обработчик входящих личных сообщений от не-ботов
        @client.on(events.NewMessage(
            incoming=True,
            func=lambda e: e.is_private
        ))
        async def on_new_message(event):
            await self.handle_incoming_message(event)
