import tkinter as tk
from tkinter import messagebox, filedialog, Frame
import sqlite3
import hashlib
import datetime
import csv


class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path  # Путь к базе данных
        self.create_tables()  # Создание таблиц
        self.alter_table()  # Изменение таблиц

    def create_tables(self):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            # Создание таблицы пользователей, если она не существует
            c.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT,
                    role TEXT DEFAULT 'user'
                )''')
            # Создание таблицы проектов, если она не существует
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
            conn.commit()  # Сохранение изменений

    def alter_table(self):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            # Попытка добавления столбца role в таблицу users
            try:
                c.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
                conn.commit()
            except sqlite3.OperationalError:
                pass

            # Попытка добавления столбца file_path в таблицу projects
            try:
                c.execute("ALTER TABLE projects ADD COLUMN file_path TEXT")
                conn.commit()
            except sqlite3.OperationalError:
                pass

    def execute_query(self, query, params=(), fetch=False):
        # Выполнение SQL-запроса
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute(query, params)
            if fetch:
                return c.fetchall()  # Возвращение результатов запроса
            conn.commit()  # Сохранение изменений


class AuthenticationManager(DatabaseManager):
    def hash_password(self, password):
        # Хеширование пароля с использованием SHA-256
        return hashlib.sha256(password.encode()).hexdigest()

    def register_user(self, username, password, role='user'):
        hashed_password = self.hash_password(password)  # Хеширование пароля
        try:
            self.execute_query(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                (username, hashed_password, role)
            )
            messagebox.showinfo("Успех", "Пользователь успешно зарегистрирован.")
        except sqlite3.IntegrityError:
            messagebox.showerror("Ошибка", "Пользователь с таким именем уже существует.")

    def authenticate(self, username, password):
        hashed_password = self.hash_password(password)  # Хеширование пароля
        user = self.execute_query(
            "SELECT id, username, role FROM users WHERE username=? AND password=?",
            (username, hashed_password),
            fetch=True
        )
        if user:
            return user[0]  # Возвращение данных пользователя
        messagebox.showerror("Ошибка", "Неправильный логин или пароль")
        return None

    def delete_user(self, user_id):
        # Удаление пользователя и связанных проектов
        self.execute_query("DELETE FROM users WHERE id=?", (user_id,))
        self.execute_query("DELETE FROM projects WHERE user_id=?", (user_id,))


class Application(tk.Tk):
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager  # Менеджер базы данных
        self.title("TaskBoard - Вход и регистрация")
        self.geometry("600x400")
        self.center_window(600, 400)  # Центрирование окна
        self.create_widgets()  # Создание виджетов
        self.update_time()  # Обновление времени

    def center_window(self, width, height):
        # Центрирование окна на экране
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

    def create_widgets(self):
        frame = tk.Frame(self)
        frame.pack(expand=True)

        self.current_time_label = tk.Label(frame, text="", font=("Helvetica", 14))
        self.current_time_label.grid(row=0, column=0, columnspan=2, pady=10)

        tk.Label(frame, text="Логин:", font=("Helvetica", 14)).grid(row=1, column=0, sticky=tk.E, padx=10, pady=10)
        self.entry_username = tk.Entry(frame, font=("Helvetica", 14))
        self.entry_username.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=10, pady=10)

        tk.Label(frame, text="Пароль:", font=("Helvetica", 14)).grid(row=2, column=0, sticky=tk.E, padx=10, pady=10)
        self.entry_password = tk.Entry(frame, show="*", font=("Helvetica", 14))
        self.entry_password.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=10, pady=10)

        tk.Button(frame, text="Вход", command=self.login, font=("Helvetica", 14)).grid(row=3, column=0, columnspan=2, pady=10)
        tk.Button(frame, text="Регистрация", command=self.open_register_window, font=("Helvetica", 14)).grid(row=4, column=0, columnspan=2, pady=10)
        tk.Button(frame, text="Список пользователей", command=self.show_users, font=("Helvetica", 14)).grid(row=5, column=0, columnspan=2, pady=10)
        tk.Button(frame, text="Выход", command=self.quit_application, font=("Helvetica", 14)).grid(row=6, column=0, columnspan=2, pady=10)

        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)

    def update_time(self):
        # Обновление текущего времени на метке
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.current_time_label.config(text=now)
        self.after(1000, self.update_time)

    def login(self):
        # Обработка входа пользователя
        username = self.entry_username.get()
        password = self.entry_password.get()
        user = self.db_manager.authenticate(username, password)
        if user:
            user_id, username, role = user
            self.destroy()
            MainWindow(self.db_manager, user_id, username, role)

    def open_register_window(self):
        # Открытие окна регистрации
        RegisterWindow(self.db_manager)

    def show_users(self):
        # Показ списка зарегистрированных пользователей
        users = self.db_manager.execute_query("SELECT username FROM users", fetch=True)
        users_window = tk.Toplevel(self)
        users_window.title("Список пользователей")
        users_window.geometry("300x200")
        self.center_window_in_window(users_window, 300, 200)
        for user in users:
            user_label = tk.Label(users_window, text=f"Пользователь: {user[0]}", font=("Helvetica", 12))
            user_label.pack(anchor='w', padx=10, pady=5)

    def center_window_in_window(self, window, width, height):
        # Центрирование дочернего окна
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        window.geometry(f"{width}x{height}+{x}+{y}")

    def quit_application(self):
        # Завершение работы приложения
        self.destroy()


class RegisterWindow(tk.Toplevel):
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager  # Менеджер базы данных
        self.title("Регистрация")
        self.geometry("400x300")
        self.center_window(400, 300)  # Центрирование окна
        self.create_widgets()  # Создание виджетов

    def center_window(self, width, height):
        # Центрирование окна на экране
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

    def create_widgets(self):
        tk.Label(self, text="Логин:", font=("Helvetica", 14)).grid(row=0, column=0, padx=10, pady=10, sticky=tk.E)
        self.entry_username = tk.Entry(self, font=("Helvetica", 14))
        self.entry_username.grid(row=0, column=1, padx=10, pady=10, sticky=tk.W)

        tk.Label(self, text="Пароль:", font=("Helvetica", 14)).grid(row=1, column=0, padx=10, pady=10, sticky=tk.E)
        self.entry_password = tk.Entry(self, show="*", font=("Helvetica", 14))
        self.entry_password.grid(row=1, column=1, padx=10, pady=10, sticky=tk.W)

        tk.Label(self, text="Подтвердите пароль:", font=("Helvetica", 14)).grid(row=2, column=0, padx=10, pady=10, sticky=tk.E)
        self.entry_confirm_password = tk.Entry(self, show="*", font=("Helvetica", 14))
        self.entry_confirm_password.grid(row=2, column=1, padx=10, pady=10, sticky=tk.W)

        tk.Label(self, text="Роль (admin или user):", font=("Helvetica", 14)).grid(row=3, column=0, padx=10, pady=10, sticky=tk.E)
        self.entry_role = tk.Entry(self, font=("Helvetica", 14))
        self.entry_role.grid(row=3, column=1, padx=10, pady=10, sticky=tk.W)

        tk.Button(self, text="Зарегистрироваться", command=self.register, font=("Helvetica", 14)).grid(row=4, column=0, columnspan=2, pady=10)

    def register(self):
        # Обработка регистрации пользователя
        username = self.entry_username.get()
        password = self.entry_password.get()
        confirm_password = self.entry_confirm_password.get()
        role = self.entry_role.get()

        if not username or not password or not confirm_password or not role:
            messagebox.showerror("Ошибка", "Все поля обязательны для заполнения")
            return

        if password != confirm_password:
            messagebox.showerror("Ошибка", "Пароли не совпадают")
            return

        if role not in ['admin', 'user']:
            messagebox.showerror("Ошибка", "Роль должна быть 'admin' или 'user'")
            return

        self.db_manager.register_user(username, password, role)
        self.destroy()


class MainWindow(tk.Tk):
    def __init__(self, db_manager, user_id, username, role):
        super().__init__()
        self.db_manager = db_manager  # Менеджер базы данных
        self.user_id = user_id  # Идентификатор пользователя
        self.username = username  # Имя пользователя
        self.role = role  # Роль пользователя
        self.title("TaskBoard - Личный кабинет")
        self.geometry("800x600")
        self.center_window(800, 600)  # Центрирование окна
        self.create_widgets()  # Создание виджетов
        self.update_time()  # Обновление времени

    def center_window(self, width, height):
        # Центрирование окна на экране
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

    def create_widgets(self):
        frame = tk.Frame(self)
        frame.pack(expand=True)

        greeting = f"Добро пожаловать, {self.username}!"
        self.greeting_label = tk.Label(frame, text=greeting, font=("Helvetica", 16))
        self.greeting_label.grid(row=0, column=0, columnspan=2, pady=10)

        self.current_time_label = tk.Label(frame, text="", font=("Helvetica", 14))
        self.current_time_label.grid(row=1, column=0, columnspan=2, pady=10)

        tk.Button(frame, text="Проекты", command=self.open_projects_window, font=("Helvetica", 14)).grid(row=2, column=0, columnspan=2, pady=10)
        tk.Button(frame, text="Удалить свой аккаунт", command=self.delete_own_account, font=("Helvetica", 14)).grid(row=3, column=0, columnspan=2, pady=10)
        tk.Button(frame, text="Экспортировать проекты в CSV", command=self.export_projects_to_csv, font=("Helvetica", 14)).grid(row=4, column=0, columnspan=2, pady=10)

        if self.role == 'admin':
            tk.Button(frame, text="Управление пользователями", command=self.manage_users, font=("Helvetica", 14)).grid(row=5, column=0, columnspan=2, pady=10)

        tk.Button(frame, text="Выход", command=self.logout, font=("Helvetica", 14)).grid(row=6, column=0, columnspan=2, pady=10)

        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)

    def update_time(self):
        # Обновление текущего времени на метке
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.current_time_label.config(text=now)
        self.after(1000, self.update_time)

    def open_projects_window(self):
        # Открытие окна проектов
        self.withdraw()
        ProjectsWindow(self.db_manager, self.user_id, self)

    def delete_own_account(self):
        # Удаление собственного аккаунта
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить свой аккаунт?"):
            self.db_manager.delete_user(self.user_id)
            messagebox.showinfo("Успех", "Ваш аккаунт успешно удален.")
            self.logout()

    def export_projects_to_csv(self):
        # Экспорт проектов в CSV файл
        projects = self.db_manager.execute_query(
            "SELECT name, type, start_date, end_date, completed, file_path FROM projects WHERE user_id=?",
            (self.user_id,), fetch=True
        )

        if not projects:
            messagebox.showinfo("Информация", "Нет проектов для экспорта")
            return

        with open('projects.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Название", "Тип", "Дата начала", "Дата окончания", "Завершен", "Путь к файлу"])
            writer.writerows(projects)

        messagebox.showinfo("Успех", "Проекты успешно экспортированы в projects.csv")

    def logout(self):
        # Выход из аккаунта и возврат на экран входа
        self.destroy()
        app = Application(self.db_manager)
        app.mainloop()

    def manage_users(self):
        # Открытие окна управления пользователями (для администраторов)
        ManageUsersWindow(self.db_manager, self)


class ManageUsersWindow(tk.Toplevel):
    def __init__(self, db_manager, parent):
        super().__init__()
        self.db_manager = db_manager  # Менеджер базы данных
        self.parent = parent  # Родительское окно
        self.title("Управление пользователями")
        self.geometry("400x300")
        self.center_window(400, 300)  # Центрирование окна
        self.create_widgets()  # Создание виджетов

    def center_window(self, width, height):
        # Центрирование окна на экране
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

    def create_widgets(self):
        # Создание виджетов для управления пользователями
        users = self.db_manager.execute_query("SELECT id, username, role FROM users", fetch=True)
        for i, user in enumerate(users):
            user_id, username, role = user
            tk.Label(self, text=f"{username} ({role})", font=("Helvetica", 14)).grid(row=i, column=0, padx=10, pady=10)
            tk.Button(self, text="Удалить", command=lambda u=user_id: self.delete_user(u), font=("Helvetica", 14)).grid(row=i, column=1, padx=10, pady=10)

    def delete_user(self, user_id):
        # Удаление пользователя и обновление списка пользователей
        self.db_manager.delete_user(user_id)
        self.destroy()
        self.__init__(self.db_manager, self.parent)


class ProjectsWindow(tk.Toplevel):
    def __init__(self, db_manager, user_id, parent):
        super().__init__()
        self.db_manager = db_manager  # Менеджер базы данных
        self.user_id = user_id  # Идентификатор пользователя
        self.parent = parent  # Родительское окно
        self.title("TaskBoard - Проекты")
        self.geometry("800x600")
        self.center_window(800, 600)  # Центрирование окна
        self.create_widgets()  # Создание виджетов
        self.update_time()  # Обновление времени

    def center_window(self, width, height):
        # Центрирование окна на экране
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

    def create_widgets(self):
        frame = tk.Frame(self)
        frame.pack(expand=True)

        self.current_time_label = tk.Label(frame, text="", font=("Helvetica", 14))
        self.current_time_label.grid(row=0, column=0, columnspan=3, pady=10)

        tk.Label(frame, text="Название проекта:", font=("Helvetica", 14)).grid(row=1, column=0, sticky=tk.E, padx=10, pady=10)
        self.entry_project_name = tk.Entry(frame, font=("Helvetica", 14))
        self.entry_project_name.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), padx=10, pady=10)

        tk.Label(frame, text="Тип проекта:", font=("Helvetica", 14)).grid(row=2, column=0, sticky=tk.E, padx=10, pady=10)
        self.entry_project_type = tk.Entry(frame, font=("Helvetica", 14))
        self.entry_project_type.grid(row=2, column=1, columnspan=2, sticky=(tk.W, tk.E), padx=10, pady=10)

        tk.Label(frame, text="Дата начала:", font=("Helvetica", 14)).grid(row=3, column=0, sticky=tk.E, padx=10, pady=10)
        self.entry_start_date = tk.Entry(frame, font=("Helvetica", 14))
        self.entry_start_date.grid(row=3, column=1, columnspan=2, sticky=(tk.W, tk.E), padx=10, pady=10)

        tk.Label(frame, text="Дата окончания:", font=("Helvetica", 14)).grid(row=4, column=0, sticky=tk.E, padx=10, pady=10)
        self.entry_end_date = tk.Entry(frame, font=("Helvetica", 14))
        self.entry_end_date.grid(row=4, column=1, columnspan=2, sticky=(tk.W, tk.E), padx=10, pady=10)

        tk.Label(frame, text="Прикрепленный файл:", font=("Helvetica", 14)).grid(row=5, column=0, sticky=tk.E, padx=10, pady=10)
        self.entry_file_path = tk.Entry(frame, font=("Helvetica", 14))
        self.entry_file_path.grid(row=5, column=1, sticky=(tk.W, tk.E), padx=10, pady=10)
        tk.Button(frame, text="Выбрать файл", command=self.select_file, font=("Helvetica", 14)).grid(row=5, column=2, sticky=(tk.W, tk.E), padx=10, pady=10)

        tk.Button(frame, text="Добавить проект", command=self.add_project, font=("Helvetica", 14)).grid(row=6, column=0, pady=10)
        tk.Button(frame, text="Выход", command=self.close_window, font=("Helvetica", 14)).grid(row=6, column=2, padx=10, pady=10)

        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_columnconfigure(2, weight=1)

    def update_time(self):
        # Обновление текущего времени на метке
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.current_time_label.config(text=now)
        self.after(1000, self.update_time)

    def select_file(self):
        # Открытие диалогового окна для выбора файла
        file_path = filedialog.askopenfilename()
        if file_path:
            self.entry_file_path.delete(0, tk.END)
            self.entry_file_path.insert(0, file_path)

    def add_project(self):
        # Добавление нового проекта в базу данных
        project_name = self.entry_project_name.get()
        project_type = self.entry_project_type.get()
        start_date = self.entry_start_date.get()
        end_date = self.entry_end_date.get()
        file_path = self.entry_file_path.get()
        self.db_manager.execute_query(
            "INSERT INTO projects (name, type, start_date, end_date, file_path, user_id) VALUES (?, ?, ?, ?, ?, ?)",
            (project_name, project_type, start_date, end_date, file_path, self.user_id)
        )
        self.display_projects_window()

    def display_projects_window(self):
        # Показать окно со всеми проектами
        self.withdraw()
        DisplayProjectsWindow(self.db_manager, self.user_id, self)

    def close_window(self):
        # Закрытие текущего окна и возврат к родительскому окну
        self.destroy()
        self.parent.deiconify()


class DisplayProjectsWindow(tk.Toplevel):
    def __init__(self, db_manager, user_id, parent):
        super().__init__()
        self.db_manager = db_manager  # Менеджер базы данных
        self.user_id = user_id  # Идентификатор пользователя
        self.parent = parent  # Родительское окно
        self.title("TaskBoard - Все проекты")
        self.geometry("800x600")
        self.center_window(800, 600)  # Центрирование окна
        self.create_widgets()  # Создание виджетов
        self.update_time()  # Обновление времени

    def center_window(self, width, height):
        # Центрирование окна на экране
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

    def create_widgets(self):
        frame = tk.Frame(self)
        frame.pack(expand=True, fill=tk.BOTH)

        self.current_time_label = tk.Label(frame, text="", font=("Helvetica", 14))
        self.current_time_label.grid(row=0, column=0, columnspan=3, pady=10)

        self.project_canvas = tk.Canvas(frame)
        self.project_canvas.grid(row=1, column=0, columnspan=3, sticky='nsew')
        self.scrollbar = tk.Scrollbar(frame, orient='vertical', command=self.project_canvas.yview)
        self.scrollbar.grid(row=1, column=3, sticky='ns')
        self.project_canvas.configure(yscrollcommand=self.scrollbar.set)
        self.project_frame = tk.Frame(self.project_canvas)
        self.project_canvas.create_window((0, 0), window=self.project_frame, anchor='nw')
        self.project_frame.bind("<Configure>", lambda e: self.project_canvas.configure(scrollregion=self.project_canvas.bbox("all")))
        self.display_projects()

        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_columnconfigure(2, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        tk.Button(frame, text="Закрыть", command=self.close_window, font=("Helvetica", 14)).grid(row=2, column=0, columnspan=3, pady=10)

    def update_time(self):
        # Обновление текущего времени на метке
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.current_time_label.config(text=now)
        self.after(1000, self.update_time)

    def display_projects(self):
        # Отображение проектов в окне
        for widget in self.project_frame.winfo_children():
            widget.destroy()
        projects = self.db_manager.execute_query(
            "SELECT id, name, type, start_date, end_date, completed, file_path FROM projects WHERE user_id=?",
            (self.user_id,), fetch=True)
        for project in projects:
            project_frame = Frame(self.project_frame, padx=10, pady=5, relief=tk.RAISED, bd=2)
            project_frame.pack(fill='x', expand=True, pady=5)
            text = f"{project[1]} - {project[2]} - {project[3]} to {project[4]}"
            label = tk.Label(project_frame, text=text, font=("Helvetica", 12, "overstrike" if project[5] else "normal"))
            label.pack(anchor='w')

            if project[6]:
                file_label = tk.Label(project_frame, text=f"Файл: {project[6]}", font=("Helvetica", 12))
                file_label.pack(anchor='w')

            chk_state = tk.BooleanVar(value=project[5])
            chk = tk.Checkbutton(project_frame, variable=chk_state, command=lambda p=project[0], s=chk_state: self.toggle_project(p, s))
            chk.pack(anchor='w')

            btn_delete = tk.Button(project_frame, text="Удалить", command=lambda p=project[0]: self.delete_project(p), font=("Helvetica", 12))
            btn_delete.pack(anchor='w')

            project_name = project[1]
            try:
                project_time = project[4].split('.')
                day = int(project_time[0])
                month = int(project_time[1])
                year = int(project_time[2])
                now = datetime.datetime.now()
                DAYS_BEFORE = 2
                if not project[5]:
                    if now.year == year and now.month == month:
                        if now.day > day - DAYS_BEFORE:
                            messagebox.showerror("Важно", "До сдачи проекта " + project_name + " осталось менее " + str(DAYS_BEFORE) + " суток")
                        elif now.day == day:
                            messagebox.showerror("Важно", "Сегодня день сдачи проекта " + project_name)
                        elif now.day > day:
                            messagebox.showerror("Важно", "Проект " + project_name + " просрочен!")
                    elif now.year > year or (now.year == year and now.month > month):
                        messagebox.showerror("Важно", "Проект " + project_name + " просрочен!")
            except (ValueError, IndexError):
                pass

    def toggle_project(self, project_id, state):
        # Переключение состояния завершенности проекта
        self.db_manager.execute_query("UPDATE projects SET completed = ? WHERE id = ?", (state.get(), project_id))
        self.display_projects()

    def delete_project(self, project_id):
        # Удаление проекта из базы данных
        self.db_manager.execute_query("DELETE FROM projects WHERE id = ?", (project_id,))
        self.display_projects()

    def close_window(self):
        # Закрытие текущего окна и возврат к родительскому окну
        self.destroy()
        self.parent.deiconify()


if __name__ == "__main__":
    db_path = 'users.db'  # Путь к файлу базы данных
    db_manager = AuthenticationManager(db_path)  # Создание экземпляра менеджера аутентификации
    app = Application(db_manager)  # Создание экземпляра приложения
    app.mainloop()  # Запуск главного цикла приложения