import asyncio
from asyncio import Task
from typing import Any

from aiogram import Bot, Dispatcher, types
from aiogram.enums import ChatMemberStatus
from aiogram.types import ChatMemberAdministrator, ChatMemberMember, ChatMemberRestricted
from fastapi import Depends, HTTPException
from fastapi.responses import ORJSONResponse
from starlette.requests import Request

from src.api.tg.router import tg_router
from src.integrations.tg_bot import get_dispatcher, get_tg_bot
from src.logger import logger
from src.utils.background_tasks import tg_background_tasks


@tg_router.post('/tg')
async def tg_api(
    request: Request,
    dp: Dispatcher = Depends(get_dispatcher),
    bot: Bot = Depends(get_tg_bot),
) -> ORJSONResponse:
    data = await request.json()
    update = types.Update(**data)

    # Логируем тип обновления
    update_type = None
    chat_id = None
    user_id = None
    
    if update.message:
        update_type = 'message'
        chat_id = update.message.chat.id if update.message.chat else None
        user_id = update.message.from_user.id if update.message.from_user else None
    elif update.edited_message:
        update_type = 'edited_message'
        chat_id = update.edited_message.chat.id if update.edited_message.chat else None
        user_id = update.edited_message.from_user.id if update.edited_message.from_user else None
    elif update.deleted_messages:
        # Обработка удаленных сообщений (если Telegram начнет отправлять такие события)
        update_type = 'deleted_messages'
        chat_id = update.deleted_messages.chat.id if update.deleted_messages.chat else None
        logger.info(
            'DELETED MESSAGES UPDATE RECEIVED: chat_id=%s, message_ids=%s',
            chat_id,
            update.deleted_messages.message_ids if hasattr(update.deleted_messages, 'message_ids') else None,
        )
        # Примечание: Обработка deleted_messages должна быть реализована через специальный обработчик
        # если Telegram начнет отправлять такие события через Bot API
    elif update.my_chat_member:
        update_type = 'my_chat_member'
        chat_id = update.my_chat_member.chat.id if update.my_chat_member.chat else None
        user_id = update.my_chat_member.from_user.id if update.my_chat_member.from_user else None
    elif update.chat_member:
        update_type = 'chat_member'
        chat_id = update.chat_member.chat.id if update.chat_member.chat else None
        user_id = update.chat_member.from_user.id if update.chat_member.from_user else None
    else:
        # Логируем неизвестные типы обновлений для отладки
        update_type = 'unknown'
        logger.debug('UNKNOWN UPDATE TYPE: update_id=%s, update_keys=%s', update.update_id, list(update.model_dump().keys()))

    logger.info(
        'WEBHOOK UPDATE RECEIVED: update_id=%s, update_type=%s, chat_id=%s, user_id=%s, '
        'active_background_tasks=%s',
        update.update_id,
        update_type,
        chat_id,
        user_id,
        len(tg_background_tasks),
    )

    task: Task[Any] = asyncio.create_task(dp.feed_webhook_update(bot, update))
    tg_background_tasks.add(task)

    task.add_done_callback(tg_background_tasks.discard)

    logger.debug('WEBHOOK UPDATE PROCESSING: update_id=%s, update_type=%s', update.update_id, update_type)

    return ORJSONResponse({'success': True})


@tg_router.get('/tg/chat/{chat_id}/permissions')
async def get_chat_permissions(
    chat_id: int,
    bot: Bot = Depends(get_tg_bot),
) -> ORJSONResponse:
    """
    Проверяет права бота в указанном чате.
    
    Returns:
        Информация о правах бота, необходимых правах и отсутствующих правах
    """
    logger.info('PERMISSIONS CHECK REQUEST: chat_id=%s', chat_id)
    try:
        # Получаем информацию о чате
        chat = await bot.get_chat(chat_id)
        bot_info = await bot.get_me()
        logger.debug('PERMISSIONS CHECK: chat_id=%s, chat_title=%s, chat_type=%s', chat_id, chat.title if hasattr(chat, 'title') else None, chat.type)

        # Получаем информацию о членстве бота
        try:
            chat_member = await bot.get_chat_member(chat_id, bot_info.id)
        except Exception as e:
            logger.warning('PERMISSIONS CHECK: Bot is not a member of chat, chat_id=%s, error=%s', chat_id, e)
            raise HTTPException(status_code=404, detail=f'Bot is not a member of chat {chat_id}')

        # Безопасно получаем строковое значение статуса (может быть enum или строка)
        status_value = chat_member.status.value if hasattr(chat_member.status, 'value') else str(chat_member.status)
        logger.info('PERMISSIONS CHECK: chat_id=%s, bot_status=%s', chat_id, status_value)

        # Определяем необходимые права в зависимости от типа чата
        required_permissions = {
            'for_groups': ['can_read_messages'],
        }
        
        # Извлекаем текущие права
        current_permissions = {
            'status': status_value,
        }

        # Проверяем, является ли бот участником (обрабатываем как enum, так и строку)
        is_member = (
            chat_member.status == ChatMemberStatus.MEMBER or
            chat_member.status == ChatMemberStatus.ADMINISTRATOR or
            chat_member.status == ChatMemberStatus.RESTRICTED or
            str(chat_member.status) in ('member', 'administrator', 'restricted')
        )

        # Для администраторов получаем детальные права
        if isinstance(chat_member, ChatMemberAdministrator):
            current_permissions.update({
                'can_read_messages': True,  # Администратор всегда может читать
                'can_post_messages': chat_member.can_post_messages if hasattr(chat_member, 'can_post_messages') else None,
                'can_edit_messages': chat_member.can_edit_messages if hasattr(chat_member, 'can_edit_messages') else None,
                'can_delete_messages': chat_member.can_delete_messages if hasattr(chat_member, 'can_delete_messages') else None,
                'can_restrict_members': chat_member.can_restrict_members if hasattr(chat_member, 'can_restrict_members') else None,
                'can_promote_members': chat_member.can_promote_members if hasattr(chat_member, 'can_promote_members') else None,
                'can_invite_users': chat_member.can_invite_users if hasattr(chat_member, 'can_invite_users') else None,
                'can_pin_messages': chat_member.can_pin_messages if hasattr(chat_member, 'can_pin_messages') else None,
                'can_manage_chat': chat_member.can_manage_chat if hasattr(chat_member, 'can_manage_chat') else None,
                'can_manage_video_chats': chat_member.can_manage_video_chats if hasattr(chat_member, 'can_manage_video_chats') else None,
            })
        elif isinstance(chat_member, ChatMemberMember):
            # Обычный участник - может читать если privacy mode отключен или бот админ
            current_permissions['can_read_messages'] = True
        elif isinstance(chat_member, ChatMemberRestricted):
            # Ограниченный участник
            current_permissions['can_read_messages'] = chat_member.can_read_messages if hasattr(chat_member, 'can_read_messages') else False
            current_permissions['can_send_messages'] = chat_member.can_send_messages if hasattr(chat_member, 'can_send_messages') else False
            current_permissions['can_send_media_messages'] = chat_member.can_send_media_messages if hasattr(chat_member, 'can_send_media_messages') else False
            current_permissions['can_send_other_messages'] = chat_member.can_send_other_messages if hasattr(chat_member, 'can_send_other_messages') else False
            current_permissions['can_add_web_page_previews'] = chat_member.can_add_web_page_previews if hasattr(chat_member, 'can_add_web_page_previews') else False

        # Определяем отсутствующие права
        missing_permissions = []
        if chat.type in ('group', 'supergroup'):
            required = required_permissions['for_groups']
            for perm in required:
                if perm == 'can_read_messages' and not current_permissions.get('can_read_messages', False):
                    missing_permissions.append(perm)

        logger.info(
            'PERMISSIONS CHECK RESULT: chat_id=%s, is_member=%s, status=%s, missing_permissions=%s',
            chat_id,
            is_member,
            current_permissions.get('status'),
            missing_permissions,
        )

        return ORJSONResponse({
            'is_member': is_member,
            'chat_info': {
                'chat_id': chat.id,
                'chat_title': chat.title if hasattr(chat, 'title') else None,
                'chat_type': chat.type,
            },
            'current_permissions': current_permissions,
            'required_permissions': required_permissions,
            'missing_permissions': missing_permissions,
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error('Failed to get chat permissions: %s', e, exc_info=True)
        raise HTTPException(status_code=500, detail=f'Failed to get chat permissions: {str(e)}')
