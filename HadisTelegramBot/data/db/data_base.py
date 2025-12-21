from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable, Optional, Tuple

DB_PATH = Path(__file__).resolve().parent.parent / "hadis.db"


def _connect() -> sqlite3.Connection:
    """Создаёт подключение к базе данных хадисов."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(reset: bool = False) -> None:
    """
    Гарантирует наличие таблицы hadis с правильной структурой для книг и хадисов.

    Таблица создаётся один раз, если она отсутствует.
    Структура:
    - id: уникальный идентификатор
    - book_number: номер книги (1-97)
    - book_title: название книги
    - hadis_text: текст хадиса
    - chapter_title: название главы (заголовок хадиса) - используется для идентификации и кнопок
    """
    with _connect() as conn:
        if reset:
            # Полный пересоздание таблицы — используется только при полном
            # перепарсивании всего сборника
            conn.execute("DROP TABLE IF EXISTS hadis")
            conn.execute(
                """
                CREATE TABLE hadis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    book_number INTEGER NOT NULL,
                    book_title TEXT NOT NULL,
                    hadis_text TEXT NOT NULL,
                    chapter_title TEXT NOT NULL,
                    UNIQUE(book_number, chapter_title)
                )
                """
            )
        else:
            # Проверяем существующую структуру и мигрируем, если нужно
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='hadis'"
            )
            if cursor.fetchone():
                # Таблица существует - проверяем структуру
                cursor = conn.execute("PRAGMA table_info(hadis)")
                columns = [row[1] for row in cursor.fetchall()]
                
                has_hadis_number = 'hadis_number' in columns
                has_chapter_title = 'chapter_title' in columns
                
                if has_hadis_number:
                    # Нужна миграция: удаляем hadis_number
                    print("Выполняется миграция базы данных: удаление колонки hadis_number...")
                    # SQLite не поддерживает DROP COLUMN напрямую, нужно пересоздать таблицу
                    conn.execute("BEGIN TRANSACTION")
                    try:
                        # Создаём временную таблицу с новой структурой
                        conn.execute(
                            """
                            CREATE TABLE hadis_new (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                book_number INTEGER NOT NULL,
                                book_title TEXT NOT NULL,
                                hadis_text TEXT NOT NULL,
                                chapter_title TEXT NOT NULL,
                                UNIQUE(book_number, chapter_title)
                            )
                            """
                        )
                        # Копируем данные (используем chapter_title как обязательное поле)
                        if has_chapter_title:
                            # Если chapter_title есть, но может быть пустым или NULL
                            conn.execute(
                                """
                                INSERT INTO hadis_new (id, book_number, book_title, hadis_text, chapter_title)
                                SELECT id, book_number, book_title, hadis_text, 
                                       CASE 
                                           WHEN chapter_title IS NOT NULL AND chapter_title != '' 
                                           THEN chapter_title
                                           ELSE substr(hadis_text, 1, 100) || '...'
                                       END as chapter_title
                                FROM hadis
                                """
                            )
                        else:
                            # Если chapter_title нет, используем текст хадиса как заголовок
                            conn.execute(
                                """
                                INSERT INTO hadis_new (id, book_number, book_title, hadis_text, chapter_title)
                                SELECT id, book_number, book_title, hadis_text, 
                                       CASE 
                                           WHEN length(hadis_text) > 100 
                                           THEN substr(hadis_text, 1, 100) || '...'
                                           ELSE hadis_text
                                       END as chapter_title
                                FROM hadis
                                """
                            )
                        # Удаляем старую таблицу и переименовываем новую
                        conn.execute("DROP TABLE hadis")
                        conn.execute("ALTER TABLE hadis_new RENAME TO hadis")
                        conn.execute("COMMIT")
                        print("Миграция завершена успешно.")
                    except Exception as e:
                        conn.execute("ROLLBACK")
                        raise Exception(f"Ошибка миграции: {e}")
                elif not has_chapter_title:
                    # Добавляем chapter_title, если его нет
                    # Сначала добавляем как nullable, потом заполняем и делаем NOT NULL через пересоздание
                    try:
                        conn.execute("ALTER TABLE hadis ADD COLUMN chapter_title TEXT")
                        # Заполняем chapter_title из текста хадиса
                        conn.execute(
                            """
                            UPDATE hadis 
                            SET chapter_title = CASE 
                                WHEN length(hadis_text) > 100 
                                THEN substr(hadis_text, 1, 100) || '...'
                                ELSE hadis_text
                            END
                            WHERE chapter_title IS NULL
                            """
                        )
                    except sqlite3.OperationalError:
                        pass
            else:
                # Таблица не существует - создаём новую
                conn.execute(
                    """
                    CREATE TABLE hadis (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        book_number INTEGER NOT NULL,
                        book_title TEXT NOT NULL,
                        hadis_text TEXT NOT NULL,
                        chapter_title TEXT NOT NULL,
                        UNIQUE(book_number, chapter_title)
                    )
                    """
                )

        # Создаём индексы для быстрого поиска
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_book_number ON hadis(book_number)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_chapter_title ON hadis(chapter_title)"
        )
        conn.commit()


def get_hadis_titles(book_number: Optional[int] = None, limit: Optional[int] = None) -> Iterable[Tuple[int, str]]:
    """
    Возвращает пары (id, title) из таблицы hadis.
    
    Args:
        book_number: номер книги для фильтрации (None = все книги)
        limit: максимальное количество записей (None = все)
    """
    if book_number is not None:
        query = "SELECT id, chapter_title FROM hadis WHERE book_number = ? ORDER BY id ASC"
        params: Tuple = (book_number,)
    else:
        query = "SELECT id, chapter_title FROM hadis ORDER BY book_number ASC, id ASC"
        params: Tuple = ()

    if limit is not None:
        query += " LIMIT ?"
        if book_number is not None:
            params = (book_number, limit)
        else:
            params = (limit,)

    with _connect() as conn:
        cursor = conn.execute(query, params)
        for row in cursor.fetchall():
            # Используем chapter_title как title
            title = row["chapter_title"]
            yield row["id"], title


def get_hadis_by_id(hadis_id: int) -> Optional[dict]:
    """
    Возвращает хадис по идентификатору.

    Args:
        hadis_id: идентификатор записи в таблице hadis
    """
    with _connect() as conn:
        cursor = conn.execute(
            "SELECT id, book_number, book_title, hadis_text, chapter_title FROM hadis WHERE id = ?",
            (hadis_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return {
            "id": row["id"],
            "book_number": row["book_number"],
            "book_title": row["book_title"],
            "text": row["hadis_text"],
            "chapter_title": row["chapter_title"]
        }


def get_hadis_by_book_and_chapter(book_number: int, chapter_title: str) -> Optional[dict]:
    """
    Возвращает хадис по номеру книги и названию главы.

    Args:
        book_number: номер книги (1-97)
        chapter_title: название главы (chapter_title)
    """
    with _connect() as conn:
        cursor = conn.execute(
            "SELECT id, book_number, book_title, hadis_text, chapter_title FROM hadis WHERE book_number = ? AND chapter_title = ?",
            (book_number, chapter_title),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return {
            "id": row["id"],
            "book_number": row["book_number"],
            "book_title": row["book_title"],
            "text": row["hadis_text"],
            "chapter_title": row["chapter_title"]
        }


def get_hadis_by_book_and_number(book_number: int, hadis_number: int) -> Optional[dict]:
    """
    Устаревший метод. Используйте get_hadis_by_id или get_hadis_by_book_and_chapter.
    Оставлен для обратной совместимости, но всегда возвращает None.
    """
    return None


def get_books() -> Iterable[Tuple[int, str]]:
    """
    Возвращает список всех книг (номер, название).
    """
    with _connect() as conn:
        cursor = conn.execute(
            "SELECT DISTINCT book_number, book_title FROM hadis ORDER BY book_number ASC"
        )
        for row in cursor.fetchall():
            yield row["book_number"], row["book_title"]


def get_book_title(book_number: int) -> Optional[str]:
    """
    Возвращает название книги по её номеру.
    
    Args:
        book_number: номер книги (1-97)
    
    Returns:
        Название книги или None, если книга не найдена
    """
    with _connect() as conn:
        cursor = conn.execute(
            "SELECT DISTINCT book_title FROM hadis WHERE book_number = ? LIMIT 1",
            (book_number,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return row["book_title"]


def get_hadiths_by_book(book_number: int) -> Iterable[dict]:
    """
    Возвращает все хадисы из указанной книги.
    
    Args:
        book_number: номер книги (1-97)
    """
    with _connect() as conn:
        cursor = conn.execute(
            "SELECT id, book_number, book_title, hadis_text, chapter_title FROM hadis WHERE book_number = ? ORDER BY id ASC",
            (book_number,),
        )
        for row in cursor.fetchall():
            yield {
                "id": row["id"],
                "book_number": row["book_number"],
                "book_title": row["book_title"],
                "text": row["hadis_text"],
                "chapter_title": row["chapter_title"]
            }


def save_hadis(book_number: int, book_title: str, hadis_text: str, chapter_title: str) -> int:
    """
    Сохраняет хадис в базу данных.
    
    Args:
        book_number: номер книги (1-97)
        book_title: название книги
        hadis_text: текст хадиса
        chapter_title: название главы (заголовок хадиса) - обязательное поле для идентификации
    
    Returns:
        id сохранённого хадиса
    """
    with _connect() as conn:
        cursor = conn.execute(
            """
            INSERT OR REPLACE INTO hadis (book_number, book_title, hadis_text, chapter_title)
            VALUES (?, ?, ?, ?)
            """,
            (book_number, book_title, hadis_text, chapter_title),
        )
        conn.commit()
        return cursor.lastrowid


# Инициализируем схему при импорте, но без полного сброса данных
init_db(reset=False)