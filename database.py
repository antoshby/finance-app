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

    # НОВОЕ: Удаляем старую таблицу user_goals, если она существует
    try:
        cursor.execute("DROP TABLE IF EXISTS user_goals")
        print("Таблица 'user_goals' удалена (если существовала).")
    except sqlite3.OperationalError:
        pass # Игнорируем ошибку, если таблица не существует

    # Создаем таблицу goals, если её нет
    # НОВОЕ: user_goal_id теперь TEXT, для хранения названия фиксированной цели
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            goal_type TEXT NOT NULL,
            note TEXT NOT NULL,
            amount REAL DEFAULT 0.00,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_goal_id TEXT, -- ИЗМЕНЕНО: Теперь это TEXT, хранит название цели
            FOREIGN KEY (user_id) REFERENCES users (id)
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
    # Если она уже была TEXT, то ничего не изменится. Если была INTEGER, возможно, придется дропнуть колонку и добавить заново.
    # Для простоты, если тип не TEXT, мы можем пересоздать таблицу.
    try:
        cursor.execute("PRAGMA table_info(goals)")
        columns = cursor.fetchall()
        user_goal_id_col = next((col for col in columns if col['name'] == 'user_goal_id'), None)

        if user_goal_id_col and user_goal_id_col['type'] != 'TEXT':
            print("Колонка 'user_goal_id' имеет неверный тип. Пересоздание таблицы 'goals'...")
            # ВНИМАНИЕ: ЭТО УДАЛИТ ВСЕ ДАННЫЕ ИЗ ТАБЛИЦЫ GOALS!
            cursor.execute("DROP TABLE IF EXISTS goals")
            cursor.execute('''
                CREATE TABLE goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    goal_type TEXT NOT NULL,
                    note TEXT NOT NULL,
                    amount REAL DEFAULT 0.00,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_goal_id TEXT, -- Теперь это TEXT
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            print("Таблица 'goals' успешно пересоздана с колонкой 'user_goal_id' типа TEXT.")
        elif not user_goal_id_col:
            cursor.execute("ALTER TABLE goals ADD COLUMN user_goal_id TEXT")
            print("Колонка 'user_goal_id' успешно добавлена в таблицу goals как TEXT.")
        else:
            print("Колонка 'user_goal_id' уже существует и имеет тип TEXT.")
    except sqlite3.OperationalError as e:
        if "duplicate column name: user_goal_id" in str(e):
            print("Колонка 'user_goal_id' уже существует (пропущено).")
        else:
            raise

    conn.commit()
    conn.close()
    print("База данных инициализирована (или уже существует).")

if __name__ == '__main__':
    init_db()
