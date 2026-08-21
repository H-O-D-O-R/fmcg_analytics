from database.connection import get_connection


class LogisticsRepository:
    """
    Repository для аналитики логистики.

    Здесь находятся:
    - SQL-запросы;
    - агрегации;
    - JOIN;
    - оконные функции;
    - CTE;
    - получение данных из PostgreSQL.

    Pandas / NumPy и бизнес-расчеты находятся
    в services / analytics.
    """

    # ============================================================
    # BASIC LOGISTICS
    # ============================================================

    def total_shipments(self, year=None):
        """Общее количество поставок."""

        query = """
            SELECT
                COUNT(*) AS shipments_count
            FROM shipments
            WHERE
                %s IS NULL
                OR EXTRACT(YEAR FROM departure_date) = %s
        """

        return self._fetch_one(
            query,
            (year, year),
        )

    def total_distance(self, year=None):
        """Общая пройденная дистанция."""

        query = """
            SELECT
                COALESCE(
                    SUM(distance),
                    0
                ) AS total_distance
            FROM shipments
            WHERE
                %s IS NULL
                OR EXTRACT(YEAR FROM departure_date) = %s
        """

        return self._fetch_one(
            query,
            (year, year),
        )

    def average_distance(self, year=None):
        """Средняя дистанция одной поставки."""

        query = """
            SELECT
                ROUND(
                    COALESCE(
                        AVG(distance),
                        0
                    )::NUMERIC,
                    2
                ) AS average_distance
            FROM shipments
            WHERE
                %s IS NULL
                OR EXTRACT(YEAR FROM departure_date) = %s
        """

        return self._fetch_one(
            query,
            (year, year),
        )

    # ============================================================
    # DELIVERY TIME
    # ============================================================

    def average_delivery_time(self, year=None):
        """
        Среднее время доставки в днях.

        PostgreSQL DATE - DATE возвращает INTEGER
        с количеством дней.
        """

        query = """
            SELECT
                ROUND(
                    AVG(
                        arrival_date -
                        departure_date
                    )::NUMERIC,
                    2
                ) AS avg_delivery_days

            FROM shipments

            WHERE
                arrival_date IS NOT NULL
                AND departure_date IS NOT NULL

                AND (
                    %s IS NULL
                    OR EXTRACT(
                        YEAR FROM departure_date
                    ) = %s
                )
        """

        return self._fetch_one(
            query,
            (year, year),
        )

    def delivery_time_by_shipment(
        self,
        year=None,
    ):
        """Время доставки каждой поставки."""

        query = """
            SELECT
                sh.shipment_id,
                sh.order_id,
                sh.warehouse_id,
                sh.vehicle_id,
                sh.driver_id,

                sh.departure_date,
                sh.arrival_date,
                sh.distance,

                (
                    sh.arrival_date -
                    sh.departure_date
                ) AS delivery_days

            FROM shipments sh

            WHERE
                sh.arrival_date IS NOT NULL
                AND sh.departure_date IS NOT NULL

                AND (
                    %s IS NULL
                    OR EXTRACT(
                        YEAR FROM sh.departure_date
                    ) = %s
                )

            ORDER BY
                sh.departure_date
        """

        return self._fetch_all(
            query,
            (year, year),
        )

    # ============================================================
    # DELAYS
    # ============================================================

    def delayed_shipments(
        self,
        expected_days=7,
        year=None,
    ):
        """
        Поставки, которые доставлялись
        дольше заданного количества дней.
        """

        query = """
            SELECT
                sh.shipment_id,
                sh.order_id,
                sh.warehouse_id,
                sh.vehicle_id,
                sh.driver_id,

                sh.departure_date,
                sh.arrival_date,
                sh.distance,

                (
                    sh.arrival_date -
                    sh.departure_date
                ) AS delivery_days,

                (
                    (
                        sh.arrival_date -
                        sh.departure_date
                    ) - %s
                ) AS delay_days

            FROM shipments sh

            WHERE
                sh.arrival_date IS NOT NULL
                AND sh.departure_date IS NOT NULL

                AND (
                    sh.arrival_date -
                    sh.departure_date
                ) > %s

                AND (
                    %s IS NULL
                    OR EXTRACT(
                        YEAR FROM sh.departure_date
                    ) = %s
                )

            ORDER BY
                delay_days DESC
        """

        return self._fetch_all(
            query,
            (
                expected_days,
                expected_days,
                year,
                year,
            ),
        )

    def delay_rate(
        self,
        expected_days=7,
        year=None,
    ):
        """Общий процент задержанных поставок."""

        query = """
            SELECT
                COUNT(*) AS total_shipments,

                COUNT(
                    CASE
                        WHEN
                            (
                                arrival_date -
                                departure_date
                            ) > %s
                        THEN 1
                    END
                ) AS delayed_shipments,

                ROUND(
                    COUNT(
                        CASE
                            WHEN
                                (
                                    arrival_date -
                                    departure_date
                                ) > %s
                            THEN 1
                        END
                    )::NUMERIC
                    /
                    NULLIF(
                        COUNT(*),
                        0
                    )
                    * 100,
                    2
                ) AS delay_rate_percent

            FROM shipments

            WHERE
                arrival_date IS NOT NULL
                AND departure_date IS NOT NULL

                AND (
                    %s IS NULL
                    OR EXTRACT(
                        YEAR FROM departure_date
                    ) = %s
                )
        """

        return self._fetch_one(
            query,
            (
                expected_days,
                expected_days,
                year,
                year,
            ),
        )

    # ============================================================
    # WAREHOUSES
    # ============================================================

    def warehouse_performance(
        self,
        year=None,
    ):
        """
        Аналитика складов:

        - количество поставок;
        - общая дистанция;
        - средняя дистанция;
        - среднее время доставки.
        """

        query = """
            SELECT
                w.warehouse_id,
                w.name AS warehouse,

                COUNT(
                    sh.shipment_id
                ) AS shipments_count,

                COALESCE(
                    SUM(sh.distance),
                    0
                ) AS total_distance,

                ROUND(
                    COALESCE(
                        AVG(sh.distance),
                        0
                    )::NUMERIC,
                    2
                ) AS average_distance,

                ROUND(
                    COALESCE(
                        AVG(
                            sh.arrival_date -
                            sh.departure_date
                        ),
                        0
                    )::NUMERIC,
                    2
                ) AS average_delivery_days

            FROM warehouses w

            LEFT JOIN shipments sh
                ON sh.warehouse_id =
                   w.warehouse_id

            WHERE
                sh.shipment_id IS NULL

                OR (
                    sh.arrival_date IS NOT NULL
                    AND sh.departure_date IS NOT NULL

                    AND (
                        %s IS NULL
                        OR EXTRACT(
                            YEAR FROM sh.departure_date
                        ) = %s
                    )
                )

            GROUP BY
                w.warehouse_id,
                w.name

            ORDER BY
                shipments_count DESC
        """

        return self._fetch_all(
            query,
            (year, year),
        )

    def top_warehouses_by_shipments(
        self,
        limit=10,
        year=None,
    ):
        """Склады с наибольшим количеством поставок."""

        query = """
            SELECT
                w.warehouse_id,
                w.name AS warehouse,

                COUNT(
                    sh.shipment_id
                ) AS shipments_count,

                COALESCE(
                    SUM(sh.distance),
                    0
                ) AS total_distance

            FROM warehouses w

            JOIN shipments sh
                ON sh.warehouse_id =
                   w.warehouse_id

            WHERE
                %s IS NULL
                OR EXTRACT(
                    YEAR FROM sh.departure_date
                ) = %s

            GROUP BY
                w.warehouse_id,
                w.name

            ORDER BY
                shipments_count DESC

            LIMIT %s
        """

        return self._fetch_all(
            query,
            (
                year,
                year,
                limit,
            ),
        )

    # ============================================================
    # VEHICLES
    # ============================================================

    def vehicle_performance(
        self,
        year=None,
    ):
        """Аналитика транспорта."""

        query = """
            SELECT
                v.vehicle_id,

                COUNT(
                    sh.shipment_id
                ) AS shipments_count,

                COALESCE(
                    SUM(sh.distance),
                    0
                ) AS total_distance,

                ROUND(
                    COALESCE(
                        AVG(sh.distance),
                        0
                    )::NUMERIC,
                    2
                ) AS average_distance,

                ROUND(
                    COALESCE(
                        AVG(
                            sh.arrival_date -
                            sh.departure_date
                        ),
                        0
                    )::NUMERIC,
                    2
                ) AS average_delivery_days

            FROM vehicles v

            JOIN shipments sh
                ON sh.vehicle_id =
                   v.vehicle_id

            WHERE
                sh.arrival_date IS NOT NULL
                AND sh.departure_date IS NOT NULL

                AND (
                    %s IS NULL
                    OR EXTRACT(
                        YEAR FROM sh.departure_date
                    ) = %s
                )

            GROUP BY
                v.vehicle_id

            ORDER BY
                total_distance DESC
        """

        return self._fetch_all(
            query,
            (year, year),
        )

    def top_vehicles_by_distance(
        self,
        limit=10,
        year=None,
    ):
        """Транспорт с наибольшим пробегом."""

        query = """
            SELECT
                v.vehicle_id,

                COUNT(
                    sh.shipment_id
                ) AS shipments_count,

                COALESCE(
                    SUM(sh.distance),
                    0
                ) AS total_distance,

                ROUND(
                    COALESCE(
                        AVG(sh.distance),
                        0
                    )::NUMERIC,
                    2
                ) AS average_distance

            FROM vehicles v

            JOIN shipments sh
                ON sh.vehicle_id =
                   v.vehicle_id

            WHERE
                %s IS NULL
                OR EXTRACT(
                    YEAR FROM sh.departure_date
                ) = %s

            GROUP BY
                v.vehicle_id

            ORDER BY
                total_distance DESC

            LIMIT %s
        """

        return self._fetch_all(
            query,
            (
                year,
                year,
                limit,
            ),
        )

    # ============================================================
    # DRIVERS
    # ============================================================

    def driver_performance(
        self,
        year=None,
    ):
        """Аналитика водителей."""

        query = """
            SELECT
                d.driver_id,

                COUNT(
                    sh.shipment_id
                ) AS shipments_count,

                COALESCE(
                    SUM(sh.distance),
                    0
                ) AS total_distance,

                ROUND(
                    COALESCE(
                        AVG(sh.distance),
                        0
                    )::NUMERIC,
                    2
                ) AS average_distance,

                ROUND(
                    COALESCE(
                        AVG(
                            sh.arrival_date -
                            sh.departure_date
                        ),
                        0
                    )::NUMERIC,
                    2
                ) AS average_delivery_days

            FROM drivers d

            JOIN shipments sh
                ON sh.driver_id =
                   d.driver_id

            WHERE
                sh.arrival_date IS NOT NULL
                AND sh.departure_date IS NOT NULL

                AND (
                    %s IS NULL
                    OR EXTRACT(
                        YEAR FROM sh.departure_date
                    ) = %s
                )

            GROUP BY
                d.driver_id

            ORDER BY
                shipments_count DESC
        """

        return self._fetch_all(
            query,
            (year, year),
        )

    def top_drivers_by_distance(
        self,
        limit=10,
        year=None,
    ):
        """Водители с наибольшим пробегом."""

        query = """
            SELECT
                d.driver_id,

                COUNT(
                    sh.shipment_id
                ) AS shipments_count,

                COALESCE(
                    SUM(sh.distance),
                    0
                ) AS total_distance,

                ROUND(
                    COALESCE(
                        AVG(
                            sh.arrival_date -
                            sh.departure_date
                        ),
                        0
                    )::NUMERIC,
                    2
                ) AS average_delivery_days

            FROM drivers d

            JOIN shipments sh
                ON sh.driver_id =
                   d.driver_id

            WHERE
                sh.arrival_date IS NOT NULL
                AND sh.departure_date IS NOT NULL

                AND (
                    %s IS NULL
                    OR EXTRACT(
                        YEAR FROM sh.departure_date
                    ) = %s
                )

            GROUP BY
                d.driver_id

            ORDER BY
                total_distance DESC

            LIMIT %s
        """

        return self._fetch_all(
            query,
            (
                year,
                year,
                limit,
            ),
        )

    # ============================================================
    # MONTHLY LOGISTICS
    # ============================================================

    def monthly_logistics(
        self,
        year=None,
    ):
        """Основная месячная аналитика."""

        query = """
            SELECT
                EXTRACT(
                    YEAR FROM departure_date
                )::INT AS year,

                EXTRACT(
                    MONTH FROM departure_date
                )::INT AS month,

                COUNT(*) AS shipments_count,

                COALESCE(
                    SUM(distance),
                    0
                ) AS total_distance,

                ROUND(
                    COALESCE(
                        AVG(distance),
                        0
                    )::NUMERIC,
                    2
                ) AS average_distance,

                ROUND(
                    COALESCE(
                        AVG(
                            arrival_date -
                            departure_date
                        ),
                        0
                    )::NUMERIC,
                    2
                ) AS average_delivery_days

            FROM shipments

            WHERE
                arrival_date IS NOT NULL
                AND departure_date IS NOT NULL

                AND (
                    %s IS NULL
                    OR EXTRACT(
                        YEAR FROM departure_date
                    ) = %s
                )

            GROUP BY
                EXTRACT(
                    YEAR FROM departure_date
                ),
                EXTRACT(
                    MONTH FROM departure_date
                )

            ORDER BY
                year,
                month
        """

        return self._fetch_all(
            query,
            (year, year),
        )

    def monthly_delivery_time(
        self,
        year=None,
    ):
        """Среднее время доставки по месяцам."""

        query = """
            SELECT
                EXTRACT(
                    YEAR FROM departure_date
                )::INT AS year,

                EXTRACT(
                    MONTH FROM departure_date
                )::INT AS month,

                COUNT(*) AS shipments_count,

                ROUND(
                    COALESCE(
                        AVG(
                            arrival_date -
                            departure_date
                        ),
                        0
                    )::NUMERIC,
                    2
                ) AS average_delivery_days

            FROM shipments

            WHERE
                arrival_date IS NOT NULL
                AND departure_date IS NOT NULL

                AND (
                    %s IS NULL
                    OR EXTRACT(
                        YEAR FROM departure_date
                    ) = %s
                )

            GROUP BY
                EXTRACT(
                    YEAR FROM departure_date
                ),
                EXTRACT(
                    MONTH FROM departure_date
                )

            ORDER BY
                year,
                month
        """

        return self._fetch_all(
            query,
            (year, year),
        )

    # ============================================================
    # DISTANCE ANALYSIS
    # ============================================================

    def distance_distribution(self):
        """Распределение поставок по дистанции."""

        query = """
            SELECT
                CASE
                    WHEN distance < 500
                        THEN '<500 km'

                    WHEN distance < 1000
                        THEN '500-1000 km'

                    WHEN distance < 2000
                        THEN '1000-2000 km'

                    WHEN distance < 3000
                        THEN '2000-3000 km'

                    ELSE '3000+ km'
                END AS distance_group,

                COUNT(*) AS shipments_count,

                ROUND(
                    AVG(distance)::NUMERIC,
                    2
                ) AS average_distance

            FROM shipments

            GROUP BY
                CASE
                    WHEN distance < 500
                        THEN '<500 km'

                    WHEN distance < 1000
                        THEN '500-1000 km'

                    WHEN distance < 2000
                        THEN '1000-2000 km'

                    WHEN distance < 3000
                        THEN '2000-3000 km'

                    ELSE '3000+ km'
                END

            ORDER BY
                MIN(distance)
        """

        return self._fetch_all(query)

    # ============================================================
    # ORDER / SHIPMENT ANALYSIS
    # ============================================================

    def shipment_order_statistics(
        self,
        year=None,
    ):
        """
        Связь заказов и поставок.
        """

        query = """
            SELECT
                COUNT(*) AS shipments_count,

                COUNT(
                    DISTINCT order_id
                ) AS unique_orders,

                ROUND(
                    COUNT(*)::NUMERIC
                    /
                    NULLIF(
                        COUNT(DISTINCT order_id),
                        0
                    ),
                    2
                ) AS shipments_per_order

            FROM shipments

            WHERE
                %s IS NULL
                OR EXTRACT(
                    YEAR FROM departure_date
                ) = %s
        """

        return self._fetch_one(
            query,
            (year, year),
        )

    def orders_with_multiple_shipments(
        self,
        limit=20,
    ):
        """Заказы с несколькими поставками."""

        query = """
            SELECT
                order_id,

                COUNT(*) AS shipments_count,

                COALESCE(
                    SUM(distance),
                    0
                ) AS total_distance,

                ROUND(
                    AVG(distance)::NUMERIC,
                    2
                ) AS average_distance

            FROM shipments

            GROUP BY
                order_id

            HAVING
                COUNT(*) > 1

            ORDER BY
                shipments_count DESC,
                total_distance DESC

            LIMIT %s
        """

        return self._fetch_all(
            query,
            (limit,),
        )

    # ============================================================
    # ADVANCED ANALYTICS
    # ============================================================

    def monthly_distance_growth(self):
        """
        Рост логистической нагрузки
        относительно предыдущего месяца.

        Используется LAG.
        """

        query = """
            WITH monthly AS (

                SELECT
                    DATE_TRUNC(
                        'month',
                        departure_date
                    ) AS month,

                    SUM(distance)
                        AS total_distance,

                    COUNT(*) AS shipments_count

                FROM shipments

                GROUP BY
                    DATE_TRUNC(
                        'month',
                        departure_date
                    )
            ),

            with_previous AS (

                SELECT
                    month,
                    total_distance,
                    shipments_count,

                    LAG(total_distance)
                    OVER (
                        ORDER BY month
                    ) AS previous_distance

                FROM monthly
            )

            SELECT
                month,
                total_distance,
                shipments_count,
                previous_distance,

                ROUND(
                    (
                        total_distance -
                        previous_distance
                    )
                    /
                    NULLIF(
                        previous_distance,
                        0
                    )
                    * 100,
                    2
                ) AS growth_percent

            FROM with_previous

            ORDER BY
                month
        """

        return self._fetch_all(query)

    def warehouse_distance_ranking(
        self,
        year=None,
    ):
        """
        Рейтинг складов по логистической нагрузке.

        Использует RANK().
        """

        query = """
            WITH warehouse_stats AS (

                SELECT
                    w.warehouse_id,
                    w.name AS warehouse,

                    COUNT(
                        sh.shipment_id
                    ) AS shipments_count,

                    COALESCE(
                        SUM(sh.distance),
                        0
                    ) AS total_distance,

                    COALESCE(
                        AVG(sh.distance),
                        0
                    ) AS average_distance

                FROM warehouses w

                JOIN shipments sh
                    ON sh.warehouse_id =
                       w.warehouse_id

                WHERE
                    %s IS NULL
                    OR EXTRACT(
                        YEAR FROM sh.departure_date
                    ) = %s

                GROUP BY
                    w.warehouse_id,
                    w.name
            )

            SELECT
                warehouse_id,
                warehouse,
                shipments_count,
                total_distance,

                ROUND(
                    average_distance::NUMERIC,
                    2
                ) AS average_distance,

                RANK() OVER (
                    ORDER BY
                        total_distance DESC
                ) AS distance_rank,

                RANK() OVER (
                    ORDER BY
                        shipments_count DESC
                ) AS volume_rank

            FROM warehouse_stats

            ORDER BY
                distance_rank
        """

        return self._fetch_all(
            query,
            (year, year),
        )

    def vehicle_utilization_ranking(
        self,
        year=None,
    ):
        """
        Рейтинг транспорта по:
        - количеству рейсов;
        - общей дистанции.
        """

        query = """
            WITH vehicle_stats AS (

                SELECT
                    v.vehicle_id,

                    COUNT(
                        sh.shipment_id
                    ) AS shipments_count,

                    COALESCE(
                        SUM(sh.distance),
                        0
                    ) AS total_distance,

                    COALESCE(
                        AVG(sh.distance),
                        0
                    ) AS average_distance

                FROM vehicles v

                JOIN shipments sh
                    ON sh.vehicle_id =
                       v.vehicle_id

                WHERE
                    %s IS NULL
                    OR EXTRACT(
                        YEAR FROM sh.departure_date
                    ) = %s

                GROUP BY
                    v.vehicle_id
            )

            SELECT
                vehicle_id,
                shipments_count,
                total_distance,

                ROUND(
                    average_distance::NUMERIC,
                    2
                ) AS average_distance,

                RANK() OVER (
                    ORDER BY
                        shipments_count DESC
                ) AS volume_rank,

                RANK() OVER (
                    ORDER BY
                        total_distance DESC
                ) AS distance_rank

            FROM vehicle_stats

            ORDER BY
                volume_rank
        """

        return self._fetch_all(
            query,
            (year, year),
        )

    # ============================================================
    # DATA QUALITY
    # ============================================================

    def logistics_data_quality(self):
        """
        Проверка качества данных shipments.

        Проверяет:
        - отрицательные расстояния;
        - NULL даты;
        - некорректные даты;
        - отсутствующие FK.
        """

        query = """
            SELECT
                COUNT(*) FILTER (
                    WHERE distance < 0
                ) AS negative_distance,

                COUNT(*) FILTER (
                    WHERE departure_date IS NULL
                ) AS missing_departure,

                COUNT(*) FILTER (
                    WHERE arrival_date IS NULL
                ) AS missing_arrival,

                COUNT(*) FILTER (
                    WHERE
                        arrival_date <
                        departure_date
                ) AS invalid_dates,

                COUNT(*) FILTER (
                    WHERE warehouse_id IS NULL
                ) AS missing_warehouse,

                COUNT(*) FILTER (
                    WHERE vehicle_id IS NULL
                ) AS missing_vehicle,

                COUNT(*) FILTER (
                    WHERE driver_id IS NULL
                ) AS missing_driver

            FROM shipments
        """

        return self._fetch_one(query)

    # ============================================================
    # DATABASE HELPERS
    # ============================================================

    def _fetch_all(
        self,
        query,
        params=None,
    ):
        """Выполнить SELECT и вернуть все строки."""

        connection = get_connection()

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    query,
                    params or (),
                )

                return cursor.fetchall()

        finally:
            connection.close()

    def _fetch_one(
        self,
        query,
        params=None,
    ):
        """Выполнить SELECT и вернуть одну строку."""

        connection = get_connection()

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    query,
                    params or (),
                )

                return cursor.fetchone()

        finally:
            connection.close()