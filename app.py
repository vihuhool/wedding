from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

DB_PATH = 'wedding.db'

def init_db():
    if not os.path.exists(DB_PATH):
        with sqlite3.connect(DB_PATH) as conn:
            with open('schema.sql', 'r', encoding='utf-8') as f:
                conn.executescript(f.read())

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

class User(UserMixin):
    def __init__(self, id_, email):
        self.id = id_
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, email FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return User(user[0], user[1])
    return None

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        hashed = generate_password_hash(password)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (email, password_hash) VALUES (?, ?)", (email, hashed))
            conn.commit()
            flash('Регистрация успешна. Теперь войдите.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Пользователь уже существует.', 'danger')
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, password_hash FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()
        if user and check_password_hash(user[1], password):
            login_user(User(user[0], email))
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        flash('Неверные данные.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route("/submit_rsvp", methods=["POST"])
@login_required
def submit_rsvp():
    name = request.form.get("name")
    drinks = request.form.getlist("drinks")  # список
    wine_color = request.form.get("wine_color")
    wine_type = request.form.get("wine_type")
    zags = request.form.get("zags")
    restrictions = request.form.get("restrictions")
    main_dish = request.form.get("main_dish")

    # Преобразуем список напитков в строку (через запятую)
    drinks_str = ", ".join(drinks)

    conn = get_db_connection()
    conn.execute(
        "INSERT INTO guests (user_id, name, drinks, wine_color, wine_type, zags, food, main_dish) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (current_user.id, name, drinks_str, wine_color, wine_type, zags, restrictions, main_dish),
    )
    conn.commit()
    conn.close()

    flash("Ответ успешно отправлен! 💌", "success")
    return redirect(url_for("index", confetti="1"))


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
