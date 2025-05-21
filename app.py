from flask import Flask, render_template, request, redirect, url_for, g, session, flash
import sqlite3
from database import init_db, get_db_connection, DATABASE
from werkzeug.security import generate_password_hash, check_password_hash
import functools  # Для создания декоратора

app = Flask(__name__)
# НОВОЕ: Секретный ключ для сессий. ОЧЕНЬ ВАЖНО!
# В реальном приложении это должна быть длинная случайная строка,
# которую нельзя хранить прямо в коде (например, через переменную окружения).
app.config['SECRET_KEY'] = '2qy5nytxmcen56zc9yzho6'  # Замените на свою уникальную строку!


# Функция для получения соединения с БД для каждого запроса
def get_db():
    if 'db' not in g:
        g.db = get_db_connection()
    return g.db


# Функция, которая будет закрывать соединение с БД после каждого запроса
@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


# НОВОЕ: Загрузка пользователя перед каждым запросом
@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        g.user = cursor.fetchone()


# НОВОЕ: Декоратор для защиты страниц, требующих входа в систему
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash('Для доступа к этой странице необходимо войти в систему.', 'warning')
            return redirect(url_for('login'))
        return view(**kwargs)

    return wrapped_view


# Инициализация базы данных при запуске приложения
with app.app_context():
    init_db()


# НОВОЕ: Страница регистрации
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        error = None

        if not username:
            error = 'Имя пользователя обязательно.'
        elif not password:
            error = 'Пароль обязателен.'

        conn = get_db()
        cursor = conn.cursor()

        if error is None:
            try:
                # Хешируем пароль перед сохранением!
                hashed_password = generate_password_hash(password)
                cursor.execute(
                    "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                    (username, hashed_password)
                )
                conn.commit()
            except sqlite3.IntegrityError:
                # Ошибка, если имя пользователя уже существует (UNIQUE NOT NULL)
                error = f"Пользователь '{username}' уже зарегистрирован."
            else:
                flash('Вы успешно зарегистрировались! Теперь войдите в систему.', 'success')
                return redirect(url_for('login'))

        flash(error, 'danger')  # Показываем ошибку, если она есть

    return render_template('register.html')


# НОВОЕ: Страница входа
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        error = None

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        )
        user = cursor.fetchone()

        if user is None:
            error = 'Неверное имя пользователя.'
        elif not check_password_hash(user['password_hash'], password):
            error = 'Неверный пароль.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']  # Сохраняем ID пользователя в сессию
            flash('Вы успешно вошли в систему!', 'success')
            return redirect(url_for('index'))  # Перенаправляем на главную страницу после входа

        flash(error, 'danger')  # Показываем ошибку

    return render_template('login.html')


# НОВОЕ: Страница выхода
@app.route('/logout')
def logout():
    session.clear()  # Очищаем сессию, удаляя user_id
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('index'))


# Измененная главная страница - теперь требует входа для добавления цели
@app.route('/')
@login_required  # Защищаем эту страницу
def index():
    """Главная страница для добавления цели (только для вошедших пользователей)."""
    return render_template('index.html')


@app.route('/add_goal', methods=['POST'])
@login_required  # Защищаем эту страницу
def add_goal():
    """Обрабатывает добавление новой цели."""
    # Теперь user_id берем из g.user, так как пользователь уже авторизован
    user_id = g.user['id']
    goal_type = request.form['goal_type']
    note = request.form['note'].strip()

    if not note:  # Имя пользователя уже не нужно, так как оно из сессии
        flash("Пожалуйста, заполните заметку!", 'warning')
        return redirect(url_for('index'))

    conn = get_db()
    cursor = conn.cursor()

    # Добавляем цель для текущего пользователя
    cursor.execute("INSERT INTO goals (user_id, goal_type, note) VALUES (?, ?, ?)",
                   (user_id, goal_type, note))
    conn.commit()
    flash('Цель успешно добавлена!', 'success')
    return redirect(
        url_for('user_notes', username=g.user['username']))  # Перенаправляем на заметки текущего пользователя


# Измененная страница заметок - теперь требует входа
@app.route('/notes/<username>')
@login_required  # Защищаем эту страницу
def user_notes(username):
    """Отображает заметки для конкретного пользователя и форму поиска."""
    # Убедимся, что пользователь просматривает свои собственные заметки
    if g.user['username'] != username:
        flash('Вы не можете просматривать заметки других пользователей.', 'danger')
        return redirect(url_for('index'))

    conn = get_db()
    cursor = conn.cursor()

    user_id = g.user['id']  # Берем ID текущего пользователя

    # Получаем все заметки для этого пользователя
    cursor.execute("SELECT * FROM goals WHERE user_id = ?", (user_id,))
    notes = cursor.fetchall()

    return render_template('notes.html', username=username, notes=notes)


# Измененная страница поиска заметок - теперь требует входа
@app.route('/search_notes', methods=['POST'])
@login_required  # Защищаем эту страницу
def search_notes():
    """Обрабатывает поиск заметок."""
    # Имя пользователя берем из g.user
    username = g.user['username']
    user_id = g.user['id']
    search_query = request.form['search_query'].strip()

    conn = get_db()
    cursor = conn.cursor()

    # Выполняем поиск заметок по ключевому слову в поле 'note'
    cursor.execute("SELECT * FROM goals WHERE user_id = ? AND note LIKE ?",
                   (user_id, f"%{search_query}%"))
    found_notes = cursor.fetchall()

    flash(f"Результаты поиска по запросу '{search_query}'", 'info')
    return render_template('notes.html', username=username, notes=found_notes, search_query=search_query)


if __name__ == '__main__':
    app.run(debug=True)
