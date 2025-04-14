import sqlite3
import random
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.anchorlayout import AnchorLayout
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.graphics import Rectangle, Color
from datetime import datetime, timedelta


Window.size = (360, 640)
Window.clearcolor = (0.2, 0.35, 0.6, 1)
DB_PATH = 'study_var.db'
class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.failed_attempts = 0
        self.lock_count = 0  # счётчик блокировок
        self.locked_until = None
        self.timer_event = None

        anchor_layout = AnchorLayout(anchor_y='top')

        layout = BoxLayout(orientation='vertical', padding=20, spacing=15, size_hint=(1, None))
        layout.bind(minimum_height=layout.setter('height'))

        from kivy.uix.image import Image

        img = Image(source='trippi troppa.png', size_hint_y=None, height=150, allow_stretch=True)
        layout.add_widget(img)

        layout.add_widget(Label(text='Вход', font_size=24, color=(1, 1, 1, 1), size_hint_y=None, height=50))

        self.username = TextInput(hint_text='Логин', multiline=False, size_hint_y=None, height=40)
        self.password = TextInput(hint_text='Пароль', password=True, multiline=False, size_hint_y=None, height=40)
        self.login_btn = Button(text='Войти', size_hint_y=None, height=44, background_color=(0.3, 0.3, 0.3, 1))
        self.login_btn.bind(on_release=self.check_login)

        self.timer_label = Label(text='', font_size=16, color=(1, 0.3, 0.3, 1), size_hint_y=None, height=30)

        layout.add_widget(self.username)
        layout.add_widget(self.password)
        layout.add_widget(self.login_btn)
        layout.add_widget(self.timer_label)

        anchor_layout.add_widget(layout)
        self.add_widget(anchor_layout)

    def check_login(self, instance):
        if self.locked_until and datetime.now() < self.locked_until:
            self.username.text = ''
            self.password.text = ''
            self.username.hint_text = 'Заблокировано'
            self.password.hint_text = 'Ожидайте'
            return

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM admin WHERE login=? AND password=?", (self.username.text, self.password.text))
        user = cursor.fetchone()
        conn.close()

        if user:
            self.failed_attempts = 0
            self.lock_count = 0
            self.login_btn.disabled = False
            self.timer_label.text = ''
            if self.timer_event:
                self.timer_event.cancel()
            self.manager.transition = SlideTransition(direction="left")
            self.manager.current = 'main'
        else:
            self.failed_attempts += 1
            self.username.text = ''
            self.password.text = ''
            self.username.hint_text = 'Неверный логин'
            self.password.hint_text = 'или пароль'

            if self.failed_attempts >= 5:
                self.lock_count += 1
                lock_duration = self.lock_count * 60
                self.locked_until = datetime.now() + timedelta(seconds=lock_duration)
                self.login_btn.disabled = True
                self.timer_event = Clock.schedule_interval(self.update_timer, 1)
                Clock.schedule_once(self.unlock_login, lock_duration)

    def update_timer(self, dt):
        remaining = int((self.locked_until - datetime.now()).total_seconds())
        if remaining > 0:
            self.timer_label.text = f"Ожидайте {remaining} секунд для новой попытки"
        else:
            self.timer_label.text = ''

    def unlock_login(self, dt):
        self.failed_attempts = 0
        self.locked_until = None
        self.login_btn.disabled = False
        self.username.hint_text = 'Логин'
        self.password.hint_text = 'Пароль'
        self.timer_label.text = ''
        if self.timer_event:
            self.timer_event.cancel()
            self.timer_event = None

    def reset_fields(self):
        self.username.text = ''
        self.password.text = ''
        self.username.hint_text = 'Логин'
        self.password.hint_text = 'Пароль'
        self.timer_label.text = ''

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        from kivy.uix.image import Image
        img = Image(source='kruto.png', size_hint_y=None, height=180, allow_stretch=True)
        layout.add_widget(img)

        layout.add_widget(Label(text='Выберите таблицу', size_hint_y=None, height=40, font_size=20, color=(1, 1, 1, 1)))

        scroll = ScrollView(size_hint=(1, 1))
        grid = GridLayout(cols=1, spacing=10, size_hint_y=None, padding=5)
        grid.bind(minimum_height=grid.setter('height'))

        self.tables = self.get_tables()
        for table in self.tables:
            btn = Button(
                text=table,
                size_hint_y=None,
                height=44,
                background_color=(0.2, 0.4, 0.6, 1),
                color=(1, 1, 1, 1)
            )
            btn.bind(on_release=self.open_table)
            grid.add_widget(btn)

        scroll.add_widget(grid)
        layout.add_widget(scroll)


        logout_btn = Button(
            text='Выйти',
            size_hint_y=None,
            height=44,
            background_color=(0.6, 0.2, 0.2, 1),
            color=(1, 1, 1, 1)
        )
        logout_btn.bind(on_release=self.logout)
        layout.add_widget(logout_btn)

        self.add_widget(layout)

    def get_tables(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        return [t for t in tables if t.lower() != 'admin']

    def open_table(self, instance):
        self.manager.transition = SlideTransition(direction="left")
        table_screen = self.manager.get_screen('table')
        table_screen.load_table(instance.text)
        self.manager.current = 'table'

    def logout(self, instance):
        login_screen = self.manager.get_screen('login')
        login_screen.reset_fields()
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = 'login'



class TableScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sort_column = None
        self.sort_reverse = False
        self.selected_row = None
        self.columns = []

    def load_table(self, table_name):
        self.clear_widgets()
        self.table_name = table_name

        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        main_layout.add_widget(Label(text=f'Таблица: {table_name}', font_size=18, size_hint_y=None, height=30, color=(1,1,1,1)))

        search_box = BoxLayout(size_hint_y=None, height=40, spacing=10)
        self.search_input = TextInput(hint_text="Поиск...")
        search_button = Button(text="Поиск", size_hint_x=None, width=80, background_color=(0.1, 0.5, 0.8, 1))
        search_button.bind(on_release=self.apply_filter)
        search_box.add_widget(self.search_input)
        search_box.add_widget(search_button)
        main_layout.add_widget(search_box)

        scroll = ScrollView(size_hint=(1, 1))
        self.table_container = GridLayout(cols=1, size_hint_y=None, spacing=5, padding=5)
        self.table_container.bind(minimum_height=self.table_container.setter('height'))
        scroll.add_widget(self.table_container)
        main_layout.add_widget(scroll)

        self.action_buttons = BoxLayout(size_hint_y=None, height=50, spacing=10)
        self.edit_btn = Button(text="Редактировать", background_color=(0.2, 0.6, 0.3, 1))
        self.delete_btn = Button(text="Удалить", background_color=(0.6, 0.2, 0.2, 1))
        self.edit_btn.bind(on_release=self.edit_record)
        self.delete_btn.bind(on_release=self.delete_record)
        self.edit_btn.disabled = True
        self.delete_btn.disabled = True
        self.action_buttons.add_widget(self.edit_btn)
        self.action_buttons.add_widget(self.delete_btn)
        main_layout.add_widget(self.action_buttons)

        nav_buttons = BoxLayout(size_hint_y=None, height=50, spacing=10)
        add_btn = Button(text="Добавить", background_color=(0, 0.5, 0, 1))
        back_btn = Button(text="Назад", background_color=(0.3, 0.3, 0.3, 1))
        add_btn.bind(on_release=self.add_record)
        back_btn.bind(on_release=self.go_back)
        nav_buttons.add_widget(add_btn)
        nav_buttons.add_widget(back_btn)
        main_layout.add_widget(nav_buttons)

        self.add_widget(main_layout)
        self.refresh_data()

    def apply_filter(self, instance=None):
        self.refresh_data()

    def refresh_data(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({self.table_name})")
        self.columns = [col[1] for col in cursor.fetchall()]

        query = f"SELECT * FROM {self.table_name}"
        params = []
        if self.search_input.text:
            like_expr = " OR ".join([f"{col} LIKE ?" for col in self.columns])
            query += f" WHERE {like_expr}"
            params = [f"%{self.search_input.text}%"] * len(self.columns)

        cursor.execute(query, params)
        self.rows = cursor.fetchall()
        conn.close()

        if self.sort_column:
            index = self.columns.index(self.sort_column)
            self.rows.sort(key=lambda x: str(x[index]), reverse=self.sort_reverse)

        self.table_container.clear_widgets()
        self.selected_row = None
        self.edit_btn.disabled = True
        self.delete_btn.disabled = True

        for row in self.rows:
            row_text = " | ".join([str(cell) for cell in row])
            btn = Button(
                text=row_text,
                size_hint_y=None,
                height=44,
                halign='left',
                text_size=(Window.width - 40, None),
                background_color=(0.3, 0.3, 0.4, 1),
                color=(1, 1, 1, 1)
            )
            btn.bind(on_release=lambda inst, r=row: self.select_row(r, inst))
            self.table_container.add_widget(btn)

    def select_row(self, row, instance):
        self.selected_row = row
        self.edit_btn.disabled = False
        self.delete_btn.disabled = False

        for widget in self.table_container.children:
            widget.background_color = (0.3, 0.3, 0.4, 1)
        instance.background_color = (0.1, 0.6, 0.6, 1)

    def go_back(self, instance):
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = 'main'

    def add_record(self, instance):
        self.manager.get_screen('form').load_form(self.table_name, self.columns)
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = 'form'

    def edit_record(self, instance):
        if self.selected_row:
            self.manager.get_screen('form').load_form(self.table_name, self.columns, self.selected_row)
            self.manager.transition = SlideTransition(direction="left")
            self.manager.current = 'form'

    def delete_record(self, instance):
        if not self.selected_row:
            return
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        pk_column = self.columns[0]
        cursor.execute(f"DELETE FROM {self.table_name} WHERE {pk_column}=?", (self.selected_row[0],))
        conn.commit()
        conn.close()
        self.refresh_data()


class FormScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.inputs = []

    def load_form(self, table_name, columns, row=None):
        self.clear_widgets()
        self.inputs = []
        self.table_name = table_name
        self.existing_row = row

        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        for i, col in enumerate(columns):
            line = BoxLayout(size_hint_y=None, height=40)
            label = Label(text=col, size_hint_x=0.3, color=(1,1,1,1))
            input_field = TextInput()
            if row:
                input_field.text = str(row[i])
                if i == 0:
                    input_field.disabled = True
            self.inputs.append((col, input_field))
            line.add_widget(label)
            line.add_widget(input_field)
            layout.add_widget(line)

        save_btn = Button(text="Сохранить", size_hint_y=None, height=44)
        cancel_btn = Button(text="Отмена", size_hint_y=None, height=44)
        save_btn.bind(on_release=self.save_record)
        cancel_btn.bind(on_release=self.cancel_form)

        layout.add_widget(save_btn)
        layout.add_widget(cancel_btn)
        self.add_widget(layout)

    def cancel_form(self, instance):
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = 'table'

    def save_record(self, instance):
        values = [ti.text for _, ti in self.inputs]
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        if self.existing_row:
            set_clause = ', '.join([f"{col}=?" for col, _ in self.inputs[1:]])
            query = f"UPDATE {self.table_name} SET {set_clause} WHERE {self.inputs[0][0]}=?"
            data = [ti.text for _, ti in self.inputs[1:]] + [self.inputs[0][1].text]
        else:
            placeholders = ','.join(['?'] * len(values))
            query = f"INSERT INTO {self.table_name} VALUES ({placeholders})"
            data = values

        cursor.execute(query, data)
        conn.commit()
        conn.close()

        self.manager.get_screen('table').refresh_data()
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = 'table'


class DBApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(TableScreen(name='table'))
        sm.add_widget(FormScreen(name='form'))
        sm.current = 'login'
        return sm

if __name__ == '__main__':
    DBApp().run()
