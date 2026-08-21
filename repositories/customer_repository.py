from database.connection import get_connection


class CustomerRepository:
    """
    Repository для аналитики клиентов.

    SQL:
    - агрегирует историю заказов;
    - строит RFM / LTV / retention datasets;
    - рассчитывает основные клиентские метрики.

    pandas / numpy:
    - дальнейшая сегментация;
    - scoring;
    - кластеризация;
    - визуализация.
    """

    # ============================================================
    # BASIC CUSTOMER METRICS
    # ============================================================

    def total_customers(self):
        """Общее количество клиентов."""

        query = """
            SELECT
                COUNT(*) AS customers_count
            FROM customers
        """

        return self._fetch_one(query)


    def active_customers(self, year=None):
        """Количество клиентов, совершивших хотя бы одну покупку."""

        query = """
            SELECT
                COUNT(DISTINCT o.customer_id)
                    AS active_customers

            FROM orders o

            WHERE
                %s IS NULL
                OR EXTRACT(
                    YEAR FROM o.order_date
                ) = %s
        """

        return self._fetch_one(
            query,
            (year, year)
        )


    def inactive_customers(self):
        """Клиенты, которые никогда ничего не покупали."""

        query = """
            SELECT
                c.customer_id,
                c.name

            FROM customers c

            LEFT JOIN orders o
                ON o.customer_id =
                   c.customer_id

            WHERE
                o.order_id IS NULL

            ORDER BY
                c.name
        """

        return self._fetch_all(query)


    # ============================================================
    # CUSTOMER REVENUE
    # ============================================================

    def customer_revenue(self, year=None):
        """
        Полная статистика клиента:

        - заказы;
        - товары;
        - количество единиц;
        - выручка.
        """

        query = """
            SELECT
                c.customer_id,
                c.name,

                COUNT(
                    DISTINCT o.order_id
                ) AS orders_count,

                SUM(
                    oi.quantity
                ) AS units_bought,

                SUM(
                    oi.quantity * oi.price
                ) AS revenue

            FROM customers c

            JOIN orders o
                ON o.customer_id =
                   c.customer_id

            JOIN order_items oi
                ON oi.order_id =
                   o.order_id

            WHERE
                %s IS NULL
                OR EXTRACT(
                    YEAR FROM o.order_date
                ) = %s

            GROUP BY
                c.customer_id,
                c.name

            ORDER BY
                revenue DESC
        """

        return self._fetch_all(
            query,
            (year, year)
        )


    def top_customers_by_revenue(
        self,
        limit=10,
        year=None
    ):
        """Топ клиентов по выручке."""

        query = """
            SELECT
                c.customer_id,
                c.name,

                COUNT(
                    DISTINCT o.order_id
                ) AS orders_count,

                SUM(
                    oi.quantity * oi.price
                ) AS revenue

            FROM customers c

            JOIN orders o
                ON o.customer_id =
                   c.customer_id

            JOIN order_items oi
                ON oi.order_id =
                   o.order_id

            WHERE
                %s IS NULL
                OR EXTRACT(
                    YEAR FROM o.order_date
                ) = %s

            GROUP BY
                c.customer_id,
                c.name

            ORDER BY
                revenue DESC

            LIMIT %s
        """

        return self._fetch_all(
            query,
            (year, year, limit)
        )


    # ============================================================
    # AVERAGE ORDER VALUE
    # ============================================================

    def customer_average_check(self, year=None):
        """
        Средний чек клиента.

        Сначала рассчитывается стоимость
        каждого заказа, затем AVG по клиенту.
        """

        query = """
            WITH orders_total AS (

                SELECT
                    o.order_id,
                    o.customer_id,

                    SUM(
                        oi.quantity * oi.price
                    ) AS order_value

                FROM orders o

                JOIN order_items oi
                    ON oi.order_id =
                       o.order_id

                WHERE
                    %s IS NULL
                    OR EXTRACT(
                        YEAR FROM o.order_date
                    ) = %s

                GROUP BY
                    o.order_id,
                    o.customer_id
            )

            SELECT
                c.customer_id,
                c.name,

                COUNT(
                    ot.order_id
                ) AS orders_count,

                AVG(
                    ot.order_value
                ) AS average_check,

                SUM(
                    ot.order_value
                ) AS total_revenue

            FROM customers c

            JOIN orders_total ot
                ON ot.customer_id =
                   c.customer_id

            GROUP BY
                c.customer_id,
                c.name

            ORDER BY
                average_check DESC
        """

        return self._fetch_all(
            query,
            (year, year)
        )


    def customers_above_average_check(
        self,
        year=None
    ):
        """
        Клиенты, чей средний чек выше
        среднего чека по всем клиентам.
        """

        query = """
            WITH order_totals AS (

                SELECT
                    o.order_id,
                    o.customer_id,

                    SUM(
                        oi.quantity * oi.price
                    ) AS order_value

                FROM orders o

                JOIN order_items oi
                    ON oi.order_id =
                       o.order_id

                WHERE
                    %s IS NULL
                    OR EXTRACT(
                        YEAR FROM o.order_date
                    ) = %s

                GROUP BY
                    o.order_id,
                    o.customer_id
            ),

            customer_avg AS (

                SELECT
                    customer_id,
                    AVG(order_value)
                        AS average_check

                FROM order_totals

                GROUP BY
                    customer_id
            ),

            global_avg AS (

                SELECT
                    AVG(average_check)
                        AS global_average_check

                FROM customer_avg
            )

            SELECT
                c.customer_id,
                c.name,

                ca.average_check,
                ga.global_average_check

            FROM customer_avg ca

            JOIN customers c
                ON c.customer_id =
                   ca.customer_id

            CROSS JOIN global_avg ga

            WHERE
                ca.average_check >
                ga.global_average_check

            ORDER BY
                ca.average_check DESC
        """

        return self._fetch_all(
            query,
            (year, year)
        )


    # ============================================================
    # REPEAT CUSTOMERS
    # ============================================================

    def repeat_customers(self, year=None):
        """Клиенты с двумя и более заказами."""

        query = """
            SELECT
                c.customer_id,
                c.name,

                COUNT(
                    o.order_id
                ) AS orders_count

            FROM customers c

            JOIN orders o
                ON o.customer_id =
                   c.customer_id

            WHERE
                %s IS NULL
                OR EXTRACT(
                    YEAR FROM o.order_date
                ) = %s

            GROUP BY
                c.customer_id,
                c.name

            HAVING
                COUNT(o.order_id) > 1

            ORDER BY
                orders_count DESC
        """

        return self._fetch_all(
            query,
            (year, year)
        )


    def one_time_customers(self, year=None):
        """Клиенты, совершившие ровно одну покупку."""

        query = """
            SELECT
                c.customer_id,
                c.name

            FROM customers c

            JOIN orders o
                ON o.customer_id =
                   c.customer_id

            WHERE
                %s IS NULL
                OR EXTRACT(
                    YEAR FROM o.order_date
                ) = %s

            GROUP BY
                c.customer_id,
                c.name

            HAVING
                COUNT(o.order_id) = 1

            ORDER BY
                c.name
        """

        return self._fetch_all(
            query,
            (year, year)
        )


    # ============================================================
    # PURCHASE FREQUENCY
    # ============================================================

    def customer_purchase_frequency(self):
        """
        Средний интервал между заказами клиента.

        Использует LAG().
        """

        query = """
            WITH customer_orders AS (

                SELECT
                    customer_id,
                    order_id,
                    order_date,

                    LAG(order_date)
                        OVER(
                            PARTITION BY customer_id
                            ORDER BY order_date
                        ) AS previous_order_date

                FROM orders
            )

            SELECT
                c.customer_id,
                c.name,

                COUNT(
                    co.order_id
                ) AS orders_count,

                AVG(
                    co.order_date -
                    co.previous_order_date
                ) AS average_days_between_orders

            FROM customer_orders co

            JOIN customers c
                ON c.customer_id =
                   co.customer_id

            WHERE
                co.previous_order_date IS NOT NULL

            GROUP BY
                c.customer_id,
                c.name

            ORDER BY
                average_days_between_orders ASC
        """

        return self._fetch_all(query)


    # ============================================================
    # RFM
    # ============================================================

    def rfm_dataset(self):
        """
        Базовый датасет для RFM:

        Recency  — дней с последнего заказа
        Frequency — количество заказов
        Monetary — общая сумма покупок
        """

        query = """
            SELECT
                c.customer_id,
                c.name,

                CURRENT_DATE -
                MAX(
                    o.order_date
                )::DATE AS recency,

                COUNT(
                    DISTINCT o.order_id
                ) AS frequency,

                SUM(
                    oi.quantity * oi.price
                ) AS monetary

            FROM customers c

            JOIN orders o
                ON o.customer_id =
                   c.customer_id

            JOIN order_items oi
                ON oi.order_id =
                   o.order_id

            GROUP BY
                c.customer_id,
                c.name

            ORDER BY
                monetary DESC
        """

        return self._fetch_all(query)


    def rfm_dataset_by_year(self, year):
        """RFM-датасет за конкретный год."""

        query = """
            SELECT
                c.customer_id,
                c.name,

                MAX(
                    o.order_date
                )::DATE AS last_order_date,

                COUNT(
                    DISTINCT o.order_id
                ) AS frequency,

                SUM(
                    oi.quantity * oi.price
                ) AS monetary

            FROM customers c

            JOIN orders o
                ON o.customer_id =
                   c.customer_id

            JOIN order_items oi
                ON oi.order_id =
                   o.order_id

            WHERE
                EXTRACT(
                    YEAR FROM o.order_date
                ) = %s

            GROUP BY
                c.customer_id,
                c.name
        """

        return self._fetch_all(
            query,
            (year,)
        )


    # ============================================================
    # CUSTOMER LIFETIME VALUE
    # ============================================================

    def customer_lifetime_value(self):
        """
        Исторический LTV клиента.

        Здесь LTV = вся выручка клиента.
        Более сложную модель LTV можно считать
        в analytics.
        """

        query = """
            SELECT
                c.customer_id,
                c.name,

                MIN(
                    o.order_date
                ) AS first_order_date,

                MAX(
                    o.order_date
                ) AS last_order_date,

                COUNT(
                    DISTINCT o.order_id
                ) AS orders_count,

                SUM(
                    oi.quantity * oi.price
                ) AS lifetime_value

            FROM customers c

            JOIN orders o
                ON o.customer_id =
                   c.customer_id

            JOIN order_items oi
                ON oi.order_id =
                   o.order_id

            GROUP BY
                c.customer_id,
                c.name

            ORDER BY
                lifetime_value DESC
        """

        return self._fetch_all(query)


    # ============================================================
    # CUSTOMER PROFITABILITY
    # ============================================================

    def customer_profitability(self):
        """Прибыльность клиентов."""

        query = """
            SELECT
                c.customer_id,
                c.name,

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
                ) AS profit

            FROM customers c

            JOIN orders o
                ON o.customer_id =
                   c.customer_id

            JOIN order_items oi
                ON oi.order_id =
                   o.order_id

            JOIN product_prices pp
                ON pp.product_id =
                   oi.product_id

                AND pp.year =
                    EXTRACT(
                        YEAR FROM o.order_date
                    )

            GROUP BY
                c.customer_id,
                c.name

            ORDER BY
                profit DESC
        """

        return self._fetch_all(query)


    # ============================================================
    # CUSTOMER PRODUCT PREFERENCES
    # ============================================================

    def customer_favorite_categories(self):
        """
        Какие категории покупает каждый клиент.

        ROW_NUMBER() позволяет найти
        самую популярную категорию клиента.
        """

        query = """
            WITH category_sales AS (

                SELECT
                    c.customer_id,
                    c.name AS customer,

                    cat.category_id,
                    cat.name AS category,

                    SUM(
                        oi.quantity
                    ) AS units_bought,

                    SUM(
                        oi.quantity *
                        oi.price
                    ) AS revenue

                FROM customers c

                JOIN orders o
                    ON o.customer_id =
                       c.customer_id

                JOIN order_items oi
                    ON oi.order_id =
                       o.order_id

                JOIN products p
                    ON p.product_id =
                       oi.product_id

                JOIN categories cat
                    ON cat.category_id =
                       p.category_id

                GROUP BY
                    c.customer_id,
                    c.name,
                    cat.category_id,
                    cat.name
            ),

            ranked AS (

                SELECT
                    *,

                    ROW_NUMBER() OVER(
                        PARTITION BY customer_id
                        ORDER BY
                            revenue DESC
                    ) AS category_rank

                FROM category_sales
            )

            SELECT
                customer_id,
                customer,
                category,
                units_bought,
                revenue

            FROM ranked

            WHERE
                category_rank = 1

            ORDER BY
                revenue DESC
        """

        return self._fetch_all(query)


    # ============================================================
    # COHORT ANALYSIS
    # ============================================================

    def customer_cohorts(self):
        """
        Определяет cohort клиента
        по месяцу его первой покупки.
        """

        query = """
            WITH first_orders AS (

                SELECT
                    customer_id,

                    DATE_TRUNC(
                        'month',
                        MIN(order_date)
                    ) AS cohort_month

                FROM orders

                GROUP BY
                    customer_id
            )

            SELECT
                fo.cohort_month,

                DATE_TRUNC(
                    'month',
                    o.order_date
                ) AS order_month,

                COUNT(
                    DISTINCT o.customer_id
                ) AS active_customers

            FROM first_orders fo

            JOIN orders o
                ON o.customer_id =
                   fo.customer_id

            GROUP BY
                fo.cohort_month,
                order_month

            ORDER BY
                fo.cohort_month,
                order_month
        """

        return self._fetch_all(query)


    def cohort_retention(self):
        """
        Retention по когортам.

        Возвращает:
        cohort_month
        month_number
        active_customers
        cohort_size
        retention_percent
        """

        query = """
            WITH first_orders AS (

                SELECT
                    customer_id,

                    DATE_TRUNC(
                        'month',
                        MIN(order_date)
                    ) AS cohort_month

                FROM orders

                GROUP BY
                    customer_id
            ),

            activity AS (

                SELECT DISTINCT
                    o.customer_id,

                    fo.cohort_month,

                    DATE_TRUNC(
                        'month',
                        o.order_date
                    ) AS activity_month

                FROM orders o

                JOIN first_orders fo
                    ON fo.customer_id =
                       o.customer_id
            ),

            cohort_sizes AS (

                SELECT
                    cohort_month,

                    COUNT(
                        DISTINCT customer_id
                    ) AS cohort_size

                FROM first_orders

                GROUP BY
                    cohort_month
            )

            SELECT
                a.cohort_month,

                (
                    EXTRACT(
                        YEAR FROM
                        AGE(
                            a.activity_month,
                            a.cohort_month
                        )
                    ) * 12

                    +

                    EXTRACT(
                        MONTH FROM
                        AGE(
                            a.activity_month,
                            a.cohort_month
                        )
                    )
                )::INT AS month_number,

                COUNT(
                    DISTINCT a.customer_id
                ) AS active_customers,

                cs.cohort_size,

                ROUND(
                    COUNT(
                        DISTINCT a.customer_id
                    )::NUMERIC
                    /
                    NULLIF(
                        cs.cohort_size,
                        0
                    ) * 100,
                    2
                ) AS retention_percent

            FROM activity a

            JOIN cohort_sizes cs
                ON cs.cohort_month =
                   a.cohort_month

            GROUP BY
                a.cohort_month,
                a.activity_month,
                cs.cohort_size

            ORDER BY
                a.cohort_month,
                month_number
        """

        return self._fetch_all(query)


    # ============================================================
    # CUSTOMER GROWTH
    # ============================================================

    def monthly_active_customers(self):
        """Количество активных клиентов по месяцам."""

        query = """
            SELECT
                DATE_TRUNC(
                    'month',
                    order_date
                ) AS month,

                COUNT(
                    DISTINCT customer_id
                ) AS active_customers

            FROM orders

            GROUP BY
                month

            ORDER BY
                month
        """

        return self._fetch_all(query)


    def new_customers_by_month(self):
        """
        Количество новых клиентов
        по месяцам.
        """

        query = """
            WITH first_orders AS (

                SELECT
                    customer_id,

                    MIN(order_date)
                        AS first_order_date

                FROM orders

                GROUP BY
                    customer_id
            )

            SELECT
                DATE_TRUNC(
                    'month',
                    first_order_date
                ) AS month,

                COUNT(
                    customer_id
                ) AS new_customers

            FROM first_orders

            GROUP BY
                month

            ORDER BY
                month
        """

        return self._fetch_all(query)


    # ============================================================
    # RETENTION / CHURN
    # ============================================================

    def customer_last_purchase(self):
        """Последняя покупка каждого клиента."""

        query = """
            SELECT
                c.customer_id,
                c.name,

                MAX(
                    o.order_date
                ) AS last_order_date,

                CURRENT_DATE -
                MAX(
                    o.order_date
                )::DATE AS days_since_purchase

            FROM customers c

            JOIN orders o
                ON o.customer_id =
                   c.customer_id

            GROUP BY
                c.customer_id,
                c.name

            ORDER BY
                days_since_purchase DESC
        """

        return self._fetch_all(query)


    def churn_candidates(self, days=90):
        """
        Клиенты, которые не покупали
        дольше заданного количества дней.
        """

        query = """
            SELECT
                c.customer_id,
                c.name,

                MAX(
                    o.order_date
                ) AS last_order_date,

                CURRENT_DATE -
                MAX(
                    o.order_date
                )::DATE AS days_since_purchase

            FROM customers c

            JOIN orders o
                ON o.customer_id =
                   c.customer_id

            GROUP BY
                c.customer_id,
                c.name

            HAVING
                CURRENT_DATE -
                MAX(
                    o.order_date
                )::DATE > %s

            ORDER BY
                days_since_purchase DESC
        """

        return self._fetch_all(
            query,
            (days,)
        )


    # ============================================================
    # CUSTOMER RANKING
    # ============================================================

    def customer_revenue_rank(self):
        """Рейтинг клиентов по выручке."""

        query = """
            WITH customer_sales AS (

                SELECT
                    c.customer_id,
                    c.name,

                    SUM(
                        oi.quantity *
                        oi.price
                    ) AS revenue

                FROM customers c

                JOIN orders o
                    ON o.customer_id =
                       c.customer_id

                JOIN order_items oi
                    ON oi.order_id =
                       o.order_id

                GROUP BY
                    c.customer_id,
                    c.name
            )

            SELECT
                customer_id,
                name,
                revenue,

                RANK() OVER(
                    ORDER BY revenue DESC
                ) AS revenue_rank,

                ROUND(
                    revenue /
                    NULLIF(
                        SUM(revenue)
                            OVER(),
                        0
                    ) * 100,
                    2
                ) AS revenue_share_percent

            FROM customer_sales

            ORDER BY
                revenue_rank
        """

        return self._fetch_all(query)


    # ============================================================
    # ADVANCED CUSTOMER DATASET
    # ============================================================

    def customer_analytics_dataset(self):
        """
        Большой универсальный датасет клиента.

        Удобно отдавать в pandas:
        - RFM;
        - LTV;
        - segmentation;
        - clustering;
        - customer dashboard.
        """

        query = """
            WITH customer_orders AS (

                SELECT
                    o.customer_id,
                    o.order_id,
                    o.order_date,

                    SUM(
                        oi.quantity *
                        oi.price
                    ) AS order_value,

                    SUM(
                        oi.quantity
                    ) AS units

                FROM orders o

                JOIN order_items oi
                    ON oi.order_id =
                       o.order_id

                GROUP BY
                    o.customer_id,
                    o.order_id,
                    o.order_date
            ),

            customer_stats AS (

                SELECT
                    customer_id,

                    MIN(
                        order_date
                    ) AS first_order_date,

                    MAX(
                        order_date
                    ) AS last_order_date,

                    COUNT(
                        order_id
                    ) AS orders_count,

                    SUM(
                        order_value
                    ) AS lifetime_revenue,

                    SUM(
                        units
                    ) AS units_bought,

                    AVG(
                        order_value
                    ) AS average_check

                FROM customer_orders

                GROUP BY
                    customer_id
            )

            SELECT
                c.customer_id,
                c.name,

                cs.first_order_date,
                cs.last_order_date,

                CURRENT_DATE -
                cs.last_order_date::DATE
                    AS recency_days,

                cs.orders_count
                    AS frequency,

                cs.lifetime_revenue
                    AS monetary,

                cs.units_bought,
                cs.average_check,

                CURRENT_DATE -
                cs.first_order_date::DATE
                    AS customer_age_days

            FROM customers c

            JOIN customer_stats cs
                ON cs.customer_id =
                   c.customer_id

            ORDER BY
                cs.lifetime_revenue DESC
        """

        return self._fetch_all(query)


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