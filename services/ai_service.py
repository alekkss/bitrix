"""Сервис для работы с AI"""

from openai import OpenAI
import sys
sys.path.append('..')
import config


class AIService:
    """Класс для генерации ответов через AI"""
    
    def __init__(self, knowledge_service=None, conversation_service=None):
        """
        Инициализация клиента OpenAI
        
        Args:
            knowledge_service: Сервис базы знаний (опционально)
            conversation_service: Сервис истории диалогов (опционально)
        """
        self.client = OpenAI(
            base_url=config.OPENAI_BASE_URL,
            api_key=config.OPENAI_API_KEY,
        )
        self.model = config.AI_MODEL
        self.knowledge_service = knowledge_service
        self.conversation_service = conversation_service
    
    def generate_response(self, user_message: str, user_name: str = "Пользователь", 
                         user_id: int = None, username: str = None) -> str:
        """
        Генерирует ответ на основе сообщения пользователя
        
        Args:
            user_message: Текст сообщения пользователя
            user_name: Имя пользователя
            user_id: ID пользователя для истории диалога
            username: Username пользователя (без @)
            
        Returns:
            Сгенерированный ответ или сообщение об ошибке
        """
        try:
            # Получение РЕЛЕВАНТНОГО контекста из базы знаний с семантическим поиском
            knowledge_context = ""
            if self.knowledge_service:
                knowledge_context = self.knowledge_service.get_context_for_ai(
                    user_query=user_message,  # Передаём вопрос для семантического поиска
                    max_items=5  # Топ-5 релевантных знаний
                )
            
            # Формирование системного промпта
            system_prompt = config.AI_SYSTEM_PROMPT
            if knowledge_context:
                system_prompt += f"\n\n{knowledge_context}"
            
            # Формирование истории сообщений для API
            messages = [{"role": "system", "content": system_prompt}]
            
            # Добавляем историю диалога если есть user_id
            if user_id and self.conversation_service:
                history = self.conversation_service.get_user_history(user_id, limit=6)
                
                # Добавляем историю в формате OpenAI
                for msg in history:
                    messages.append({
                        "role": msg['role'],
                        "content": msg['message']
                    })
            
            # Добавляем текущее сообщение пользователя
            messages.append({
                "role": "user",
                "content": user_message
            })
            
            # Генерация ответа
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=config.AI_MAX_TOKENS,
            )
            
            if response.choices:
                ai_response = response.choices[0].message.content.strip()
                
                # Сохраняем сообщение пользователя и ответ AI в историю
                if user_id and self.conversation_service:
                    self.conversation_service.add_message(
                        user_id, username, user_name, 'user', user_message
                    )
                    self.conversation_service.add_message(
                        user_id, username, user_name, 'assistant', ai_response
                    )
                
                return ai_response
            
            return "Извини, не могу сейчас ответить. Попробуй позже!"
            
        except Exception as e:
            print(f"Ошибка при генерации ответа AI: {e}")
            return "Произошла ошибка при обработке сообщения. Попробуй ещё раз!"
