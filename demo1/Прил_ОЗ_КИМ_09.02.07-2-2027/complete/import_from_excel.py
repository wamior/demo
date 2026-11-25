import psycopg
from openpyxl import load_workbook
from decimal import Decimal

conn = psycopg.connect(host="31.77.226.172", port=5432, user="postgres", password="1234", dbname="postgres1")
cur = conn.cursor()

roles = {}

def users():
    wb = load_workbook("Users_import.xlsx")
    ws = wb.active
    for row in ws.iter_rows(min_row=2, values_only=True):
        surname, name, patronymic, login, role_name = row[:5]
        if role_name not in roles:
            cur.execute("INSERT INTO roles (role_name) VALUES (%s) RETURNING id", (role_name,))
            roles[role_name] = cur.fetchone()[0]
        cur.execute("INSERT INTO users (surname, name, patronymic, login, role_id) VALUES (%s, %s, %s, %s, %s)", (surname, name, patronymic, login, roles[role_name]))
    conn.commit()

def sizes():
    wb = load_workbook("Sizes_import.xlsx")
    ws = wb.active
    for row in ws.iter_rows(min_row=2, values_only=True):
        cur.execute("INSERT INTO sizes (size) VALUES (%s)", (row[0],))
    conn.commit()

def products():
    wb = load_workbook("Products_import.xlsx")
    ws = wb.active
    for row in ws.iter_rows(min_row=2, values_only=True):
        category, subcategory, image, name, production, description, compound, price = row[:8]
        cur.execute("INSERT INTO products (category, subcategory, image, name, production, description, compound, price) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (category, subcategory, image, name, production, description, compound, price))
    conn.commit()

def stocks():
    wb = load_workbook("Stock_Items_import.xlsx")
    ws = wb.active
    cur.execute("SELECT id, name FROM products")
    products_dict = {r[1].strip(): r[0] for r in cur.fetchall()}
    cur.execute("SELECT id, size FROM sizes")
    sizes_dict = {r[1]: r[0] for r in cur.fetchall()}
    for row in ws.iter_rows(min_row=2, values_only=True):
        name, production, size, count = row[0].strip(), row[1], row[2], row[3]
        product_id = products_dict.get(name)
        size_id = sizes_dict.get(Decimal(str(size)))
        if product_id is None:
            print(f"Товар не найден: '{name}'")
            continue
        if size_id is None:
            print(f"Размер не найден: '{size}'")
            continue
        cur.execute("INSERT INTO stocks (product_id, size_id, count) VALUES (%s, %s, %s)", (product_id, size_id, count))
    conn.commit()

def orders():
    wb = load_workbook("Orders_import.xlsx")
    ws = wb.active
    cur.execute("SELECT id, surname, name, patronymic FROM users")
    users_dict = {f"{r[1]} {r[2]} {r[3]}": r[0] for r in cur.fetchall()}
    seen_orders = set()
    for row in ws.iter_rows(min_row=2, values_only=True):
        order_id, order_date, full_name = row[0], row[1], row[2].strip()
        if order_id not in seen_orders:
            seen_orders.add(order_id)
            user_id = users_dict.get(full_name)
            if user_id is None:
                print(f"Пользователь не найден: '{full_name}'")
                continue
            cur.execute("INSERT INTO orders (order_date, user_id) VALUES (%s, %s)", (order_date, user_id))
    conn.commit()

def order_items():
    wb = load_workbook("Orders_import.xlsx")
    ws = wb.active
    cur.execute("""
        SELECT p.name, s.size, st.id
        FROM stocks st
        JOIN products p ON p.id = st.product_id
        JOIN sizes s ON s.id = st.size_id
    """)
    stocks_dict = {(r[0].strip(), Decimal(str(r[1]))): r[2] for r in cur.fetchall()}
    cur.execute("SELECT id FROM orders ORDER BY id")
    order_ids = [r[0] for r in cur.fetchall()]
    seen_orders = {}
    counter = 0
    for row in ws.iter_rows(min_row=2, values_only=True):
        order_id, order_date, full_name, category, name, production, size, quantity, unit_price = row[:9]
        if order_id not in seen_orders:
            seen_orders[order_id] = order_ids[counter]
            counter += 1
        real_order_id = seen_orders[order_id]
        stock_id = stocks_dict.get((name.strip(), Decimal(str(size))))
        if stock_id is None:
            print(f"Склад не найден: '{name}' размер {size}")
            continue
        cur.execute("INSERT INTO orders_item (order_id, stock_id, quantity, unit_price) VALUES (%s, %s, %s, %s)", (real_order_id, stock_id, quantity, unit_price))
    conn.commit()

users()
sizes()
products()
stocks()
orders()
order_items()