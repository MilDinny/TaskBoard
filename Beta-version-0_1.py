#Переход к ООП и PEP-8

import tkinter as tk
from tkinter import messagebox, filedialog
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import sqlite3
import hashlib
import datetime


class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.create_tables()
        self.alter_table()

    def create_tables(self):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT
                )''')
            c.execute('''
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    type TEXT,
                    start_date TEXT,
                    end_date TEXT,
                    completed INTEGER DEFAULT 0,
                    user_id INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )''')
            conn.commit()

    def alter_table(self):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            try:
                c.execute("ALTER TABLE projects ADD COLUMN file_path TEXT")
                conn.commit()
            except sqlite3.OperationalError:
                # Столбец уже существует
                pass

    def execute_query(self, query, params=(), fetch=False):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute(query, params)
            if fetch:
                return c.fetchall()
            conn.commit()


class AuthenticationManager(DatabaseManager):
    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def register_user(self, username, password):
        hashed_password = self.hash_password(password)
        try:
            self.execute_query("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
            messagebox.showinfo("Успех", "Пользователь успешно зарегистрирован.")
        except sqlite3.IntegrityError:
            messagebox.showerror("Ошибка", "Пользователь с таким именем уже существует.")

    def authenticate(self, username, password):
        hashed_password = self.hash_password(password)
        user = self.execute_query("SELECT * FROM users WHERE username=? AND password=?", (username, hashed_password),
                                  fetch=True)
        if user:
            return user[0][0]
        messagebox.showerror("Ошибка", "Неправильный логин или пароль")
        return None


class Application(ttk.Window):
    def __init__(self, db_manager):
        super().__init__(themename="superhero")
        self.db_manager = db_manager
        self.title("Вход и регистрация")
        self.create_widgets()

    def create_widgets(self):
        frame = ttk.Frame(self, padding="10 10 10 10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        ttk.Label(frame, text="Логин:").grid(row=0, column=0, sticky=tk.W)
        self.entry_username = ttk.Entry(frame)
        self.entry_username.grid(row=0, column=1, sticky=(tk.W, tk.E))

        ttk.Label(frame, text="Пароль:").grid(row=1, column=0, sticky=tk.W)
        self.entry_password = ttk.Entry(frame, show="*")
        self.entry_password.grid(row=1, column=1, sticky=(tk.W, tk.E))

        ttk.Button(frame, text="Вход", command=self.login, bootstyle=SUCCESS).grid(row=2, column=0, columnspan=2,
                                                                                   pady=5)
        ttk.Button(frame, text="Регистрация", command=self.register, bootstyle=PRIMARY).grid(row=3, column=0,
                                                                                             columnspan=2)

        for child in frame.winfo_children():
            child.grid_configure(padx=5, pady=5)

    def login(self):
        username = self.entry_username.get()
        password = self.entry_password.get()
        user_id = self.db_manager.authenticate(username, password)
        if user_id:
            self.destroy()
            MainWindow(self.db_manager, user_id).mainloop()

    def register(self):
        username = self.entry_username.get()
        password = self.entry_password.get()
        self.db_manager.register_user(username, password)


class MainWindow(ttk.Window):
    def __init__(self, db_manager, user_id):
        super().__init__(themename="superhero")
        self.db_manager = db_manager
        self.user_id = user_id
        self.title("Главное окно")
        self.create_widgets()

    def create_widgets(self):
        frame = ttk.Frame(self, padding="10 10 10 10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        ttk.Label(frame, text="Название проекта:").grid(row=0, column=0, sticky=tk.W)
        self.entry_project_name = ttk.Entry(frame)
        self.entry_project_name.grid(row=0, column=1, sticky=(tk.W, tk.E))

        ttk.Label(frame, text="Тип проекта:").grid(row=1, column=0, sticky=tk.W)
        self.entry_project_type = ttk.Entry(frame)
        self.entry_project_type.grid(row=1, column=1, sticky=(tk.W, tk.E))

        ttk.Label(frame, text="Дата начала:").grid(row=2, column=0, sticky=tk.W)
        self.entry_start_date = ttk.Entry(frame)
        self.entry_start_date.grid(row=2, column=1, sticky=(tk.W, tk.E))

        ttk.Label(frame, text="Дата окончания:").grid(row=3, column=0, sticky=tk.W)
        self.entry_end_date = ttk.Entry(frame)
        self.entry_end_date.grid(row=3, column=1, sticky=(tk.W, tk.E))

        ttk.Label(frame, text="Прикрепленный файл:").grid(row=4, column=0, sticky=tk.W)
        self.entry_file_path = ttk.Entry(frame)
        self.entry_file_path.grid(row=4, column=1, sticky=(tk.W, tk.E))
        ttk.Button(frame, text="Выбрать файл", command=self.select_file, bootstyle=INFO).grid(row=4, column=2,
                                                                                              sticky=(tk.W, tk.E))

        ttk.Button(frame, text="Добавить проект", command=self.add_project, bootstyle=SUCCESS).grid(row=5, column=0,
                                                                                                    columnspan=3,
                                                                                                    pady=5)

        self.project_frame = ttk.Frame(frame)
        self.project_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))

        for child in frame.winfo_children():
            child.grid_configure(padx=5, pady=5)

        self.display_projects()

    def select_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.entry_file_path.delete(0, tk.END)
            self.entry_file_path.insert(0, file_path)

    def add_project(self):
        project_name = self.entry_project_name.get()
        project_type = self.entry_project_type.get()
        start_date = self.entry_start_date.get()
        end_date = self.entry_end_date.get()
        file_path = self.entry_file_path.get()
        self.db_manager.execute_query(
            "INSERT INTO projects (name, type, start_date, end_date, file_path, user_id) VALUES (?, ?, ?, ?, ?, ?)",
            (project_name, project_type, start_date, end_date, file_path, self.user_id)
        )
        self.display_projects()

    def display_projects(self):
        for widget in self.project_frame.winfo_children():
            widget.destroy()
        projects = self.db_manager.execute_query(
            "SELECT id, name, type, start_date, end_date, completed, file_path FROM projects WHERE user_id=?",
            (self.user_id,), fetch=True)
        for project in projects:
            text = f"{project[1]} - {project[2]} - {project[3]} to {project[4]}"
            label = ttk.Label(self.project_frame, text=text,
                              font=("Helvetica", 10, "overstrike" if project[5] else "normal"))
            label.pack(anchor='w')
            if project[6]:
                file_label = ttk.Label(self.project_frame, text=f"Файл: {project[6]}")
                file_label.pack(anchor='w')
            chk_state = tk.BooleanVar(value=project[5])
            chk = ttk.Checkbutton(self.project_frame, variable=chk_state,
                                  command=lambda p=project[0], s=chk_state: self.toggle_project(p, s))
            chk.pack(anchor='w')

            project_name = project[1]
            project_time = project[4].split('.')
            day = int(project_time[0])
            month = int(project_time[1])
            year = int(project_time[2])
            now = datetime.datetime.now()
            DAYS_BEFORE = 2
            if not project[5]:
                if now.year == year and now.month == month:
                    if now.day > day - DAYS_BEFORE:
                        messagebox.showerror("Важно", "До сдачи проекта " + project_name + " осталось менее " + str(
                            DAYS_BEFORE) + " суток")
                    elif now.day == day:
                        messagebox.showerror("Важно", "Сегодня день сдачи проекта " + project_name)
                    elif now.day > day:
                        messagebox.showerror("Важно", "Проект " + project_name + " просрочен!")
                elif now.year > year or (now.year == year and now.month > month):
                    messagebox.showerror("Важно", "Проект " + project_name + " просрочен!")

    def toggle_project(self, project_id, state):
        self.db_manager.execute_query("UPDATE projects SET completed = ? WHERE id = ?", (state.get(), project_id))
        self.display_projects()


if __name__ == "__main__":
    db_path = 'users.db'
    db_manager = AuthenticationManager(db_path)
    app = Application(db_manager)
    app.mainloop()