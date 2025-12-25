# filename: src/utils/attachments.py
"""
Утилиты для работы с вложениями (attachments) в сообщениях Telegram.
Извлекает file_id и метаданные из фото, видео, документов и других типов медиа.
"""
from typing import Any, Dict, List, Optional
from aiogram.types import Message


def extract_attachments_from_message(message: Message) -> Optional[List[Dict[str, Any]]]:
    """
    Извлекает информацию о вложениях из сообщения Telegram.
    
    Для стикеров, видео и фото возвращает только тип медиа.
    Для других типов медиа возвращает тип и базовую информацию.
    
    Returns:
        Список словарей с типом медиа или None, если вложений нет
    """
    attachments = []
    
    # Обработка фото - только тип
    if message.photo:
        attachments.append({"type": "photo"})
    
    # Обработка видео - только тип
    if message.video:
        attachments.append({"type": "video"})
    
    # Обработка стикеров - только тип
    if message.sticker:
        attachments.append({"type": "sticker"})
    
    # Обработка документов - тип и базовые данные
    if message.document:
        doc_data = {"type": "document"}
        if message.document.file_name:
            doc_data["file_name"] = message.document.file_name
        attachments.append(doc_data)
    
    # Обработка голосовых сообщений - тип и длительность
    if message.voice:
        attachments.append({
            "type": "voice",
            "duration": message.voice.duration,
        })
    
    # Обработка аудио - тип и базовая информация
    if message.audio:
        audio_data = {"type": "audio"}
        if message.audio.duration:
            audio_data["duration"] = message.audio.duration
        if message.audio.title:
            audio_data["title"] = message.audio.title
        if message.audio.performer:
            audio_data["performer"] = message.audio.performer
        attachments.append(audio_data)
    
    # Обработка видео-заметок (кружочки) - только тип
    if message.video_note:
        attachments.append({"type": "video_note"})
    
    # Обработка анимаций (GIF) - только тип
    if message.animation:
        attachments.append({"type": "animation"})
    
    # Обработка контактов - только тип
    if message.contact:
        attachments.append({"type": "contact"})
    
    # Обработка локации - только тип
    if message.location:
        attachments.append({"type": "location"})
    
    # Обработка venue - только тип
    if message.venue:
        attachments.append({"type": "venue"})
    
    # Обработка poll - только тип
    if message.poll:
        attachments.append({"type": "poll"})
    
    return attachments if attachments else None

