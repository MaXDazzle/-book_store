from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os
from datetime import datetime, timedelta

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

        # Таблица заказов (покупка/аренда)
        c.execute('''CREATE TABLE orders (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        book_id INTEGER,
                        type TEXT,
                        end_date TEXT)''')

        # Добавим тестовые книги
        books_data = [
            ('Мастер и Маргарита', 'М. Булгаков', 'Роман', 1967, 500),
            ('Преступление и наказание', 'Ф. Достоевский', 'Роман', 1866, 450),
            ('Война и мир', 'Л. Толстой', 'Роман', 1869, 700)
        ]
        c.executemany("INSERT INTO books (title, author, category, year, price) VALUES (?, ?, ?, ?, ?)", books_data)

        # Создаём администратора
        c.execute("INSERT INTO users (username, password, role) VALUES ('admin', 'admin', 'admin')")

        conn.commit()
        conn.close()

# Главная страница с фильтрацией
@app.route('/')
def index():
    sort = request.args.get('sort')
    conn = sqlite3.connect('books.db')
    c = conn.cursor()
    query = "SELECT * FROM books"
    if sort == "author":
        query += " ORDER BY author"
    elif sort == "category":
        query += " ORDER BY category"
    elif sort == "year":
        query += " ORDER BY year"
    c.execute(query)
    books = c.fetchall()
    conn.close()
    return render_template('index.html', books=books)

# Страница книги
@app.route('/book/<int:book_id>')
def book(book_id):
    conn = sqlite3.connect('books.db')
    c = conn.cursor()
    c.execute("SELECT * FROM books WHERE id=?", (book_id,))
    book = c.fetchone()
    conn.close()
    return render_template('book.html', book=book)

# Аренда или покупка книги
@app.route('/order/<int:book_id>', methods=['POST'])
def order(book_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    order_type = request.form['type']
    end_date = None
    if order_type != "buy":
        period = int(request.form['period'])
        end_date = (datetime.now() + timedelta(days=period)).strftime("%Y-%m-%d")

    conn = sqlite3.connect('books.db')
    c = conn.cursor()
    c.execute("INSERT INTO orders (user_id, book_id, type, end_date) VALUES (?, ?, ?, ?)",
              (session['user_id'], book_id, order_type, end_date))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

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

# Выход
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# Админ-панель
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'role' not in session or session['role'] != 'admin':
        return "Доступ запрещен"

    conn = sqlite3.connect('books.db')
    c = conn.cursor()

    # Добавление книги
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        category = request.form['category']
        year = int(request.form['year'])
        price = float(request.form['price'])
        c.execute("INSERT INTO books (title, author, category, year, price) VALUES (?, ?, ?, ?, ?)",
                  (title, author, category, year, price))
        conn.commit()

    # Проверка аренды
    today = datetime.now().date()
    c.execute("SELECT orders.id, users.username, books.title, orders.end_date FROM orders "
              "JOIN users ON orders.user_id = users.id "
              "JOIN books ON orders.book_id = books.id "
              "WHERE orders.end_date IS NOT NULL")
    orders = c.fetchall()
    reminders = [o for o in orders if datetime.strptime(o[3], "%Y-%m-%d").date() <= today + timedelta(days=3)]

    # Список книг
    c.execute("SELECT * FROM books")
    books = c.fetchall()
    conn.close()

    return render_template('admin.html', books=books, reminders=reminders)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
