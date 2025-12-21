import re
import sys
import time
from pathlib import Path
from typing import List, Dict

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Добавляем корневую директорию проекта в sys.path для корректных импортов
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from data.db import data_base


BASE_URL = "https://isnad.link"
BOOK_INDEX_URL = f"{BASE_URL}/book/sahih-al-buhari"
REQUEST_TIMEOUT = 15

REQUEST_DELAY = 1.0  # пауза между запросами, чтобы не нагружать сайт


def fetch_html(url: str) -> str:
    """
    Загружает HTML‑страницу и возвращает её текст.
    При ошибке выбрасывает исключение.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        )
    }
    response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    # Явно указываем кодировку
    if not response.encoding:
        response.encoding = "utf-8"
    return response.text


def parse_books_index(html: str) -> List[Dict]:
    """
    Парсит главную страницу сборника и извлекает список всех 97 книг.

    Возвращает список словарей:
        {
            "book_number": int,
            "book_title": str,
            "url": str
        }
    """
    soup = BeautifulSoup(html, "html5lib")

    sections_ul = soup.find("ul", class_="sections")
    if not sections_ul:
        raise RuntimeError("Не найден список книг (ul.sections) на странице индекса.")

    books: List[Dict] = []

    for li in sections_ul.find_all("li"):
        a = li.find("a")
        if not a or not a.get("href"):
            continue

        # Текст книги в русской части — первый div.column
        ru_col = a.find("div", class_="column")
        if not ru_col:
            continue

        title_text = ru_col.get_text(strip=True)

        # Фильтруем служебные разделы типа "О сборнике"
        if "Книга" not in title_text and "книга" not in title_text:
            continue

        # В начале обычно идёт номер: "1.  Книга: ..."
        m_num = re.match(r"^\s*(\d+)\s*\.", title_text)
        if not m_num:
            continue

        book_number = int(m_num.group(1))
        full_url = urljoin(BASE_URL, a["href"])

        books.append(
            {
                "book_number": book_number,
                "book_title": title_text,
                "url": full_url,
            }
        )

    if not books:
        raise RuntimeError("Не удалось найти ни одной книги на странице индекса.")

    # Сортируем по номеру книги на всякий случай
    books.sort(key=lambda b: b["book_number"])
    return books


# Функция _extract_hadith_number больше не используется, т.к. идентификация теперь по chapter_title


def parse_book_page(book: Dict, html: str) -> List[Dict]:
    """
    Парсит страницу конкретной книги и извлекает все хадисы.

    book: словарь с ключами book_number, book_title, url
    Возвращает список словарей:
        {
            "book_number": int,
            "book_title": str,
            "hadis_text": str,
            "chapter_title": str,
        }
    """
    soup = BeautifulSoup(html, "html5lib")

    results: List[Dict] = []

    # Каждый хадис на странице имеет блок:
    # <div class="columns">
    #   <div class="column hadeeth"><span class="hadeeth-num"> ... </span></div>
    # </div>
    # и следующий за ним блок с текстом:
    # <div class="columns">
    #   <div class="column">
    #       <article> ... <p>текст хадиса</p> ... </article>
    #   </div>
    #   <div class="column is-hidden-mobile"> ... арабский текст ... </div>
    # </div>

    for header_col in soup.select("div.column.hadeeth"):
        header_text = header_col.get_text(" ", strip=True)

        # Находим родителя-строку и следующий за ним блок с текстом
        row = header_col.find_parent("div", class_="columns")
        if not row:
            continue

        content_row = row.find_next_sibling("div", class_="columns")
        if not content_row:
            continue

        text_column = content_row.find("div", class_="column")
        if not text_column:
            continue

        article = text_column.find("article")
        if not article:
            continue

        paragraphs = article.find_all("p")
        text_parts = [p.get_text(" ", strip=True) for p in paragraphs]
        full_text = " ".join(t for t in text_parts if t).strip()
        if not full_text:
            continue

        # Используем chapter_title (header_text) как обязательное поле
        # Если header_text пустой, используем первые слова текста хадиса
        if not header_text or not header_text.strip():
            # Берем первые 100 символов текста как chapter_title
            header_text = full_text[:100].strip()
            if len(full_text) > 100:
                header_text += "..."

        results.append(
            {
                "book_number": book["book_number"],
                "book_title": book["book_title"],
                "hadis_text": full_text,
                "chapter_title": header_text.strip(),
            }
        )

    return results


def import_all_hadiths() -> None:
    """
    Главная функция: обходит все книги «Сахих аль‑Бухари» на isnad.link
    и сохраняет все хадисы в БД.
    """
    print("Инициализирую базу данных (таблица hadis будет пересоздана)...")
    # Полный сброс таблицы делаем осознанно только здесь
    data_base.init_db(reset=True)

    print(f"Загружаю индекс книг: {BOOK_INDEX_URL}")
    index_html = fetch_html(BOOK_INDEX_URL)
    books = parse_books_index(index_html)

    print(f"Найдено книг: {len(books)}")

    total_hadiths = 0

    for i, book in enumerate(books, start=1):
        print(
            f"[{i}/{len(books)}] "
            f"Книга {book['book_number']}: {book['book_title']} "
            f"→ {book['url']}"
        )

        try:
            html = fetch_html(book["url"])
        except Exception as e:
            print(f"  ❌ Ошибка загрузки книги: {e}")
            continue

        try:
            hadiths = parse_book_page(book, html)
        except Exception as e:
            print(f"  ❌ Ошибка парсинга книги: {e}")
            continue

        print(f"  Найдено хадисов в книге: {len(hadiths)}")

        for h in hadiths:
            data_base.save_hadis(
                book_number=h["book_number"],
                book_title=h["book_title"],
                hadis_text=h["hadis_text"],
                chapter_title=h["chapter_title"],
            )
            total_hadiths += 1

        # Небольшая пауза между книгами
        time.sleep(REQUEST_DELAY)

    print(f"Импорт завершён. Всего сохранено хадисов: {total_hadiths}")


if __name__ == "__main__":
    import_all_hadiths()

