#Увеличены окна приложения

import tkinter as tk
from tkinter import messagebox, filedialog, Menu
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
                    file_path TEXT,
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

    def delete_user(self, user_id):
        self.execute_query("DELETE FROM users WHERE id=?", (user_id,))
        self.execute_query("DELETE FROM projects WHERE user_id=?", (user_id,))


class Application(tk.Tk):
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.title("TaskBoard - Вход и регистрация")
        self.geometry("600x400")
        self.create_widgets()

    def create_widgets(self):
        menu_bar = Menu(self)
        self.config(menu=menu_bar)

        user_menu = Menu(menu_bar, tearoff=0)
        user_menu.add_command(label="Список пользователей", command=self.show_users)
        user_menu.add_command(label="Удалить свой аккаунт", command=self.delete_own_account)
        menu_bar.add_cascade(label="Пользователи", menu=user_menu)

        tk.Label(self, text="Логин:", font=("Helvetica", 14)).grid(row=0, column=0, sticky=tk.W, padx=10, pady=10)
        self.entry_username = tk.Entry(self, font=("Helvetica", 14))
        self.entry_username.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=10, pady=10)

        tk.Label(self, text="Пароль:", font=("Helvetica", 14)).grid(row=1, column=0, sticky=tk.W, padx=10, pady=10)
        self.entry_password = tk.Entry(self, show="*", font=("Helvetica", 14))
        self.entry_password.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=10, pady=10)

        tk.Button(self, text="Вход", command=self.login, font=("Helvetica", 14)).grid(row=2, column=0, columnspan=2,
                                                                                      pady=10)
        tk.Button(self, text="Регистрация", command=self.register, font=("Helvetica", 14)).grid(row=3, column=0,
                                                                                                columnspan=2, pady=10)

    def login(self):
        username = self.entry_username.get()
        password = self.entry_password.get()
        user_id = self.db_manager.authenticate(username, password)
        if user_id:
            self.destroy()
            MainWindow(self.db_manager, user_id)

    def register(self):
        username = self.entry_username.get()
        password = self.entry_password.get()
        self.db_manager.register_user(username, password)

    def show_users(self):
        users = self.db_manager.execute_query("SELECT id, username FROM users", fetch=True)
        users_window = tk.Toplevel(self)
        users_window.title("Список пользователей")
        users_window.geometry("300x200")
        for user in users:
            user_label = tk.Label(users_window, text=f"{user[0]}: {user[1]}", font=("Helvetica", 12))
            user_label.pack(anchor='w', padx=10, pady=5)

    def delete_own_account(self):
        username = self.entry_username.get()
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить свой аккаунт?"):
            user = self.db_manager.execute_query("SELECT id FROM users WHERE username=?", (username,), fetch=True)
            if user:
                user_id = user[0][0]
                self.db_manager.delete_user(user_id)
                messagebox.showinfo("Успех", "Ваш аккаунт успешно удален.")


class MainWindow(tk.Tk):
    def __init__(self, db_manager, user_id):
        super().__init__()
        self.db_manager = db_manager
        self.user_id = user_id
        self.title("TaskBoard - Личный кабинет")
        self.geometry("800x600")
        self.create_widgets()
        self.update_time()

    def create_widgets(self):
        self.current_time_label = tk.Label(self, text="", font=("Helvetica", 14))
        self.current_time_label.grid(row=0, column=0, columnspan=3, pady=10)

        tk.Label(self, text="Название проекта:", font=("Helvetica", 14)).grid(row=1, column=0, sticky=tk.W, padx=10,
                                                                              pady=10)
        self.entry_project_name = tk.Entry(self, font=("Helvetica", 14))
        self.entry_project_name.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), padx=10, pady=10)

        tk.Label(self, text="Тип проекта:", font=("Helvetica", 14)).grid(row=2, column=0, sticky=tk.W, padx=10, pady=10)
        self.entry_project_type = tk.Entry(self, font=("Helvetica", 14))
        self.entry_project_type.grid(row=2, column=1, columnspan=2, sticky=(tk.W, tk.E), padx=10, pady=10)

        tk.Label(self, text="Дата начала:", font=("Helvetica", 14)).grid(row=3, column=0, sticky=tk.W, padx=10, pady=10)
        self.entry_start_date = tk.Entry(self, font=("Helvetica", 14))
        self.entry_start_date.grid(row=3, column=1, columnspan=2, sticky=(tk.W, tk.E), padx=10, pady=10)

        tk.Label(self, text="Дата окончания:", font=("Helvetica", 14)).grid(row=4, column=0, sticky=tk.W, padx=10,
                                                                            pady=10)
        self.entry_end_date = tk.Entry(self, font=("Helvetica", 14))
        self.entry_end_date.grid(row=4, column=1, columnspan=2, sticky=(tk.W, tk.E), padx=10, pady=10)

        tk.Label(self, text="Прикрепленный файл:", font=("Helvetica", 14)).grid(row=5, column=0, sticky=tk.W, padx=10,
                                                                                pady=10)
        self.entry_file_path = tk.Entry(self, font=("Helvetica", 14))
        self.entry_file_path.grid(row=5, column=1, sticky=(tk.W, tk.E), padx=10, pady=10)
        tk.Button(self, text="Выбрать файл", command=self.select_file, font=("Helvetica", 14)).grid(row=5, column=2,
                                                                                                    sticky=(tk.W, tk.E),
                                                                                                    padx=10, pady=10)

        tk.Button(self, text="Добавить проект", command=self.add_project, font=("Helvetica", 14)).grid(row=6, column=0,
                                                                                                       columnspan=3,
                                                                                                       pady=10)
        tk.Button(self, text="Выход", command=self.logout, font=("Helvetica", 14)).grid(row=7, column=0, columnspan=3,
                                                                                        pady=10)

        self.project_frame = tk.Frame(self)
        self.project_frame.grid(row=8, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=10)

        self.display_projects()

        tk.Button(self, text="Список пользователей", command=self.show_users, font=("Helvetica", 14)).grid(row=9,
                                                                                                           column=0,
                                                                                                           columnspan=3,
                                                                                                           pady=10)
        tk.Button(self, text="Удалить свой аккаунт", command=self.delete_own_account, font=("Helvetica", 14)).grid(
            row=10, column=0, columnspan=3, pady=10)

    def update_time(self):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.current_time_label.config(text=now)
        self.after(1000, self.update_time)

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
            label = tk.Label(self.project_frame, text=text,
                             font=("Helvetica", 12, "overstrike" if project[5] else "normal"))
            label.pack(anchor='w', padx=10, pady=5)
            if project[6]:
                file_label = tk.Label(self.project_frame, text=f"Файл: {project[6]}", font=("Helvetica", 12))
                file_label.pack(anchor='w', padx=10, pady=5)
            chk_state = tk.BooleanVar(value=project[5])
            chk = tk.Checkbutton(self.project_frame, variable=chk_state,
                                 command=lambda p=project[0], s=chk_state: self.toggle_project(p, s))
            chk.pack(anchor='w', padx=10, pady=5)

            btn_delete = tk.Button(self.project_frame, text="Удалить",
                                   command=lambda p=project[0]: self.delete_project(p), font=("Helvetica", 12))
            btn_delete.pack(anchor='w', padx=10, pady=5)

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

    def delete_project(self, project_id):
        self.db_manager.execute_query("DELETE FROM projects WHERE id = ?", (project_id,))
        self.display_projects()

    def show_users(self):
        users = self.db_manager.execute_query("SELECT id, username FROM users", fetch=True)
        users_window = tk.Toplevel(self)
        users_window.title("Список пользователей")
        users_window.geometry("400x300")
        for user in users:
            user_label = tk.Label(users_window, text=f"{user[0]}: {user[1]}", font=("Helvetica", 12))
            user_label.pack(anchor='w', padx=10, pady=5)

    def delete_own_account(self):
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить свой аккаунт?"):
            self.db_manager.delete_user(self.user_id)
            messagebox.showinfo("Успех", "Ваш аккаунт успешно удален.")
            self.logout()

    def logout(self):
        self.destroy()
        app = Application(self.db_manager)
        app.mainloop()


if __name__ == "__main__":
    db_path = 'users.db'
    db_manager = AuthenticationManager(db_path)
    app = Application(db_manager)
    app.mainloop()