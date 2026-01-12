"""Обработчики для приватных чатов."""
from pathlib import Path

from aiogram import F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiogram.types import FSInputFile

from src.handlers.private.router import private_router
from src.handlers.private.texts import (
    BACK_TO_CHOICE,
    CHOOSE_SALE_TYPE,
    OPT_MANAGERS_HEADER,
    OPT_QUANTITY_QUESTION,
    OPT_SMALL_QUANTITY,
    START_GREETING,
)

# Контакты менеджеров для опта
OPT_MANAGERS = [
    {"telegram": "@Duxa_VLIQ"},
    {"telegram": "@ArtemVLiQ"},
    {"telegram": "@elVLIQ"},
]

# Текст для розницы
RETAIL_TEXT = """Привет! Уже совсем скоро наши ароматизаторы вернутся на OZON и Яндекс.Маркет. Следите за обновлениями в нашем Telegram-канале. А пока ищите VLIQ в шопах своего города."""


def get_start_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру для выбора типа продажи."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🛒 Розница", callback_data="sale_type:retail"),
                InlineKeyboardButton(text="📦 ОПТ", callback_data="sale_type:opt"),
            ],
        ]
    )
    return keyboard


def get_quantity_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру для подтверждения количества."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да", callback_data="quantity:yes"),
                InlineKeyboardButton(text="❌ Нет", callback_data="quantity:no"),
            ],
            [InlineKeyboardButton(text="🔙 " + BACK_TO_CHOICE, callback_data="back_to_start")],
        ]
    )
    return keyboard


def get_back_to_start_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру для возврата к началу."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 " + BACK_TO_CHOICE, callback_data="back_to_start")],
        ]
    )
    return keyboard


def get_image_path() -> Path:
    """Возвращает путь к изображению."""
    # Получаем путь к корню проекта (от src/handlers/private/main.py)
    project_root = Path(__file__).parent.parent.parent.parent
    image_path = project_root / "src" / "templates" / "start" / "main_photo.jpg"
    return image_path


@private_router.message(Command("start"), F.chat.type == "private")
async def handle_start(message: Message, state: FSMContext):
    """Обработчик команды /start."""
    # Очищаем состояние
    await state.clear()

    # Получаем путь к изображению
    image_path = get_image_path()

    # Проверяем существование файла
    if not image_path.exists():
        # Если файл не найден, отправляем только текст
        await message.answer(
            f"{START_GREETING}\n\n{CHOOSE_SALE_TYPE}",
            reply_markup=get_start_keyboard(),
        )
        return

    # Отправляем фото с текстом и кнопками
    photo = FSInputFile(image_path)
    await message.answer_photo(
        photo=photo,
        caption=f"{START_GREETING}\n\n{CHOOSE_SALE_TYPE}",
        reply_markup=get_start_keyboard(),
    )


@private_router.callback_query(F.data == "back_to_start")
async def handle_back_to_start(callback: CallbackQuery, state: FSMContext):
    """Обработчик возврата к началу."""
    await state.clear()

    # Получаем путь к изображению
    image_path = get_image_path()

    # Удаляем старое сообщение
    try:
        await callback.message.delete()
    except Exception:
        # Если не удалось удалить (например, сообщение уже удалено), продолжаем
        pass

    # Проверяем существование файла
    if not image_path.exists():
        # Если файл не найден, отправляем только текст
        await callback.message.answer(
            f"{START_GREETING}\n\n{CHOOSE_SALE_TYPE}",
            reply_markup=get_start_keyboard(),
        )
        await callback.answer()
        return

    # Отправляем фото с текстом и кнопками
    photo = FSInputFile(image_path)
    await callback.message.answer_photo(
        photo=photo,
        caption=f"{START_GREETING}\n\n{CHOOSE_SALE_TYPE}",
        reply_markup=get_start_keyboard(),
    )
    await callback.answer()


@private_router.callback_query(F.data == "sale_type:retail")
async def handle_retail_choice(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора розницы."""
    await state.clear()

    # Если сообщение содержит фото, удаляем его и отправляем новое текстовое
    if callback.message.photo:
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer(
            RETAIL_TEXT,
            reply_markup=get_back_to_start_keyboard(),
        )
    else:
        await callback.message.edit_text(
            RETAIL_TEXT,
            reply_markup=get_back_to_start_keyboard(),
        )
    await callback.answer()


@private_router.callback_query(F.data == "sale_type:opt")
async def handle_opt_choice(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора ОПТ."""
    # Если сообщение содержит фото, удаляем его и отправляем новое текстовое
    if callback.message.photo:
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer(
            OPT_QUANTITY_QUESTION,
            reply_markup=get_quantity_keyboard(),
        )
    else:
        await callback.message.edit_text(
            OPT_QUANTITY_QUESTION,
            reply_markup=get_quantity_keyboard(),
        )
    await callback.answer()


@private_router.callback_query(F.data == "quantity:yes")
async def handle_quantity_yes(callback: CallbackQuery, state: FSMContext):
    """Обработчик подтверждения количества >= 5 шт."""
    await state.clear()

    # Формируем список менеджеров
    managers_text = OPT_MANAGERS_HEADER
    for i, manager in enumerate(OPT_MANAGERS, 1):
        managers_text += f"{i}. {manager['telegram']}\n"

    # Если сообщение содержит фото, удаляем его и отправляем новое текстовое
    if callback.message.photo:
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer(
            managers_text,
            reply_markup=get_back_to_start_keyboard(),
        )
    else:
        await callback.message.edit_text(
            managers_text,
            reply_markup=get_back_to_start_keyboard(),
        )
    await callback.answer()


@private_router.callback_query(F.data == "quantity:no")
async def handle_quantity_no(callback: CallbackQuery, state: FSMContext):
    """Обработчик отказа при количестве < 5 шт."""
    # Если сообщение содержит фото, удаляем его и отправляем новое текстовое
    if callback.message.photo:
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer(
            OPT_SMALL_QUANTITY,
            reply_markup=get_back_to_start_keyboard(),
        )
    else:
        await callback.message.edit_text(
            OPT_SMALL_QUANTITY,
            reply_markup=get_back_to_start_keyboard(),
        )
    await callback.answer()

