from flask import Flask, render_template, request, redirect, url_for, g, session, flash
import sqlite3
from database import init_db, get_db_connection, DATABASE
from werkzeug.security import generate_password_hash, check_password_hash
import functools
# Импортируем нашу локальную функцию перевода
from locales import LOCALES, gettext_manual as _
import datetime  # Импорт datetime для работы с датами

app = Flask(__name__)
# Делаем нашу _() функцию доступной в шаблонах Jinja2
app.jinja_env.globals['_'] = _
app.config['SECRET_KEY'] = '2qy5nytxmcen56zc9yzho6'  # Замените на свою уникальную строку!


# Функция для определения локали (языка) для каждого запроса
def get_locale_from_request():
    lang = request.args.get('lang')
    if lang in LOCALES:  # Проверяем, что язык есть в нашем словаре
        session['lang'] = lang
        return lang

    if 'lang' in session and session['lang'] in LOCALES:
        return session['lang']

    # Используем best_match() для надежного определения языка из заголовка браузера
    best_browser_match = request.accept_languages.best_match(LOCALES.keys())
    if best_browser_match and best_browser_match in LOCALES:
        return best_browser_match

    return 'ru'  # Язык по умолчанию, если ничего не найдено


# Добавляем g.locale для использования в шаблонах
@app.before_request
def set_g_locale():
    # print("DEBUG: >>> set_g_locale function started. <<<") # ДИАГНОСТИКА: Можно раскомментировать, если нужно
    g.locale = get_locale_from_request()
    # print(f"DEBUG: Active locale in g.locale: {g.locale}") # ДИАГНОСТИКА
    # print("DEBUG: <<< set_g_locale function finished. >>>") # ДИАГНОСТИКА


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


# Загрузка пользователя перед каждым запросом
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


# Декоратор для защиты страниц, требующих входа в систему
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash(_('Для доступа к этой странице необходимо войти в систему.'), 'warning')
            return redirect(url_for('login'))
        return view(**kwargs)

    return wrapped_view


# Инициализация базы данных при запуске приложения
with app.app_context():
    init_db()


# Страница регистрации
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        error = None

        if not username:
            error = _('Имя пользователя обязательно.')
        elif not password:
            error = _('Пароль обязателен.')

        conn = get_db()
        cursor = conn.cursor()

        if error is None:
            try:
                hashed_password = generate_password_hash(password)
                cursor.execute(
                    "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                    (username, hashed_password)
                )
                conn.commit()
            except sqlite3.IntegrityError:
                error = _("Пользователь '%(username)s' уже зарегистрирован.") % {'username': username}
            else:
                flash(_('Вы успешно зарегистрировались! Теперь войдите в систему.'), 'success')
                return redirect(url_for('login'))

        flash(error, 'danger')

    return render_template('register.html')


# Страница входа
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
            error = _('Неверное имя пользователя.')
        elif not check_password_hash(user['password_hash'], password):
            error = _('Неверный пароль.')

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            flash(_('Вы успешно вошли в систему!'), 'success')
            return redirect(url_for('index'))

        flash(error, 'danger')

    return render_template('login.html')


# Страница выхода
@app.route('/logout')
def logout():
    session.clear()
    flash(_('Вы вышли из системы.'), 'info')
    return redirect(url_for('index'))


# Главная страница
@app.route('/')
@login_required
def index():
    """Главная страница для добавления цели (только для вошедших пользователей)."""
    # print(f"Текущая локаль: {g.locale}") # ДИАГНОСТИКА: Можно раскомментировать, если нужно
    # print(f"Перевод 'Мои Финансы': {_('Мои Финансы')}") # ДИАГНОСТИКА

    conn = get_db()
    cursor = conn.cursor()
    user_id = g.user['id']

    # Получаем все цели, созданные пользователем, для выпадающего списка
    cursor.execute("SELECT id, name FROM user_goals WHERE user_id = ? ORDER BY name ASC", (user_id,))
    user_goals = cursor.fetchall()

    return render_template('index.html', user_goals=user_goals)


@app.route('/add_goal', methods=['POST'])
@login_required
def add_goal():
    """Обрабатывает добавление новой цели."""
    user_id = g.user['id']
    goal_type = request.form['goal_type']
    note = request.form['note'].strip()
    amount_str = request.form['amount'].strip()
    user_goal_id = request.form.get('user_goal_id')  # Получаем user_goal_id из формы (может быть пустым)

    # Валидация и преобразование суммы
    try:
        amount = float(amount_str)
    except ValueError:
        flash(_('Сумма должна быть числом.'), 'danger')
        return redirect(url_for('index'))

    if not note:
        flash(_("Пожалуйста, заполните заметку!"), 'warning')
        return redirect(url_for('index'))

    conn = get_db()
    cursor = conn.cursor()

    # Добавляем цель для текущего пользователя, включая сумму и user_goal_id
    # Если user_goal_id пустой, сохраняем его как NULL
    cursor.execute("INSERT INTO goals (user_id, goal_type, note, amount, user_goal_id) VALUES (?, ?, ?, ?, ?)",
                   (user_id, goal_type, note, amount, user_goal_id if user_goal_id else None))
    conn.commit()
    flash(_('Цель успешно добавлена!'), 'success')
    return redirect(url_for('user_notes', username=g.user['username']))


# Страница заметок
@app.route('/notes/<username>')
@login_required
def user_notes(username):
    """Отображает заметки для конкретного пользователя и форму поиска, а также месячное и общее саммари."""
    if g.user['username'] != username:
        flash(_('Вы не можете просматривать заметки других пользователей.'), 'danger')
        return redirect(url_for('index'))

    conn = get_db()
    cursor = conn.cursor()

    user_id = g.user['id']

    # Получаем все заметки для этого пользователя
    cursor.execute("SELECT * FROM goals WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    notes = cursor.fetchall()

    # --- Расчет месячного саммари ---
    today = datetime.date.today()
    first_day_of_month = today.replace(day=1)

    monthly_summary = {
        'income': 0.0,
        'expense': 0.0,
        'saving': 0.0
    }

    cursor.execute(
        "SELECT goal_type, amount FROM goals WHERE user_id = ? AND created_at >= ? AND created_at < ?",
        (user_id, first_day_of_month.isoformat(),
         (first_day_of_month + datetime.timedelta(days=32)).replace(day=1).isoformat())
    )
    monthly_records = cursor.fetchall()

    for record in monthly_records:
        if record['goal_type'] in monthly_summary:
            monthly_summary[record['goal_type']] += record['amount']

    # --- Расчет общего саммари по всем временам ---
    total_summary = {
        'total_income': 0.0,
        'total_expense': 0.0,
        'total_saving': 0.0
    }
    cursor.execute("SELECT goal_type, amount FROM goals WHERE user_id = ?", (user_id,))
    all_records = cursor.fetchall()

    for record in all_records:
        if record['goal_type'] == 'income':
            total_summary['total_income'] += record['amount']
        elif record['goal_type'] == 'expense':
            total_summary['total_expense'] += record['amount']
        elif record['goal_type'] == 'saving':
            total_summary['total_saving'] += record['amount']

    # --- Саммари по конкретным целям сбережений ---
    goals_summary = {}
    # Получаем все пользовательские цели
    cursor.execute("SELECT id, name FROM user_goals WHERE user_id = ? ORDER BY name ASC", (user_id,))
    user_goals_list_for_summary = cursor.fetchall()

    for ug in user_goals_list_for_summary:
        goals_summary[ug['name']] = 0.0  # Инициализируем сумму для каждой цели

    # Суммируем накопления по каждой цели
    cursor.execute(
        "SELECT ug.name, SUM(g.amount) FROM goals g JOIN user_goals ug ON g.user_goal_id = ug.id WHERE g.user_id = ? AND g.goal_type = 'saving' GROUP BY ug.name",
        (user_id,)
    )
    saving_by_goal_records = cursor.fetchall()

    for record in saving_by_goal_records:
        goal_name = record[0]  # Имя цели
        total_amount = record[1]  # Сумма
        goals_summary[goal_name] = total_amount

    # Также получаем общую сумму накоплений без привязки к цели (если таковые есть)
    cursor.execute(
        "SELECT SUM(amount) FROM goals WHERE user_id = ? AND goal_type = 'saving' AND user_goal_id IS NULL",
        (user_id,)
    )
    saving_no_goal_record = cursor.fetchone()
    if saving_no_goal_record and saving_no_goal_record[0] is not None:
        goals_summary[_('Без цели')] = saving_no_goal_record[0]  # Добавляем в саммари

    return render_template('notes.html',
                           username=username,
                           notes=notes,
                           monthly_summary=monthly_summary,
                           total_summary=total_summary,  # Передаем в шаблон
                           goals_summary=goals_summary,  # Передаем в шаблон
                           user_goals_list_full=user_goals_list_for_summary)  # Передаем для отображения цели записи


# Страница поиска заметок
@app.route('/search_notes', methods=['POST'])
@login_required
def search_notes():
    """Обрабатывает поиск заметок."""
    username = g.user['username']
    user_id = g.user['id']
    search_query = request.form['search_query'].strip()

    conn = get_db()
    cursor = conn.cursor()

    # Выполняем поиск заметок по ключевому слову в поле 'note'
    cursor.execute("SELECT * FROM goals WHERE user_id = ? AND note LIKE ?",
                   (user_id, f"%{search_query}%"))
    found_notes = cursor.fetchall()

    flash(_("Результаты поиска по запросу '%(query)s'") % {'query': search_query}, 'info')
    return render_template('notes.html', username=username, notes=found_notes, search_query=search_query)


# Страница редактирования записи
@app.route('/edit_goal/<int:goal_id>', methods=['GET', 'POST'])
@login_required
def edit_goal(goal_id):
    conn = get_db()
    cursor = conn.cursor()
    user_id = g.user['id']

    # Получаем запись из БД
    cursor.execute("SELECT * FROM goals WHERE id = ?", (goal_id,))
    goal = cursor.fetchone()

    # Проверяем, существует ли запись и принадлежит ли она текущему пользователю
    if goal is None or goal['user_id'] != user_id:
        flash(_('Запись не найдена или у вас нет прав доступа.'), 'danger')
        return redirect(url_for('user_notes', username=g.user['username']))

    # Получаем все цели, созданные пользователем, для выпадающего списка
    cursor.execute("SELECT id, name FROM user_goals WHERE user_id = ? ORDER BY name ASC", (user_id,))
    user_goals = cursor.fetchall()

    if request.method == 'POST':
        goal_type = request.form['goal_type']
        note = request.form['note'].strip()
        amount_str = request.form['amount'].strip()
        user_goal_id = request.form.get('user_goal_id')

        # Валидация и преобразование суммы
        try:
            amount = float(amount_str)
        except ValueError:
            flash(_('Сумма должна быть числом.'), 'danger')
            return render_template('edit_goal.html', goal=goal, user_goals=user_goals)

        if not note:
            flash(_('Пожалуйста, заполните заметку!'), 'warning')
            return render_template('edit_goal.html', goal=goal, user_goals=user_goals)

        # Обновляем запись в БД, включая сумму и user_goal_id
        cursor.execute(
            "UPDATE goals SET goal_type = ?, note = ?, amount = ?, user_goal_id = ? WHERE id = ?",
            (goal_type, note, amount, user_goal_id if user_goal_id else None, goal_id)
        )
        conn.commit()
        flash(_('Запись успешно обновлена!'), 'success')
        return redirect(url_for('user_notes', username=g.user['username']))

    return render_template('edit_goal.html', goal=goal, user_goals=user_goals)


# НОВОЕ: Маршрут для удаления финансовой записи
@app.route('/delete_goal/<int:goal_id>', methods=['POST'])
@login_required
def delete_goal(goal_id):
    conn = get_db()
    cursor = conn.cursor()
    user_id = g.user['id']

    # Проверяем, существует ли запись и принадлежит ли она текущему пользователю
    cursor.execute("SELECT id, user_id FROM goals WHERE id = ?", (goal_id,))
    goal_to_delete = cursor.fetchone()

    if goal_to_delete is None or goal_to_delete['user_id'] != user_id:
        flash(_('Запись не найдена или у вас нет прав доступа.'), 'danger')
        return redirect(url_for('user_notes', username=g.user['username']))

    cursor.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
    conn.commit()
    flash(_('Запись успешно удалена.'), 'success')
    return redirect(url_for('user_notes', username=g.user['username']))


# Страница для управления пользовательскими целями (создание, просмотр)
@app.route('/goals', methods=['GET', 'POST'])
@login_required
def goals():
    conn = get_db()
    cursor = conn.cursor()
    user_id = g.user['id']
    error = None

    if request.method == 'POST':
        goal_name = request.form['goal_name'].strip()
        if not goal_name:
            error = _('Название цели не может быть пустым.')
        else:
            try:
                cursor.execute("INSERT INTO user_goals (user_id, name) VALUES (?, ?)",
                               (user_id, goal_name))
                conn.commit()
                # Правильное форматирование строки
                flash(_('Цель "%(goal_name)s" успешно добавлена!', goal_name=goal_name), 'success')
            except sqlite3.IntegrityError:
                error = _('Цель с таким названием уже существует.')

            if error:
                flash(error, 'danger')

    # Получаем все цели, созданные пользователем
    cursor.execute("SELECT id, name FROM user_goals WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    user_goals = cursor.fetchall()

    return render_template('goals.html', user_goals=user_goals)


if __name__ == '__main__':
    app.run(debug=True)
