import sqlite3

DATABASE = 'finance.db' # Имя файла нашей базы данных

def get_db_connection():
    """Устанавливает соединение с базой данных."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row # Позволяет получать строки как объекты, к которым можно обращаться по имени столбца
    return conn

def init_db():
    """Инициализирует базу данных, создавая необходимые таблицы."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Создаем таблицу пользователей
    # НОВОЕ: Добавлено поле password_hash
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')

    # Создаем таблицу целей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            goal_type TEXT NOT NULL, -- Тип цели: 'сбережение', 'накопление', 'инвестиции'
            note TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()
    print("База данных инициализирована (или уже существует).")

if __name__ == '__main__':
    # Если запустить этот файл напрямую, он инициализирует базу данных
    init_db()
