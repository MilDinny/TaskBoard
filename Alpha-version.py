import tkinter as tk
from tkinter import messagebox
import sqlite3
import hashlib
import os

# Удаление существующей базы данных, если она есть
db_path = 'users.db'
if os.path.exists(db_path):
    os.remove(db_path)


# Создание базы данных и таблиц
def create_tables():
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT
            )''')
        c.execute('''
            CREATE TABLE projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                type TEXT,
                start_date TEXT,
                end_date TEXT,
                completed INTEGER DEFAULT 0,
                user_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )''')


# Хеширование пароля
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# Регистрация нового пользователя
def register(username, password):
    try:
        with sqlite3.connect(db_path) as conn:
            c = conn.cursor()
            hashed_password = hash_password(password)
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        messagebox.showinfo("Успех", "Пользователь успешно зарегистрирован.")
    except sqlite3.IntegrityError:
        messagebox.showerror("Ошибка", "Пользователь с таким именем уже существует.")


# Аутентификация пользователя
def authenticate(username, password):
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        hashed_password = hash_password(password)
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hashed_password))
        return c.fetchone()


# Получение проектов пользователя с дополнительной информацией
def get_user_projects(user_id):
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute("SELECT id, name, type, start_date, end_date, completed FROM projects WHERE user_id=?", (user_id,))
        return c.fetchall()


# Отмечаем проект как завершенный
def mark_project_as_completed(project_id, label, var):
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        new_status = 1 if var.get() else 0
        c.execute("UPDATE projects SET completed = ? WHERE id = ?", (new_status, project_id))
        conn.commit()
        # Обновление стиля текста в зависимости от статуса
        if var.get():
            label.config(font=("Arial", 10, "overstrike"))
        else:
            label.config(font=("Arial", 10, "normal"))


# Функции GUI
def open_main_window(user_id):
    def add_project():
        project_name = entry_project_name.get()
        project_type = entry_project_type.get()
        start_date = entry_start_date.get()
        end_date = entry_end_date.get()
        with sqlite3.connect(db_path) as conn:
            c = conn.cursor()
            c.execute("INSERT INTO projects (name, type, start_date, end_date, user_id) VALUES (?, ?, ?, ?, ?)",
                      (project_name, project_type, start_date, end_date, user_id))
        messagebox.showinfo("Успех", "Проект успешно добавлен.")
        main_window.destroy()
        open_main_window(user_id)

    main_window = tk.Tk()
    main_window.title("Главное окно")

    tk.Label(main_window, text="Название проекта:").grid(row=0, column=0)
    entry_project_name = tk.Entry(main_window)
    entry_project_name.grid(row=0, column=1)

    tk.Label(main_window, text="Тип проекта:").grid(row=1, column=0)
    entry_project_type = tk.Entry(main_window)
    entry_project_type.grid(row=1, column=1)

    tk.Label(main_window, text="Дата начала:").grid(row=2, column=0)
    entry_start_date = tk.Entry(main_window)
    entry_start_date.grid(row=2, column=1)

    tk.Label(main_window, text="Дата окончания:").grid(row=3, column=0)
    entry_end_date = tk.Entry(main_window)
    entry_end_date.grid(row=3, column=1)

    tk.Button(main_window, text="Добавить проект", command=add_project).grid(row=4, column=0, columnspan=2)

    frame = tk.Frame(main_window)
    frame.grid(row=5, column=0, columnspan=2)

    projects = get_user_projects(user_id)
    for project in projects:
        chk_state = tk.BooleanVar()
        chk_state.set(project[5])  # Установка состояния чекбокса в зависимости от статуса выполнения
        label_text = f"{project[1]} - {project[2]} - Начало: {project[3]} Окончание: {project[4]}"
        label = tk.Label(frame, text=label_text, font=("Arial", 10, "overstrike" if project[5] else "normal"))
        label.pack(anchor='w')
        chk = tk.Checkbutton(frame, var=chk_state, onvalue=True, offvalue=False,
                             command=lambda p=project[0], l=label, var=chk_state: mark_project_as_completed(p, l, var))
        chk.pack(anchor='w')

    main_window.mainloop()


def login():
    username = entry_username.get()
    password = entry_password.get()
    user = authenticate(username, password)
    if user:
        messagebox.showinfo("Успех", f"Аутентификация успешна. Добро пожаловать, {username}!")
        login_window.destroy()
        open_main_window(user[0])
    else:
        messagebox.showerror("Ошибка", "Неправильный логин или пароль")


create_tables()

login_window = tk.Tk()
login_window.title("Вход и регистрация")

tk.Label(login_window, text="Логин:").grid(row=0, column=0)
entry_username = tk.Entry(login_window)
entry_username.grid(row=0, column=1)

tk.Label(login_window, text="Пароль:").grid(row=1, column=0)
entry_password = tk.Entry(login_window, show="*")
entry_password.grid(row=1, column=1)

tk.Button(login_window, text="Вход", command=login).grid(row=2, column=0, columnspan=2)
tk.Button(login_window, text="Регистрация", command=lambda: register(entry_username.get(), entry_password.get())).grid(
    row=3, column=0, columnspan=2)

login_window.mainloop()