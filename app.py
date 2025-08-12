from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'secret_key_for_session'

# Создание базы при первом запуске
def init_db():
    if not os.path.exists('books.db'):
        conn = sqlite3.connect('books.db')
        c = conn.cursor()

        # Таблица пользователей
        c.execute('''CREATE TABLE users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE,
                        password TEXT,
                        role TEXT DEFAULT 'user')''')

        # Таблица книг
        c.execute('''CREATE TABLE books (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT,
                        author TEXT,
                        category TEXT,
                        year INTEGER,
                        price REAL,
                        status TEXT DEFAULT 'available')''')

        # Добавим тестовые книги
        c.execute("INSERT INTO books (title, author, category, year, price) VALUES ('Мастер и Маргарита', 'М. Булгаков', 'Роман', 1967, 500)")
        c.execute("INSERT INTO books (title, author, category, year, price) VALUES ('Преступление и наказание', 'Ф. Достоевский', 'Роман', 1866, 450)")
        c.execute("INSERT INTO books (title, author, category, year, price) VALUES ('Война и мир', 'Л. Толстой', 'Роман', 1869, 700)")

        conn.commit()
        conn.close()

# Главная страница
@app.route('/')
def index():
    conn = sqlite3.connect('books.db')
    c = conn.cursor()
    c.execute("SELECT * FROM books")
    books = c.fetchall()
    conn.close()
    return render_template('index.html', books=books)

# Регистрация
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('books.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except:
            conn.close()
            return "Пользователь уже существует!"
    return render_template('register.html')

# Вход
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('books.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()

        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['role'] = user[3]
            return redirect(url_for('index'))
        else:
            return "Неверный логин или пароль!"
    return render_template('login.html')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
