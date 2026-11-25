from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

import psycopg
from psycopg.rows import dict_row

from config import DB_SETTINGS

def get_previous_month_period(calculation_date):
    current_month_start = calculation_date.replace(day=1)

    previous_month_last_day = (
        current_month_start - timedelta(days=1)
    )
    previous_month_start = previous_month_last_day.replace(day=1)

    return previous_month_start, current_month_start

def calculate_price(price, has_orders):
    if has_orders:
        return price
    return (price * Decimal('0.75')).quantize(
        Decimal('0.01'),
        rounding=ROUND_HALF_UP,
    )

def load_products(calculation_date=None):
    if calculation_date is None:
        calculation_date = date.today()

    period_start, period_end = get_previous_month_period(calculation_date)

    query = """
        SELECT
            p.product_id,
            p.category,
            p.product_name,
            p.manufacturer,
            p.composition,
            p.description,
            p.image_path,
            p.price,
            
            COALESCE(
                (
                    SELECT SUM(s.quantity_available)
                    FROM public.stock_items AS s
                    WHERE s.product_id = p.product_id
                ),
                0
            ) AS total_quantity,
            
            EXISTS (
                SELECT 1
                FROM public.order_items AS oi
                JOIN public.orders AS o
                    ON o.order_id = oi.order_id
                WHERE oi.product_id = p.product_id
                  AND o.order_date >= %s
                  AND o.order_date < %s
            ) AS has_orders
        FROM public.products AS p
        ORDER BY p.product_id;
    """

    with psycopg.connect(
        **DB_SETTINGS,
        row_factory=dict_row,
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, (period_start, period_end))
            products = cursor.fetchall()

    for product in products:
        product['final_price'] = calculate_price(
            product['price'],
            product['has_orders'],
        )

    return products

def find_user(login):
    with psycopg.connect(**DB_SETTINGS, row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT u.user_id, u.last_name, u.first_name, u.middle_name,
                       u.login, r.role_name
                FROM public.users AS u
                JOIN public.roles AS r ON r.role_id = u.role_id
                WHERE u.login = %s
            """, (login.strip(),))
            return cursor.fetchone()

def get_product_details(product_id):
    # Повторно читаем модель: если цены или остатки изменились
    product = next((p for p in load_products()
                    if p['product_id'] == product_id), None)
    if product is None:
        raise ValueError('Модель не найдена. Обновите каталог.')
    with psycopg.connect(**DB_SETTINGS, row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT s.stock_item_id, s.product_id, s.size_id,
                       z.size_value, s.quantity_available
                FROM public.stock_items AS s
                JOIN public.sizes AS z ON z.size_id = s.size_id
                WHERE s.product_id = %s ORDER BY z.size_value
            """, (product_id,))
            return product, cursor.fetchall()

def validate_quantity(value):
    text = str(value).strip()
    if not text or not text.isascii() or not text.isdecimal():
        raise ValueError('Введите положительное целое число')
    quantity = int(text)
    if not 1 <= quantity <= 2147483647:
        raise ValueError('Количество должно быть от 1 до 2147483647.')
    return quantity

def save_order(user_id, basket):
    if not basket:
        raise ValueError('Корзина пуста.')
    quantities = {sid: validate_quantity(item['quantity'])
                  for sid, item in basket.items()}
    today = date.today()
    period_start, period_end = get_previous_month_period(today)
    with psycopg.connect(**DB_SETTINGS, row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT u.user_id FROM public.users AS u
                JOIN public.roles AS r ON r.role_id = u.role_id
                WHERE u.user_id = %s
            """, (user_id,))
            if cursor.fetchone() is None:
                raise ValueError('Пользователь не найден. Войдите заново.')

            position = []
            for sid in sorted(quantities):
                cursor.execute("""
                    SELECT * FROM public.stock_items
                    WHERE stock_item_id = %s FOR UPDATE
                """, (sid,))
                stock = cursor.fetchone()
                if stock is None or stock['quantity_available'] < quantities[sid]:
                    raise ValueError('Недостаточно товара. Уменьшите количество.')
                cursor.execute("""
                    SELECT p.price, EXISTS(
                        SELECT 1 FROM public.order_items AS oi
                        JOIN public.orders AS o on o.order_id = oi.order_id
                        WHERE oi.product_id = p.product_id
                        AND o.order_date >= %s AND o.order_date < %s) AS has_orders
                    FROM public.products AS p WHERE p.product_id = %s
                    """, (period_start, period_end, stock['product_id']))
                model = cursor.fetchone()
                if model is None:
                    raise ValueError('Модель удалена.')
                price = calculate_price(model['price'], model['has_orders'])
                if price != basket[sid]['price']:
                    raise ValueError('Цена изменилась. Обновите корзину.')
                position.append((stock, quantities[sid], price))

            cursor.execute("""
                INSERT INTO public.orders (order_date, user_id)
                VALUES (%s, %s) RETURNING order_id
                """, (today, user_id))
            order_id = cursor.fetchone()['order_id']
            for stock, quantity, price in position:
                cursor.execute("""
                    INSERT INTO public.order_items (
                        order_id, product_id, size_id, quantity, price)
                    VALUES (%s, %s, %s, %s, %s)
                """, (order_id, stock['product_id'], stock['size_id'], quantity, price))
                cursor.execute("""
                        UPDATE public.stock_items
                        SET quantity_available = quantity_available - %s
                        WHERE stock_item_id = %s
                        """, (quantity, stock['stock_item_id']))
        return order_id





















