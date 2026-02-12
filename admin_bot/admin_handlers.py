"""Обработчики команд для админ-бота"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import sys
sys.path.append('..')
from database.knowledge_service import KnowledgeService
from services.vps_service import VPSService
import config

class AdminHandlers:
    """Класс для обработки команд администратора"""
    
    def __init__(self, knowledge_service: KnowledgeService, ai_service=None):
        """
        Инициализация обработчиков админки
        Args:
            knowledge_service: Сервис базы знаний
            ai_service: Сервис AI для тестирования (опционально)
        """
        self.knowledge_service = knowledge_service
        self.ai_service = ai_service
        # НОВОЕ: Инициализация VPS сервиса
        self.vps_service = VPSService(
            host=config.VPS_HOST,
            username=config.VPS_USERNAME,
            password=config.VPS_PASSWORD,
            key_path=config.VPS_SSH_KEY_PATH,
            port=config.VPS_SSH_PORT
        )
    
    def is_admin(self, user_id: int) -> bool:
        """
        Проверка прав администратора
        Args:
            user_id: ID пользователя
        Returns:
            True если пользователь является администратором
        """
        return user_id in config.ADMIN_IDS
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user_id = update.effective_user.id
        if not self.is_admin(user_id):
            await update.message.reply_text("У вас нет доступа к этому боту.")
            return
        
        keyboard = [
            [InlineKeyboardButton("📚 Просмотреть знания", callback_data="view_all")],
            [InlineKeyboardButton("➕ Добавить знание", callback_data="add_knowledge")],
            [InlineKeyboardButton("📄 Импорт из файла", callback_data="import_file")],
            [InlineKeyboardButton("✏️ Редактировать знание", callback_data="edit_knowledge")],
            [InlineKeyboardButton("🔍 Поиск знания", callback_data="search_knowledge")],
            [InlineKeyboardButton("🗑 Удалить знание", callback_data="delete_knowledge")],
            [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
            [InlineKeyboardButton("🧪 Тест AI", callback_data="test_ai")],
            [InlineKeyboardButton("🚫 Черный список", callback_data="blacklist")],
            [InlineKeyboardButton("🔄 Перезапуск VPS", callback_data="restart_vps")],  # НОВАЯ КНОПКА
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "🤖 *Админ-панель управления базой знаний*\n\n"
            "Выберите действие:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий на кнопки"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        if not self.is_admin(user_id):
            await query.edit_message_text("У вас нет доступа.")
            return
        
        if query.data == "view_all":
            await self.view_all_knowledge(query, context)
        elif query.data == "add_knowledge":
            await self.start_add_knowledge(query, context)
        elif query.data == "import_file":
            await self.start_import_file(query, context)
        elif query.data == "edit_knowledge":
            await self.start_edit_knowledge(query, context)
        elif query.data == "search_knowledge":
            await self.start_search_knowledge(query, context)
        elif query.data == "delete_knowledge":
            await self.start_delete_knowledge(query, context)
        elif query.data == "stats":
            await self.show_stats(query, context)
        elif query.data == "test_ai":
            await self.start_test_ai(query, context)
        elif query.data == "blacklist":
            await self.show_blacklist(query, context)
        elif query.data == "blacklist_add":
            await self.start_add_to_blacklist(query, context)
        elif query.data.startswith("blacklist_remove_"):
            await self.remove_from_blacklist(query, context)
        elif query.data == "restart_vps":  # НОВАЯ СТРОКА
            await self.restart_vps_process(query, context)  # НОВАЯ СТРОКА
        elif query.data == "back_to_menu":
            await self.back_to_menu(query, context)
        elif query.data.startswith("delete_"):
            await self.confirm_delete(query, context)
    
    async def view_all_knowledge(self, query, context):
        """Просмотр всех знаний"""
        knowledge_list = self.knowledge_service.get_all_knowledge()
        
        if not knowledge_list:
            text = "📚 База знаний пуста."
        else:
            text = "📚 *База знаний:*\n\n"
            for item in knowledge_list[:10]:  # Показываем первые 10
                text += f"🆔 ID: {item['id']}\n"
                text += f"📂 Категория: {item['category']}\n"
                text += f"📌 Тема: {item['topic']}\n"
                text += f"📝 Содержание: {item['content'][:100]}...\n"
                text += f"📅 Создано: {item['created_at']}\n\n"
        
        keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def start_add_knowledge(self, query, context):
        """Начало процесса добавления знания"""
        context.user_data['action'] = 'add_knowledge'
        context.user_data['step'] = 'category'
        
        keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "➕ *Добавление нового знания*\n\n"
            "Шаг 1/3: Введите категорию (например: Битрикс24, Python, API)",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def start_edit_knowledge(self, query, context):
        """Начало процесса редактирования знания"""
        context.user_data['action'] = 'edit_knowledge_id'
        
        keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "✏️ *Редактирование знания*\n\n"
            "Введите ID знания, которое нужно отредактировать:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def start_search_knowledge(self, query, context):
        """Начало поиска знания"""
        context.user_data['action'] = 'search_knowledge'
        
        keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🔍 *Поиск знания*\n\n"
            "Введите ключевое слово для поиска:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def start_delete_knowledge(self, query, context):
        """Начало удаления знания"""
        context.user_data['action'] = 'delete_knowledge'
        
        keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🗑 *Удаление знания*\n\n"
            "Введите ID знания, которое нужно удалить:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def show_stats(self, query, context):
        """Показать статистику базы знаний"""
        knowledge_list = self.knowledge_service.get_all_knowledge()
        categories = {}
        
        for item in knowledge_list:
            cat = item['category']
            categories[cat] = categories.get(cat, 0) + 1
        
        text = "📊 *Статистика базы знаний*\n\n"
        text += f"📚 Всего записей: {len(knowledge_list)}\n\n"
        text += "*Записей по категориям:*\n"
        
        for cat, count in categories.items():
            text += f"• {cat}: {count}\n"
        
        keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def back_to_menu(self, query, context):
        """Возврат в главное меню"""
        context.user_data.clear()
        
        keyboard = [
            [InlineKeyboardButton("📚 Просмотреть знания", callback_data="view_all")],
            [InlineKeyboardButton("➕ Добавить знание", callback_data="add_knowledge")],
            [InlineKeyboardButton("📄 Импорт из файла", callback_data="import_file")],
            [InlineKeyboardButton("✏️ Редактировать знание", callback_data="edit_knowledge")],
            [InlineKeyboardButton("🔍 Поиск знания", callback_data="search_knowledge")],
            [InlineKeyboardButton("🗑 Удалить знание", callback_data="delete_knowledge")],
            [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
            [InlineKeyboardButton("🧪 Тест AI", callback_data="test_ai")],
            [InlineKeyboardButton("🚫 Черный список", callback_data="blacklist")],
            [InlineKeyboardButton("🔄 Перезапуск VPS", callback_data="restart_vps")],  # НОВАЯ КНОПКА
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "🤖 *Админ-панель управления базой знаний*\n\n"
            "Выберите действие:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений и файлов для многошагового ввода"""
        user_id = update.effective_user.id
        if not self.is_admin(user_id):
            return
        
        action = context.user_data.get('action')
        
        # КРИТИЧНО: Проверка документа ПЕРЕД всем остальным
        if update.message.document:
            print(f"Получен файл: {update.message.document.file_name}")
            if action == 'import_file':
                await self.handle_file_import(update, context)
            else:
                await update.message.reply_text(
                    "Файл получен, но режим импорта не активен. Нажмите 📄 Импорт из файла в меню."
                )
            return
        
        # Обработка текстовых сообщений
        if action == 'add_knowledge':
            await self.handle_add_knowledge_steps(update, context)
        elif action == 'edit_knowledge_id':
            await self.handle_edit_id(update, context)
        elif action == 'edit_knowledge':
            await self.handle_edit_steps(update, context)
        elif action == 'search_knowledge':
            await self.handle_search(update, context)
        elif action == 'delete_knowledge':
            await self.handle_delete(update, context)
        elif action == 'test_ai':
            await self.handle_test_ai(update, context)
        elif action == 'blacklist_add':
            await self.handle_add_to_blacklist(update, context)
    
    async def handle_add_knowledge_steps(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка шагов добавления знания"""
        step = context.user_data.get('step')
        
        if step == 'category':
            context.user_data['category'] = update.message.text
            context.user_data['step'] = 'topic'
            
            await update.message.reply_text(
                "✅ Категория сохранена!\n\n"
                "Шаг 2/3: Введите тему:",
                parse_mode='Markdown'
            )
        
        elif step == 'topic':
            context.user_data['topic'] = update.message.text
            context.user_data['step'] = 'content'
            
            await update.message.reply_text(
                "✅ Тема сохранена!\n\n"
                "Шаг 3/3: Введите содержание знания:",
                parse_mode='Markdown'
            )
        
        elif step == 'content':
            category = context.user_data['category']
            topic = context.user_data['topic']
            content = update.message.text
            
            # Добавляем знание в базу
            knowledge_id = self.knowledge_service.add_knowledge(category, topic, content)
            
            context.user_data.clear()
            
            keyboard = [[InlineKeyboardButton("⬅️ В меню", callback_data="back_to_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"✅ *Знание успешно добавлено!*\n\n"
                f"🆔 ID: {knowledge_id}\n"
                f"📂 Категория: {category}\n"
                f"📌 Тема: {topic}\n"
                f"📝 Содержание: {content[:100]}...",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
    
    async def handle_edit_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ввода ID для редактирования"""
        try:
            knowledge_id = int(update.message.text)
            knowledge = self.knowledge_service.get_knowledge_by_id(knowledge_id)
            
            if not knowledge:
                await update.message.reply_text(
                    "❌ Знание с таким ID не найдено. Попробуйте снова или отправьте /start для возврата в меню."
                )
                return
            
            context.user_data['edit_id'] = knowledge_id
            context.user_data['edit_original'] = knowledge
            context.user_data['action'] = 'edit_knowledge'
            context.user_data['step'] = 'category'
            
            text = (
                f"✏️ *Редактирование знания ID {knowledge_id}*\n\n"
                f"📂 Текущая категория: `{knowledge['category']}`\n"
                f"📌 Текущая тема: `{knowledge['topic']}`\n"
                f"📝 Текущее содержание:\n`{knowledge['content'][:200]}{'...' if len(knowledge['content']) > 200 else ''}`\n\n"
                "━━━━━━━━━━━━━━━━━━\n\n"
                "Шаг 1/3: Введите новую категорию\n"
                "(или напишите 'skip' чтобы оставить текущую):"
            )
            
            await update.message.reply_text(text, parse_mode='Markdown')
        
        except ValueError:
            await update.message.reply_text("❌ Неверный формат ID. Введите число:")
    
    async def handle_edit_steps(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка шагов редактирования"""
        step = context.user_data.get('step')
        original = context.user_data['edit_original']
        
        if step == 'category':
            new_value = update.message.text.strip()
            context.user_data['new_category'] = original['category'] if new_value.lower() == 'skip' else new_value
            context.user_data['step'] = 'topic'
            
            await update.message.reply_text(
                f"✅ Категория: `{context.user_data['new_category']}`\n\n"
                "Шаг 2/3: Введите новую тему\n"
                "(или 'skip' чтобы оставить текущую):",
                parse_mode='Markdown'
            )
        
        elif step == 'topic':
            new_value = update.message.text.strip()
            context.user_data['new_topic'] = original['topic'] if new_value.lower() == 'skip' else new_value
            context.user_data['step'] = 'content'
            
            await update.message.reply_text(
                f"✅ Тема: `{context.user_data['new_topic']}`\n\n"
                "Шаг 3/3: Введите дополнительную информацию\n"
                "(или 'skip' чтобы оставить только текущую):",
                parse_mode='Markdown'
            )
        
        elif step == 'content':
            new_value = update.message.text.strip()
            
            # КЛЮЧЕВОЕ ИЗМЕНЕНИЕ: добавляем новую информацию к старой
            if new_value.lower() == 'skip':
                new_content = original['content']
            else:
                # Объединяем старое и новое содержимое
                new_content = f"{original['content']}\n\n{new_value}"
            
            knowledge_id = context.user_data['edit_id']
            category = context.user_data['new_category']
            topic = context.user_data['new_topic']
            
            # Обновляем знание в базе
            success = self.knowledge_service.update_knowledge(knowledge_id, category, topic, new_content)
            
            context.user_data.clear()
            
            if success:
                keyboard = [[InlineKeyboardButton("⬅️ В меню", callback_data="back_to_menu")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    f"✅ *Знание ID {knowledge_id} успешно обновлено!*\n\n"
                    f"📂 Категория: {category}\n"
                    f"📌 Тема: {topic}\n"
                    f"📝 Полное содержание: {new_content[:150]}...",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text("❌ Ошибка при обновлении знания. Попробуйте снова или отправьте /start")
    
    async def handle_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка поиска"""
        search_term = update.message.text
        results = self.knowledge_service.search_knowledge(search_term)
        
        if not results:
            text = f"🔍 По запросу '{search_term}' ничего не найдено."
        else:
            text = f"🔍 *Результаты поиска по '{search_term}':*\n\n"
            for item in results[:5]:
                text += f"🆔 ID: {item['id']}\n"
                text += f"📂 {item['category']} - {item['topic']}\n"
                text += f"📝 {item['content'][:100]}...\n\n"
        
        keyboard = [[InlineKeyboardButton("⬅️ В меню", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.user_data.clear()
        
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def handle_delete(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка удаления"""
        try:
            knowledge_id = int(update.message.text)
            
            # Сначала получаем информацию о знании
            knowledge = self.knowledge_service.get_knowledge_by_id(knowledge_id)
            
            if not knowledge:
                text = f"❌ Знание с ID {knowledge_id} не найдено."
            else:
                deleted = self.knowledge_service.delete_knowledge(knowledge_id)
                
                if deleted:
                    text = (
                        f"✅ *Знание ID {knowledge_id} успешно удалено!*\n\n"
                        f"Было удалено:\n"
                        f"📂 {knowledge['category']} - {knowledge['topic']}\n"
                        f"📝 {knowledge['content'][:100]}..."
                    )
                else:
                    text = f"❌ Ошибка при удалении знания с ID {knowledge_id}."
        
        except ValueError:
            text = "❌ Неверный формат ID. Введите число."
        
        keyboard = [[InlineKeyboardButton("⬅️ В меню", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.user_data.clear()
        
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def confirm_delete(self, query, context):
        """Подтверждение удаления"""
        knowledge_id = int(query.data.split('_')[1])
        deleted = self.knowledge_service.delete_knowledge(knowledge_id)
        
        if deleted:
            text = f"✅ Знание с ID {knowledge_id} удалено!"
        else:
            text = f"❌ Ошибка при удалении."
        
        keyboard = [[InlineKeyboardButton("⬅️ В меню", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def start_import_file(self, query, context):
        """Начало процесса импорта из файла"""
        context.user_data['action'] = 'import_file'
        
        keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📄 *Импорт знаний из файлов*\n\n"
            "Отправьте один или несколько текстовых файлов (.txt).\n\n"
            "📁 *Форматы:*\n"
            "• Одиночный файл\n"
            "• Несколько файлов (media group)\n"
            "• Несколько файлов по очереди\n\n"
            "📝 *Формат файла:*\n"
            "```"
            "Категория: Битрикс24\n"
            "Тема: Название темы\n\n"
            "ПРОБЛЕМА:\n"
            "[Описание]\n\n"
            "РЕШЕНИЕ:\n"
            "[Решение]\n"
            "```\n\n"
            "⚡ Каждый файл будет обработан отдельно и добавлен как независимая запись.",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def handle_file_import(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка импорта файла или группы файлов"""
        try:
            # Проверяем есть ли документы
            documents = []
            
            # Одиночный файл
            if update.message.document:
                documents = [update.message.document]
            
            # Медиа-группа (несколько файлов одновременно)
            elif update.message.media_group_id:
                # Сохраняем media_group_id для группировки
                media_group_id = update.message.media_group_id
                
                # Проверяем, обрабатывали ли мы уже эту группу
                if context.user_data.get('last_media_group_id') == media_group_id:
                    # Эта группа уже обработана, игнорируем дубликаты
                    return
                
                # Сохраняем ID группы
                context.user_data['last_media_group_id'] = media_group_id
                
                # Ждём все файлы из группы (Telegram отправляет их по очереди)
                await update.message.reply_text("📦 Получена группа файлов. Обработка...")
                
                # В этом случае обрабатываем только текущий файл
                # так как Telegram вызовет handler для каждого файла в группе
                if update.message.document:
                    documents = [update.message.document]
            
            if not documents:
                await update.message.reply_text("❌ Не обнаружено документов для обработки")
                return
            
            # Обрабатываем каждый файл отдельно
            results = []
            for document in documents:
                result = await self._process_single_file(document, update)
                results.append(result)
            
            # Формируем итоговый отчёт
            await self._send_import_summary(update, results)
        
        except Exception as e:
            print(f"Ошибка при импорте файлов: {e}")
            keyboard = [[InlineKeyboardButton("⬅️ В меню", callback_data="back_to_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"❌ Произошла ошибка при обработке файлов: {str(e)}\n\n"
                "Попробуйте снова или обратитесь к администратору.",
                reply_markup=reply_markup
            )
    
    async def _process_single_file(self, document, update: Update) -> dict:
        """
        Обработка одного файла
        Returns:
            dict с результатом: {
                'success': bool,
                'filename': str,
                'message': str,
                'knowledge_id': int,
                'category': str,
                'topic': str
            }
        """
        result = {
            'success': False,
            'filename': document.file_name,
            'message': '',
            'knowledge_id': 0,
            'category': '',
            'topic': ''
        }
        
        try:
            # Проверка типа файла
            if not document.file_name.endswith('.txt'):
                result['message'] = "Не .txt файл"
                return result
            
            # Проверка размера (макс 5 МБ)
            if document.file_size > 5 * 1024 * 1024:
                result['message'] = "Файл слишком большой (>5MB)"
                return result
            
            # Скачивание файла
            file = await document.get_file()
            file_content = await file.download_as_bytearray()
            
            # Декодирование содержимого
            text_content = None
            for encoding in ['utf-8', 'windows-1251', 'cp1251']:
                try:
                    text_content = file_content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if not text_content:
                result['message'] = "Не удалось прочитать (проблема кодировки)"
                return result
            
            # Парсинг и добавление в базу
            success, message, knowledge_id = self.knowledge_service.add_knowledge_from_file(text_content)
            
            result['success'] = success
            result['message'] = message
            result['knowledge_id'] = knowledge_id
            
            if success:
                # Получаем информацию о добавленном знании
                knowledge = self.knowledge_service.get_knowledge_by_id(knowledge_id)
                result['category'] = knowledge.get('category', '')
                result['topic'] = knowledge.get('topic', '')
            
            return result
        
        except Exception as e:
            result['message'] = f"Ошибка: {str(e)}"
            return result
    
    async def _send_import_summary(self, update: Update, results: list):
        """Отправка итогового отчёта о импорте"""
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        
        # Формируем текст отчёта
        text_parts = []
        
        if successful:
            text_parts.append(f"✅ *Успешно импортировано: {len(successful)}*\n")
            for r in successful:
                text_parts.append(
                    f"📄 `{r['filename']}`\n"
                    f"  🆔 ID: {r['knowledge_id']}\n"
                    f"  📂 {r['category']} → {r['topic']}\n"
                )
        
        if failed:
            text_parts.append(f"\n❌ *Ошибки: {len(failed)}*\n")
            for r in failed:
                text_parts.append(
                    f"📄 `{r['filename']}`\n"
                    f"  ⚠️ {r['message']}\n"
                )
        
        # Итоги
        text_parts.append(
            f"\n━━━━━━━━━━━━━━━━━━\n"
            f"📊 *Итого:*\n"
            f"• Обработано файлов: {len(results)}\n"
            f"• Успешно: {len(successful)}\n"
            f"• Ошибок: {len(failed)}"
        )
        
        keyboard = [[InlineKeyboardButton("⬅️ В меню", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        summary_text = ''.join(text_parts)
        
        # Если текст слишком длинный, разбиваем на части
        if len(summary_text) > 4000:
            # Отправляем по частям
            await update.message.reply_text(
                f"📦 *Результаты импорта*\n\n"
                f"✅ Успешно: {len(successful)}\n"
                f"❌ Ошибок: {len(failed)}",
                parse_mode='Markdown'
            )
            
            # Детали успешных
            if successful:
                success_text = "✅ *Успешно импортированные файлы:*\n\n"
                for r in successful:
                    success_text += f"📄 {r['filename']} → ID {r['knowledge_id']}\n"
                await update.message.reply_text(success_text, parse_mode='Markdown')
            
            # Детали ошибок
            if failed:
                fail_text = "❌ *Файлы с ошибками:*\n\n"
                for r in failed:
                    fail_text += f"📄 {r['filename']}: {r['message']}\n"
                await update.message.reply_text(fail_text, parse_mode='Markdown')
            
            # Финальное меню
            await update.message.reply_text(
                "Импорт завершён.",
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                summary_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
    
    async def start_test_ai(self, query, context):
        """Начало тестирования AI"""
        if not self.ai_service:
            await query.edit_message_text(
                "❌ AI сервис не доступен в админ-панели.\n"
                "Функция временно отключена."
            )
            return
        
        context.user_data['action'] = 'test_ai'
        
        keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Получаем статистику базы знаний
        knowledge_list = self.knowledge_service.get_all_knowledge()
        
        await query.edit_message_text(
            "🧪 *Тестирование AI*\n\n"
            f"Текущая база знаний: {len(knowledge_list)} записей\n\n"
            "Отправьте любое сообщение, и AI ответит как будто вы написали на ваш личный аккаунт @ADorin1.\n\n"
            "AI будет использовать всю базу знаний для формирования ответа.\n\n"
            "💡 Примеры вопросов:\n"
            "• Как создать лид в Битрикс24?\n"
            "• Расскажи про REST API\n"
            "• Как настроить права доступа?",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def handle_test_ai(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка тестового запроса к AI"""
        if not self.ai_service:
            await update.message.reply_text("❌ AI сервис недоступен.")
            context.user_data.clear()
            return
        
        user_message = update.message.text
        user_name = update.effective_user.first_name or "Администратор"
        
        # Отправляем индикатор "печатает..."
        await update.message.chat.send_action(action="typing")
        
        try:
            # Генерируем ответ через AI (как для обычного пользователя)
            ai_response = self.ai_service.generate_response(user_message, user_name)
            
            # Получаем информацию о контексте
            context_info = self.knowledge_service.get_context_for_ai()
            context_length = len(context_info)
            
            keyboard = [
                [InlineKeyboardButton("🔄 Ещё вопрос", callback_data="test_ai")],
                [InlineKeyboardButton("⬅️ В меню", callback_data="back_to_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            response_text = (
                f"🧪 *Ответ AI:*\n\n"
                f"{ai_response}\n\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"📊 *Использовано контекста:* {context_length} символов\n"
                f"💬 *Ваш вопрос:* {user_message[:100]}..."
            )
            
            await update.message.reply_text(
                response_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
            # Сохраняем action для возможности задать ещё вопрос
            # НЕ очищаем context.user_data, чтобы можно было продолжить
        
        except Exception as e:
            print(f"Ошибка при тестировании AI: {e}")
            keyboard = [[InlineKeyboardButton("⬅️ В меню", callback_data="back_to_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"❌ Произошла ошибка при обработке запроса:\n\n{str(e)}\n\n"
                "Проверьте настройки AI или попробуйте позже.",
                reply_markup=reply_markup
            )
            
            context.user_data.clear()
    
    async def show_blacklist(self, query, context):
        """Показать текущий черный список"""
        blacklist = config.BLACKLIST_USERNAMES
        
        if not blacklist:
            text = "🚫 *Черный список пуст*\n\nВсе пользователи получают ответы от AI."
        else:
            text = f"🚫 *Черный список ({len(blacklist)})*\n\n"
            text += "AI не будет отвечать этим пользователям:\n\n"
            
            for idx, username in enumerate(blacklist, 1):
                text += f"{idx}. @{username}\n"
            
            text += "\n💡 Для удаления выберите username ниже."
        
        # Кнопки для удаления пользователей из списка
        keyboard = []
        for username in blacklist[:10]:  # Максимум 10 кнопок
            keyboard.append([
                InlineKeyboardButton(
                    f"❌ @{username}",
                    callback_data=f"blacklist_remove_{username}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("➕ Добавить пользователя", callback_data="blacklist_add")])
        keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_to_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def start_add_to_blacklist(self, query, context):
        """Начало добавления пользователя в черный список"""
        context.user_data['action'] = 'blacklist_add'
        
        keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="blacklist")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "➕ *Добавление в черный список*\n\n"
            "Введите username пользователя (без @):\n\n"
            "Примеры:\n"
            "• `spam_bot`\n"
            "• `annoying_user`\n\n"
            "⚠️ AI перестанет отвечать этому пользователю.",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def handle_add_to_blacklist(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка добавления username в черный список"""
        username = update.message.text.strip().replace('@', '').lower()
        
        if not username:
            await update.message.reply_text("❌ Введите корректный username")
            return
        
        # Проверка на дубликат
        if username in [u.lower() for u in config.BLACKLIST_USERNAMES]:
            keyboard = [[InlineKeyboardButton("⬅️ В меню", callback_data="blacklist")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"⚠️ Пользователь @{username} уже в черном списке",
                reply_markup=reply_markup
            )
            context.user_data.clear()
            return
        
        # Добавляем в конфиг (только в памяти, нужно вручную добавить в config.py)
        config.BLACKLIST_USERNAMES.append(username)
        
        keyboard = [[InlineKeyboardButton("⬅️ В меню", callback_data="blacklist")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.user_data.clear()
        
        await update.message.reply_text(
            f"✅ *Добавлено в черный список!*\n\n"
            f"@{username} больше не будет получать ответы от AI.\n\n"
            f"⚠️ *ВАЖНО:* Для постоянного сохранения добавьте `\"{username}\"` в список "
            f"`BLACKLIST_USERNAMES` в файле `config.py` и перезапустите бота.",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def remove_from_blacklist(self, query, context):
        """Удаление пользователя из черного списка"""
        username = query.data.replace("blacklist_remove_", "")
        
        # Удаляем из конфига (только в памяти)
        if username in config.BLACKLIST_USERNAMES:
            config.BLACKLIST_USERNAMES.remove(username)
            text = (
                f"✅ *Удалено из черного списка!*\n\n"
                f"@{username} снова будет получать ответы от AI.\n\n"
                f"⚠️ *ВАЖНО:* Для постоянного сохранения удалите `\"{username}\"` из списка "
                f"`BLACKLIST_USERNAMES` в файле `config.py` и перезапустите бота."
            )
        else:
            text = f"❌ @{username} не найден в черном списке"
        
        keyboard = [[InlineKeyboardButton("⬅️ Назад к списку", callback_data="blacklist")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def restart_vps_process(self, query, context):
        """Перезапуск процесса на VPS"""
        await query.edit_message_text(
            "🔄 *Перезапуск процесса на VPS*\n\n"
            "⏳ Подключение к серверу...",
            parse_mode='Markdown'
        )
        
        try:
            # Проверяем существование сессии
            session_exists, check_msg = await self.vps_service.check_tmux_session(
                config.TMUX_SESSION_NAME
            )
            
            if not session_exists:
                keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="back_to_menu")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    f"❌ *Ошибка*\n\n"
                    f"Tmux сессия '{config.TMUX_SESSION_NAME}' не найдена.\n\n"
                    f"{check_msg}",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                return
            
            # Перезапускаем процесс
            success, message = await self.vps_service.restart_tmux_session(
                session_name=config.TMUX_SESSION_NAME,
                script_path=config.TMUX_SCRIPT_PATH,
                working_dir=config.TMUX_WORKING_DIR
            )
            
            if success:
                text = (
                    f"✅ *Процесс успешно перезапущен!*\n\n"
                    f"🖥 Сервер: `{config.VPS_HOST}`\n"
                    f"📺 Tmux сессия: `{config.TMUX_SESSION_NAME}`\n"
                    f"🚀 Команда: `{config.TMUX_SCRIPT_PATH}`\n\n"
                    f"💡 Процесс остановлен (Ctrl+C) и запущен заново."
                )
            else:
                text = (
                    f"❌ *Ошибка при перезапуске*\n\n"
                    f"{message}\n\n"
                    f"Проверьте:\n"
                    f"• SSH подключение к {config.VPS_HOST}\n"
                    f"• Существование tmux сессии '{config.TMUX_SESSION_NAME}'\n"
                    f"• Права доступа"
                )
        
        except Exception as e:
            text = (
                f"❌ *Критическая ошибка*\n\n"
                f"Не удалось выполнить перезапуск:\n"
                f"`{str(e)}`\n\n"
                f"Обратитесь к системному администратору."
            )
        
        keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
