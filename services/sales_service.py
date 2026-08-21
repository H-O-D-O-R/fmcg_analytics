import numpy as np
import pandas as pd

from repositories.sales_repository import SalesRepository


class SalesService:
    """
    Business/service layer для аналитики продаж.

    Repository:
        SQL + получение данных

    Service:
        DataFrame + подготовка + бизнес-метрики

    Analytics:
        сложные аналитические модели

    Visualization:
        matplotlib
    """

    def __init__(self):
        self.repository = SalesRepository()

    # ============================================================
    # HELPERS
    # ============================================================

    @staticmethod
    def _to_dataframe(rows, columns):
        """
        Преобразует результат repository в DataFrame.
        """

        return pd.DataFrame(
            rows,
            columns=columns
        )

    # ============================================================
    # BASIC SALES
    # ============================================================

    def get_total_revenue(self, year=None):
        """Возвращает общую выручку."""

        row = self.repository.total_revenue(year)

        if row is None:
            return 0

        return float(row[0] or 0)


    def get_total_units_sold(self, year=None):
        """Возвращает количество проданных единиц."""

        row = self.repository.total_units_sold(year)

        if row is None:
            return 0

        return int(row[0] or 0)


    def get_total_orders(self, year=None):
        """Возвращает количество заказов."""

        row = self.repository.total_orders(year)

        if row is None:
            return 0

        return int(row[0] or 0)


    def get_sales_summary(self, year=None):
        """
        Общая сводка продаж.

        Возвращает словарь для dashboard.
        """

        revenue = self.get_total_revenue(year)
        units = self.get_total_units_sold(year)
        orders = self.get_total_orders(year)

        average_order_value = (
            revenue / orders
            if orders
            else 0
        )

        return {
            "revenue": revenue,
            "units_sold": units,
            "orders": orders,
            "average_order_value": average_order_value,
        }

    # ============================================================
    # TIME ANALYSIS
    # ============================================================

    def get_revenue_by_year(self):
        """Выручка по годам."""

        rows = self.repository.revenue_by_year()

        return self._to_dataframe(
            rows,
            [
                "year",
                "revenue",
            ]
        )


    def get_revenue_by_month(self, year=None):
        """Помесячная выручка."""

        rows = self.repository.revenue_by_month(year)

        df = self._to_dataframe(
            rows,
            [
                "year",
                "month",
                "revenue",
            ]
        )

        if df.empty:
            return df

        df["year"] = df["year"].astype(int)
        df["month"] = df["month"].astype(int)

        df["date"] = pd.to_datetime(
            dict(
                year=df["year"],
                month=df["month"],
                day=1
            )
        )

        return df


    def get_monthly_sales_dynamics(self):
        """
        Динамика продаж по месяцам.

        Добавляет:
        - абсолютный рост;
        - процентный рост;
        - направление изменения.
        """

        rows = self.repository.monthly_sales_dynamics()

        df = self._to_dataframe(
            rows,
            [
                "month",
                "revenue",
                "previous_revenue",
                "revenue_change",
                "growth_percent",
            ]
        )

        if df.empty:
            return df

        df["month"] = pd.to_datetime(
            df["month"]
        )

        df["growth_percent"] = pd.to_numeric(
            df["growth_percent"],
            errors="coerce"
        )

        df["trend"] = np.select(
            [
                df["growth_percent"] > 0,
                df["growth_percent"] < 0,
                df["growth_percent"] == 0,
            ],
            [
                "growth",
                "decline",
                "stable",
            ],
            default="unknown",
        )

        return df


    def get_yearly_growth(self):
        """Рост продаж год к году."""

        rows = self.repository.yearly_growth()

        df = self._to_dataframe(
            rows,
            [
                "year",
                "revenue",
                "previous_revenue",
                "revenue_change",
                "growth_percent",
            ]
        )

        if df.empty:
            return df

        df["year"] = df["year"].astype(int)

        df["trend"] = np.select(
            [
                df["growth_percent"] > 0,
                df["growth_percent"] < 0,
                df["growth_percent"] == 0,
            ],
            [
                "growth",
                "decline",
                "stable",
            ],
            default="unknown",
        )

        return df


    # ============================================================
    # PRODUCT ANALYSIS
    # ============================================================

    def get_top_products_by_quantity(
        self,
        limit=10,
        year=None,
    ):
        """Топ товаров по количеству продаж."""

        rows = self.repository.top_products_by_quantity(
            limit=limit,
            year=year,
        )

        return self._to_dataframe(
            rows,
            [
                "product_id",
                "name",
                "units_sold",
                "orders_count",
                "revenue",
            ]
        )


    def get_top_products_by_revenue(
        self,
        limit=10,
        year=None,
    ):
        """Топ товаров по выручке."""

        rows = self.repository.top_products_by_revenue(
            limit=limit,
            year=year,
        )

        df = self._to_dataframe(
            rows,
            [
                "product_id",
                "name",
                "units_sold",
                "revenue",
            ]
        )

        if not df.empty:
            df["revenue_share"] = (
                df["revenue"]
                / df["revenue"].sum()
                * 100
            )

        return df


    def get_top_products_by_profit(
        self,
        limit=10,
        year=None,
    ):
        """Топ товаров по прибыли."""

        rows = self.repository.top_products_by_profit(
            limit=limit,
            year=year,
        )

        df = self._to_dataframe(
            rows,
            [
                "product_id",
                "name",
                "units_sold",
                "profit",
                "revenue",
            ]
        )

        if not df.empty:
            df["margin_percent"] = np.where(
                df["revenue"] != 0,
                df["profit"]
                / df["revenue"]
                * 100,
                0,
            )

        return df


    def get_bottom_products_by_profit(
        self,
        limit=10,
        year=None,
    ):
        """Самые убыточные товары."""

        rows = self.repository.bottom_products_by_profit(
            limit=limit,
            year=year,
        )

        df = self._to_dataframe(
            rows,
            [
                "product_id",
                "name",
                "profit",
            ]
        )

        return df


    # ============================================================
    # PROFITABILITY
    # ============================================================

    def get_profit_by_month(self, year=None):
        """Прибыль и выручка по месяцам."""

        rows = self.repository.profit_by_month(year)

        df = self._to_dataframe(
            rows,
            [
                "year",
                "month",
                "profit",
                "revenue",
            ]
        )

        if df.empty:
            return df

        df["margin_percent"] = np.where(
            df["revenue"] != 0,
            df["profit"]
            / df["revenue"]
            * 100,
            0,
        )

        df["date"] = pd.to_datetime(
            dict(
                year=df["year"].astype(int),
                month=df["month"].astype(int),
                day=1,
            )
        )

        return df


    def get_product_profitability(self, year=None):
        """Полная прибыльность товаров."""

        rows = self.repository.product_profitability(
            year
        )

        df = self._to_dataframe(
            rows,
            [
                "product_id",
                "name",
                "units_sold",
                "revenue",
                "cost",
                "profit",
                "margin_percent",
            ]
        )

        if df.empty:
            return df

        # Дополнительная классификация товара
        df["profitability"] = np.select(
            [
                df["margin_percent"] >= 30,
                df["margin_percent"] >= 15,
                df["margin_percent"] >= 0,
                df["margin_percent"] < 0,
            ],
            [
                "high",
                "medium",
                "low",
                "loss",
            ],
            default="unknown",
        )

        return df


    # ============================================================
    # CATEGORY / BRAND
    # ============================================================

    def get_category_performance(self, year=None):
        """Аналитика категорий."""

        rows = self.repository.category_performance(
            year
        )

        df = self._to_dataframe(
            rows,
            [
                "category_id",
                "category",
                "units_sold",
                "revenue",
                "cost",
                "profit",
            ]
        )

        if df.empty:
            return df

        df["margin_percent"] = np.where(
            df["revenue"] != 0,
            df["profit"]
            / df["revenue"]
            * 100,
            0,
        )

        total_revenue = df["revenue"].sum()

        df["revenue_share"] = np.where(
            total_revenue != 0,
            df["revenue"]
            / total_revenue
            * 100,
            0,
        )

        return df


    def get_brand_performance(self, year=None):
        """Аналитика брендов."""

        rows = self.repository.brand_performance(
            year
        )

        df = self._to_dataframe(
            rows,
            [
                "brand_id",
                "brand",
                "products_count",
                "units_sold",
                "revenue",
                "profit",
            ]
        )

        if df.empty:
            return df

        df["margin_percent"] = np.where(
            df["revenue"] != 0,
            df["profit"]
            / df["revenue"]
            * 100,
            0,
        )

        return df


    # ============================================================
    # RANKING
    # ============================================================

    def get_product_category_ranking(
        self,
        year=None,
    ):
        """
        Рейтинг товаров внутри категорий.
        """

        rows = self.repository.products_ranked_inside_category(
            year
        )

        return self._to_dataframe(
            rows,
            [
                "category",
                "product",
                "revenue",
                "category_rank",
            ]
        )


    # ============================================================
    # ABC ANALYSIS
    # ============================================================

    def get_abc_analysis(self, year=None):
        """
        ABC-анализ товаров.

        SQL уже определяет классы,
        service добавляет дополнительные показатели.
        """

        rows = self.repository.abc_analysis(
            year
        )

        df = self._to_dataframe(
            rows,
            [
                "product_id",
                "name",
                "revenue",
                "cumulative_share",
                "abc_class",
            ]
        )

        if df.empty:
            return df

        df["revenue_percent"] = (
            df["revenue"]
            / df["revenue"].sum()
            * 100
        )

        return df


    def get_abc_summary(self, year=None):
        """
        Сводка ABC:

        количество товаров;
        выручка;
        доля выручки.
        """

        df = self.get_abc_analysis(year)

        if df.empty:
            return pd.DataFrame(
                columns=[
                    "abc_class",
                    "products_count",
                    "revenue",
                    "revenue_share",
                ]
            )

        summary = (
            df
            .groupby("abc_class", as_index=False)
            .agg(
                products_count=(
                    "product_id",
                    "count",
                ),
                revenue=(
                    "revenue",
                    "sum",
                ),
            )
        )

        total_revenue = summary["revenue"].sum()

        summary["revenue_share"] = np.where(
            total_revenue != 0,
            summary["revenue"]
            / total_revenue
            * 100,
            0,
        )

        return summary


    # ============================================================
    # PRODUCT SHARE
    # ============================================================

    def get_product_revenue_share(
        self,
        year=None,
    ):
        """Доля каждого товара в общей выручке."""

        rows = self.repository.product_revenue_share(
            year
        )

        df = self._to_dataframe(
            rows,
            [
                "product_id",
                "name",
                "revenue",
                "revenue_share_percent",
            ]
        )

        if df.empty:
            return df

        # Накопительная доля для Pareto
        df["cumulative_revenue_share"] = (
            df["revenue_share_percent"]
            .cumsum()
        )

        # Группа Pareto
        df["pareto_zone"] = np.select(
            [
                df["cumulative_revenue_share"] <= 80,
                df["cumulative_revenue_share"] <= 95,
            ],
            [
                "A",
                "B",
            ],
            default="C",
        )

        return df


    # ============================================================
    # BEST / WORST
    # ============================================================

    def get_best_sales_month(self, year=None):
        """Лучший месяц."""

        row = self.repository.best_sales_month(
            year
        )

        if row is None:
            return None

        return {
            "month": int(row[0]),
            "revenue": float(row[1]),
        }


    def get_worst_sales_month(self, year=None):
        """Худший месяц."""

        row = self.repository.worst_sales_month(
            year
        )

        if row is None:
            return None

        return {
            "month": int(row[0]),
            "revenue": float(row[1]),
        }


    # ============================================================
    # MANAGEMENT DASHBOARD
    # ============================================================

    def get_dashboard_data(self, year=None):
        """
        Основной агрегатор для dashboard.

        Один вызов service возвращает
        основные показатели продаж.
        """

        summary = self.get_sales_summary(year)

        monthly = self.get_revenue_by_month(year)

        products = self.get_top_products_by_revenue(
            limit=10,
            year=year,
        )

        profit = self.get_profit_by_month(year)

        categories = self.get_category_performance(
            year
        )

        return {
            "summary": summary,
            "monthly_revenue": monthly,
            "top_products": products,
            "monthly_profit": profit,
            "categories": categories,
        }


    # ============================================================
    # DATA QUALITY
    # ============================================================

    def validate_sales_data(self):
        """
        Базовая проверка качества данных.

        Не заменяет отдельный data-quality модуль,
        но позволяет быстро увидеть проблемы.
        """

        checks = {}

        checks["negative_quantities"] = self._fetch_scalar(
            """
            SELECT COUNT(*)
            FROM order_items
            WHERE quantity < 0
            """
        )

        checks["negative_prices"] = self._fetch_scalar(
            """
            SELECT COUNT(*)
            FROM order_items
            WHERE price < 0
            """
        )

        checks["missing_orders"] = self._fetch_scalar(
            """
            SELECT COUNT(*)
            FROM order_items oi
            LEFT JOIN orders o
                ON o.order_id = oi.order_id
            WHERE o.order_id IS NULL
            """
        )

        checks["missing_products"] = self._fetch_scalar(
            """
            SELECT COUNT(*)
            FROM order_items oi
            LEFT JOIN products p
                ON p.product_id = oi.product_id
            WHERE p.product_id IS NULL
            """
        )

        checks["missing_cost_prices"] = self._fetch_scalar(
            """
            SELECT COUNT(*)
            FROM order_items oi
            JOIN orders o
                ON o.order_id = oi.order_id
            LEFT JOIN product_prices pp
                ON pp.product_id = oi.product_id
                AND pp.year =
                    EXTRACT(
                        YEAR FROM o.order_date
                    )
            WHERE pp.product_id IS NULL
            """
        )

        return checks


    # ============================================================
    # DATABASE HELPERS
    # ============================================================

    def _fetch_scalar(self, query, params=None):
        """Получить одно скалярное значение."""

        row = self.repository._fetch_one(
            query,
            params
        )

        if row is None:
            return 0

        return row[0] or 0