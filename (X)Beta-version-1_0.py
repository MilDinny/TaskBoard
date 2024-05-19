# Импорт необходимых библиотек
import tkinter as tk
from tkinter import messagebox, filedialog, Menu, Frame
import sqlite3
import hashlib
import datetime

# Класс для управления базой данных
class DatabaseManager:
    def __init__(self, db_path):
        # Инициализация диспетчер баз данных путем к базе данных
        self.db_path = db_path
        # Создание таблицы в базе данных, если они не существуют.
        self.create_tables()
        # Изменение таблицы проектов, чтобы добавить столбец пути к файлу
        self.alter_table()

    def create_tables(self):
        # Создание таблиц в базе данных с помощью SQL-запросов
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
        # Изменение таблицы проектов, чтобы добавить столбец пути к файлу
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            try:
                c.execute("ALTER TABLE projects ADD COLUMN file_path TEXT")
                conn.commit()
            except sqlite3.OperationalError:
                pass

    def execute_query(self, query, params=(), fetch=False):
        # Выполнение SQL-запрос к базе данных
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute(query, params)
            if fetch:
                return c.fetchall()
            conn.commit()

# Класс для управления аутентификацией пользователя
class AuthenticationManager(DatabaseManager):
    def hash_password(self, password):
        # Хэширование пароля с помощью SHA-256
        return hashlib.sha256(password.encode()).hexdigest()

    def register_user(self, username, password):
        # Зарегистрировать нового пользователя
        hashed_password = self.hash_password(password)
        try:
            self.execute_query("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
            messagebox.showinfo("Успех", "Пользователь успешно зарегистрирован.")
        except sqlite3.IntegrityError:
            messagebox.showerror("Ошибка", "Пользователь с таким именем уже существует.")

    def authenticate(self, username, password):
        # Аутентификация пользователя
        hashed_password = self.hash_password(password)
        user = self.execute_query("SELECT * FROM users WHERE username=? AND password=?", (username, hashed_password), fetch=True)
        if user:
            return user[0][0]
        messagebox.showerror("Ошибка", "Неправильный логин или пароль")
        return None

    def delete_user(self, user_id):
        # Удаление пользователя
        self.execute_query("DELETE FROM users WHERE id=?", (user_id,))
        self.execute_query("DELETE FROM projects WHERE user_id=?", (user_id,))

# Класс для главного окна приложения
class Application(tk.Tk):
    def __init__(self, db_manager):
        # Инициализируем окно приложения
        super().__init__()
        self.db_manager = db_manager
        self.title("TaskBoard - Вход и регистрация")
        self.geometry("600x400")
        self.center_window(600, 400)
        self.create_widgets()

    def center_window(self, width, height):
        # окно по центру экрана
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

    def create_widgets(self):
        # Создание виджетов для окна приложения
        tk.Label(self, text="Логин:", font=("Helvetica", 14)).grid(row=0, column=0, sticky=tk.W, padx=10, pady=10)
        self.entry_username = tk.Entry(self, font=("Helvetica", 14))
        self.entry_username.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=10, pady=10)

        tk.Label(self, text="Пароль:", font=("Helvetica", 14)).grid(row=1, column=0, sticky=tk.W, padx=10, pady=10)
        self.entry_password = tk.Entry(self, show="*", font=("Helvetica", 14))
        self.entry_password.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=10, pady=10)

        tk.Button(self, text="Вход", command=self.login, font=("Helvetica", 14)).grid(row=2, column=0, columnspan=2, pady=10)
        tk.Button(self, text="Регистрация", command=self.register, font=("Helvetica", 14)).grid(row=3, column=0, columnspan=2, pady=10)
        tk.Button(self, text="Список пользователей", command=self.show_users, font=("Helvetica", 14)).grid(row=4, column=0, columnspan=2, pady=10)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

    def login(self):
        # Обработка входа пользователя в систему
        username = self.entry_username.get()
        password = self.entry_password.get()
        user_id = self.db_manager.authenticate(username, password)
        if user_id:
            self.destroy()
            MainWindow(self.db_manager, user_id)

    def register(self):
        #обработка регистрации пользователя
        username = self.entry_username.get()
        password = self.entry_password.get()
        self.db_manager.register_user(username, password)

    def show_users(self):
        # Отображение списка пользователей
        users = self.db_manager.execute_query("SELECT username FROM users", fetch=True)
        users_window = tk.Toplevel(self)
        users_window.title("Список пользователей")
        users_window.geometry("300x200")
        self.center_window_in_window(users_window, 300, 200)
        for user in users:
            user_label = tk.Label(users_window, text=f"Пользователь: {user[0]}", font=("Helvetica", 12))
            user_label.pack(anchor='w', padx=10, pady=5)

    def center_window_in_window(self, window, width, height):
        # Центровка окна
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        window.geometry(f"{width}x{height}+{x}+{y}")

# Класс для главного окна приложения после успешного входа в систему
class MainWindow(tk.Tk):
    # Инициализируем главное окно приложения
    def __init__(self, db_manager, user_id):
        super().__init__()
        self.db_manager = db_manager
        self.user_id = user_id
        self.title("TaskBoard - Личный кабинет")
        self.geometry("800x600")
        self.center_window(800, 600)
        self.create_widgets()
        self.update_time()

    def center_window(self, width, height):# окно по центру экрана
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

    def create_widgets(self):# Создание кнопок для главного окна приложения
        self.current_time_label = tk.Label(self, text="", font=("Helvetica", 14))
        self.current_time_label.grid(row=0, column=0, columnspan=3, pady=10)

        tk.Button(self, text="Проекты", command=self.open_projects_window, font=("Helvetica", 14)).grid(row=1, column=0, columnspan=3, pady=10)
        tk.Button(self, text="Удалить свой аккаунт", command=self.delete_own_account, font=("Helvetica", 14)).grid(row=2, column=0, columnspan=3, pady=10)
        tk.Button(self, text="Выход", command=self.logout, font=("Helvetica", 14)).grid(row=3, column=0, columnspan=3, pady=10)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)

    def open_projects_window(self): #открытие окна проектов
        self.withdraw()
        ProjectsWindow(self.db_manager, self.user_id, self)

    def update_time(self):# Определить метод для обновления метки текущего времени
        # Получить текущую дату и время
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Обновить метку текущего времени текущим временем
        self.current_time_label.config(text=now)
        # Запланировать вызов метода update_time снова через 1000 миллисекунд (1 секунду)
        self.after(1000, self.update_time)

    def show_users(self):# метод для отображения списка пользователей
        # Выполнить запрос для получения списка имен пользователей из базы данных
        users = self.db_manager.execute_query("SELECT username FROM users", fetch=True)
         # Создать новое окно для отображения списка пользователей
        users_window = tk.Toplevel(self)
        # Установить заголовок окна
        users_window.title("Список пользователей")
        # Установить геометрию окна
        users_window.geometry("400x300")
        # Центрировать окно на экране
        self.center_window_in_window(users_window, 400, 300)
        # Итерировать по списку пользователей и создать метку для каждого
        for user in users:
            user_label = tk.Label(users_window, text=f"Пользователь: {user[0]}", font=("Helvetica", 12))
            # Упаковать метку в окно
            user_label.pack(anchor='w', padx=10, pady=5)

    def delete_own_account(self):# Определить метод для удаления аккаунта текущего пользователя
        # Спросить у пользователя, уверен ли он, что хочет удалить свой аккаунт
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить свой аккаунт?"):
            # Удалить аккаунт пользователя из базы данных
            self.db_manager.delete_user(self.user_id)
            # Показать сообщение об успехе
            messagebox.showinfo("Успех", "Ваш аккаунт успешно удален.")
            # Выйти из системы
            self.logout()
    #метод выхода из системы
    def logout(self):
        # Уничтожить текущее окно
        self.destroy()
        # Создать новый экземпляр класса Application
        app = Application(self.db_manager)
        # Запустить основной цикл событий нового приложения
        app.mainloop()
# Класс для представления окна проектов
class ProjectsWindow(tk.Toplevel):
    def __init__(self, db_manager, user_id, parent):
        # Инициализировать окно
        super().__init__()
        # Установить менеджер базы данных и идентификатор пользователя
        self.db_manager = db_manager
        self.user_id = user_id
        self.parent = parent
        # Установить заголовок окна
        self.title("TaskBoard - Проекты")
        # Установить геометрию окна
        self.geometry("800x600")
        # Центрировать окно на экране
        self.center_window(800, 600)
        # Создать виджеты для окна
        self.create_widgets()
        # Обновить метку текущего времени
        self.update_time()

 #  метод для центрирования окна на экране
    def center_window(self, width, height):
         # Получить ширину и высоту экрана
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        # Рассчитать координаты x и y для центрирования окна
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        # Установить геометрию окна
        self.geometry(f"{width}x{height}+{x}+{y}")
 #  метод для создания виджетов для окна
    def create_widgets(self):
        # Создать метку для отображения текущего времени
        self.current_time_label = tk.Label(self, text="", font=("Helvetica", 14))
         # Упаковать метку в окно
        self.current_time_label.grid(row=0, column=0, columnspan=3, pady=10)
         # Создать метки и поля ввода для имени проекта, типа, даты начала, даты окончания и пути к файлу
        tk.Label(self, text="Название проекта:", font=("Helvetica", 14)).grid(row=1, column=0, sticky=tk.W, padx=10, pady=10)
        self.entry_project_name = tk.Entry(self, font=("Helvetica", 14))
        self.entry_project_name.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), padx=10, pady=10)

        tk.Label(self, text="Тип проекта:", font=("Helvetica", 14)).grid(row=2, column=0, sticky=tk.W, padx=10, pady=10)
        self.entry_project_type = tk.Entry(self, font=("Helvetica", 14))
        self.entry_project_type.grid(row=2, column=1, columnspan=2, sticky=(tk.W, tk.E), padx=10, pady=10)

        tk.Label(self, text="Дата начала:", font=("Helvetica", 14)).grid(row=3, column=0, sticky=tk.W, padx=10, pady=10)
        self.entry_start_date = tk.Entry(self, font=("Helvetica", 14))
        self.entry_start_date.grid(row=3, column=1, columnspan=2, sticky=(tk.W, tk.E), padx=10, pady=10)

        tk.Label(self, text="Дата окончания:", font=("Helvetica", 14)).grid(row=4, column=0, sticky=tk.W, padx=10, pady=10)
        self.entry_end_date = tk.Entry(self, font=("Helvetica", 14))
        self.entry_end_date.grid(row=4, column=1, columnspan=2, sticky=(tk.W, tk.E), padx=10, pady=10)

        tk.Label(self, text="Прикрепленный файл:", font=("Helvetica", 14)).grid(row=5, column=0, sticky=tk.W, padx=10, pady=10)
        self.entry_file_path = tk.Entry(self, font=("Helvetica", 14))
        self.entry_file_path.grid(row=5, column=1, sticky=(tk.W, tk.E), padx=10, pady=10)
        tk.Button(self, text="Выбрать файл", command=self.select_file, font=("Helvetica", 14)).grid(row=5, column=2, sticky=(tk.W, tk.E), padx=10, pady=10)

        tk.Button(self, text="Добавить проект", command=self.add_project, font=("Helvetica", 14)).grid(row=6, column=0, pady=10)
        tk.Button(self, text="Выход", command=self.close_window, font=("Helvetica", 14)).grid(row=6, column=2, padx=10, pady=10)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
#  метод для обновления метки текущего времени
    def update_time(self):
        # Получить текущую дату и время
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Обновить метку текущего времени текущим временем
        self.current_time_label.config(text=now)
        # Запланировать вызов метода update_time снова через 1000 миллисекунд (1 секунду)
        self.after(1000, self.update_time)
        # метод для выбора файла
    def select_file(self):
        # Открыть диалоговое окно для выбора файла
        file_path = filedialog.askopenfilename()
        # Если файл был выбран, обновить поле ввода пути к файлу
        if file_path:
            self.entry_file_path.delete(0, tk.END)
            self.entry_file_path.insert(0, file_path)
#метод для добавления проекта
    def add_project(self):
        # Получить имя проекта, тип, дату начала, дату окончания и путь к файлу из полей ввода
        project_name = self.entry_project_name.get()
        project_type = self.entry_project_type.get()
        start_date = self.entry_start_date.get()
        end_date = self.entry_end_date.get()
        file_path = self.entry_file_path.get()
        # Выполнить запрос для вставки проекта в базу данных
        self.db_manager.execute_query(
            "INSERT INTO projects (name, type, start_date, end_date, file_path, user_id) VALUES (?, ?, ?, ?, ?, ?)",
            (project_name, project_type, start_date, end_date, file_path, self.user_id)
        )
        # Отобразить окно проектов
        self.display_projects_window()
#  метод для отображения окна проектов
    def display_projects_window(self):
        # Свернуть текущее окно
        self.withdraw()
        # Создать новый экземпляр класса DisplayProjectsWindow
        DisplayProjectsWindow(self.db_manager, self.user_id, self)
#метод для закрытия окна
    def close_window(self):
        # Уничтожить текущее окно
        self.destroy()
        # Восстановить родительское окно
        self.parent.deiconify()
# Класс для представления окна отображения проектов
class DisplayProjectsWindow(tk.Toplevel):
    def __init__(self, db_manager, user_id, parent):
        # Инициализировать окно
        super().__init__()
        # Установить менеджер базы данных и идентификатор пользователя
        self.db_manager = db_manager
        self.user_id = user_id
        self.parent = parent
        # Установить заголовок окна
        self.title("TaskBoard - Все проекты")
        # Установить геометрию окна
        self.geometry("800x600")
        # Центрировать окно на экране
        self.center_window(800, 600)
        self.create_widgets()
        self.update_time()

    def center_window(self, width, height):
        # Получить ширину и высоту экрана
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        # Рассчитать координаты x и y для центрирования окна
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        # Установить геометрию окна с рассчитанными шириной, высотой и координатами
        self.geometry(f"{width}x{height}+{x}+{y}")

    def create_widgets(self):
        # Создать метку для отображения текущего времени
        self.current_time_label = tk.Label(self, text="", font=("Helvetica", 14))
        self.current_time_label.grid(row=0, column=0, columnspan=3, pady=10)

        # Область для отображения проектов
        self.project_canvas = tk.Canvas(self)
        self.project_canvas.grid(row=1, column=0, columnspan=3, sticky='nsew')
        # Создать полосу прокрутки для холста
        self.scrollbar = tk.Scrollbar(self, orient='vertical', command=self.project_canvas.yview)
        self.scrollbar.grid(row=1, column=3, sticky='ns')
        # Настроить холст для использования полосы прокрутки
        self.project_canvas.configure(yscrollcommand=self.scrollbar.set)
        # Создать фрейм для хранения проектов
        self.project_frame = tk.Frame(self.project_canvas)
        self.project_canvas.create_window((0, 0), window=self.project_frame, anchor='nw')
        # Привязать событие настройки фрейма для обновления области прокрутки холста
        self.project_frame.bind("<Configure>", lambda e: self.project_canvas.configure(scrollregion=self.project_canvas.bbox("all")))
        # Отобразить проекты
        self.display_projects()
        # Установить веса столбцов и строк для расширения холста
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(1, weight=1)
         # Создать кнопку для закрытия окна
        tk.Button(self, text="Закрыть", command=self.close_window, font=("Helvetica", 14)).grid(row=2, column=0, columnspan=3, pady=10)

    def update_time(self):
        # Обновить метку текущего времени
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.current_time_label.config(text=now)
        # Запланировать следующее обновление через 1 секунду
        self.after(1000, self.update_time)

    def display_projects(self):
        # Уничтожить любые существующие виджеты в фрейме проектов
        for widget in self.project_frame.winfo_children():
            widget.destroy()
            # Запросить базу данных для проектов
        projects = self.db_manager.execute_query(
            "SELECT id, name, type, start_date, end_date, completed, file_path FROM projects WHERE user_id=?",
            (self.user_id,), fetch=True)
        # Создать фрейм для каждого проекта
        for project in projects:
            project_frame = Frame(self.project_frame, padx=10, pady=5, relief=tk.RAISED, bd=2)
            project_frame.pack(fill='x', expand=True, pady=5)
             # Создать метку для отображения имени и типа проекта
            text = f"{project[1]} - {project[2]} - {project[3]} to {project[4]}"
            label = tk.Label(project_frame, text=text,
                             font=("Helvetica", 12, "overstrike" if project[5] else "normal"))
            label.pack(anchor='w')

            if project[6]:
                file_label = tk.Label(project_frame, text=f"Файл: {project[6]}", font=("Helvetica", 12))
                file_label.pack(anchor='w')# Размещаем метку слева

            chk_state = tk.BooleanVar(value=project[5])# Создаем булевую переменную для состояния выполнения проекта
            chk = tk.Checkbutton(project_frame, variable=chk_state,
                                 command=lambda p=project[0], s=chk_state: self.toggle_project(p, s))
            chk.pack(anchor='w')# Размещаем чекбокс слева


            btn_delete = tk.Button(project_frame, text="Удалить",
                                   command=lambda p=project[0]: self.delete_project(p), font=("Helvetica", 12))
            btn_delete.pack(anchor='w')# Размещаем кнопку удаления слева


            project_name = project[1]# Получаем имя проекта
            try:
                project_time = project[4].split('.')# Разделяем дедлайн проекта на день, месяц и год
                day = int(project_time[0])
                month = int(project_time[1])
                year = int(project_time[2])
                now = datetime.datetime.now() # Получаем текущую дату и время
                DAYS_BEFORE = 2 # Устанавливаем количество дней до дедлайна
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
            except (ValueError, IndexError):
                pass
# Функция для переключения статуса выполнения проекта
    def toggle_project(self, project_id, state):
        # Обновляет поле 'completed' проекта с заданным ID на новый статус
        self.db_manager.execute_query("UPDATE projects SET completed = ? WHERE id = ?", (state.get(), project_id))
        # Обновляет отображение проектов
        self.display_projects()
# Функция для удаления проекта
    def delete_project(self, project_id):
        # Удаляет проект с заданным ID из базы данных
        self.db_manager.execute_query("DELETE FROM projects WHERE id = ?", (project_id,))
        # Обновляет отображение проектов
        self.display_projects()

    def close_window(self):# Функция для закрытия текущего окна и показа родительского окна
        self.destroy()# Уничтожает текущее окно
        self.parent.deiconify()# Показывает родительское окно

if __name__ == "__main__":# Главная функция для запуска приложения
    db_path = 'users.db'# Устанавливает путь к файлу базы данных
    db_manager = AuthenticationManager(db_path)# Создает экземпляр класса AuthenticationManager для управления базой данных
    app = Application(db_manager)# Создает экземпляр класса Application для запуска GUI
    app.mainloop() # Запускает главный цикл событий GUI