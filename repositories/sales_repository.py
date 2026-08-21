from database.connection import get_connection


class SalesRepository:
    """
    Repository для аналитики продаж.

    Здесь только SQL и получение данных.
    pandas / numpy / matplotlib находятся выше по архитектуре.
    """

    # ============================================================
    # BASIC SALES
    # ============================================================

    def total_revenue(self, year=None):
        """Общая выручка."""

        query = """
            SELECT
                COALESCE(SUM(oi.quantity * oi.price), 0) AS revenue
            FROM order_items oi
            JOIN orders o
                ON o.order_id = oi.order_id
            WHERE
                %s IS NULL
                OR EXTRACT(YEAR FROM o.order_date) = %s
        """

        return self._fetch_one(query, (year, year))


    def total_units_sold(self, year=None):
        """Общее количество проданных единиц."""

        query = """
            SELECT
                COALESCE(SUM(oi.quantity), 0) AS units_sold
            FROM order_items oi
            JOIN orders o
                ON o.order_id = oi.order_id
            WHERE
                %s IS NULL
                OR EXTRACT(YEAR FROM o.order_date) = %s
        """

        return self._fetch_one(query, (year, year))


    def total_orders(self, year=None):
        """Количество заказов."""

        query = """
            SELECT
                COUNT(DISTINCT o.order_id) AS orders_count
            FROM orders o
            WHERE
                %s IS NULL
                OR EXTRACT(YEAR FROM o.order_date) = %s
        """

        return self._fetch_one(query, (year, year))


    # ============================================================
    # TIME ANALYSIS
    # ============================================================

    def revenue_by_year(self):
        """Выручка по годам."""

        query = """
            SELECT
                EXTRACT(YEAR FROM o.order_date)::INT AS year,
                SUM(oi.quantity * oi.price) AS revenue
            FROM orders o
            JOIN order_items oi
                ON oi.order_id = o.order_id
            GROUP BY year
            ORDER BY year
        """

        return self._fetch_all(query)


    def revenue_by_month(self, year=None):
        """Выручка по месяцам."""

        query = """
            SELECT
                EXTRACT(YEAR FROM o.order_date)::INT AS year,
                EXTRACT(MONTH FROM o.order_date)::INT AS month,
                SUM(oi.quantity * oi.price) AS revenue
            FROM orders o
            JOIN order_items oi
                ON oi.order_id = o.order_id
            WHERE
                %s IS NULL
                OR EXTRACT(YEAR FROM o.order_date) = %s
            GROUP BY
                year,
                month
            ORDER BY
                year,
                month
        """

        return self._fetch_all(query, (year, year))


    def monthly_sales_dynamics(self):
        """
        Помесячная динамика:
        - revenue
        - previous month
        - absolute growth
        - growth %
        """

        query = """
            WITH monthly AS (
                SELECT
                    DATE_TRUNC(
                        'month',
                        o.order_date
                    ) AS month,

                    SUM(
                        oi.quantity * oi.price
                    ) AS revenue

                FROM orders o

                JOIN order_items oi
                    ON oi.order_id = o.order_id

                GROUP BY month
            )

            SELECT
                month,
                revenue,

                LAG(revenue)
                    OVER (
                        ORDER BY month
                    ) AS previous_revenue,

                revenue -
                LAG(revenue)
                    OVER (
                        ORDER BY month
                    ) AS revenue_change,

                ROUND(
                    (
                        (
                            revenue -
                            LAG(revenue)
                                OVER (
                                    ORDER BY month
                                )
                        )
                        /
                        NULLIF(
                            LAG(revenue)
                                OVER (
                                    ORDER BY month
                                ),
                            0
                        ) * 100
                    )::numeric,
                    2
                ) AS growth_percent

            FROM monthly

            ORDER BY month
        """

        return self._fetch_all(query)


    def yearly_growth(self):
        """Рост выручки относительно предыдущего года."""

        query = """
            WITH yearly AS (
                SELECT
                    EXTRACT(
                        YEAR FROM o.order_date
                    )::INT AS year,

                    SUM(
                        oi.quantity * oi.price
                    ) AS revenue

                FROM orders o

                JOIN order_items oi
                    ON oi.order_id = o.order_id

                GROUP BY year
            )

            SELECT
                year,
                revenue,

                LAG(revenue)
                    OVER (
                        ORDER BY year
                    ) AS previous_revenue,

                revenue -
                LAG(revenue)
                    OVER (
                        ORDER BY year
                    ) AS revenue_change,

                ROUND(
                    (
                        (
                            revenue -
                            LAG(revenue)
                                OVER (
                                    ORDER BY year
                                )
                        )
                        /
                        NULLIF(
                            LAG(revenue)
                                OVER (
                                    ORDER BY year
                                ),
                            0
                        ) * 100
                    )::numeric,
                    2
                ) AS growth_percent

            FROM yearly

            ORDER BY year
        """

        return self._fetch_all(query)


    # ============================================================
    # PRODUCTS
    # ============================================================

    def top_products_by_quantity(self, limit=10, year=None):
        """Топ товаров по количеству продаж."""

        query = """
            SELECT
                p.product_id,
                p.name,

                SUM(oi.quantity) AS units_sold,

                COUNT(DISTINCT oi.order_id)
                    AS orders_count,

                SUM(oi.quantity * oi.price)
                    AS revenue

            FROM products p

            JOIN order_items oi
                ON oi.product_id = p.product_id

            JOIN orders o
                ON o.order_id = oi.order_id

            WHERE
                %s IS NULL
                OR EXTRACT(YEAR FROM o.order_date) = %s

            GROUP BY
                p.product_id,
                p.name

            ORDER BY
                units_sold DESC

            LIMIT %s
        """

        return self._fetch_all(
            query,
            (year, year, limit)
        )


    def top_products_by_revenue(self, limit=10, year=None):
        """Топ товаров по выручке."""

        query = """
            SELECT
                p.product_id,
                p.name,

                SUM(oi.quantity) AS units_sold,

                SUM(
                    oi.quantity * oi.price
                ) AS revenue

            FROM products p

            JOIN order_items oi
                ON oi.product_id = p.product_id

            JOIN orders o
                ON o.order_id = oi.order_id

            WHERE
                %s IS NULL
                OR EXTRACT(YEAR FROM o.order_date) = %s

            GROUP BY
                p.product_id,
                p.name

            ORDER BY
                revenue DESC

            LIMIT %s
        """

        return self._fetch_all(
            query,
            (year, year, limit)
        )


    def top_products_by_profit(self, limit=10, year=None):
        """Топ товаров по прибыли."""

        query = """
            SELECT
                p.product_id,
                p.name,

                SUM(oi.quantity) AS units_sold,

                SUM(
                    oi.quantity *
                    (
                        oi.price -
                        pp.cost_price
                    )
                ) AS profit,

                SUM(
                    oi.quantity * oi.price
                ) AS revenue

            FROM products p

            JOIN order_items oi
                ON oi.product_id = p.product_id

            JOIN orders o
                ON o.order_id = oi.order_id

            JOIN product_prices pp
                ON pp.product_id = oi.product_id
                AND pp.year =
                    EXTRACT(
                        YEAR FROM o.order_date
                    )

            WHERE
                %s IS NULL
                OR EXTRACT(YEAR FROM o.order_date) = %s

            GROUP BY
                p.product_id,
                p.name

            ORDER BY
                profit DESC

            LIMIT %s
        """

        return self._fetch_all(
            query,
            (year, year, limit)
        )


    def bottom_products_by_profit(self, limit=10, year=None):
        """Самые убыточные товары."""

        query = """
            SELECT
                p.product_id,
                p.name,

                SUM(
                    oi.quantity *
                    (
                        oi.price -
                        pp.cost_price
                    )
                ) AS profit

            FROM products p

            JOIN order_items oi
                ON oi.product_id = p.product_id

            JOIN orders o
                ON o.order_id = oi.order_id

            JOIN product_prices pp
                ON pp.product_id = oi.product_id
                AND pp.year =
                    EXTRACT(
                        YEAR FROM o.order_date
                    )

            WHERE
                %s IS NULL
                OR EXTRACT(YEAR FROM o.order_date) = %s

            GROUP BY
                p.product_id,
                p.name

            ORDER BY
                profit ASC

            LIMIT %s
        """

        return self._fetch_all(
            query,
            (year, year, limit)
        )


    # ============================================================
    # PROFIT
    # ============================================================

    def profit_by_month(self, year=None):
        """Прибыль по месяцам."""

        query = """
            SELECT
                EXTRACT(
                    YEAR FROM o.order_date
                )::INT AS year,

                EXTRACT(
                    MONTH FROM o.order_date
                )::INT AS month,

                SUM(
                    oi.quantity *
                    (
                        oi.price -
                        pp.cost_price
                    )
                ) AS profit,

                SUM(
                    oi.quantity * oi.price
                ) AS revenue

            FROM orders o

            JOIN order_items oi
                ON oi.order_id = o.order_id

            JOIN product_prices pp
                ON pp.product_id = oi.product_id
                AND pp.year =
                    EXTRACT(
                        YEAR FROM o.order_date
                    )

            WHERE
                %s IS NULL
                OR EXTRACT(YEAR FROM o.order_date) = %s

            GROUP BY
                year,
                month

            ORDER BY
                year,
                month
        """

        return self._fetch_all(
            query,
            (year, year)
        )


    def product_profitability(self, year=None):
        """
        Полная прибыльность товара:
        revenue
        cost
        profit
        margin
        units
        """

        query = """
            SELECT
                p.product_id,
                p.name,

                SUM(oi.quantity)
                    AS units_sold,

                SUM(
                    oi.quantity * oi.price
                ) AS revenue,

                SUM(
                    oi.quantity *
                    pp.cost_price
                ) AS cost,

                SUM(
                    oi.quantity *
                    (
                        oi.price -
                        pp.cost_price
                    )
                ) AS profit,

                ROUND(
                    (
                        SUM(
                            oi.quantity *
                            (
                                oi.price -
                                pp.cost_price
                            )
                        )
                        /
                        NULLIF(
                            SUM(
                                oi.quantity *
                                oi.price
                            ),
                            0
                        ) * 100
                    )::numeric,
                    2
                ) AS margin_percent

            FROM products p

            JOIN order_items oi
                ON oi.product_id = p.product_id

            JOIN orders o
                ON o.order_id = oi.order_id

            JOIN product_prices pp
                ON pp.product_id = oi.product_id
                AND pp.year =
                    EXTRACT(
                        YEAR FROM o.order_date
                    )

            WHERE
                %s IS NULL
                OR EXTRACT(YEAR FROM o.order_date) = %s

            GROUP BY
                p.product_id,
                p.name

            ORDER BY
                profit DESC
        """

        return self._fetch_all(
            query,
            (year, year)
        )


    # ============================================================
    # CATEGORIES
    # ============================================================

    def category_performance(self, year=None):
        """Продажи и прибыль по категориям."""

        query = """
            SELECT
                c.category_id,
                c.name AS category,

                SUM(oi.quantity) AS units_sold,

                SUM(
                    oi.quantity * oi.price
                ) AS revenue,

                SUM(
                    oi.quantity * pp.cost_price
                ) AS cost,

                SUM(
                    oi.quantity *
                    (
                        oi.price - pp.cost_price
                    )
                ) AS profit

            FROM categories c

            JOIN brands b
                ON b.category_id = c.category_id

            JOIN products p
                ON p.brand_id = b.brand_id

            JOIN order_items oi
                ON oi.product_id = p.product_id

            JOIN orders o
                ON o.order_id = oi.order_id

            JOIN product_prices pp
                ON pp.product_id = oi.product_id
                AND pp.year = EXTRACT(
                    YEAR FROM o.order_date
                )

            WHERE
                %s IS NULL
                OR EXTRACT(
                    YEAR FROM o.order_date
                ) = %s

            GROUP BY
                c.category_id,
                c.name

            ORDER BY
                revenue DESC
        """

        return self._fetch_all(
            query,
            (year, year)
        )


    def brand_performance(self, year=None):
        """Продажи и прибыль по брендам."""

        query = """
            SELECT
                b.brand_id,
                b.name AS brand,

                COUNT(
                    DISTINCT p.product_id
                ) AS products_count,

                SUM(oi.quantity)
                    AS units_sold,

                SUM(
                    oi.quantity * oi.price
                ) AS revenue,

                SUM(
                    oi.quantity *
                    (
                        oi.price -
                        pp.cost_price
                    )
                ) AS profit

            FROM brands b

            JOIN products p
                ON p.brand_id = b.brand_id

            JOIN order_items oi
                ON oi.product_id = p.product_id

            JOIN orders o
                ON o.order_id = oi.order_id

            JOIN product_prices pp
                ON pp.product_id = oi.product_id
                AND pp.year =
                    EXTRACT(
                        YEAR FROM o.order_date
                    )

            WHERE
                %s IS NULL
                OR EXTRACT(YEAR FROM o.order_date) = %s

            GROUP BY
                b.brand_id,
                b.name

            ORDER BY
                revenue DESC
        """

        return self._fetch_all(
            query,
            (year, year)
        )


    # ============================================================
    # RANKING
    # ============================================================

    def products_ranked_inside_category(self, year=None):
        """
        Рейтинг товаров внутри каждой категории.
        """

        query = """
            WITH product_sales AS (

                SELECT
                    c.category_id,
                    c.name AS category,

                    p.product_id,
                    p.name AS product,

                    SUM(
                        oi.quantity * oi.price
                    ) AS revenue

                FROM categories c

                JOIN products p
                    ON p.category_id =
                       c.category_id

                JOIN order_items oi
                    ON oi.product_id =
                       p.product_id

                JOIN orders o
                    ON o.order_id =
                       oi.order_id

                WHERE
                    %s IS NULL
                    OR EXTRACT(
                        YEAR FROM o.order_date
                    ) = %s

                GROUP BY
                    c.category_id,
                    c.name,
                    p.product_id,
                    p.name
            )

            SELECT
                category,
                product,
                revenue,

                RANK() OVER(
                    PARTITION BY category_id
                    ORDER BY revenue DESC
                ) AS category_rank

            FROM product_sales

            ORDER BY
                category,
                category_rank
        """

        return self._fetch_all(
            query,
            (year, year)
        )


    # ============================================================
    # PARETO / ABC
    # ============================================================

    def abc_analysis(self, year=None):
        """
        ABC-анализ товаров.

        A <= 80%
        B <= 95%
        C > 95%

        cumulative_share считается через
        оконную функцию.
        """

        query = """
            WITH product_revenue AS (

                SELECT
                    p.product_id,
                    p.name,

                    SUM(
                        oi.quantity * oi.price
                    ) AS revenue

                FROM products p

                JOIN order_items oi
                    ON oi.product_id =
                       p.product_id

                JOIN orders o
                    ON o.order_id =
                       oi.order_id

                WHERE
                    %s IS NULL
                    OR EXTRACT(
                        YEAR FROM o.order_date
                    ) = %s

                GROUP BY
                    p.product_id,
                    p.name
            ),

            ranked AS (

                SELECT
                    product_id,
                    name,
                    revenue,

                    SUM(revenue) OVER(
                        ORDER BY revenue DESC
                    )
                    /
                    NULLIF(
                        SUM(revenue) OVER(),
                        0
                    ) AS cumulative_share

                FROM product_revenue
            )

            SELECT
                product_id,
                name,
                revenue,
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
                revenue DESC
        """

        return self._fetch_all(
            query,
            (year, year)
        )


    # ============================================================
    # PRODUCT SHARE
    # ============================================================

    def product_revenue_share(self, year=None):
        """
        Доля товара в общей выручке.
        """

        query = """
            WITH sales AS (

                SELECT
                    p.product_id,
                    p.name,

                    SUM(
                        oi.quantity * oi.price
                    ) AS revenue

                FROM products p

                JOIN order_items oi
                    ON oi.product_id =
                       p.product_id

                JOIN orders o
                    ON o.order_id =
                       oi.order_id

                WHERE
                    %s IS NULL
                    OR EXTRACT(
                        YEAR FROM o.order_date
                    ) = %s

                GROUP BY
                    p.product_id,
                    p.name
            )

            SELECT
                product_id,
                name,
                revenue,

                ROUND(
                    (
                        revenue
                        /
                        NULLIF(
                            SUM(revenue) OVER(),
                            0
                        ) * 100
                    )::numeric,
                    2
                ) AS revenue_share_percent

            FROM sales

            ORDER BY
                revenue DESC
        """

        return self._fetch_all(
            query,
            (year, year)
        )


    # ============================================================
    # BEST / WORST MONTH
    # ============================================================

    def best_sales_month(self, year=None):
        """Лучший месяц по выручке."""

        query = """
            SELECT
                EXTRACT(
                    MONTH FROM o.order_date
                )::INT AS month,

                SUM(
                    oi.quantity * oi.price
                ) AS revenue

            FROM orders o

            JOIN order_items oi
                ON oi.order_id =
                   o.order_id

            WHERE
                %s IS NULL
                OR EXTRACT(
                    YEAR FROM o.order_date
                ) = %s

            GROUP BY month

            ORDER BY
                revenue DESC

            LIMIT 1
        """

        return self._fetch_one(
            query,
            (year, year)
        )


    def worst_sales_month(self, year=None):
        """Худший месяц по выручке."""

        query = """
            SELECT
                EXTRACT(
                    MONTH FROM o.order_date
                )::INT AS month,

                SUM(
                    oi.quantity * oi.price
                ) AS revenue

            FROM orders o

            JOIN order_items oi
                ON oi.order_id =
                   o.order_id

            WHERE
                %s IS NULL
                OR EXTRACT(
                    YEAR FROM o.order_date
                ) = %s

            GROUP BY month

            ORDER BY
                revenue ASC

            LIMIT 1
        """

        return self._fetch_one(
            query,
            (year, year)
        )


    # ============================================================
    # GLOBAL HELPERS
    # ============================================================

    def _fetch_all(self, query, params=None):
        """Выполнение SELECT с возвратом всех строк."""

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


    def _fetch_one(self, query, params=None):
        """Выполнение SELECT с возвратом одной строки."""

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