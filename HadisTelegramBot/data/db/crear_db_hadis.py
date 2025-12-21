import sqlite3
from pathlib import Path
from data.JSON.hadis import HADIS


def import_hadis_db():
    #! Установка соединения с базой данных
    # Получаем путь к базе данных относительно корня проекта
    db_path = Path(__file__).resolve().parent.parent / 'hadis.db'
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    # ?! Создание таблицы hadis
    cursor.execute('''CREATE TABLE IF NOT EXISTS hadis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    text TEXT NOT NULL   
)
''')
    cursor.execute('DELETE FROM hadis')  # ? Очистка таблицы перед импортом
    cursor.execute('DELETE FROM sqlite_sequence WHERE name="hadis"')
    batch_size = 10
    total_imported = 0

    for i in range(0, len(HADIS), batch_size):
        batch = HADIS[i:i + batch_size]

        # *ПОДГОТОВКА ДАННЫХ ДЛЯ ВСТАВКИ
        data_to_insert = [
            (hadis['title'], hadis['text'])
            for hadis in batch
        ]

        # ! ВСТАВКА ДАННЫХ В ТАБЛИЦУ
        cursor.executemany(
            'INSERT INTO hadis (title, text) VALUES (?, ?)',
            data_to_insert
        )

        total_imported += len(batch)
        print(f"Импортировано пакет {i//batch_size + 1}: {total_imported} хадисов")

    # ?СОХРАНЕНИЕ ИЗМЕНЕНИЙ (после цикла)
    connection.commit()
    connection.close()

    print(f"Импортировано всего хадисов: {total_imported}")

if __name__ == "__main__":
    import_hadis_db()
