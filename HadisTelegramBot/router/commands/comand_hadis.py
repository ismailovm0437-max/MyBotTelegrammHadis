
from aiogram import Bot, Router  # !ВСЕ ИМОПРТЫ ЗДЕСЬ
from aiogram import Dispatcher
from aiogram import types
from aiogram.filters import CommandStart, Command
from aiogram.types import CallbackQuery
from keyboard_bt.button import ButtonText, hadis_keyboard_bt, inline_hadis_keyboard, inline_book_keyboard, inline_hadis_list_keyboard
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from data.data_base import get_hadis_by_id, get_book_title
router = Router()


@router.message(Command("hadis"))
async def hendle_hadis(message: types.Message):
    await message.answer(
        text="Читай во имя Господа своего :",
        reply_markup=hadis_keyboard_bt(),
    )


@router.message(lambda message: message.text == ButtonText.BUTT_HADIS)
async def hendle_bukhari_hadis(message: types.Message):
    """Старт: пользователь нажал кнопку 'Хадисы Аль-Бухари'."""
    await message.answer(
        text="Выберите книгу хадисов из сборника «Сахих аль‑Бухари»:",
        reply_markup=inline_book_keyboard(page=1),
    )


@router.callback_query(lambda c: c.data and c.data.startswith("book_"))
async def handle_book(callback: CallbackQuery):
    """
    Обработка выбора книги.

    Ожидает callback_data вида: book_{book_number}
    """
    try:
        book_number = int(callback.data.split("_", maxsplit=1)[1])
    except (IndexError, ValueError):
        await callback.answer("Не удалось определить книгу", show_alert=True)
        return

    # Получаем название книги для отображения
    book_title = get_book_title(book_number)
    if book_title:
        # Укорачиваем название, если оно слишком длинное
        short_title = book_title.split("(хадисы")[0].strip()
        if len(short_title) > 50:
            short_title = short_title[:47] + "..."
        text = f"Книга {book_number}: {short_title}\n\nВыберите хадис:"
    else:
        text = f"Книга {book_number}. Выберите хадис:"
    
    await callback.message.edit_text(
        text=text,
        reply_markup=inline_hadis_list_keyboard(book_number, page=1),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("hlist_"))
async def handle_hadith_page(callback: CallbackQuery):
    """
    Пагинация списка хадисов.

    Ожидает callback_data вида: hlist_{book_number}_{page}
    """
    try:
        _, book_str, page_str = callback.data.split("_", maxsplit=2)
        book_number = int(book_str)
        page = int(page_str)
    except (ValueError, IndexError):
        await callback.answer("Некорректный номер страницы", show_alert=True)
        return

    # Получаем название книги для отображения
    book_title = get_book_title(book_number)
    if book_title:
        # Укорачиваем название, если оно слишком длинное
        short_title = book_title.split("(хадисы")[0].strip()
        if len(short_title) > 50:
            short_title = short_title[:47] + "..."
        text = f"Книга {book_number}: {short_title}\n\nВыберите хадис:"
    else:
        text = f"Книга {book_number}. Выберите хадис:"
    
    await callback.message.edit_text(
        text=text,
        reply_markup=inline_hadis_list_keyboard(book_number, page=page),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("hadis_"))
async def handle_hadis(callback: CallbackQuery):
    """
    Обработка выбора конкретного хадиса.

    Ожидает callback_data вида: hadis_{hadis_id}
    """
    try:
        _, hadis_id_str = callback.data.split("_", maxsplit=1)
        hadis_id = int(hadis_id_str)
    except (ValueError, IndexError):
        await callback.answer("Некорректный формат данных хадиса", show_alert=True)
        return

    hadis = get_hadis_by_id(hadis_id)

    if hadis:
        book_number = hadis["book_number"]
        # Кнопка "Назад" к списку хадисов этой же книги
        back_button = InlineKeyboardButton(
            text="◀️ Назад к хадисам книги",
            callback_data=f"book_{book_number}",
        )
        markup = InlineKeyboardMarkup(inline_keyboard=[[back_button]])

        await callback.message.edit_text(
            text=hadis["text"],
            reply_markup=markup,
        )
    else:
        await callback.answer("Хадис не найден", show_alert=True)

    await callback.answer()


@router.callback_query(lambda c: c.data == "back_to_books")
async def handle_back_to_books(callback: CallbackQuery):
    """Возврат от списка хадисов к списку книг."""
    await callback.message.edit_text(
        text="Выберите книгу хадисов из сборника «Сахих аль‑Бухари»:",
        reply_markup=inline_book_keyboard(page=1),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("bpage_"))
async def handle_book_page(callback: CallbackQuery):
    """
    Пагинация списка книг.

    Ожидает callback_data вида: bpage_{page}
    """
    try:
        _, page_str = callback.data.split("_", maxsplit=1)
        page = int(page_str)
    except (ValueError, IndexError):
        await callback.answer("Некорректный номер страницы книг", show_alert=True)
        return

    await callback.message.edit_text(
        text="Выберите книгу хадисов из сборника «Сахих аль‑Бухари»:",
        reply_markup=inline_book_keyboard(page=page),
    )
    await callback.answer()
