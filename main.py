from flask import Flask, render_template, request, redirect, url_for, session, g
import sqlite3

app = Flask(__name__)
app.secret_key = 'supersecretkey'
DATABASE = 'database.db'

# Подключение к БД
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Создание таблиц
with app.app_context():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE,
                        password TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS projects (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        name TEXT,
                        content TEXT,
                        FOREIGN KEY(user_id) REFERENCES users(id))''')
    db.commit()

# Главная страница (регистрация)
@app.route('/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        try:
            db.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            db.commit()
            return redirect(url_for('login'))
        except:
            return "Пользователь уже существует!"
    return render_template('register.html')

# Страница логина
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password)).fetchone()
        if user:
            session['user_id'] = user[0]
            return redirect(url_for('dashboard'))
        else:
            return "Неверные данные!"
    return render_template('login.html')

# Дашборд - список проектов
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    db = get_db()
    projects = db.execute("SELECT * FROM projects WHERE user_id = ?", (session['user_id'],)).fetchall()
    return render_template('dashboard.html', projects=projects)

# Создание проекта
@app.route('/create', methods=['GET', 'POST'])
def create():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        content = request.form['content']
        db = get_db()
        db.execute("INSERT INTO projects (user_id, name, content) VALUES (?, ?, ?)", (session['user_id'], name, content))
        db.commit()
        return redirect(url_for('dashboard'))
    return render_template('create.html')

# Редактирование проекта
@app.route('/edit/<int:project_id>', methods=['GET', 'POST'])
def edit(project_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    db = get_db()
    project = db.execute("SELECT * FROM projects WHERE id = ? AND user_id = ?", (project_id, session['user_id'])).fetchone()
    if not project:
        return "Проект не найден!"
    if request.method == 'POST':
        content = request.form['content']
        db.execute("UPDATE projects SET content = ? WHERE id = ?", (content, project_id))
        db.commit()
        return redirect(url_for('dashboard'))
    return render_template('edit.html', project=project)

if __name__ == '__main__':
    app.run(debug=True)
