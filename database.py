import sqlite3
import os

DATABASE = os.path.join('data', 'finance.db')

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Создаем таблицу users, если её нет
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')

    # НОВОЕ: Создаем таблицу для конкретных целей сбережений
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL UNIQUE, -- Название цели (например, "На машину", "На квартиру")
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Создаем таблицу goals, если её нет
    # НОВОЕ: Добавляем колонку user_goal_id, которая будет ссылаться на user_goals
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            goal_type TEXT NOT NULL,
            note TEXT NOT NULL,
            amount REAL DEFAULT 0.00,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_goal_id INTEGER, -- НОВОЕ: Колонка для связи с конкретной целью
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (user_goal_id) REFERENCES user_goals (id)
        )
    ''')

    # Проверяем и добавляем колонку 'amount' в таблицу goals (если еще нет)
    try:
        cursor.execute("ALTER TABLE goals ADD COLUMN amount REAL DEFAULT 0.00")
        print("Колонка 'amount' успешно добавлена в таблицу goals.")
    except sqlite3.OperationalError as e:
        if "duplicate column name: amount" in str(e):
            print("Колонка 'amount' уже существует.")
        else:
            raise

    # НОВОЕ: Проверяем и добавляем колонку 'user_goal_id' в таблицу goals (если еще нет)
    try:
        cursor.execute("ALTER TABLE goals ADD COLUMN user_goal_id INTEGER")
        print("Колонка 'user_goal_id' успешно добавлена в таблицу goals.")
    except sqlite3.OperationalError as e:
        if "duplicate column name: user_goal_id" in str(e):
            print("Колонка 'user_goal_id' уже существует.")
        else:
            raise

    conn.commit()
    conn.close()
    print("База данных инициализирована (или уже существует).")

if __name__ == '__main__':
    init_db()