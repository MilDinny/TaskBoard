import tkinter as tk
from tkinter import messagebox
import sqlite3
import hashlib
import datetime


# Класс DatabaseManager - необходим для работы с БД
class DatabaseManager:
    # Коструктор класса принимает путь до файла БД
    def __init__(self, db_path):
        # Сохраняем путь
        self.db_path = db_path
        # Создаем таблицу пользователей
        self.create_tables()

    # Метод для создания таблицы пользователей
    def create_tables(self):
        # Открытие файла БД, с последующим автоматическим закрытием
        with sqlite3.connect(self.db_path) as conn:
            # Переменная курсора для работы с файлом БД
            c = conn.cursor()
            # Создание таблицы пользователей
            c.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT
                )''')
            # Создание таблицы проектов всех пользователей
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

    # Метод для отправки запроса к БД для получения или записи результата
    def execute_query(self, query, params=(), fetch=False):
        # Открытие файла БД, с последующим автоматическим закрытием
        with sqlite3.connect(self.db_path) as conn:
            # Переменная курсора для работы с файлом БД
            c = conn.cursor()
            # Обращение к БД с запросом query и параметрами params
            c.execute(query, params)
            # Если запрос был на получение результата
            if fetch:
                # Возвращаем результат
                return c.fetchall()
            # Сохраняем изменения
            conn.commit()


# AuthenticationManager - класс для авторизации / регистрации пользователей
class AuthenticationManager(DatabaseManager):
    # Метод для хеширования пароля
    def hash_password(self, password):
        # Возвращает захешированный пароль
        return hashlib.sha256(password.encode()).hexdigest()

    # Метод для регистрации пользователя
    def register_user(self, username, password):
        # Захешированный пароль
        hashed_password = self.hash_password(password)
        # Попытка записать в БД нового пользователя
        try:
            # Запись пользователя в таблицу пользователей
            self.execute_query("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
            # Вывод всплывающего сообщения об успешной регистрации
            messagebox.showinfo("Успех", "Пользователь успешно зарегистрирован.")
        # Если все прошло неудачно
        except sqlite3.IntegrityError:
            # Вывод сообщения об ошибке
            messagebox.showerror("Ошибка", "Пользователь с таким именем уже существует.")

    # Метод авторизации пользователя
    def authenticate(self, username, password):
        # Захешированный пароль
        hashed_password = self.hash_password(password)
        # Чтение пользователя с переданными логином и паролем
        user = self.execute_query("SELECT * FROM users WHERE username=? AND password=?", (username, hashed_password),
                                  fetch=True)
        # Если этот пользователь есть в БД
        if user:
            # Возврат информации о пользователе
            return user[0][0]
        # Вывод сообщения об ошибке
        messagebox.showerror("Ошибка", "Неправильный логин или пароль")
        return None


# Класс первого окна, с входом и регистрацией.
class Application(tk.Tk):
    # Конструктор класса, принимает объект класса AuthenticationManager для авторизации и регистрации пользователей
    def __init__(self, db_manager):
        # Вызов конструктора родительского класса
        super().__init__()
        # Инициализация объекта клааса AuthenticationManager
        self.db_manager = db_manager
        # Установка заголовка окна
        self.title("Вход и регистрация")
        # Вызов метода для создания элементов интерфейса
        self.create_widgets()

    # Метод для создания виджетов
    def create_widgets(self):
        # Создание надписи "Логин:"
        tk.Label(self, text="Логин:").grid(row=0, column=0)
        # Создание поля для ввода имени пользователя
        self.entry_username = tk.Entry(self)
        # Расположение поля для ввода имени
        self.entry_username.grid(row=0, column=1)
        # Создание надписи "Пароль:"
        tk.Label(self, text="Пароль:").grid(row=1, column=0)
        # Создание поля для ввода пароля пользователя
        self.entry_password = tk.Entry(self, show="*")
        # Расположение поля для ввода пароля
        self.entry_password.grid(row=1, column=1)
        # Создание кнопки "Вход"
        tk.Button(self, text="Вход", command=self.login).grid(row=2, column=0, columnspan=2)
        # Создание кнопки "Регистрация"
        tk.Button(self, text="Регистрация", command=self.register).grid(row=3, column=0, columnspan=2)

    # Метод для авторизации пользователя
    def login(self):
        # Получение имени пользователя из соответствующего поля для ввода
        username = self.entry_username.get()
        # Получение пароля пользователя из соответствующего поля для ввода
        password = self.entry_password.get()
        # Попытка авторизации пользователя
        user_id = self.db_manager.authenticate(username, password)
        # Если авторизация прошла успешно
        if user_id:
            # Закрываем текущее окно
            self.destroy()
            # Открываем следующее окно
            MainWindow(self.db_manager, user_id)

    # Метод для регистрации пользователя
    def register(self):
        # Получение имени пользователя из соответствующего поля для ввода
        username = self.entry_username.get()
        # Получение пароля пользователя из соответствующего поля для ввода
        password = self.entry_password.get()
        # Регистрация пользователя
        self.db_manager.register_user(username, password)


# Класс окна проектов пользователя
class MainWindow(tk.Tk):
    '''
    Конструктор класса MainWindow, принимает:
    db_manager - объект класса AuthenticationManager для авторизации и регистрации пользователей
    user_id - id пользователя, который успешно авторизовался
    '''
    def __init__(self, db_manager, user_id):
        # Вызов конструктора родительского класса
        super().__init__()
        # Инициализация объекта клааса AuthenticationManager
        self.db_manager = db_manager
        # Инициализация переменной user_id айдишником пользователя
        self.user_id = user_id
        # Установка заголовка окна
        self.title("Главное окно")
        # Вызов метода для создания элементов интерфейса
        self.create_widgets()

    # Метод для создания виджетов
    def create_widgets(self):
        # Создание надписи "Название проекта:"
        tk.Label(self, text="Название проекта:").grid(row=0, column=0)
        # Создание поля для ввода названия проекта
        self.entry_project_name = tk.Entry(self)
        # Расположение поля для ввода названия проекта
        self.entry_project_name.grid(row=0, column=1)
        # Создание надписи "Тип проекта:"
        tk.Label(self, text="Тип проекта:").grid(row=1, column=0)
        # Создание поля для ввода типа проекта
        self.entry_project_type = tk.Entry(self)
        # Расположение поля для ввода типа проекта
        self.entry_project_type.grid(row=1, column=1)
        # Создание надписи "Дата начала:"
        tk.Label(self, text="Дата начала:").grid(row=2, column=0)
        # Создание поля для ввода даты начала проекта
        self.entry_start_date = tk.Entry(self)
        # Расположение поля для ввода даты начала проекта
        self.entry_start_date.grid(row=2, column=1)
        # Создание надписи "Дата окончания:"
        tk.Label(self, text="Дата окончания:").grid(row=3, column=0)
        # Создание поля для ввода даты окончания проекта
        self.entry_end_date = tk.Entry(self)
        # Расположение поля для ввода даты окончания проекта
        self.entry_end_date.grid(row=3, column=1)
        # Создание кнопки "Добавить проект"
        tk.Button(self, text="Добавить проект", command=self.add_project).grid(row=4, column=0, columnspan=2)
        # Создание контейнера для отображения проектов пользователя
        self.project_frame = tk.Frame(self)
        # Расположение контейнера проектов
        self.project_frame.grid(row=5, column=0, columnspan=2)
        # Вызов метода отображения проектов на экране
        self.display_projects()

    # Метод добавления нового проекта
    def add_project(self):
        # Считывание названия проекта
        project_name = self.entry_project_name.get()
        # Считывание типа проекта
        project_type = self.entry_project_type.get()
        # Считывание даты начала проекта
        start_date = self.entry_start_date.get()
        # Считывание даты окончания проекта
        end_date = self.entry_end_date.get()
        # Обращение к БД для внесения нового проекта пользователя
        self.db_manager.execute_query("INSERT INTO projects (name, type, start_date, end_date, user_id) VALUES (?, ?, ?, ?, ?)",
                                      (project_name, project_type, start_date, end_date, self.user_id))
        # Вызов метода отображения проектов на экране
        self.display_projects()

    # Метод отображения проектов на экране
    def display_projects(self):
        # Цикл перебора всех текущих проектов пользователя на экране
        for widget in self.project_frame.winfo_children():
            # Удаление проекта с экрана
            widget.destroy()
        # Получение информации об актуальных проектах
        projects = self.db_manager.execute_query("SELECT id, name, type, start_date, end_date, completed FROM projects WHERE user_id=?",
                                                 (self.user_id,), fetch=True)
        # Цикл перебора актуальных проектов пользователя
        for project in projects:
            # Генерация текста, содержащего информацию об очередном проекте
            text = f"{project[1]} - {project[2]} - {project[3]} to {project[4]}"
            # Создание надписи, содержащей информацию о проекте
            # Если проект сдан, текст будет зачеркнутым
            label = tk.Label(self.project_frame, text=text, font=("Arial", 10, "overstrike" if project[5] else "normal"))
            # Вывод информации о проекте на экран
            label.pack()
            # Создание логической переменной для чекбокса, который отвечает за статус выполнения проекта
            chk_state = tk.BooleanVar(value=project[5])
            # Создание чекбокса, который отвечает за статус выполнения проекта
            # Если проект был выполнен, автоматически ставится галочка
            chk = tk.Checkbutton(self.project_frame, var=chk_state,
                                 command=lambda p=project[0], s=chk_state: self.toggle_project(p, s))
            # Вывод чекбокса на экран
            chk.pack()

            # Подрузамеваем, что дата задается в формате dd.mm.yyyy
            # Получение названия проекта
            project_name = project[1]
            # Разбиение времени сдачи проекта по символу '.'
            project_time = project[4].split('.')
            # Получение дня сдачи проекта
            day = int(project_time[0])
            # Получение месяца сдачи проекта
            month = int(project_time[1])
            # Получение года сдачи проекта
            year = int(project_time[2])
            # Получение текущего времени компьютера
            now = datetime.datetime.now()
            # Создание константы, отвечающей за кол-во дней, за которое пояаится напоминание о сдачи проекта
            DAYS_BEFORE = 2
            # Показываем уведомление за DAYS_BEFORE дней до сдачи проекта
            # Если проект не сдан
            if not project[5]:
                # Если год и месяц сдачи проекта совпадают с сегодняшними
                if now.year == year and now.month == month:
                    # Если до сдачи проекта осталось менее DAYS_BEFORE дней
                    if now.day > day - DAYS_BEFORE:
                        # Показываем соответствующеее уведомление
                        messagebox.showerror("Важно", "До сдачи проекта " + project_name
                                             + " осталось менее " + str(DAYS_BEFORE) + " суток")
                    # Если сдача проекта сегодня
                    elif now.day == day:
                        # Показываем соответствующеее уведомление
                        messagebox.showerror("Важно", "Сегодня день сдачи проекта " + project_name)
                    # Если преокт просрочен
                    elif now.day > day:
                        # Показываем соответствующеее уведомление
                        messagebox.showerror("Важно", "Проект " + project_name
                                             + " просрочен!")
                # Если проект просрочен более, чем на месяц или год
                elif now.year > year or (now.year == year and now.month > month):
                    # Показываем соответствующеее уведомление
                    messagebox.showerror("Важно", "Проект " + project_name
                                         + " просрочен!")

    '''
    Метод, который вызывается при нажатии на чекбокс.
    Принимает id проекта и статус его выполнения.
    Информация о статусе выполнении обновляется в БД.
    '''
    def toggle_project(self, project_id, state):
        # Обновление информации о статусе проекта в БД
        self.db_manager.execute_query("UPDATE projects SET completed = ? WHERE id = ?", (state.get(), project_id))
        # Отображение изменений
        self.display_projects()


if __name__ == "__main__":
    # Переменная для хранения названия БД
    db_path = 'users.db'
    # Создание объекта класса AuthenticationManager для авторизации / регистрации пользователей
    db_manager = AuthenticationManager(db_path)
    # Создание объекта класса первого экрана приложения (экрана входа)
    app = Application(db_manager)
    # Запуск первого экрана приложения
    app.mainloop()