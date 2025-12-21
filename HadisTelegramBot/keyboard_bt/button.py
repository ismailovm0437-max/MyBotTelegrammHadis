
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from data.data_base import get_books, get_hadiths_by_book
import math


class ButtonText:
    BUTT_HADIS = "Хадисы Аль-Бухари"


def hadis_keyboard_bt():
    """Возвращает ReplyKeyboardMarkup для кнопки хадисов.

    Функция вынесена на уровень модуля, чтобы её можно было импортировать
    как `from keyboard_bt.button import hadis_keyboard_bt`.
    """
    butt_hadis = KeyboardButton(text=ButtonText.BUTT_HADIS)

    markup = ReplyKeyboardMarkup(
        keyboard=[[butt_hadis]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return markup


def inline_hadis_keyboard():
    """Возвращает InlineKeyboardMarkup для кнопки "Назад" к хадисам."""
    back_button = InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_hadis"
    )

    markup = InlineKeyboardMarkup(
        inline_keyboard=[[back_button]]
    )
    return markup


def inline_book_keyboard(page: int = 1) -> InlineKeyboardMarkup:
    """
    Возвращает InlineKeyboardMarkup для выбора книги хадисов из базы данных.

    - Книги разбиваются на страницы (по page_size штук), чтобы не превышать лимит Telegram.
    - Каждая кнопка имеет callback_data вида: book_{book_number}
    - Для переключения страниц используются callback_data: bpage_{page}
    """
    all_books = list(get_books())
    page_size = 15  # книг на одной странице
    total = len(all_books)
    if total == 0:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="◀️ Назад",
                        callback_data="back_to_hadis",
                    )
                ]
            ]
        )

    total_pages = max(1, math.ceil(total / page_size))
    if page < 1:
        page = 1
    if page > total_pages:
        page = total_pages

    start = (page - 1) * page_size
    end = start + page_size
    books = all_books[start:end]

    buttons = []

    # Вычисляем глобальный порядковый номер для первой книги на странице
    global_start_index = (page - 1) * page_size

    for idx, (book_number, book_title) in enumerate(books):
        # Порядковый номер кнопки на текущей странице (начинается с 1)

        # Укорачиваем заголовок: отрежем часть с "(хадисы ...)", если есть
        short_title = book_title.split("(хадисы")[0].strip()

        # Формируем текст кнопки с порядковым номером: "№{порядковый_номер}. {название}"
        # Сокращаем название, чтобы поместиться в лимит Telegram (64 символа)
        max_title_length = 50  # Оставляем место для "№{номер}. "
        if len(short_title) > max_title_length:
            short_title = short_title[:max_title_length - 3] + "..."

        # Формат: "№{порядковый_номер}. {название_книги}"
        text = f" {short_title}" if short_title else f" Книга {book_number}"

        buttons.append(
            [
                InlineKeyboardButton(
                    text=text,
                    callback_data=f"book_{book_number}",
                )
            ]
        )

    # Навигация по страницам, если страниц больше одной
    nav_row = []
    if total_pages > 1:
        if page > 1:
            nav_row.append(
                InlineKeyboardButton(
                    text="⬅️ Предыдущие",
                    callback_data=f"bpage_{page - 1}",
                )
            )
        if page < total_pages:
            nav_row.append(
                InlineKeyboardButton(
                    text="Следующие ➡️",
                    callback_data=f"bpage_{page + 1}",
                )
            )
    if nav_row:
        buttons.append(nav_row)

    # Кнопка "Назад" к главному меню хадисов
    buttons.append(
        [
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data="back_to_hadis",
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def inline_hadis_list_keyboard(book_number: int, page: int = 1):
    """
    Возвращает InlineKeyboardMarkup со списком хадисов для выбранной книги.

    - Кнопки хадисов: text = "№{порядковый_номер}. {chapter_title}",
      callback_data = "hadis_{hadis_id}"
    - Внизу есть кнопка "Назад к книгам".
    """
    page_size = 20  # количество хадисов на одной странице
    hadiths = list(get_hadiths_by_book(book_number))
    total = len(hadiths)
    if total == 0:
        # Если по какой-то причине хадисов нет, показываем только кнопку "Назад"
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="◀️ Назад к книгам",
                        callback_data="back_to_books",
                    )
                ]
            ]
        )

    total_pages = max(1, math.ceil(total / page_size))
    # Нормализуем номер страницы
    if page < 1:
        page = 1
    if page > total_pages:
        page = total_pages

    start = (page - 1) * page_size
    end = start + page_size

    buttons = []

    # Вычисляем глобальный порядковый номер для первого хадиса на странице
    global_start_index = (page - 1) * page_size

    for idx, h in enumerate(hadiths[start:end]):
        hadis_id = h["id"]
        chapter_title = h.get("chapter_title", "Без названия")

        # Порядковый номер кнопки на текущей странице (начинается с 1)
        button_order = global_start_index + idx + 1

        # Используем chapter_title как название кнопки
        # Ограничиваем длину, чтобы поместиться в лимит Telegram (64 символа)
        max_title_length = 50  # Оставляем место для "№{номер}. "

        # Формируем краткое название из chapter_title
        if len(chapter_title) > max_title_length:
            short_title = chapter_title[:max_title_length - 3] + "..."
        else:
            short_title = chapter_title

        # Формат: "№{порядковый_номер}. {chapter_title}"
        text = f"{short_title}"

        # Дополнительная проверка на максимальную длину (64 символа для Telegram)
        if len(text) > 64:
            # Если все еще не помещается, сокращаем еще больше
            available_length = 64 - len(f"")
            if available_length > 0:
                text = f" {short_title[:available_length - 3]}..."

        buttons.append(
            [
                InlineKeyboardButton(
                    text=text,
                    callback_data=f"hadis_{hadis_id}",
                )
            ]
        )

    # Навигация по страницам (если страниц больше одной)
    nav_row = []
    if total_pages > 1:
        if page > 1:
            nav_row.append(
                InlineKeyboardButton(
                    text="⬅️ Предыдущая",
                    callback_data=f"hlist_{book_number}_{page - 1}",
                )
            )
        if page < total_pages:
            nav_row.append(
                InlineKeyboardButton(
                    text="Следующая ➡️",
                    callback_data=f"hlist_{book_number}_{page + 1}",
                )
            )
    if nav_row:
        buttons.append(nav_row)

    # Кнопка "Назад к книгам"
    buttons.append(
        [
            InlineKeyboardButton(
                text="◀️ Назад к книгам",
                callback_data="back_to_books",
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=buttons)
