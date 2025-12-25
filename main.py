"""Основной скрипт для прослушивания и пересылки сообщений из Telegram чата."""
import asyncio
import json
import logging
import os
import sys
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from config import Config


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class MessageForwarder:
    """Класс для пересылки сообщений между чатами."""
    
    def __init__(self, config: Config):
        """Инициализирует forwarder с конфигурацией."""
        self.config = config
        self.client = None
        # Используем директорию data для сохранения состояния
        os.makedirs('data', exist_ok=True)
        self.state_file = 'data/forwarder_state.json'
        self.target_chat_ids = config.get_target_chat_ids()
        self.target_chat_entities = []  # Будет заполнено при старте
        # Загружаем сохраненное состояние или начинаем с 0
        self.target_chat_index = self._load_state()
    
    async def start(self):
        """Запускает клиент и начинает прослушивание."""
        # Создание клиента с string session
        # Для StringSession api_id и api_hash нужны при создании клиента,
        # но если они не указаны, используем значения по умолчанию
        session = StringSession(self.config.telegram_session_string)
        api_id = self.config.api_id or 1
        api_hash = self.config.api_hash or '1'
        self.client = TelegramClient(session, api_id=api_id, api_hash=api_hash)
        
        await self.client.start()
        logger.info("Клиент успешно запущен")
        
        # Проверка авторизации
        if not await self.client.is_user_authorized():
            logger.error("Ошибка: аккаунт не авторизован")
            raise RuntimeError("Аккаунт не авторизован. Проверьте TELEGRAM_SESSION_STRING")
        
        me = await self.client.get_me()
        logger.info(f"Авторизован как: {me.first_name} (@{me.username})")
        
        # Загрузка всех диалогов для заполнения кеша (критично для приватных чатов)
        logger.info("Загрузка диалогов для заполнения кеша...")
        try:
            await self.client.get_dialogs(limit=None)
            logger.info("Диалоги загружены, кеш заполнен")
        except Exception as e:
            logger.warning(f"Не удалось загрузить все диалоги: {e}, продолжаю...")
        
        # Попытка получить информацию об исходном чате для проверки доступа
        try:
            # Пробуем преобразовать в int, если это число
            try:
                source_chat_id_int = int(self.config.source_chat_id)
            except ValueError:
                source_chat_id_int = self.config.source_chat_id
            
            source_chat = await self.client.get_entity(source_chat_id_int)
            chat_title = getattr(source_chat, 'title', getattr(source_chat, 'first_name', 'Unknown'))
            logger.info(f"Исходный чат найден: {chat_title} (ID: {self.config.source_chat_id})")
        except Exception as e:
            logger.warning(f"Не удалось получить информацию об исходном чате {self.config.source_chat_id}: {e}")
            logger.warning("Продолжаю работу, но сообщения могут не обрабатываться")
            logger.warning("Убедитесь, что:")
            logger.warning("  1. ID чата указан правильно (для групп используйте отрицательный ID)")
            logger.warning("  2. Аккаунт имеет доступ к этому чату")
        
        # Предзагрузка entity для всех целевых чатов (важно для приватных чатов)
        logger.info("Предзагрузка информации о целевых чатах...")
        self.target_chat_entities = []
        for i, target_chat_id in enumerate(self.target_chat_ids):
            try:
                # Пробуем преобразовать в int, если это число
                try:
                    target_chat_id_int = int(target_chat_id)
                except ValueError:
                    target_chat_id_int = target_chat_id
                
                target_entity = await self.client.get_entity(target_chat_id_int)
                self.target_chat_entities.append(target_entity)
                
                chat_title = getattr(target_entity, 'title', getattr(target_entity, 'first_name', 'Unknown'))
                logger.info(f"  Целевой чат {i+1}/{len(self.target_chat_ids)} загружен: {chat_title} (ID: {target_chat_id})")
            except Exception as e:
                logger.error(f"  Не удалось загрузить целевой чат {target_chat_id}: {e}")
                # Сохраняем None для этого чата, чтобы не ломать индексацию
                self.target_chat_entities.append(None)
        
        # Проверяем, что хотя бы один чат загружен успешно
        loaded_count = sum(1 for e in self.target_chat_entities if e is not None)
        if loaded_count == 0:
            logger.error("Не удалось загрузить ни один целевой чат! Проверьте доступ к чатам.")
            raise RuntimeError("Не удалось загрузить целевые чаты")
        elif loaded_count < len(self.target_chat_ids):
            logger.warning(f"Загружено только {loaded_count} из {len(self.target_chat_ids)} целевых чатов")
        
        # Регистрация обработчика всех новых сообщений
        # Фильтрация по чату будет происходить в обработчике
        @self.client.on(events.NewMessage())
        async def handler(event):
            await self.handle_new_message(event)
        
        logger.info(f"Начинаю прослушивание чата: {self.config.source_chat_id}")
        logger.info(f"Целевые чаты для пересылки: {', '.join(self.target_chat_ids)}")
        
        # Запуск прослушивания
        await self.client.run_until_disconnected()
    
    def _load_state(self) -> int:
        """Загружает сохраненное состояние индекса целевого чата."""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    index = state.get('target_chat_index', 0)
                    # Проверяем валидность индекса
                    if 0 <= index < len(self.target_chat_ids):
                        logger.info(f"Загружено сохраненное состояние: следующий чат #{index + 1}")
                        return index
                    else:
                        logger.warning(f"Некорректный индекс в состоянии: {index}, начинаю с 0")
        except Exception as e:
            logger.warning(f"Не удалось загрузить состояние: {e}, начинаю с 0")
        return 0
    
    def _save_state(self):
        """Сохраняет текущее состояние индекса целевого чата."""
        try:
            state = {
                'target_chat_index': self.target_chat_index
            }
            with open(self.state_file, 'w') as f:
                json.dump(state, f)
        except Exception as e:
            logger.warning(f"Не удалось сохранить состояние: {e}")
    
    async def handle_new_message(self, event):
        """Обрабатывает новое сообщение из исходного чата."""
        try:
            # Получение информации о сообщении
            message_id = event.id
            chat_id = str(event.chat_id)
            
            # Проверка, что сообщение из нужного чата
            # Сравниваем как строки, так как ID может быть в разных форматах
            str_match = (chat_id == self.config.source_chat_id)
            
            if not str_match:
                # Также пробуем сравнить как числа
                try:
                    int_chat_id = int(chat_id)
                    int_source_id = int(self.config.source_chat_id)
                    int_match = (int_chat_id == int_source_id)
                    if not int_match:
                        return
                except (ValueError, TypeError):
                    return
            
            logger.info(f"Получено новое сообщение #{message_id} из чата {chat_id}")
            
            # Выбор целевого чата (round-robin)
            target_index = self.target_chat_index
            self.target_chat_index = (self.target_chat_index + 1) % len(self.target_chat_ids)
            target_chat_id = self.target_chat_ids[target_index]
            target_entity = self.target_chat_entities[target_index]
            
            if target_entity is None:
                logger.error(f"Целевой чат {target_chat_id} не был загружен при старте, пропускаю сообщение")
                return
            
            # Пересылка сообщения (используем entity вместо ID для надежности)
            try:
                await self.client.forward_messages(
                    entity=target_entity,
                    messages=event.message
                )
                logger.info(
                    f"Сообщение #{message_id} успешно переслано в чат {target_chat_id} "
                    f"(следующий чат: {self.target_chat_ids[self.target_chat_index]})"
                )
                # Сохраняем состояние после успешной пересылки
                self._save_state()
            except Exception as e:
                logger.error(
                    f"Ошибка при пересылке сообщения #{message_id} в чат {target_chat_id}: {e}"
                )
                
        except Exception as e:
            logger.error(f"Ошибка при обработке сообщения: {e}", exc_info=True)
    
    async def stop(self):
        """Останавливает клиент."""
        if self.client:
            await self.client.disconnect()
            logger.info("Клиент остановлен")


async def main():
    """Главная функция."""
    try:
        # Загрузка конфигурации
        config = Config()
        logger.info("Конфигурация загружена успешно")
        
        # Создание и запуск forwarder
        forwarder = MessageForwarder(config)
        
        try:
            await forwarder.start()
        except KeyboardInterrupt:
            logger.info("Получен сигнал остановки")
        finally:
            await forwarder.stop()
            
    except ValueError as e:
        logger.error(f"Ошибка конфигурации: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
