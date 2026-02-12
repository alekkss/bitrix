"""Сервис для работы с базой данных SQLite"""

import sqlite3
from contextlib import contextmanager
from typing import List, Tuple, Any
import pickle


class DatabaseService:
    """Класс для управления подключением к базе данных"""
    
    def __init__(self, db_path: str):
        """
        Инициализация сервиса базы данных
        
        Args:
            db_path: Путь к файлу базы данных SQLite
        """
        self.db_path = db_path
        self._init_database()
        self._migrate_database()  # ← НОВОЕ: Применение миграций
    
    @contextmanager
    def _get_connection(self):
        """Контекстный менеджер для работы с подключением к БД"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def _init_database(self):
        """Инициализация базы данных и создание таблиц"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Создание таблицы знаний
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS knowledge (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category VARCHAR(100) NOT NULL,
                    topic VARCHAR(200) NOT NULL,
                    content TEXT NOT NULL,
                    embedding BLOB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Создание таблицы истории диалогов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    username VARCHAR(100),
                    user_first_name VARCHAR(100),
                    role VARCHAR(20) NOT NULL,
                    message TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Создание индексов для быстрого поиска
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_category 
                ON knowledge(category)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_topic 
                ON knowledge(topic)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_user_id 
                ON conversation_history(user_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_created_at 
                ON conversation_history(created_at)
            ''')
            
            conn.commit()
            print("База данных инициализирована успешно")
    
    def _migrate_database(self):
        """Применение миграций для обновления структуры БД"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Проверяем наличие колонки embedding
            cursor.execute("PRAGMA table_info(knowledge)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'embedding' not in columns:
                print("Применение миграции: добавление колонки embedding...")
                cursor.execute("ALTER TABLE knowledge ADD COLUMN embedding BLOB")
                conn.commit()
                print("✅ Колонка embedding успешно добавлена")
            else:
                print("Колонка embedding уже существует")
    
    def execute_query(self, query: str, params: Tuple = ()) -> List[sqlite3.Row]:
        """
        Выполнение SELECT запроса
        
        Args:
            query: SQL запрос
            params: Параметры запроса
            
        Returns:
            Список строк результата
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def execute_update(self, query: str, params: Tuple = ()) -> int:
        """
        Выполнение INSERT/UPDATE/DELETE запроса
        
        Args:
            query: SQL запрос
            params: Параметры запроса
            
        Returns:
            ID последней вставленной записи или количество затронутых строк
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid if cursor.lastrowid else cursor.rowcount
