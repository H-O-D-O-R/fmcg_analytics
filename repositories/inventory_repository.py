from database.connection import get_connection


class InventoryRepository:
    """
    Repository для аналитики складских запасов.

    SQL:
    - получает данные;
    - агрегирует;
    - формирует аналитические датасеты.

    pandas / numpy:
    - прогнозирование;
    - сложные скоринги;
    - нормализация;
    - визуализация.
    """

    # ============================================================
    # BASIC INVENTORY
    # ============================================================

    def total_stock(self):
        """Общее количество единиц товара на всех складах."""

        query = """
            SELECT
                COALESCE(SUM(quantity), 0) AS total_units
            FROM inventory
        """

        return self._fetch_one(query)


    def total_stock_value(self):
        """
        Общая стоимость текущих запасов.

        stock_value =
            quantity * актуальная себестоимость
        """

        query = """
            SELECT
                COALESCE(
                    SUM(
                        i.quantity * pp.cost_price
                    ),
                    0
                ) AS stock_value

            FROM inventory i

            JOIN product_prices pp
                ON pp.product_id = i.product_id

            WHERE
                pp.year = (
                    SELECT MAX(pp2.year)
                    FROM product_prices pp2
                    WHERE
                        pp2.product_id =
                        pp.product_id
                )
        """

        return self._fetch_one(query)


    def products_count_in_stock(self):
        """Количество товаров, которые сейчас есть на складе."""

        query = """
            SELECT
                COUNT(DISTINCT product_id)
                    AS products_count
            FROM inventory
            WHERE quantity > 0
        """

        return self._fetch_one(query)


    # ============================================================
    # CURRENT STOCK
    # ============================================================

    def current_stock(self):
        """
        Полный текущий остаток:

        - товар;
        - категория;
        - бренд;
        - склад;
        - количество.
        """

        query = """
            SELECT
                p.product_id,
                p.name AS product,

                c.name AS category,
                b.name AS brand,

                w.warehouse_id,
                w.name AS warehouse,

                i.quantity

            FROM inventory i

            JOIN products p
                ON p.product_id =
                   i.product_id

            LEFT JOIN categories c
                ON c.category_id =
                   p.category_id

            LEFT JOIN brands b
                ON b.brand_id =
                   p.brand_id

            JOIN warehouses w
                ON w.warehouse_id =
                   i.warehouse_id

            ORDER BY
                w.name,
                i.quantity DESC
        """

        return self._fetch_all(query)


    def stock_by_product(self):
        """Суммарный остаток каждого товара."""

        query = """
            SELECT
                p.product_id,
                p.name,

                SUM(i.quantity)
                    AS total_stock

            FROM products p

            JOIN inventory i
                ON i.product_id =
                   p.product_id

            GROUP BY
                p.product_id,
                p.name

            ORDER BY
                total_stock DESC
        """

        return self._fetch_all(query)


    def stock_by_category(self):
        """Остатки по категориям."""

        query = """
            SELECT
                c.category_id,
                c.name AS category,

                COUNT(
                    DISTINCT p.product_id
                ) AS products_count,

                SUM(i.quantity)
                    AS total_stock

            FROM categories c

            JOIN products p
                ON p.category_id =
                   c.category_id

            JOIN inventory i
                ON i.product_id =
                   p.product_id

            GROUP BY
                c.category_id,
                c.name

            ORDER BY
                total_stock DESC
        """

        return self._fetch_all(query)


    # ============================================================
    # LOW STOCK / OUT OF STOCK
    # ============================================================

    def low_stock_products(
        self,
        threshold=10
    ):
        """Товары с остатком ниже заданного порога."""

        query = """
            SELECT
                p.product_id,
                p.name,

                SUM(i.quantity)
                    AS current_stock

            FROM products p

            JOIN inventory i
                ON i.product_id =
                   p.product_id

            GROUP BY
                p.product_id,
                p.name

            HAVING
                SUM(i.quantity) < %s

            ORDER BY
                current_stock ASC
        """

        return self._fetch_all(
            query,
            (threshold,)
        )


    def out_of_stock_products(self):
        """
        Товары, которых нет в наличии.

        Используется LEFT JOIN,
        чтобы найти товары без остатков.
        """

        query = """
            SELECT
                p.product_id,
                p.name

            FROM products p

            LEFT JOIN inventory i
                ON i.product_id =
                   p.product_id

            GROUP BY
                p.product_id,
                p.name

            HAVING
                COALESCE(
                    SUM(i.quantity),
                    0
                ) = 0

            ORDER BY
                p.name
        """

        return self._fetch_all(query)


    # ============================================================
    # DEAD STOCK
    # ============================================================

    def dead_stock_products(self):
        """
        Dead stock.

        Товар есть на складе,
        но за весь период не было продаж.
        """

        query = """
            SELECT
                p.product_id,
                p.name,

                SUM(i.quantity)
                    AS stock_quantity

            FROM products p

            JOIN inventory i
                ON i.product_id =
                   p.product_id

            LEFT JOIN order_items oi
                ON oi.product_id =
                   p.product_id

            GROUP BY
                p.product_id,
                p.name

            HAVING
                SUM(i.quantity) > 0

                AND COUNT(
                    oi.product_id
                ) = 0

            ORDER BY
                stock_quantity DESC
        """

        return self._fetch_all(query)


    def inactive_stock(
        self,
        days=90
    ):
        """
        Товары, которые давно не продавались.

        days — количество дней без продаж.
        """

        query = """
            SELECT
                p.product_id,
                p.name,

                SUM(i.quantity)
                    AS stock_quantity,

                MAX(o.order_date)
                    AS last_sale_date,

                CURRENT_DATE -
                MAX(o.order_date)::DATE
                    AS days_since_sale

            FROM products p

            JOIN inventory i
                ON i.product_id =
                   p.product_id

            LEFT JOIN order_items oi
                ON oi.product_id =
                   p.product_id

            LEFT JOIN orders o
                ON o.order_id =
                   oi.order_id

            GROUP BY
                p.product_id,
                p.name

            HAVING
                SUM(i.quantity) > 0

                AND (
                    MAX(o.order_date) IS NULL
                    OR
                    CURRENT_DATE -
                    MAX(o.order_date)::DATE
                    > %s
                )

            ORDER BY
                days_since_sale DESC NULLS FIRST
        """

        return self._fetch_all(
            query,
            (days,)
        )


    # ============================================================
    # STOCK VALUE
    # ============================================================

    def stock_value_by_product(self):
        """Стоимость запасов каждого товара."""

        query = """
            WITH latest_prices AS (

                SELECT
                    pp.product_id,
                    pp.cost_price

                FROM product_prices pp

                JOIN (
                    SELECT
                        product_id,
                        MAX(year) AS max_year
                    FROM product_prices
                    GROUP BY product_id
                ) latest

                    ON latest.product_id =
                       pp.product_id

                    AND latest.max_year =
                        pp.year
            )

            SELECT
                p.product_id,
                p.name,

                SUM(i.quantity)
                    AS stock_quantity,

                lp.cost_price,

                SUM(i.quantity)
                * lp.cost_price
                    AS stock_value

            FROM products p

            JOIN inventory i
                ON i.product_id =
                   p.product_id

            JOIN latest_prices lp
                ON lp.product_id =
                   p.product_id

            GROUP BY
                p.product_id,
                p.name,
                lp.cost_price

            ORDER BY
                stock_value DESC
        """

        return self._fetch_all(query)


    def stock_value_by_category(self):
        """Стоимость запасов по категориям."""

        query = """
            WITH latest_prices AS (

                SELECT
                    pp.product_id,
                    pp.cost_price

                FROM product_prices pp

                JOIN (
                    SELECT
                        product_id,
                        MAX(year) AS max_year
                    FROM product_prices
                    GROUP BY product_id
                ) latest

                    ON latest.product_id =
                       pp.product_id

                    AND latest.max_year =
                        pp.year
            )

            SELECT
                c.category_id,
                c.name AS category,

                SUM(
                    i.quantity *
                    lp.cost_price
                ) AS stock_value

            FROM categories c

            JOIN products p
                ON p.category_id =
                   c.category_id

            JOIN inventory i
                ON i.product_id =
                   p.product_id

            JOIN latest_prices lp
                ON lp.product_id =
                   p.product_id

            GROUP BY
                c.category_id,
                c.name

            ORDER BY
                stock_value DESC
        """

        return self._fetch_all(query)


    # ============================================================
    # SALES VS STOCK
    # ============================================================

    def stock_and_sales(
        self,
        year=None
    ):
        """
        Сравнение текущего остатка
        с продажами.

        Это основной датасет для
        расчета оборачиваемости.
        """

        query = """
            WITH sales AS (

                SELECT
                    product_id,

                    SUM(quantity)
                        AS units_sold,

                    SUM(
                        quantity * price
                    ) AS revenue

                FROM order_items oi

                JOIN orders o
                    ON o.order_id =
                       oi.order_id

                WHERE
                    %s IS NULL

                    OR EXTRACT(
                        YEAR FROM o.order_date
                    ) = %s

                GROUP BY
                    product_id
            ),

            stock AS (

                SELECT
                    product_id,

                    SUM(quantity)
                        AS stock_quantity

                FROM inventory

                GROUP BY
                    product_id
            )

            SELECT
                p.product_id,
                p.name,

                COALESCE(
                    s.units_sold,
                    0
                ) AS units_sold,

                COALESCE(
                    s.revenue,
                    0
                ) AS revenue,

                COALESCE(
                    st.stock_quantity,
                    0
                ) AS stock_quantity

            FROM products p

            LEFT JOIN sales s
                ON s.product_id =
                   p.product_id

            LEFT JOIN stock st
                ON st.product_id =
                   p.product_id

            ORDER BY
                units_sold DESC
        """

        return self._fetch_all(
            query,
            (year, year)
        )


    # ============================================================
    # INVENTORY TURNOVER
    # ============================================================

    def inventory_turnover(
        self,
        year=None
    ):
        """
        Упрощенная оборачиваемость:

            sales / current_stock

        Более сложную версию с average inventory
        лучше считать в analytics через pandas.
        """

        query = """
            WITH sales AS (

                SELECT
                    product_id,

                    SUM(quantity)
                        AS units_sold

                FROM order_items oi

                JOIN orders o
                    ON o.order_id =
                       oi.order_id

                WHERE
                    %s IS NULL
                    OR EXTRACT(
                        YEAR FROM o.order_date
                    ) = %s

                GROUP BY
                    product_id
            ),

            stock AS (

                SELECT
                    product_id,

                    SUM(quantity)
                        AS stock_quantity

                FROM inventory

                GROUP BY
                    product_id
            )

            SELECT
                p.product_id,
                p.name,

                COALESCE(
                    s.units_sold,
                    0
                ) AS units_sold,

                COALESCE(
                    st.stock_quantity,
                    0
                ) AS stock_quantity,

                ROUND(
                    COALESCE(
                        s.units_sold,
                        0
                    )::NUMERIC
                    /
                    NULLIF(
                        st.stock_quantity,
                        0
                    ),
                    2
                ) AS turnover

            FROM products p

            LEFT JOIN sales s
                ON s.product_id =
                   p.product_id

            LEFT JOIN stock st
                ON st.product_id =
                   p.product_id

            ORDER BY
                turnover DESC NULLS LAST
        """

        return self._fetch_all(
            query,
            (year, year)
        )


    # ============================================================
    # INVENTORY COVERAGE
    # ============================================================

    def stock_coverage(
        self,
        year=None
    ):
        """
        Примерно сколько дней текущего
        остатка хватит при текущем темпе продаж.

            stock / average_daily_sales
        """

        query = """
            WITH sales AS (

                SELECT
                    product_id,

                    SUM(quantity)
                        AS units_sold,

                    COUNT(
                        DISTINCT DATE(
                            o.order_date
                        )
                    ) AS active_days

                FROM order_items oi

                JOIN orders o
                    ON o.order_id =
                       oi.order_id

                WHERE
                    %s IS NULL
                    OR EXTRACT(
                        YEAR FROM o.order_date
                    ) = %s

                GROUP BY
                    product_id
            ),

            stock AS (

                SELECT
                    product_id,
                    SUM(quantity)
                        AS stock_quantity

                FROM inventory

                GROUP BY
                    product_id
            )

            SELECT
                p.product_id,
                p.name,

                st.stock_quantity,
                s.units_sold,
                s.active_days,

                ROUND(
                    st.stock_quantity
                    /
                    NULLIF(
                        s.units_sold::NUMERIC
                        /
                        NULLIF(
                            s.active_days,
                            0
                        ),
                        0
                    ),
                    2
                ) AS estimated_days_left

            FROM products p

            JOIN stock st
                ON st.product_id =
                   p.product_id

            JOIN sales s
                ON s.product_id =
                   p.product_id

            ORDER BY
                estimated_days_left ASC
        """

        return self._fetch_all(
            query,
            (year, year)
        )


    # ============================================================
    # ABC STOCK ANALYSIS
    # ============================================================

    def abc_stock_analysis(self):
        """
        ABC-анализ запасов по стоимости.

        Показывает, какие товары
        формируют основную стоимость склада.
        """

        query = """
            WITH latest_prices AS (

                SELECT
                    pp.product_id,
                    pp.cost_price

                FROM product_prices pp

                JOIN (
                    SELECT
                        product_id,
                        MAX(year) AS max_year

                    FROM product_prices

                    GROUP BY product_id
                ) latest

                    ON latest.product_id =
                       pp.product_id

                    AND latest.max_year =
                        pp.year
            ),

            product_stock AS (

                SELECT
                    p.product_id,
                    p.name,

                    SUM(i.quantity)
                        AS stock_quantity,

                    SUM(i.quantity)
                    * lp.cost_price
                        AS stock_value

                FROM products p

                JOIN inventory i
                    ON i.product_id =
                       p.product_id

                JOIN latest_prices lp
                    ON lp.product_id =
                       p.product_id

                GROUP BY
                    p.product_id,
                    p.name,
                    lp.cost_price
            ),

            ranked AS (

                SELECT
                    product_id,
                    name,
                    stock_quantity,
                    stock_value,

                    SUM(stock_value)
                        OVER(
                            ORDER BY
                                stock_value DESC
                        )
                    /
                    NULLIF(
                        SUM(stock_value)
                            OVER(),
                        0
                    ) AS cumulative_share

                FROM product_stock
            )

            SELECT
                product_id,
                name,
                stock_quantity,
                stock_value,
                cumulative_share,

                CASE
                    WHEN cumulative_share <= 0.80
                        THEN 'A'

                    WHEN cumulative_share <= 0.95
                        THEN 'B'

                    ELSE 'C'
                END AS abc_class

            FROM ranked

            ORDER BY
                stock_value DESC
        """

        return self._fetch_all(query)


    # ============================================================
    # WAREHOUSE ANALYTICS
    # ============================================================

    def warehouse_load(self):
        """Количество товаров и запасов на каждом складе."""

        query = """
            SELECT
                w.warehouse_id,
                w.name AS warehouse,

                COUNT(
                    DISTINCT i.product_id
                ) AS products_count,

                COALESCE(
                    SUM(i.quantity),
                    0
                ) AS total_units

            FROM warehouses w

            LEFT JOIN inventory i
                ON i.warehouse_id =
                   w.warehouse_id

            GROUP BY
                w.warehouse_id,
                w.name

            ORDER BY
                total_units DESC
        """

        return self._fetch_all(query)


    def warehouse_stock_value(self):
        """Стоимость запасов по складам."""

        query = """
            WITH latest_prices AS (

                SELECT
                    pp.product_id,
                    pp.cost_price

                FROM product_prices pp

                JOIN (
                    SELECT
                        product_id,
                        MAX(year) AS max_year

                    FROM product_prices

                    GROUP BY product_id
                ) latest

                    ON latest.product_id =
                       pp.product_id

                    AND latest.max_year =
                        pp.year
            )

            SELECT
                w.warehouse_id,
                w.name AS warehouse,

                SUM(
                    i.quantity
                    * lp.cost_price
                ) AS stock_value

            FROM warehouses w

            JOIN inventory i
                ON i.warehouse_id =
                   w.warehouse_id

            JOIN latest_prices lp
                ON lp.product_id =
                   i.product_id

            GROUP BY
                w.warehouse_id,
                w.name

            ORDER BY
                stock_value DESC
        """

        return self._fetch_all(query)


    # ============================================================
    # RISK ANALYSIS
    # ============================================================

    def inventory_risk_dataset(
        self,
        year=None
    ):
        """
        Датасет для оценки риска товара.

        SQL собирает исходные показатели,
        а итоговый risk score лучше делать
        в pandas/numpy.
        """

        query = """
            WITH sales AS (

                SELECT
                    product_id,

                    SUM(quantity)
                        AS units_sold,

                    COUNT(
                        DISTINCT order_id
                    ) AS orders_count,

                    MAX(o.order_date)
                        AS last_sale_date

                FROM order_items oi

                JOIN orders o
                    ON o.order_id =
                       oi.order_id

                WHERE
                    %s IS NULL
                    OR EXTRACT(
                        YEAR FROM o.order_date
                    ) = %s

                GROUP BY
                    product_id
            ),

            stock AS (

                SELECT
                    product_id,

                    SUM(quantity)
                        AS stock_quantity

                FROM inventory

                GROUP BY
                    product_id
            )

            SELECT
                p.product_id,
                p.name,

                COALESCE(
                    st.stock_quantity,
                    0
                ) AS stock_quantity,

                COALESCE(
                    s.units_sold,
                    0
                ) AS units_sold,

                COALESCE(
                    s.orders_count,
                    0
                ) AS orders_count,

                s.last_sale_date,

                CASE
                    WHEN s.last_sale_date IS NULL
                        THEN NULL

                    ELSE
                        CURRENT_DATE -
                        s.last_sale_date::DATE
                END AS days_since_sale

            FROM products p

            LEFT JOIN stock st
                ON st.product_id =
                   p.product_id

            LEFT JOIN sales s
                ON s.product_id =
                   p.product_id

            ORDER BY
                stock_quantity DESC
        """

        return self._fetch_all(
            query,
            (year, year)
        )


    # ============================================================
    # DATABASE HELPERS
    # ============================================================

    def _fetch_all(
        self,
        query,
        params=None
    ):
        """Выполнить SELECT и вернуть все строки."""

        connection = get_connection()

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    query,
                    params or ()
                )

                return cursor.fetchall()

        finally:
            connection.close()


    def _fetch_one(
        self,
        query,
        params=None
    ):
        """Выполнить SELECT и вернуть одну строку."""

        connection = get_connection()

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    query,
                    params or ()
                )

                return cursor.fetchone()

        finally:
            connection.close()