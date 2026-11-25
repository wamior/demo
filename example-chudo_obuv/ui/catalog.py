import tkinter as tk
from tkinter import messagebox, ttk
from decimal import Decimal

import psycopg

from data.database import (load_products, find_user, get_product_details, validate_quantity, save_order)

from config import ASSETS_DIR, PRODUCT_IMAGES_DIR


class CatalogApp:
    def __init__(self):
        self.root = tk.Tk()
        self.current_user = None
        self.basket = {}

        self.root.title("Чудо Обувь — каталог товаров")
        self.root.geometry("1000x650")
        self.root.minsize(900, 500)
        self.root.configure(bg="#FFFFFF")
        self.icon_photo = self.load_asset_image(
            "Чудо Обувь.png",
            64,
            64,
        )

        if self.icon_photo is not None:
            self.root.iconphoto(True, self.icon_photo)

        self.create_header()
        self.create_filters()
        self.create_catalog_area()

        self.root.after(100, self.refresh_catalog)

    def load_asset_image(self, file_name, max_width, max_height):
        path = ASSETS_DIR / file_name

        try:
            photo = tk.PhotoImage(
                master=self.root,
                file=str(path),
            )

            factor = max(
                1,
                (photo.width() + max_width - 1) // max_width,
                (photo.height() + max_height - 1) // max_height,
            )

            return photo.subsample(factor, factor)

        except tk.TclError as error:
            print(f"Не удалось открыть {path}: {error}")
            return None

    def create_header(self):
        self.header = tk.Frame(
            self.root,
            bg="#D2F6E7",
            padx=16,
            pady=12,
        )
        self.header.pack(fill="x")


        self.header.grid_columnconfigure(1, weight=1)


        self.logo_photo = self.load_asset_image(
            "Чудо Обувь.png",
            64,
            64,
        )

        if self.logo_photo is not None:
            self.logo_label = tk.Label(
                self.header,
                image=self.logo_photo,
                bg="#D2F6E7",
            )
            self.logo_label.grid(
                row=0,
                column=0,
                padx=(0, 14),
                sticky="w",
            )

        # Название приложения.
        self.title_label = tk.Label(
            self.header,
            text="Чудо Обувь",
            bg="#D2F6E7",
            font=("Calibri", 22, "bold"),
            anchor="w",
        )
        self.title_label.grid(
            row=0,
            column=1,
            sticky="w",
        )


        self.account_panel = tk.Frame(
            self.header,
            bg="#D2F6E7",
        )
        self.account_panel.grid(
            row=0,
            column=2,
            padx=(16, 0),
            sticky="e",
        )

        self.account_label = tk.Label(
            self.account_panel,
            text="Гость",
            bg="#D2F6E7",
            font=("Calibri", 11),
            justify="right",
            anchor="e",
            wraplength=280,
        )
        self.account_label.pack(anchor="e")


        self.toolbar = tk.Frame(
            self.root,
            bg="#FFFFFF",
            padx=16,
            pady=10,
        )
        self.toolbar.pack(fill="x")
        self.toolbar.grid_columnconfigure(0, weight=1)

        self.section_label = tk.Label(
            self.toolbar,
            text="Каталог товаров",
            bg="#FFFFFF",
            font=("Calibri", 16, "bold"),
            anchor="w",
        )
        self.section_label.grid(
            row=0,
            column=0,
            sticky="w",
        )

        self.refresh_button = tk.Button(
            self.toolbar,
            text="Обновить",
            command=self.refresh_catalog,
            bg="#70B2AF",
            font=("Calibri", 11),
            padx=12,
            pady=5,
        )
        self.refresh_button.grid(
            row=0,
            column=1,
            padx=(12, 0),
        )

        self.cart_button = tk.Button(
            self.toolbar,
            text="Корзина",
            command=self.show_cart,
            state="disabled",
            bg="#70B2AF",
            font=("Calibri", 11),
            padx=12,
            pady=5,
        )
        self.cart_button.grid(
            row=0,
            column=2,
            padx=(8, 0),
        )

        self.login_button = tk.Button(
            self.toolbar,
            text="Войти",
            command=self.show_login,
            bg="#70B2AF",
            font=("Calibri", 11),
            padx=12,
            pady=5,
        )
        self.login_button.grid(
            row=0,
            column=3,
            padx=(8, 0),
        )


        self.status_label = tk.Label(
            self.root,
            text="Загрузка каталога...",
            bg="#FFFFFF",
            font=("Calibri", 11),
            anchor="w",
            padx=16,
            pady=6,
        )
        self.status_label.pack(fill="x")

    def create_catalog_area(self):
        self.catalog_area = tk.Frame(
            self.root,
            bg="#FFFFFF",
        )
        self.catalog_area.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(
            self.catalog_area,
            bg="#FFFFFF",
            highlightthickness=0,
        )

        self.scrollbar = tk.Scrollbar(
            self.catalog_area,
            orient="vertical",
            command=self.canvas.yview,
        )

        self.canvas.configure(
            yscrollcommand=self.scrollbar.set,
        )

        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(
            side="left",
            fill="both",
            expand=True,
        )

        self.cards_frame = tk.Frame(
            self.canvas,
            bg="#FFFFFF",
        )

        self.catalog_window = self.canvas.create_window(
            (0, 0),
            window=self.cards_frame,
            anchor="nw",
        )

        self.cards_frame.bind(
            "<Configure>",
            self.update_scroll_region,
        )

        self.canvas.bind(
            "<Configure>",
            self.update_catalog_width,
        )

    def update_scroll_region(self, event):
        self.canvas.configure(
            scrollregion=self.canvas.bbox("all"),
        )

    def update_catalog_width(self, event):
        self.canvas.itemconfigure(
            self.catalog_window,
            width=event.width,
        )

    def refresh_catalog(self):
        try:
            products = load_products()

        except psycopg.Error as error:
            self.status_label.configure(
                text="Не удалось загрузить каталог",
            )

            messagebox.showerror(
                "Ошибка загрузки",
                "Не удалось получить товары из PostgreSQL.\n"
                "Проверьте подключение и настройки config.py.\n\n"
                f"Подробности: {error}",
                parent=self.root,
            )
            return

        self.products = products
        categories = ['Все категории'] + sorted({
            p['category'] for p in products if p['category']
        })
        self.category_box.configure(value=categories)
        if self.category_var.get() not in categories:
            self.category_var.set('Все категории')
        self.apply_filters()

    def load_product_image(self, image_path):
        paths = []

        if image_path:
            file_name = str(image_path).strip()
            paths.append(PRODUCT_IMAGES_DIR / file_name)

        paths.append(ASSETS_DIR / "picture.png")

        for path in paths:
            try:
                photo = tk.PhotoImage(
                    master=self.root,
                    file=str(path),
                )

                factor = max(
                    1,
                    (photo.width() + 129) // 130,
                    (photo.height() + 129) // 130,
                )

                return photo.subsample(factor, factor)

            except tk.TclError:
                continue

        return None

    def create_product_card(self, product):
        quantity = product["total_quantity"]

        if quantity <= 3:
            background = "#ff8080"
        else:
            background = "#FFFFFF"

        card = tk.Frame(
            self.cards_frame,
            bg=background,
            bd=1,
            relief="solid",
            padx=12,
            pady=12,
        )
        card.pack(fill="x", padx=12, pady=6)

        card.grid_columnconfigure(1, weight=1)

        photo = self.load_product_image(
            product["image_path"]
        )

        image_label = tk.Label(
            card,
            bg=background,
        )

        if photo is not None:
            image_label.configure(
                image=photo,
                width=140,
                height=140,
            )


            image_label.image = photo

        else:
            image_label.configure(
                text="Изображение\nнедоступно",
                font=("Calibri", 12),
                width=14,
                height=6,
            )

        image_label.grid(
            row=0,
            column=0,
            rowspan=2,
            padx=(0, 15),
        )

        title = (
            f'{product["manufacturer"]} | '
            f'{product["product_name"]}'
        )

        title_label = tk.Label(
            card,
            text=title,
            bg=background,
            font=("Calibri", 14, "bold"),
            anchor="w",
            justify="left",
            wraplength=680,
        )
        title_label.grid(
            row=0,
            column=1,
            sticky="nsew",
        )

        composition = product["composition"] or "Не указан"

        details = (
            f'Категория: {product["category"]}\n'
            f'Количество: {quantity} пар\n'
            f'Состав: {composition}'
        )

        details_label = tk.Label(
            card,
            text=details,
            bg=background,
            font=("Calibri", 12),
            anchor="w",
            justify="left",
            wraplength=450,
        )
        details_label.grid(
            row=1,
            column=1,
            sticky="nw",
            pady=(8, 0),
        )

        price_frame = tk.Frame(
            card,
            bg=background,
        )
        price_frame.grid(
            row=0,
            column=2,
            rowspan=2,
            sticky="ne",
            padx=(15, 0),
        )

        price_text = f'{product["final_price"]:,.2f}'
        price_text = price_text.replace(",", " ")
        price_text = price_text.replace(".", ",")

        price_label = tk.Label(
            price_frame,
            text=price_text + " ₽",
            bg=background,
            font=("Calibri", 17, "bold"),
        )
        price_label.pack(anchor="e")

        if not product["has_orders"]:
            discount_label = tk.Label(
                price_frame,
                text="Скидка 25%",
                bg=background,
                font=("Calibri", 11),
            )
            discount_label.pack(anchor="e")
        tk.Button(
            price_frame,
            text="Подробнее",
            command=lambda pid=product['product_id']: self.show_product(pid),
            bg='#70B2AF',
            font=('Calibri', 11),
        ).pack(anchor='e', pady=8)

        for widget in (card, image_label, title_label, details_label):
            widget.configure(cursor='hand2')
            widget.bind(
                "<Button-1>",
                lambda event, pid=product['product_id']: self.show_product(pid)
            )

    def create_filters(self):
        self.products = []
        self.search_var = tk.StringVar()
        self.category_var = tk.StringVar(value='Все категории')
        self.sort_var = tk.StringVar(value='Без сортировки')
        self.filters_frame = tk.Frame(self.root, bg='#FFFFFF', padx=15, pady=8)
        tk.Label(self.filters_frame, text='Поиск:', bg='#FFFFFF').pack(side='left')
        tk.Entry(self.filters_frame, textvariable=self.search_var, width=25).pack(side='left', padx=6)
        self.category_box = ttk.Combobox(
            self.filters_frame, textvariable=self.category_var,
            state='readonly', width=23, values=['Все категории']
        )
        self.category_box.pack(side='left', padx=6)
        ttk.Combobox(
            self.filters_frame, textvariable=self.sort_var,
            state='readonly', width=23,
            values=['Без сортировки', 'Цена по возрастанию', 'Цена по убыванию']
        ).pack(side='left', padx=6)
        for variable in (self.search_var, self.category_var, self.sort_var):
            variable.trace_add('write', self.apply_filters)

    def update_account(self):
        if self.current_user:
            fio = ' '.join(self.current_user[k] for k in ('last_name', 'first_name', 'middle_name')
                          if self.current_user[k])
            self.account_label.configure(text=fio + '\n' + self.current_user['role_name'])
            self.login_button.configure(text='Выйти', command=self.logout)
            self.cart_button.configure(state='normal')
            self.filters_frame.pack(fill='x', before=self.catalog_area)
        else:
            self.account_label.configure(text='Гость')
            self.login_button.configure(text='Войти', command=self.show_login)
            self.cart_button.configure(state='disabled')
            self.filters_frame.pack_forget()

    def show_login(self):
        self.root.title('Чудо Обувь - вход')
        window = tk.Toplevel(self.root)
        window.title('Вход в систему')
        window.geometry('430x240')
        window.configure(bg='#FFFFFF')
        window.grab_set()
        window.protocol('WM_DELETE_WINDOW', self.close_app)
        tk.Label(window, text='Введите логин', bg='#FFFFFF', font=('Calibri', 13)
                 ).pack(pady=20)
        login_var = tk.StringVar()
        entry = tk.Entry(window, textvariable=login_var, width=30)
        entry.pack(pady=8)
        entry.focus_set()

        def finish(user):
            self.current_user = user
            window.destroy()
            self.update_account()
            self.root.title('Чудо Обувь - каталог товаров')
            self.refresh_catalog()
        def enter():
            try:
                if not login_var.get().strip():
                    raise ValueError('Введите логин.')
                user = find_user(login_var.get())
                if user is None:
                    raise ValueError('Такой логин не найден.')
                finish(user)
            except (psycopg.Error, ValueError) as error:
                self.show_error(error, window)

        tk.Button(window, text='Войти', command=enter, bg='#70B2AF').pack(pady=5)
        tk.Button(window, text='Продолжить как гость',
                command=lambda: finish(None), bg='#70B2AF').pack(pady=5)

        entry.bind('<Return>', lambda event: enter())

    def apply_filters(self, *args):
        if not hasattr(self, 'cards_frame'):
            return
        rows = self.products[:]
        if self.current_user:
            text = self.search_var.get().strip().casefold()
            category = self.category_var.get()
            rows = [p for p in rows
                    if (category == 'Все категории' or p['category'] == category)
                    and (not text or text in p['product_name'].casefold()
                         or text in (p['description'] or '').casefold())]
            if self.sort_var.get() == 'Цена по возрастанию':
                rows.sort(key=lambda p: p['final_price'])
            elif self.sort_var.get() == 'Цена по убыванию':
                rows.sort(key=lambda p: p['final_price'], reverse=True)

        for widget in self.cards_frame.winfo_children():
            widget.destroy()
        for product in rows:
            self.create_product_card(product)
        self.status_label.configure(text=f'Найдено моделей: {len(rows)} из {len(self.products)}')
        if not rows:
            tk.Label(self.cards_frame, text='Ничего не найдено',
                     bg='#FFFFFF', font=('Calibri', 14), pady=30).pack()
        self.canvas.yview_moveto(0)

    def create_module_window(self, title):
        window = tk.Toplevel(self.root)
        window.title('Чудо Обувь - ' + title)
        window.geometry('960x700')
        window.minsize(900, 600)
        window.configure(bg='#FFFFFF')
        window.transient(self.root)
        bar = tk.Frame(window, bg='#D2F6E7', padx=12, pady=10)
        bar.pack(fill='x')
        if self.logo_photo is not None:
            tk.Label(bar, image=self.logo_photo, bg='#D2F6E7').pack(side='left')
        tk.Button(bar, text='Назад', command=window.destroy, bg='#70B2AF').pack(side='left', padx=10)
        tk.Label(bar, text=title, bg='#D2F6E7', font=('Calibri', 15, 'bold')).pack(side='left')
        tk.Label(bar, text=self.account_label.cget('text'), bg='#D2F6E7',
                 justify='right').pack(side='right')
        window.wait_visibility()
        window.grab_set()
        return window
    def show_product(self, product_id):
        try:
            product, sizes = get_product_details(product_id)
        except (psycopg.Error, ValueError) as error:
            self.show_error(error)
            return
        window = self.create_module_window('Просмотр модели')
        canvas = tk.Canvas(window, bg='#FFFFFF', highlightthickness=0)
        scroll = tk.Scrollbar(window, command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)

        scroll.pack(side='right', fill='y')
        canvas.pack(fill='both', expand=True)
        body = tk.Frame(canvas, bg='#FFFFFF', pady=12, padx=20)
        item_id = canvas.create_window((0, 0), window=body, anchor='nw')
        body.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind('Configure>', lambda e: canvas.itemconfigure(item_id, width=e.width))
        photo = self.load_product_image(product['image_path'])
        if photo is not None:
            image = tk.Label(body, image=photo, bg='#FFFFFF')
            image.image = photo
            image.pack()
        texts = [f'{product["manufacturer"]} | {product["product_name"]}',
                 f'Категория: {product["category"]}',
                 f'Цена: {product["final_price"]:.2f} руб.' + (' (скидка 25%)' if not product["has_orders"] else ''),
                 'Состав: ' + (product['composition']),
                 'Описание: ' + (product['description']),
                 'Размерный ряд: ' + (', '.join(str(s['size_value']) for s in sizes))]
        for text in texts:
            tk.Label(body, text=text, bg='#FFFFFF', justify='left',
                     wraplength=820, font=('Calibri', 12)).pack(anchor='w', pady=5)
        for size in sizes:
            tk.Label(body, text=f'Размер {size["size_value"]}: {size["quantity_available"]} пар',
                     bg='#FFFFFF').pack(anchor='w')
        if not self.current_user:
            tk.Label(body, text='Для заказа войдите по логину', bg='#FFFFFF').pack(pady=15)
            return
        available = [s for s in sizes if s['quantity_available'] > 0]
        if not available:
            tk.Label(body, text='Нет доступных размеров', bg='#FFFFFF').pack(pady=15)
            return
        size_var = tk.StringVar(value=str(available[0]['size_value']))
        quantity_var = tk.StringVar(value='1')
        tk.Label(body, text='Размер', bg='#FFFFFF').pack(anchor='w')
        ttk.Combobox(body, textvariable=size_var, state='readonly',
                     values=[str(s["size_value"]) for s in available]).pack(anchor='w')
        tk.Label(body, text='Введите количество:', bg='#FFFFFF').pack(anchor='w')
        tk.Entry(body, textvariable=quantity_var, width=12). pack(anchor='w', pady=5)

        def add():
            try:
                quantity = validate_quantity(quantity_var.get())
                fresh, fresh_sizes = get_product_details(product_id)
                stock = next((s for s in fresh_sizes
                              if str(s['size_value']) == size_var.get()), None)
                if stock is None:
                    raise ValueError('Размер недоступен. Откройте модель заново.')
                sid = stock['stock_item_id']
                quantity += self.basket.get(sid, {}).get('quantity', 0)
                if quantity > stock['quantity_available']:
                    raise ValueError(f'Доступно {stock["quantity_available"]} пар; '
                                     f'с учётом корзины запрошено {quantity}.')
                self.basket[sid] = dict(
                    product_id=product_id, size_id=stock['size_id'],
                    size_value=stock['size_value'], product_name=fresh['product_name'],
                    quantity=quantity, price=fresh['final_price'],
                    available=stock['quantity_available'])
                messagebox.showinfo('Добавлено', 'Позиция добавлена в корзину.', parent=window)
            except (psycopg.Error, ValueError) as error:
                messagebox.showerror('Не удалось добавить товар', str(error), parent=window)

        def cart():
            window.destroy()
            self.show_cart()

        tk.Button(body, text='Добавить в заказ', command=add, bg='#70B2AF').pack(anchor='w', pady=5)
        tk.Button(body, text='Перейти в корзину', command=cart, bg='#70B2AF').pack(anchor='w', pady=5)

    def basket_sum(self):
        return sum((item['price'] * item['quantity'] for item in self.basket.values()), Decimal('0.00'))

    def refresh_basket(self):
        updated = {}
        for sid, item in self.basket.items():
            product, sizes = get_product_details(item['product_id'])
            stock = next((s for s in sizes if s['stock_item_id'] == sid), None)
            if stock is None:
                raise ValueError('Позиция удалена из БД. Удалите её из корзины.')
            updated[sid] = dict(item, price=product['final_price'],
                                product_name=product['product_name'],
                                available=stock['quantity_available'])
        # Заменяем только после успешного чтения всех строк.
        self.basket = updated

    def show_cart(self):
        if not self.current_user:
            messagebox.showwarning('Требуется вход', 'Войдите по логину.', parent=self.root)
            return
        try:
            self.refresh_basket()
        except (psycopg.Error, ValueError) as error:
            self.show_error(error)
            # Оставляем старые строки доступными для удаления.
        window = self.create_module_window('Корзина')
        columns = ('name', 'size', 'quantity', 'available', 'price', 'sum')
        tree = ttk.Treeview(window, columns=columns, show='headings', selectmode='browse')
        for col, title, width in zip(columns,
                                     ('Модель', 'Размер', 'Пар', 'Доступно', 'Цена', 'Сумма'),
                                     (330, 70, 70, 80, 100, 110)):
            tree.heading(col, text=title)
            tree.column(col, width=width, stretch=(col == 'name'))
        area = tk.Frame(window, bg='#FFFFFF')
        area.pack(side='bottom', fill='x', padx=12, pady=12)
        total_label = tk.Label(area, bg='#FFFFFF', font=('Calibri', 14, 'bold'))
        total_label.pack(anchor='e')
        scroll = ttk.Scrollbar(window, command=tree.yview)
        scroll.pack(side='right', fill='y')
        tree.configure(yscrollcommand=scroll.set)
        tree.pack(fill='both', expand=True, padx=12, pady=12)
        quantity_var = tk.StringVar(value='1')
        tk.Label(area, text='Количество для выбранной строки:', bg='#FFFFFF').pack(anchor='w')
        tk.Entry(area, textvariable=quantity_var, width=12).pack(anchor='w', pady=5)

        def redraw():
            tree.delete(*tree.get_children())
            for sid, item in self.basket.items():
                tree.insert('', 'end', iid=str(sid), values=(
                    item['product_name'], item['size_value'], item['quantity'],
                    item['available'], f'{item["price"]:.2f}',
                    f'{item["price"] * item["quantity"]:.2f}'))
            total_label.configure(text=f'Итого: {self.basket_sum():.2f} ₽')

        def selected_id():
            if not tree.selection():
                raise ValueError('Сначала выберите строку корзины.')
            return int(tree.selection()[0])

        def select(event):
            if tree.selection():
                quantity_var.set(str(self.basket[selected_id()]['quantity']))

        tree.bind('<<TreeviewSelect>>', select)

        def change():
            try:
                sid = selected_id()
                quantity = validate_quantity(quantity_var.get())
                self.refresh_basket()
                if quantity > self.basket[sid]['available']:
                    raise ValueError('Количество превышает доступный остаток.')
                self.basket[sid]['quantity'] = quantity
                redraw()
            except (psycopg.Error, ValueError) as error:
                self.show_error(error, window)

        def remove():
            try:
                sid = selected_id()
                if messagebox.askyesno('Удаление', 'Убрать позицию из заказа?', parent=window):
                    del self.basket[sid]
                    redraw()
            except ValueError as error:
                self.show_error(error, window)

        def update():
            try:
                self.refresh_basket()
                redraw()
            except (psycopg.Error, ValueError) as error:
                self.show_error(error, window)

        def cancel():
            if messagebox.askyesno('Отказ от заказа', 'Очистить корзину без сохранения?', parent=window):
                self.basket.clear()
                window.destroy()

        def confirm():
            if not self.basket:
                messagebox.showwarning('Пустая корзина', 'Добавьте хотя бы одну позицию.', parent=window)
                return
            if not messagebox.askyesno('Подтверждение',
                                       f'Оформить заказ на {self.basket_sum():.2f} ₽?', parent=window):
                return
            try:
                order_id = save_order(self.current_user['user_id'], self.basket)
            except (psycopg.Error, ValueError) as error:
                self.show_error(error, window)
                return
            self.basket.clear()
            window.destroy()
            messagebox.showinfo('Готово', f'Заказ №{order_id} сохранён.', parent=self.root)
            self.refresh_catalog()

        buttons = tk.Frame(area, bg='#FFFFFF')
        buttons.pack(fill='x', pady=8)
        for text, command in [('Изменить', change), ('Удалить', remove),
                              ('Обновить корзину', update), ('Отказаться', cancel),
                              ('Подтвердить', confirm)]:
            tk.Button(buttons, text=text, command=command,
                      bg='#70B2AF', padx=8, pady=5).pack(side='left', padx=4)
        redraw()

    def logout(self):
        if self.basket and not messagebox.askyesno('Выход',
                                                   'Корзина будет очищена. Продолжить?', parent=self.root):
            return
        self.basket.clear()
        self.current_user = None
        self.search_var.set('')
        self.category_var.set('Все категории')
        self.sort_var.set('Без сортировки')
        self.update_account()
        self.apply_filters()
        self.show_login()

    def close_app(self):
        if self.basket and not messagebox.askyesno('Закрытие',
                                                   'Корзина не сохранена. Закрыть программу?', parent=self.root):
            return
        self.root.destroy()

    def run(self):
        self.root.mainloop()
