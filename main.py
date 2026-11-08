import sqlite3
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.core.window import Window

Window.size = (360, 640)

class SouvenirsApp(App):
    def build(self):
        self.conn = sqlite3.connect('souvenirs.db')
        self.c = self.conn.cursor()
        self.init_db()

        self.root = BoxLayout(orientation='vertical', padding=10, spacing=8)
        self.show_main_menu()
        return self.root

    def init_db(self):
        self.c.execute('''CREATE TABLE IF NOT EXISTS items
                         (id INTEGER PRIMARY KEY, name TEXT, stock INTEGER)''')
        self.c.execute('''CREATE TABLE IF NOT EXISTS events
                         (id INTEGER PRIMARY KEY, name TEXT, active INTEGER)''')
        self.c.execute('''CREATE TABLE IF NOT EXISTS movements
                         (id INTEGER PRIMARY KEY, event_id INTEGER, item_id INTEGER,
                          type TEXT, qty INTEGER, price REAL)''')
        self.conn.commit()

    def clear_root(self):
        self.root.clear_widgets()

    # ---------- ГЛАВНОЕ МЕНЮ ----------
    def show_main_menu(self):
        self.clear_root()
        self.root.add_widget(Label(text="[b]Склад сувениров ДН[/b]", markup=True,
                                   size_hint_y=None, height=40, font_size='18sp'))
        btn1 = Button(text="1. Приход (закупка)", size_hint_y=None, height=50,
                      background_color=(0.2, 0.7, 0.2, 1))
        btn1.bind(on_press=lambda x: self.show_add_item())
        self.root.add_widget(btn1)

        btn2 = Button(text="2. Отгрузить на мероприятие", size_hint_y=None, height=50,
                      background_color=(0.2, 0.5, 0.8, 1))
        btn2.bind(on_press=lambda x: self.show_ship())
        self.root.add_widget(btn2)

        btn3 = Button(text="3. Продажа (на мероприятии)", size_hint_y=None, height=50,
                      background_color=(0.9, 0.8, 0.2, 1))
        btn3.bind(on_press=lambda x: self.show_sell())
        self.root.add_widget(btn3)

        btn4 = Button(text="4. Возврат на склад", size_hint_y=None, height=50,
                      background_color=(0.9, 0.5, 0.2, 1))
        btn4.bind(on_press=lambda x: self.show_return())
        self.root.add_widget(btn4)

        btn5 = Button(text="5. Остатки на складе", size_hint_y=None, height=50,
                      background_color=(0.5, 0.5, 0.5, 1))
        btn5.bind(on_press=lambda x: self.show_stock())
        self.root.add_widget(btn5)

    # ---------- 1. ПРИХОД ----------
    def show_add_item(self):
        self.clear_root()
        self.root.add_widget(Label(text="Приход (закупка)", size_hint_y=None, height=40, font_size='16sp'))
        self.name_input = TextInput(hint_text="Название сувенира", multiline=False,
                                    size_hint_y=None, height=45)
        self.root.add_widget(self.name_input)
        self.qty_input = TextInput(hint_text="Количество", input_filter='int',
                                   multiline=False, size_hint_y=None, height=45)
        self.root.add_widget(self.qty_input)
        btn = Button(text="Добавить на склад", size_hint_y=None, height=50,
                     background_color=(0.2, 0.7, 0.2, 1))
        btn.bind(on_press=self.add_item)
        self.root.add_widget(btn)
        self.add_back_button()

    def add_item(self, instance):
        name = self.name_input.text.strip()
        qty = self.qty_input.text.strip()
        if not name or not qty:
            return
        try:
            qty = int(qty)
        except:
            return
        self.c.execute("SELECT id, stock FROM items WHERE name = ?", (name,))
        row = self.c.fetchone()
        if row:
            self.c.execute("UPDATE items SET stock = ? WHERE id = ?", (row[1] + qty, row[0]))
        else:
            self.c.execute("INSERT INTO items (name, stock) VALUES (?, ?)", (name, qty))
        self.conn.commit()
        self.name_input.text = ""
        self.qty_input.text = ""
        self.root.add_widget(Label(text=f"Добавлено: {name} +{qty}", size_hint_y=None, height=30))

    # ---------- 2. ОТГРУЗКА ----------
    def show_ship(self):
        self.clear_root()
        self.root.add_widget(Label(text="Отгрузка на мероприятие", size_hint_y=None, height=40, font_size='16sp'))
        self.event_input = TextInput(hint_text="Название мероприятия", multiline=False,
                                     size_hint_y=None, height=45)
        self.root.add_widget(self.event_input)

        self.ship_layout = GridLayout(cols=1, spacing=3, size_hint_y=None)
        self.ship_layout.bind(minimum_height=self.ship_layout.setter('height'))
        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(self.ship_layout)
        self.root.add_widget(scroll)

        self.refresh_ship_list()
        self.add_back_button()

    def refresh_ship_list(self):
        self.ship_layout.clear_widgets()
        self.c.execute("SELECT id, name, stock FROM items WHERE stock > 0 ORDER BY name")
        rows = self.c.fetchall()
        if not rows:
            self.ship_layout.add_widget(Label(text="На складе ничего нет", size_hint_y=None, height=30))
            return
        for item_id, name, stock in rows:
            row_box = BoxLayout(size_hint_y=None, height=45, spacing=5)
            lbl = Label(text=f"{name} (есть {stock})", size_hint_x=0.6)
            inp = TextInput(hint_text="кол-во", input_filter='int', multiline=False, size_hint_x=0.2)
            btn = Button(text="Везём", size_hint_x=0.2, background_color=(0.2, 0.5, 0.8, 1))
            btn.bind(on_press=lambda x, i=item_id, n=name, s=stock, field=inp: self.do_ship(i, n, s, field))
            row_box.add_widget(lbl)
            row_box.add_widget(inp)
            row_box.add_widget(btn)
            self.ship_layout.add_widget(row_box)

    def do_ship(self, item_id, name, stock, field):
        qty_str = field.text.strip()
        if not qty_str:
            return
        try:
            qty = int(qty_str)
        except:
            return
        if qty <= 0 or qty > stock:
            self.root.add_widget(Label(text=f"Ошибка: нельзя отгрузить {qty} (есть {stock})",
                                       size_hint_y=None, height=30))
            return
        event_name = self.event_input.text.strip()
        if not event_name:
            self.root.add_widget(Label(text="Введите название мероприятия", size_hint_y=None, height=30))
            return
        # Ищем или создаём мероприятие
        self.c.execute("SELECT id FROM events WHERE name = ? AND active = 1", (event_name,))
        row = self.c.fetchone()
        if row:
            event_id = row[0]
        else:
            self.c.execute("INSERT INTO events (name, active) VALUES (?, 1)", (event_name,))
            event_id = self.c.lastrowid
        # Списываем со склада и пишем движение
        self.c.execute("UPDATE items SET stock = stock - ? WHERE id = ?", (qty, item_id))
        self.c.execute("INSERT INTO movements (event_id, item_id, type, qty) VALUES (?, ?, 'ship', ?)",
                       (event_id, item_id, qty))
        self.conn.commit()
        field.text = ""
        self.root.add_widget(Label(text=f"Отгружено: {name} x{qty} на «{event_name}»",
                                   size_hint_y=None, height=30))
        self.refresh_ship_list()

    # ---------- 3. ПРОДАЖА ----------
    def show_sell(self):
        self.clear_root()
        self.root.add_widget(Label(text="Продажа на мероприятии", size_hint_y=None, height=40, font_size='16sp'))
        self.sell_layout = GridLayout(cols=1, spacing=3, size_hint_y=None)
        self.sell_layout.bind(minimum_height=self.sell_layout.setter('height'))
        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(self.sell_layout)
        self.root.add_widget(scroll)
        self.refresh_sell_list()
        self.add_back_button()

    def refresh_sell_list(self):
        self.sell_layout.clear_widgets()
        self.c.execute('''SELECT m.id, i.name, e.name, m.qty
                         FROM movements m
                         JOIN items i ON m.item_id = i.id
                         JOIN events e ON m.event_id = e.id
                         WHERE m.type = 'ship' AND m.qty > 0 AND e.active = 1''')
        rows = self.c.fetchall()
        if not rows:
            self.sell_layout.add_widget(Label(text="Нет активных отгрузок", size_hint_y=None, height=30))
            return
        for ship_id, name, event_name, qty_left in rows:
            row_box = BoxLayout(size_hint_y=None, height=45, spacing=5)
            lbl = Label(text=f"{name} на «{event_name}» (ост. {qty_left})", size_hint_x=0.6)
            inp = TextInput(hint_text="продано", input_filter='int', multiline=False, size_hint_x=0.2)
            price_inp = TextInput(hint_text="цена", input_filter='float', multiline=False, size_hint_x=0.2)
            btn = Button(text="OK", size_hint_x=0.2, background_color=(0.9, 0.8, 0.2, 1))
            btn.bind(on_press=lambda x, sid=ship_id, n=name, left=qty_left, q_field=inp, p_field=price_inp: self.do_sell(sid, n, left, q_field, p_field))
            row_box.add_widget(lbl)
            row_box.add_widget(inp)
            row_box.add_widget(price_inp)
            row_box.add_widget(btn)
            self.sell_layout.add_widget(row_box)

    def do_sell(self, ship_id, name, qty_left, q_field, p_field):
        qty_str = q_field.text.strip()
        price_str = p_field.text.strip()
        if not qty_str or not price_str:
            return
        try:
            qty = int(qty_str)
            price = float(price_str)
        except:
            return
        if qty <= 0 or qty > qty_left:
            self.root.add_widget(Label(text=f"Ошибка: продано {qty}, остаток {qty_left}",
                                       size_hint_y=None, height=30))
            return
        # Уменьшаем остаток отгрузки и пишем продажу
        self.c.execute("UPDATE movements SET qty = qty - ? WHERE id = ?", (qty, ship_id))
        self.c.execute("INSERT INTO movements (event_id, item_id, type, qty, price) VALUES ((SELECT event_id FROM movements WHERE id=?), (SELECT item_id FROM movements WHERE id=?), 'sell', ?, ?)",
                       (ship_id, ship_id, qty, price))
        self.conn.commit()
        q_field.text = ""
        p_field.text = ""
        self.root.add_widget(Label(text=f"Продано: {name} x{qty} на {qty*price} руб.",
                                   size_hint_y=None, height=30))
        self.refresh_sell_list()

    # ---------- 4. ВОЗВРАТ ----------
    def show_return(self):
        self.clear_root()
        self.root.add_widget(Label(text="Возврат на склад", size_hint_y=None, height=40, font_size='16sp'))
        self.return_layout = GridLayout(cols=1, spacing=3, size_hint_y=None)
        self.return_layout.bind(minimum_height=self.return_layout.setter('height'))
        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(self.return_layout)
        self.root.add_widget(scroll)
        self.refresh_return_list()
        self.add_back_button()

    def refresh_return_list(self):
        self.return_layout.clear_widgets()
        self.c.execute('''SELECT m.id, i.name, e.name, m.qty
                         FROM movements m
                         JOIN items i ON m.item_id = i.id
                         JOIN events e ON m.event_id = e.id
                         WHERE m.type = 'ship' AND m.qty > 0 AND e.active = 1''')
        rows = self.c.fetchall()
        if not rows:
            self.return_layout.add_widget(Label(text="Нет активных отгрузок", size_hint_y=None, height=30))
            return
        for ship_id, name, event_name, qty_left in rows:
            row_box = BoxLayout(size_hint_y=None, height=45, spacing=5)
            lbl = Label(text=f"{name} с «{event_name}» (ост. {qty_left})", size_hint_x=0.7)
            btn = Button(text="Вернуть всё", size_hint_x=0.3, background_color=(0.9, 0.5, 0.2, 1))
            btn.bind(on_press=lambda x, sid=ship_id, n=name, q=qty_left: self.do_return(sid, n, q))
            row_box.add_widget(lbl)
            row_box.add_widget(btn)
            self.return_layout.add_widget(row_box)

    def do_return(self, ship_id, name, qty_left):
        # Возвращаем остаток на склад
        item_id = self.c.execute("SELECT item_id FROM movements WHERE id=?", (ship_id,)).fetchone()[0]
        self.c.execute("UPDATE items SET stock = stock + ? WHERE id = ?", (qty_left, item_id))
        self.c.execute("UPDATE movements SET qty = 0 WHERE id = ?", (ship_id,))
        self.conn.commit()
        self.root.add_widget(Label(text=f"Возвращено: {name} x{qty_left}",
                                   size_hint_y=None, height=30))
        self.refresh_return_list()

    # ---------- 5. ОСТАТКИ ----------
    def show_stock(self):
        self.clear_root()
        self.root.add_widget(Label(text="Остатки на складе", size_hint_y=None, height=40, font_size='16sp'))
        layout = GridLayout(cols=1, spacing=3, size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))
        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(layout)
        self.root.add_widget(scroll)

        self.c.execute("SELECT name, stock FROM items ORDER BY name")
        rows = self.c.fetchall()
        if not rows:
            layout.add_widget(Label(text="Склад пуст", size_hint_y=None, height=30))
        else:
            for name, stock in rows:
                layout.add_widget(Label(text=f"{name}: {stock} шт.", size_hint_y=None, height=30))

        # Показываем активные мероприятия и что там
        self.root.add_widget(Label(text="[b]На мероприятиях:[/b]", markup=True, size_hint_y=None, height=30))
        event_layout = GridLayout(cols=1, spacing=3, size_hint_y=None)
        event_layout.bind(minimum_height=event_layout.setter('height'))
        scroll2 = ScrollView(size_hint=(1, 0.5))
        scroll2.add_widget(event_layout)
        self.root.add_widget(scroll2)

        self.c.execute('''SELECT e.name, i.name, m.qty
                         FROM movements m
                         JOIN items i ON m.item_id = i.id
                         JOIN events e ON m.event_id = e.id
                         WHERE m.type = 'ship' AND m.qty > 0 AND e.active = 1''')
        ev_rows = self.c.fetchall()
        if not ev_rows:
            event_layout.add_widget(Label(text="Нет активных отгрузок", size_hint_y=None, height=30))
        else:
            for event_name, item_name, qty in ev_rows:
                event_layout.add_widget(Label(text=f"{event_name}: {item_name} — {qty} шт.",
                                               size_hint_y=None, height=30))

        self.add_back_button()

    # ---------- КНОПКА НАЗАД ----------
    def add_back_button(self):
        btn = Button(text="← Назад в меню", size_hint_y=None, height=45,
                     background_color=(0.7, 0.7, 0.7, 1))
        btn.bind(on_press=lambda x: self.show_main_menu())
        self.root.add_widget(btn)

if __name__ == '__main__':
    SouvenirsApp().run()
