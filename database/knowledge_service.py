"""Сервис для работы с базой знаний"""

from typing import List, Dict
import sys
sys.path.append('..')
from database.db_service import DatabaseService
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer


class KnowledgeService:
    """Класс для управления базой знаний"""
    
    def __init__(self, db_service: DatabaseService):
        """
        Инициализация сервиса базы знаний
        
        Args:
            db_service: Сервис базы данных
        """
        self.db_service = db_service
        
        # Инициализация модели для embeddings
        print("Загрузка модели для семантического поиска...")
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        print("Модель загружена успешно")
        
        # Проверка и заполнение базы знаний
        self._populate_initial_knowledge()
        
        # Генерация embeddings для существующих записей без них
        self._generate_missing_embeddings()
    
    def _populate_initial_knowledge(self):
        """Заполнение базы начальными знаниями о Битрикс24"""
        existing = self.get_all_knowledge()
        
        if existing:
            print("База знаний о Битрикс24 уже заполнена")
            return
        
        initial_knowledge = [
            {
                "category": "Битрикс24",
                "topic": "Общее описание",
                "content": "Битрикс24 — это облачная платформа для совместной работы и управления бизнесом. Включает CRM, задачи, проекты, документы, чаты, видеозвонки и другие инструменты для автоматизации бизнес-процессов."
            },
            {
                "category": "Битрикс24",
                "topic": "CRM система",
                "content": "CRM в Битрикс24 позволяет управлять лидами, контактами, компаниями, сделками и счетами. Поддерживает автоматизацию продаж, воронки продаж, email-маркетинг и интеграцию с телефонией."
            },
            {
                "category": "Битрикс24",
                "topic": "REST API",
                "content": "Битрикс24 REST API позволяет интегрировать систему с внешними приложениями. Основные возможности: работа с CRM (лиды, сделки, контакты), задачами, пользователями, документами. Использует OAuth 2.0 для авторизации."
            },
            {
                "category": "Битрикс24",
                "topic": "Задачи и проекты",
                "content": "Модуль задач в Битрикс24 позволяет создавать задачи, подзадачи, назначать исполнителей, устанавливать сроки. Проекты объединяют задачи по группам. Поддерживаются Kanban-доски, диаграммы Ганта и Scrum."
            },
            {
                "category": "Битрикс24",
                "topic": "Автоматизация",
                "content": "Битрикс24 поддерживает бизнес-процессы и роботы для автоматизации. Можно настроить автоматическое создание задач, отправку уведомлений, изменение статусов сделок, интеграцию с внешними сервисами через webhooks и API."
            },
            {
                "category": "Битрикс24",
                "topic": "Интеграции",
                "content": "Битрикс24 интегрируется с почтой, календарями, облачными хранилищами, телефонией, мессенджерами, платежными системами. Доступен Маркетплейс с готовыми приложениями и возможность создания собственных приложений."
            },
            {
                "category": "Битрикс24",
                "topic": "Документы и диск",
                "content": "Битрикс24.Диск — облачное хранилище для документов компании. Поддерживает совместное редактирование, контроль версий, доступы по группам. Интегрирован с Office Online и Google Docs."
            },
            {
                "category": "Битрикс24",
                "topic": "Коммуникации",
                "content": "Битрикс24 включает внутренний чат, видеозвонки, корпоративную соцсеть (Живая лента), группы. Доступны мобильные приложения для iOS и Android. Поддерживает интеграцию с внешними мессенджерами."
            }
        ]
        
        for item in initial_knowledge:
            self.add_knowledge(item["category"], item["topic"], item["content"])
        
        print("База знаний о Битрикс24 успешно заполнена")
    
    def _generate_missing_embeddings(self):
        """Генерация embeddings для записей без них"""
        query = "SELECT id, content FROM knowledge WHERE embedding IS NULL"
        rows = self.db_service.execute_query(query)
        
        if not rows:
            print("Все записи уже имеют embeddings")
            return
        
        print(f"Генерация embeddings для {len(rows)} записей...")
        
        for row in rows:
            knowledge_id = row['id']
            content = row['content']
            
            # Генерируем embedding
            embedding = self.model.encode(content)
            embedding_blob = pickle.dumps(embedding)
            
            # Сохраняем в БД
            update_query = "UPDATE knowledge SET embedding = ? WHERE id = ?"
            self.db_service.execute_update(update_query, (embedding_blob, knowledge_id))
        
        print(f"Embeddings успешно сгенерированы для {len(rows)} записей")
    
    def add_knowledge(self, category: str, topic: str, content: str) -> int:
        """
        Добавление нового знания в базу с автоматической генерацией embedding
        
        Args:
            category: Категория знания
            topic: Тема знания
            content: Содержимое знания
            
        Returns:
            ID добавленной записи
        """
        # Генерируем embedding
        embedding = self.model.encode(content)
        embedding_blob = pickle.dumps(embedding)
        
        query = '''
            INSERT INTO knowledge (category, topic, content, embedding)
            VALUES (?, ?, ?, ?)
        '''
        return self.db_service.execute_update(query, (category, topic, content, embedding_blob))
    
    def get_all_knowledge(self) -> List[Dict]:
        """
        Получение всех знаний из базы
        
        Returns:
            Список словарей с данными о знаниях (без embeddings)
        """
        query = '''
            SELECT id, category, topic, content, created_at
            FROM knowledge
            ORDER BY created_at DESC
        '''
        rows = self.db_service.execute_query(query)
        return [dict(row) for row in rows]
    
    def search_knowledge(self, search_term: str) -> List[Dict]:
        """
        Поиск знаний по ключевому слову
        
        Args:
            search_term: Ключевое слово для поиска
            
        Returns:
            Список найденных знаний
        """
        query = '''
            SELECT id, category, topic, content, created_at
            FROM knowledge
            WHERE topic LIKE ? OR content LIKE ?
            ORDER BY created_at DESC
        '''
        search_pattern = f'%{search_term}%'
        rows = self.db_service.execute_query(query, (search_pattern, search_pattern))
        return [dict(row) for row in rows]
    
    def delete_knowledge(self, knowledge_id: int) -> bool:
        """
        Удаление знания по ID
        
        Args:
            knowledge_id: ID знания для удаления
            
        Returns:
            True если удаление успешно
        """
        query = "DELETE FROM knowledge WHERE id = ?"
        rows_affected = self.db_service.execute_update(query, (knowledge_id,))
        return rows_affected > 0
    
    def get_context_for_ai(self, user_query: str = None, max_items: int = 5) -> str:
        """
        Формирование контекста для ИИ из базы знаний с семантическим поиском
        
        Args:
            user_query: Вопрос пользователя для семантического поиска
            max_items: Максимальное количество записей для контекста
            
        Returns:
            Строка с контекстом
        """
        if user_query:
            # СЕМАНТИЧЕСКИЙ ПОИСК
            knowledge_list = self._semantic_search(user_query, max_items)
        else:
            # Обычный поиск (берём последние)
            knowledge_list = self.get_all_knowledge()[:max_items]
        
        if not knowledge_list:
            return ""
        
        context_parts = ["База знаний:"]
        for item in knowledge_list:
            context_parts.append(
                f"\n[{item['category']} - {item['topic']}]: {item['content']}"
            )
        
        return "\n".join(context_parts)
    
    def _semantic_search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Семантический поиск по базе знаний
        
        Args:
            query: Поисковый запрос
            top_k: Количество результатов
            
        Returns:
            Список наиболее релевантных знаний
        """
        # Получаем все знания с embeddings
        sql_query = "SELECT id, category, topic, content, embedding, created_at FROM knowledge"
        rows = self.db_service.execute_query(sql_query)
        
        if not rows:
            return []
        
        # Генерируем embedding для запроса
        query_embedding = self.model.encode(query)
        
        # Вычисляем сходство с каждой записью
        similarities = []
        for row in rows:
            row_dict = dict(row)
            
            if row_dict['embedding'] is None:
                continue
            
            # Десериализуем embedding из БД
            knowledge_embedding = pickle.loads(row_dict['embedding'])
            
            # Вычисляем косинусное сходство
            similarity = np.dot(query_embedding, knowledge_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(knowledge_embedding)
            )
            
            similarities.append((similarity, row_dict))
        
        # Сортируем по убыванию сходства
        similarities.sort(reverse=True, key=lambda x: x[0])
        
        # Берём топ-K
        top_results = similarities[:top_k]
        
        # Логируем результаты поиска
        print(f"\n=== Семантический поиск: '{query}' ===")
        for similarity, item in top_results:
            print(f"  {similarity:.3f} | {item['category']} - {item['topic']}")
        print("=" * 50)
        
        # Возвращаем без embedding (он не нужен в выводе)
        return [{
            'id': item['id'],
            'category': item['category'],
            'topic': item['topic'],
            'content': item['content'],
            'created_at': item['created_at']
        } for similarity, item in top_results]
    
    def update_knowledge(self, knowledge_id: int, category: str, topic: str, content: str) -> bool:
        """
        Обновление существующей записи знаний с пересчётом embedding
        
        Args:
            knowledge_id: ID записи для обновления
            category: Новая категория
            topic: Новая тема
            content: Новое содержимое
            
        Returns:
            True если обновление успешно
        """
        # Генерируем новый embedding
        embedding = self.model.encode(content)
        embedding_blob = pickle.dumps(embedding)
        
        query = '''
            UPDATE knowledge 
            SET category = ?, topic = ?, content = ?, embedding = ?
            WHERE id = ?
        '''
        rows_affected = self.db_service.execute_update(
            query, 
            (category, topic, content, embedding_blob, knowledge_id)
        )
        return rows_affected > 0
    
    def get_knowledge_by_id(self, knowledge_id: int) -> dict:
        """
        Получение конкретной записи по ID
        
        Args:
            knowledge_id: ID записи
            
        Returns:
            Словарь с данными записи или пустой словарь
        """
        query = '''
            SELECT id, category, topic, content, created_at
            FROM knowledge
            WHERE id = ?
        '''
        rows = self.db_service.execute_query(query, (knowledge_id,))
        return dict(rows[0]) if rows else {}
    
    def parse_knowledge_from_text(self, text: str) -> dict:
        """
        Парсинг структурированного текста знания
        
        Args:
            text: Текст в формате с разделами
            
        Returns:
            Словарь с полями category, topic, content или пустой словарь
        """
        try:
            lines = text.strip().split('\n')
            
            category = ""
            topic = ""
            content_parts = []
            
            # Извлекаем категорию и тему
            for line in lines[:5]:
                if line.startswith("Категория:"):
                    category = line.replace("Категория:", "").strip()
                elif line.startswith("Тема:"):
                    topic = line.replace("Тема:", "").strip()
            
            if not category or not topic:
                return {}
            
            # Собираем весь контент
            in_content = False
            for line in lines:
                if line.startswith("Категория:") or line.startswith("Тема:"):
                    continue
                if line.strip():
                    in_content = True
                if in_content:
                    content_parts.append(line)
            
            content = '\n'.join(content_parts).strip()
            
            if not content:
                return {}
            
            return {
                'category': category,
                'topic': topic,
                'content': content
            }
            
        except Exception as e:
            print(f"Ошибка при парсинге текста: {e}")
            return {}
    
    def add_knowledge_from_file(self, file_content: str) -> tuple:
        """
        Добавление знания из содержимого файла с генерацией embedding
        
        Args:
            file_content: Содержимое текстового файла
            
        Returns:
            Кортеж (success: bool, message: str, knowledge_id: int)
        """
        parsed = self.parse_knowledge_from_text(file_content)
        
        if not parsed:
            return (False, "Не удалось распознать структуру файла. Проверьте формат.", 0)
        
        knowledge_id = self.add_knowledge(
            parsed['category'],
            parsed['topic'],
            parsed['content']
        )
        
        if knowledge_id:
            return (True, f"Знание успешно добавлено! ID: {knowledge_id}", knowledge_id)
        else:
            return (False, "Ошибка при добавлении в базу данных.", 0)
