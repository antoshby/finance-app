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

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            goal_type TEXT NOT NULL,
            note TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    try:
        cursor.execute("ALTER TABLE goals ADD COLUMN amount REAL DEFAULT 0.00")
        print("Колонка 'amount' успешно добавлена в таблицу goals.")
    except sqlite3.OperationalError as e:
        if "duplicate column name: amount" in str(e):
            print("Колонка 'amount' уже существует.")
        else:
            raise

    conn.commit()
    conn.close()
    print("База данных инициализирована (или уже существует).")

if __name__ == '__main__':
    # Если вы хотите полностью пересоздать базу данных для тестирования,
    # раскомментируйте следующие строки, НО БУДЬТЕ ОСТОРОЖНЫ - ВСЕ ДАННЫЕ БУДУТ УДАЛЕНЫ!
    # if os.path.exists(DATABASE):
    #     os.remove(DATABASE)
    #     print(f"Существующая база данных '{DATABASE}' удалена.")
    init_db()