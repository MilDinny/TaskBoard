import tkinter as tk
from tkinter import messagebox, filedialog, Menu, Frame
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
        user = self.execute_query("SELECT * FROM users WHERE username=? AND password=?", (username, hashed_password), fetch=True)
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
        self.center_window(600, 400)
        self.create_widgets()
        self.dark_mode = False

    def center_window(self, width, height):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

    def create_widgets(self):
        self.menu_bar = Menu(self)
        self.config(menu=self.menu_bar)

        self.theme_menu = Menu(self.menu_bar, tearoff=0)
        self.theme_menu.add_command(label="Тёмная тема", command=self.enable_dark_mode)
        self.theme_menu.add_command(label="Светлая тема", command=self.disable_dark_mode)
        self.menu_bar.add_cascade(label="Темы", menu=self.theme_menu)

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

    def enable_dark_mode(self):
        self.dark_mode = True
        self.apply_theme()

    def disable_dark_mode(self):
        self.dark_mode = False
        self.apply_theme()

    def apply_theme(self):
        bg_color = "#2e2e2e" if self.dark_mode else "#ffffff"
        fg_color = "#ffffff" if self.dark_mode else "#000000"
        entry_bg = "#3e3e3e" if self.dark_mode else "#ffffff"
        entry_fg = "#ffffff" if self.dark_mode else "#000000"
        button_bg = "#5e5e5e" if self.dark_mode else "#f0f0f0"
        button_fg = "#ffffff" if self.dark_mode else "#000000"

        self.configure(bg=bg_color)
        for widget in self.winfo_children():
            if isinstance(widget, tk.Label):
                widget.configure(bg=bg_color, fg=fg_color)
            elif isinstance(widget, tk.Entry):
                widget.configure(bg=entry_bg, fg=entry_fg)
            elif isinstance(widget, tk.Button):
                widget.configure(bg=button_bg, fg=button_fg)
            elif isinstance(widget, tk.Toplevel):
                widget.configure(bg=bg_color)
                for child in widget.winfo_children():
                    if isinstance(child, tk.Label):
                        child.configure(bg=bg_color, fg=fg_color)
                    elif isinstance(child, tk.Entry):
                        child.configure(bg=entry_bg, fg=entry_fg)
                    elif isinstance(child, tk.Button):
                        child.configure(bg=button_bg, fg=button_fg)

    def login(self):
        username = self.entry_username.get()
        password = self.entry_password.get()
        user_id = self.db_manager.authenticate(username, password)
        if user_id:
            self.destroy()
            MainWindow(self.db_manager, user_id, self.dark_mode)

    def register(self):
        username = self.entry_username.get()
        password = self.entry_password.get()
        self.db_manager.register_user(username, password)

    def show_users(self):
        users = self.db_manager.execute_query("SELECT username FROM users", fetch=True)
        users_window = tk.Toplevel(self)
        users_window.title("Список пользователей")
        users_window.geometry("300x200")
        self.center_window_in_window(users_window, 300, 200)
        users_window.configure(bg=self['bg'])
        for user in users:
            user_label = tk.Label(users_window, text=f"Пользователь: {user[0]}", font=("Helvetica", 12), bg=self['bg'], fg=self['fg'])
            user_label.pack(anchor='w', padx=10, pady=5)

    def center_window_in_window(self, window, width, height):
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        window.geometry(f"{width}x{height}+{x}+{y}")

class MainWindow(tk.Tk):
    def __init__(self, db_manager, user_id, dark_mode):
        super().__init__()
        self.db_manager = db_manager
        self.user_id = user_id
        self.title("TaskBoard - Личный кабинет")
        self.geometry("800x600")
        self.center_window(800, 600)
        self.dark_mode = dark_mode
        self.create_widgets()
        self.apply_theme()
        self.update_time()

    def center_window(self, width, height):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

    def create_widgets(self):
        self.current_time_label = tk.Label(self, text="", font=("Helvetica", 14))
        self.current_time_label.grid(row=0, column=0, columnspan=3, pady=10)

        tk.Button(self, text="Проекты", command=self.open_projects_window, font=("Helvetica", 14)).grid(row=1, column=0, columnspan=3, pady=10)
        tk.Button(self, text="Удалить свой аккаунт", command=self.delete_own_account, font=("Helvetica", 14)).grid(row=2, column=0, columnspan=3, pady=10)
        tk.Button(self, text="Выход", command=self.logout, font=("Helvetica", 14)).grid(row=3, column=0, columnspan=3, pady=10)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)

    def apply_theme(self):
        bg_color = "#2e2e2e" if self.dark_mode else "#ffffff"
        fg_color = "#ffffff" if self.dark_mode else "#000000"
        entry_bg = "#3e3e3e" if self.dark_mode else "#ffffff"
        entry_fg = "#ffffff" if self.dark_mode else "#000000"
        button_bg = "#5e5e5e" if self.dark_mode else "#f0f0f0"
        button_fg = "#ffffff" if self.dark_mode else "#000000"

        self.configure(bg=bg_color)
        for widget in self.winfo_children():
            if isinstance(widget, tk.Label):
                widget.configure(bg=bg_color, fg=fg_color)
            elif isinstance(widget, tk.Entry):
                widget.configure(bg=entry_bg, fg=entry_fg)
            elif isinstance(widget, tk.Button):
                widget.configure(bg=button_bg, fg=button_fg)
            elif isinstance(widget, tk.Toplevel):
                widget.configure(bg=bg_color)
                for child in widget.winfo_children():
                    if isinstance(child, tk.Label):
                        child.configure(bg=bg_color, fg=fg_color)
                    elif isinstance(child, tk.Entry):
                        child.configure(bg=entry_bg, fg=entry_fg)
                    elif isinstance(child, tk.Button):
                        child.configure(bg=button_bg, fg=button_fg)

    def open_projects_window(self):
        self.withdraw()
        ProjectsWindow(self.db_manager, self.user_id, self, self.dark_mode)

    def update_time(self):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.current_time_label.config(text=now)
        self.after(1000, self.update_time)

    def delete_own_account(self):
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить свой аккаунт?"):
            self.db_manager.delete_user(self.user_id)
            messagebox.showinfo("Успех", "Ваш аккаунт успешно удален.")
            self.logout()

    def logout(self):
        self.destroy()
        app = Application(self.db_manager)
        app.mainloop()

class ProjectsWindow(tk.Toplevel):
    def __init__(self, db_manager, user_id, parent, dark_mode):
        super().__init__()
        self.db_manager = db_manager
        self.user_id = user_id
        self.parent = parent
        self.dark_mode = dark_mode
        self.title("TaskBoard - Проекты")
        self.geometry("800x600")
        self.center_window(800, 600)
        self.create_widgets()
        self.apply_theme()
        self.update_time()

    def center_window(self, width, height):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

    def create_widgets(self):
        self.current_time_label = tk.Label(self, text="", font=("Helvetica", 14))
        self.current_time_label.grid(row=0, column=0, columnspan=3, pady=10)

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

    def apply_theme(self):
        bg_color = "#2e2e2e" if self.dark_mode else "#ffffff"
        fg_color = "#ffffff" if self.dark_mode else "#000000"
        entry_bg = "#3e3e3e" if self.dark_mode else "#ffffff"
        entry_fg = "#ffffff" if self.dark_mode else "#000000"
        button_bg = "#5e5e5e" if self.dark_mode else "#f0f0f0"
        button_fg = "#ffffff" if self.dark_mode else "#000000"

        self.configure(bg=bg_color)
        for widget in self.winfo_children():
            if isinstance(widget, tk.Label):
                widget.configure(bg=bg_color, fg=fg_color)
            elif isinstance(widget, tk.Entry):
                widget.configure(bg=entry_bg, fg=entry_fg)
            elif isinstance(widget, tk.Button):
                widget.configure(bg=button_bg, fg=button_fg)
            elif isinstance(widget, tk.Toplevel):
                widget.configure(bg=bg_color)
                for child in widget.winfo_children():
                    if isinstance(child, tk.Label):
                        child.configure(bg=bg_color, fg=fg_color)
                    elif isinstance(child, tk.Entry):
                        child.configure(bg=entry_bg, fg=entry_fg)
                    elif isinstance(child, tk.Button):
                        child.configure(bg=button_bg, fg=button_fg)

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
        self.display_projects_window()

    def display_projects_window(self):
        self.withdraw()
        DisplayProjectsWindow(self.db_manager, self.user_id, self, self.dark_mode)

    def close_window(self):
        self.destroy()
        self.parent.deiconify()

class DisplayProjectsWindow(tk.Toplevel):
    def __init__(self, db_manager, user_id, parent, dark_mode):
        super().__init__()
        self.db_manager = db_manager
        self.user_id = user_id
        self.parent = parent
        self.dark_mode = dark_mode
        self.title("TaskBoard - Все проекты")
        self.geometry("800x600")
        self.center_window(800, 600)
        self.create_widgets()
        self.apply_theme()
        self.update_time()

    def center_window(self, width, height):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

    def create_widgets(self):
        self.current_time_label = tk.Label(self, text="", font=("Helvetica", 14))
        self.current_time_label.grid(row=0, column=0, columnspan=3, pady=10)

        # Область для отображения проектов
        self.project_canvas = tk.Canvas(self)
        self.project_canvas.grid(row=1, column=0, columnspan=3, sticky='nsew')

        self.scrollbar = tk.Scrollbar(self, orient='vertical', command=self.project_canvas.yview)
        self.scrollbar.grid(row=1, column=3, sticky='ns')

        self.project_canvas.configure(yscrollcommand=self.scrollbar.set)

        self.project_frame = tk.Frame(self.project_canvas)
        self.project_canvas.create_window((0, 0), window=self.project_frame, anchor='nw')

        self.project_frame.bind("<Configure>", lambda e: self.project_canvas.configure(scrollregion=self.project_canvas.bbox("all")))

        self.display_projects()

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(1, weight=1)

        tk.Button(self, text="Закрыть", command=self.close_window, font=("Helvetica", 14)).grid(row=2, column=0, columnspan=3, pady=10)

    def apply_theme(self):
        bg_color = "#2e2e2e" if self.dark_mode else "#ffffff"
        fg_color = "#ffffff" if self.dark_mode else "#000000"
        entry_bg = "#3e3e3e" if self.dark_mode else "#ffffff"
        entry_fg = "#ffffff" if self.dark_mode else "#000000"
        button_bg = "#5e5e5e" if self.dark_mode else "#f0f0f0"
        button_fg = "#ffffff" if self.dark_mode else "#000000"

        self.configure(bg=bg_color)
        for widget in self.winfo_children():
            if isinstance(widget, tk.Label):
                widget.configure(bg=bg_color, fg=fg_color)
            elif isinstance(widget, tk.Entry):
                widget.configure(bg=entry_bg, fg=entry_fg)
            elif isinstance(widget, tk.Button):
                widget.configure(bg=button_bg, fg=button_fg)
            elif isinstance(widget, tk.Toplevel):
                widget.configure(bg=bg_color)
                for child in widget.winfo_children():
                    if isinstance(child, tk.Label):
                        child.configure(bg=bg_color, fg=fg_color)
                    elif isinstance(child, tk.Entry):
                        child.configure(bg=entry_bg, fg=entry_fg)
                    elif isinstance(child, tk.Button):
                        child.configure(bg=button_bg, fg=button_fg)

    def update_time(self):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.current_time_label.config(text=now)
        self.after(1000, self.update_time)

    def display_projects(self):
        for widget in self.project_frame.winfo_children():
            widget.destroy()
        projects = self.db_manager.execute_query(
            "SELECT id, name, type, start_date, end_date, completed, file_path FROM projects WHERE user_id=?",
            (self.user_id,), fetch=True)
        for project in projects:
            project_frame = Frame(self.project_frame, padx=10, pady=5, relief=tk.RAISED, bd=2)
            project_frame.pack(fill='x', expand=True, pady=5)

            text = f"{project[1]} - {project[2]} - {project[3]} to {project[4]}"
            label = tk.Label(project_frame, text=text,
                             font=("Helvetica", 12, "overstrike" if project[5] else "normal"))
            label.pack(anchor='w')

            if project[6]:
                file_label = tk.Label(project_frame, text=f"Файл: {project[6]}", font=("Helvetica", 12))
                file_label.pack(anchor='w')

            chk_state = tk.BooleanVar(value=project[5])
            chk = tk.Checkbutton(project_frame, variable=chk_state,
                                 command=lambda p=project[0], s=chk_state: self.toggle_project(p, s))
            chk.pack(anchor='w')

            btn_delete = tk.Button(project_frame, text="Удалить",
                                   command=lambda p=project[0]: self.delete_project(p), font=("Helvetica", 12))
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

    def toggle_project(self, project_id, state):
        self.db_manager.execute_query("UPDATE projects SET completed = ? WHERE id = ?", (state.get(), project_id))
        self.display_projects()

    def delete_project(self, project_id):
        self.db_manager.execute_query("DELETE FROM projects WHERE id = ?", (project_id,))
        self.display_projects()

    def close_window(self):
        self.destroy()
        self.parent.deiconify()

if __name__ == "__main__":
    db_path = 'users.db'
    db_manager = AuthenticationManager(db_path)
    app = Application(db_manager)
    app.mainloop()