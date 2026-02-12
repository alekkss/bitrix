"""Сервис для работы с историей диалогов"""

from typing import List, Dict
import sys
sys.path.append('..')
from database.db_service import DatabaseService


class ConversationService:
    """Класс для управления историей диалогов"""
    
    def __init__(self, db_service: DatabaseService):
        """
        Инициализация сервиса диалогов
        
        Args:
            db_service: Сервис базы данных
        """
        self.db_service = db_service
    
    def add_message(self, user_id: int, username: str, user_first_name: str, 
                   role: str, message: str) -> int:
        """
        Добавление сообщения в историю
        
        Args:
            user_id: Telegram ID пользователя
            username: Username пользователя (может быть None)
            user_first_name: Имя пользователя
            role: 'user' или 'assistant'
            message: Текст сообщения
            
        Returns:
            ID добавленной записи
        """
        query = '''
            INSERT INTO conversation_history 
            (user_id, username, user_first_name, role, message)
            VALUES (?, ?, ?, ?, ?)
        '''
        return self.db_service.execute_update(
            query, 
            (user_id, username, user_first_name, role, message)
        )
    
    def get_user_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        """
        Получение истории диалога с пользователем
        
        Args:
            user_id: Telegram ID пользователя
            limit: Максимальное количество последних сообщений
            
        Returns:
            Список сообщений в формате [{role, message, created_at}, ...]
        """
        query = '''
            SELECT role, message, created_at
            FROM conversation_history
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        '''
        rows = self.db_service.execute_query(query, (user_id, limit))
        
        # Переворачиваем порядок (старые сообщения первыми)
        messages = [dict(row) for row in reversed(rows)]
        return messages
    
    def get_conversation_context(self, user_id: int, max_messages: int = 6) -> str:
        """
        Формирование контекста диалога для AI
        
        Args:
            user_id: Telegram ID пользователя
            max_messages: Максимальное количество сообщений в контексте
            
        Returns:
            Строка с историей диалога
        """
        history = self.get_user_history(user_id, limit=max_messages)
        
        if not history:
            return ""
        
        context_parts = ["История диалога:"]
        for msg in history:
            role_name = "Пользователь" if msg['role'] == 'user' else "Ты"
            context_parts.append(f"{role_name}: {msg['message']}")
        
        return "\n".join(context_parts)
    
    def clear_user_history(self, user_id: int) -> int:
        """
        Очистка истории диалога с пользователем
        
        Args:
            user_id: Telegram ID пользователя
            
        Returns:
            Количество удалённых записей
        """
        query = "DELETE FROM conversation_history WHERE user_id = ?"
        return self.db_service.execute_update(query, (user_id,))
    
    def get_all_users(self) -> List[Dict]:
        """
        Получение списка всех пользователей с историей
        
        Returns:
            Список пользователей с количеством сообщений
        """
        query = '''
            SELECT 
                user_id,
                username,
                user_first_name,
                COUNT(*) as message_count,
                MAX(created_at) as last_message_at
            FROM conversation_history
            GROUP BY user_id
            ORDER BY last_message_at DESC
        '''
        rows = self.db_service.execute_query(query)
        return [dict(row) for row in rows]
    
    def get_user_stats(self, user_id: int) -> Dict:
        """
        Получение статистики по пользователю
        
        Args:
            user_id: Telegram ID пользователя
            
        Returns:
            Словарь со статистикой
        """
        query = '''
            SELECT 
                COUNT(*) as total_messages,
                COUNT(CASE WHEN role = 'user' THEN 1 END) as user_messages,
                COUNT(CASE WHEN role = 'assistant' THEN 1 END) as assistant_messages,
                MIN(created_at) as first_message_at,
                MAX(created_at) as last_message_at
            FROM conversation_history
            WHERE user_id = ?
        '''
        rows = self.db_service.execute_query(query, (user_id,))
        return dict(rows[0]) if rows else {}
