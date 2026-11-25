# Tkinter: практическая база для экзамена

Краткий справочник по созданию оконных приложений на Python с Tkinter.
Примеры ориентированы на типовые задания: каталог, поиск и фильтрация,
просмотр записи, корзина и сообщения об ошибках.

## 1. Как устроен Tkinter

В Tkinter интерфейс состоит из:

1. **Окон** — главного `Tk()` и дополнительных `Toplevel()`.
2. **Виджетов** — кнопок, подписей, полей, таблиц и контейнеров.
3. **Обработчиков** — функций, которые запускаются при нажатии кнопки,
   выборе значения или другом событии.
4. **Цикла событий** — `mainloop()`, который ждёт действий пользователя
   и обновляет окно.

Обычно приложение создаёт один экземпляр `Tk()`. Для дополнительных окон
используется `Toplevel()`. Не создавай второй `Tk()` для каждого экрана.

## 2. Минимальное приложение

```python
import tkinter as tk
from tkinter import ttk


root = tk.Tk()
root.title("Моё приложение")
root.geometry("800x500")
root.minsize(600, 400)

title = ttk.Label(root, text="Главная страница")
title.pack(padx=16, pady=16)

root.mainloop()
```

`mainloop()` обычно вызывается один раз, в точке запуска приложения.
Пока он работает, Tkinter обрабатывает кнопки и другие события. Не создавай
собственный бесконечный цикл для интерфейса и не вызывай `mainloop()` для
каждой кнопки.

## 3. Контейнеры и расположение

`Frame` группирует виджеты. Это помогает строить интерфейс из панелей:
шапка, панель фильтров, область списка и строка состояния.

У Tkinter есть три менеджера размещения:

- `pack()` — расположить элементы рядом или один за другим;
- `grid()` — расположить элементы в строках и столбцах;
- `place()` — задавать точные координаты.

Для обычных экранов чаще всего достаточно `pack()` и `grid()`. Не смешивай
`pack()` и `grid()` **внутри одного и того же контейнера**. В разных
`Frame` можно использовать разные менеджеры.

```python
header = ttk.Frame(root, padding=12)
header.pack(fill="x")

header.columnconfigure(1, weight=1)
ttk.Label(header, text="Каталог").grid(row=0, column=0, sticky="w")
ttk.Button(header, text="Обновить").grid(row=0, column=2, sticky="e")
```

Полезные параметры:

- `fill="x"` или `fill="both"` — растянуть по ширине или в обе стороны;
- `expand=True` — разрешить элементу занимать свободное место;
- `padx`, `pady` — внешние отступы;
- `sticky="nsew"` — растянуть элемент внутри ячейки `grid`;
- `columnconfigure(..., weight=1)` — разрешить столбцу расти при изменении окна.

## 4. Основные виджеты

| Виджет | Для чего нужен |
|---|---|
| `ttk.Frame` / `tk.Frame` | Контейнер для других виджетов |
| `ttk.Label` / `tk.Label` | Подпись или текст |
| `ttk.Button` / `tk.Button` | Действие по нажатию |
| `ttk.Entry` / `tk.Entry` | Ввод одной строки |
| `ttk.Combobox` | Выпадающий список |
| `ttk.Treeview` | Таблица или список записей |
| `tk.Canvas` | Область рисования, в том числе прокручиваемая |
| `tk.Scrollbar` / `ttk.Scrollbar` | Полоса прокрутки |

`ttk` содержит виджеты с системным оформлением. Виджеты из `tk` удобны,
когда нужен точный контроль цвета, фона или размера.

Выпадающий список с выбором только из предложенных значений:

```python
category_var = tk.StringVar(value="Все категории")

category_box = ttk.Combobox(
    root,
    textvariable=category_var,
    state="readonly",
    values=["Все категории", "Ботинки", "Кроссовки"],
)
category_box.pack()
```

## 5. Переменные Tkinter и ввод

`StringVar`, `IntVar` и `BooleanVar` связывают значение виджета с кодом.

```python
search_var = tk.StringVar()
entry = ttk.Entry(root, textvariable=search_var)
```

Прочитать или изменить значение:

```python
text = search_var.get()
search_var.set("Новый текст")
```

Проверять значение всё равно нужно в коде. Например, поле количества
возвращает строку, даже если пользователь ввёл цифры.

```python
def validate_quantity(value):
    text = value.strip()
    if not text.isascii() or not text.isdecimal():
        raise ValueError("Введите целое положительное количество.")

    quantity = int(text)
    if quantity < 1:
        raise ValueError("Количество должно быть не меньше одного.")

    return quantity
```

После преобразования в число отдельно проверь предметное ограничение:
например, количество не должно превышать остаток выбранного размера.

## 6. Кнопки и события

Для кнопки указывай функцию **без скобок**:

```python
button = ttk.Button(root, text="Сохранить", command=save)
```

Так правильно: Tkinter вызовет `save`, когда пользователь нажмёт кнопку.
Запись `command=save()` вызвала бы функцию сразу во время создания кнопки.

Когда нужны аргументы, используй `lambda`:

```python
ttk.Button(
    root,
    text="Подробнее",
    command=lambda: show_product(product_id),
)
```

Для событий виджета применяется `bind`. Функция-обработчик получает объект
события:

```python
def on_enter(event):
    submit_search()


entry.bind("<Return>", on_enter)
```

Типичные события:

- `"<Return>"` — Enter;
- `"<Button-1>"` — щелчок левой кнопкой мыши;
- `"<Configure>"` — изменение размера виджета.

Названия событий пишутся в угловых скобках. В обработчиках `bind` принимай
параметр `event`, даже если его данные не используются.

## 7. Обновление поиска, фильтра и сортировки

`trace_add("write", ...)` запускает обработчик при изменении связанной
переменной. Это подходит для поиска и фильтрации в реальном времени:

```python
search_var.trace_add(
    "write",
    lambda *_: apply_filters(),
)
category_var.trace_add(
    "write",
    lambda *_: apply_filters(),
)
sort_var.trace_add(
    "write",
    lambda *_: apply_filters(),
)
```

Пример порядка обработки списка:

```python
def apply_filters():
    rows = products[:]

    if selected_category != "Все категории":
        rows = [row for row in rows
                if row["category"] == selected_category]

    if search_text:
        rows = [row for row in rows
                if search_text in row["product_name"].casefold()
                or search_text in (row["description"] or "").casefold()]

    if sort_by_price:
        rows.sort(key=lambda row: row["price"])

    render_products(rows)
```

Сначала фильтруй и ищи, потом сортируй итоговый список. Не перезаписывай
исходный `products`: иначе при следующем поиске часть записей может потеряться.

## 8. Списки и таблицы

### Карточки как набор виджетов

Для каталога можно создать отдельный `Frame` на каждую запись. Перед
перерисовкой удали старые карточки:

```python
for widget in cards_frame.winfo_children():
    widget.destroy()

for product in products_to_show:
    create_product_card(product)
```

В обработчике карточки сохраняй идентификатор записи, а не только её
отображаемое название. Для изображения храни ссылку на `PhotoImage`, чтобы
Python не удалил объект, пока он показан:

```python
photo = tk.PhotoImage(file=str(image_path))
image_label.configure(image=photo)
image_label.image = photo
```

### Таблица `Treeview`

`Treeview` подходит для корзины и списка заказов:

```python
columns = ("name", "date")
tree = ttk.Treeview(root, columns=columns, show="headings")
tree.heading("name", text="Клиент")
tree.heading("date", text="Дата")
tree.pack(fill="both", expand=True)

tree.insert("", "end", iid="order-15", values=("Иванов И.И.", "2026-11-25"))
```

`iid` — идентификатор строки. Используй его, чтобы определить выбранную
запись:

```python
selection = tree.selection()
if not selection:
    raise ValueError("Сначала выберите запись.")

selected_order_id = selection[0]
```

Чтобы перерисовать строки:

```python
tree.delete(*tree.get_children())
```

## 9. Дополнительные окна и навигация

Создавай дополнительные окна через `Toplevel`, передавая главное окно как
родителя:

```python
window = tk.Toplevel(root)
window.title("Просмотр модели")
window.transient(root)

ttk.Button(window, text="Назад", command=window.destroy).pack()
```

Если окно должно быть модальным, можно запретить взаимодействие с главным
окном, пока пользователь не закроет новое:

```python
window.grab_set()
```

Для перехода на другой экран часто достаточно создать `Toplevel`. Для кнопки
возврата закрой его через `destroy()`. Не закрывай главное окно при обычном
переходе между экранами.

## 10. Диалоги и обработка ошибок

Используй сообщения подходящего типа и не скрывай причину ошибки:

```python
from tkinter import messagebox

try:
    quantity = validate_quantity(quantity_var.get())
    save_order(quantity)
except ValueError as error:
    messagebox.showerror(
        "Проверьте количество",
        str(error),
        parent=root,
    )
```

Полезные диалоги:

```python
messagebox.showinfo("Готово", "Заказ сохранён.", parent=root)
messagebox.showwarning("Корзина пуста", "Добавьте товар.", parent=root)
messagebox.showerror("Ошибка", "Не удалось загрузить данные.", parent=root)

confirmed = messagebox.askyesno(
    "Подтверждение",
    "Удалить заказ?",
    parent=root,
)
```

Не используй пустой `except` и не показывай сообщение об успехе, если
операция завершилась ошибкой. Для ожидаемых ошибок ввода обычно достаточно
`ValueError`; ошибки БД обрабатывай отдельно с учётом используемого драйвера.

## 11. Прокручиваемая область каталога

Для списка карточек, который длиннее окна, можно поместить `Frame` внутрь
`Canvas`:

```python
canvas = tk.Canvas(root, highlightthickness=0)
scrollbar = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)
canvas.configure(yscrollcommand=scrollbar.set)

scrollbar.pack(side="right", fill="y")
canvas.pack(side="left", fill="both", expand=True)

cards_frame = ttk.Frame(canvas)
window_id = canvas.create_window((0, 0), window=cards_frame, anchor="nw")

cards_frame.bind(
    "<Configure>",
    lambda event: canvas.configure(scrollregion=canvas.bbox("all")),
)
canvas.bind(
    "<Configure>",
    lambda event: canvas.itemconfigure(window_id, width=event.width),
)
```

Следи за точным написанием `"<Configure>"`: опечатка в имени события
приведёт к тому, что обработчик не вызовется.

## 12. Изображения и ресурсы

Для PNG и GIF можно использовать `tk.PhotoImage`:

```python
photo = tk.PhotoImage(master=root, file=str(image_path))
```

Если картинка товара не загрузилась, попробуй открыть изображение-заглушку.
Обрабатывай ошибку открытия ресурса и не оставляй карточку в состоянии,
которое мешает просмотру остальных товаров.

В Tkinter изображение нужно хранить в атрибуте или другом долгоживущем
объекте:

```python
self.product_photo = photo
image_label.configure(image=self.product_photo)
```

Для JPEG и некоторых операций изменения размера может понадобиться Pillow.
Перед использованием проверь, что библиотека установлена в среде запуска.

## 13. Обновление интерфейса и архитектура

Хорошее разделение для небольшого приложения:

```text
main.py          запуск приложения
config.py        настройки и пути
data/            запросы к БД и операции с данными
ui/              окна и виджеты
assets/          картинки, логотип, иконка
```

Слой интерфейса должен:

1. получить данные от слоя `data`;
2. показать их;
3. проверить ввод пользователя;
4. вызвать нужную операцию;
5. сообщить об успехе или ошибке;
6. обновить экран после успешного изменения.

После оформления заказа вызови обновление каталога, иначе количество на
экране останется старым. Для коротких запросов к БД в небольшом экзаменационном
приложении достаточно обычного вызова. Долгая работа в обработчике может
заморозить окно, потому что она выполняется в том же потоке, что и интерфейс.

## 14. Частые ошибки

- `command=save()` вместо `command=save`;
- создание нескольких экземпляров `Tk()`;
- смешивание `pack()` и `grid()` в одном контейнере;
- ожидание, что `Entry` автоматически возвращает число;
- отсутствие проверки выбранной строки в `Treeview`;
- уничтожение списка и забытое повторное заполнение;
- потеря ссылки на `PhotoImage`;
- неправильное имя события в `bind`;
- попытка открыть несуществующую картинку без заглушки;
- ошибка в callback, из-за которой интерфейс перестаёт реагировать;
- сохранение в БД без повторной проверки остатка и цены.

## 15. Минимальная схема нового экрана

Перед кодированием экрана запиши:

1. **Данные:** что экран получает и что хранит.
2. **Виджеты:** чем пользователь смотрит или вводит данные.
3. **Действия:** какие функции вызовут кнопки и события.
4. **Проверки:** какие значения могут быть неверными или устаревшими.
5. **Обновление:** что нужно перечитать или перерисовать после операции.

Такой разбор подходит и для каталога товаров, и для списка заказов, клиентов,
заявок или оборудования.

## Официальная документация

- [Tkinter](https://docs.python.org/3/library/tkinter.html)
- [ttk](https://docs.python.org/3/library/tkinter.ttk.html)
- [TkDocs: учебник по Tkinter](https://tkdocs.com/tutorial/)
