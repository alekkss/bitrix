"""Сервис для управления VPS через SSH"""

import asyncio
import asyncssh
from typing import Tuple, Optional


class VPSService:
    """Класс для управления VPS через SSH"""
    
    def __init__(self, host: str, username: str, password: Optional[str] = None, 
                 key_path: Optional[str] = None, port: int = 22):
        """
        Инициализация VPS сервиса
        
        Args:
            host: IP или hostname VPS
            username: SSH пользователь
            password: SSH пароль (если используется)
            key_path: Путь к SSH ключу (если используется)
            port: SSH порт (по умолчанию 22)
        """
        self.host = host
        self.username = username
        self.password = password
        self.key_path = key_path
        self.port = port
    
    async def execute_command(self, command: str, timeout: int = 30) -> Tuple[bool, str]:
        """
        Выполнение команды на VPS
        
        Args:
            command: Команда для выполнения
            timeout: Таймаут выполнения в секундах
            
        Returns:
            Tuple[bool, str]: (успешность выполнения, результат/ошибка)
        """
        try:
            # Параметры подключения
            connect_kwargs = {
                'host': self.host,
                'port': self.port,
                'username': self.username,
                'known_hosts': None  # Отключаем проверку known_hosts
            }
            
            # Добавляем аутентификацию
            if self.key_path:
                connect_kwargs['client_keys'] = [self.key_path]
            elif self.password:
                connect_kwargs['password'] = self.password
            else:
                return False, "Не указан пароль или путь к ключу SSH"
            
            # Подключение и выполнение команды
            async with asyncssh.connect(**connect_kwargs) as conn:
                result = await asyncio.wait_for(
                    conn.run(command, check=True),
                    timeout=timeout
                )
                
                output = result.stdout.strip() if result.stdout else ""
                error = result.stderr.strip() if result.stderr else ""
                
                if error:
                    return False, f"Ошибка: {error}"
                    
                return True, output or "Команда выполнена успешно"
                
        except asyncio.TimeoutError:
            return False, f"Превышен таймаут выполнения команды ({timeout}с)"
        except asyncssh.Error as e:
            return False, f"SSH ошибка: {str(e)}"
        except Exception as e:
            return False, f"Неожиданная ошибка: {str(e)}"
    
    async def restart_tmux_session(self, session_name: str, script_path: str, 
                                   working_dir: str = "~") -> Tuple[bool, str]:
        """
        Перезапуск процесса в tmux сессии
        
        Args:
            session_name: Имя tmux сессии
            script_path: Путь к скрипту для запуска
            working_dir: Рабочая директория
            
        Returns:
            Tuple[bool, str]: (успешность, сообщение)
        """
        # Команда для перезапуска процесса в tmux
        # 1. Отправляем Ctrl+C в сессию
        # 2. Ждем 2 секунды
        # 3. Очищаем экран
        # 4. Переходим в рабочую директорию
        # 5. Запускаем скрипт
        command = (
            f"tmux send-keys -t {session_name} C-c && "
            f"sleep 2 && "
            f"tmux send-keys -t {session_name} 'clear' C-m && "
            f"tmux send-keys -t {session_name} 'cd {working_dir}' C-m && "
            f"tmux send-keys -t {session_name} '{script_path}' C-m"
        )
        
        return await self.execute_command(command, timeout=15)
    
    async def check_tmux_session(self, session_name: str) -> Tuple[bool, str]:
        """
        Проверка существования tmux сессии
        
        Args:
            session_name: Имя сессии
            
        Returns:
            Tuple[bool, str]: (существует ли, сообщение)
        """
        command = f"tmux has-session -t {session_name} 2>&1"
        success, output = await self.execute_command(command, timeout=5)
        
        if success:
            return True, f"Сессия '{session_name}' существует"
        else:
            return False, f"Сессия '{session_name}' не найдена"
    
    async def get_tmux_sessions(self) -> Tuple[bool, str]:
        """
        Получение списка всех tmux сессий
        
        Returns:
            Tuple[bool, str]: (успешность, список сессий)
        """
        command = "tmux list-sessions"
        return await self.execute_command(command, timeout=5)
