import sqlite3
<<<<<<< HEAD
import os # НОВОЕ: Импорт модуля os для работы с файловой системой
=======
>>>>>>> 2b93d3fa9ecfd0f552c6e2056e1368d9a88f7211

DATABASE = 'finance.db' # Имя файла нашей базы данных

def get_db_connection():
    """Устанавливает соединение с базой данных."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row # Позволяет получать строки как объекты, к которым можно обращаться по имени столбца
    return conn

def init_db():
<<<<<<< HEAD
    """Инициализирует базу данных, создавая необходимые таблицы и обновляя схему."""
=======
    """Инициализирует базу данных, создавая необходимые таблицы."""
>>>>>>> 2b93d3fa9ecfd0f552c6e2056e1368d9a88f7211
    conn = get_db_connection()
    cursor = conn.cursor()

    # Создаем таблицу пользователей
<<<<<<< HEAD
=======
    # НОВОЕ: Добавлено поле password_hash
>>>>>>> 2b93d3fa9ecfd0f552c6e2056e1368d9a88f7211
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')

    # Создаем таблицу целей
<<<<<<< HEAD
    # НОВОЕ: Добавлено поле created_at и amount
=======
>>>>>>> 2b93d3fa9ecfd0f552c6e2056e1368d9a88f7211
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
<<<<<<< HEAD
            goal_type TEXT NOT NULL,
            note TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- НОВОЕ: Добавлено поле created_at
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # НОВОЕ: Проверяем и добавляем колонку 'amount' в таблицу goals
    # Это нужно для обновления существующей базы данных без потери данных.
    # Используем try-except, чтобы избежать ошибки, если колонка уже существует.
    try:
        cursor.execute("ALTER TABLE goals ADD COLUMN amount REAL DEFAULT 0.00")
        print("Колонка 'amount' успешно добавлена в таблицу goals.")
    except sqlite3.OperationalError as e:
        if "duplicate column name: amount" in str(e):
            print("Колонка 'amount' уже существует.")
        else:
            # Если это другая OperationalError, перевыбросить её
            raise

=======
            goal_type TEXT NOT NULL, -- Тип цели: 'сбережение', 'накопление', 'инвестиции'
            note TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
>>>>>>> 2b93d3fa9ecfd0f552c6e2056e1368d9a88f7211
    conn.commit()
    conn.close()
    print("База данных инициализирована (или уже существует).")

if __name__ == '__main__':
<<<<<<< HEAD
    # Если вы хотите полностью пересоздать базу данных для тестирования,
    # раскомментируйте следующие строки, НО БУДЬТЕ ОСТОРОЖНЫ - ВСЕ ДАННЫЕ БУДУТ УДАЛЕНЫ!
    # import os
    # if os.path.exists(DATABASE):
    #     os.remove(DATABASE)
    #     print(f"Существующая база данных '{DATABASE}' удалена.")
    init_db()
=======
    # Если запустить этот файл напрямую, он инициализирует базу данных
    init_db()
>>>>>>> 2b93d3fa9ecfd0f552c6e2056e1368d9a88f7211
