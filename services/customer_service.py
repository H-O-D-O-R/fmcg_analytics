import numpy as np
import pandas as pd

from repositories.customer_repository import CustomerRepository


class CustomerService:
    """
    Service layer для аналитики клиентов.

    Repository:
        SQL + получение данных.

    Service:
        pandas + numpy + бизнес-метрики.

    Analytics:
        RFM, сегментация, retention, clustering,
        прогнозирование LTV.

    Visualization:
        matplotlib.
    """

    def __init__(self):
        self.repository = CustomerRepository()

    # ============================================================
    # HELPERS
    # ============================================================

    @staticmethod
    def _to_dataframe(rows, columns):
        """Преобразовать результат repository в DataFrame."""

        return pd.DataFrame(
            rows,
            columns=columns
        )

    @staticmethod
    def _numeric(df, columns):
        """Привести выбранные столбцы к числовому типу."""

        for column in columns:
            if column in df.columns:
                df[column] = pd.to_numeric(
                    df[column],
                    errors="coerce"
                )

        return df

    # ============================================================
    # BASIC METRICS
    # ============================================================

    def get_total_customers(self):
        """Общее количество клиентов."""

        row = self.repository.total_customers()

        if row is None:
            return 0

        return int(row[0] or 0)

    def get_active_customers(self, year=None):
        """Количество клиентов, совершивших покупки."""

        row = self.repository.active_customers(year)

        if row is None:
            return 0

        return int(row[0] or 0)

    def get_inactive_customers(self):
        """Клиенты без единого заказа."""

        rows = self.repository.inactive_customers()

        return self._to_dataframe(
            rows,
            [
                "customer_id",
                "name",
            ]
        )

    def get_customer_summary(self, year=None):
        """Основная сводка по клиентам."""

        total = self.get_total_customers()
        active = self.get_active_customers(year)

        inactive = total - active

        activity_rate = (
            active / total * 100
            if total
            else 0
        )

        return {
            "total_customers": total,
            "active_customers": active,
            "inactive_customers": inactive,
            "activity_rate_percent": activity_rate,
        }

    # ============================================================
    # CUSTOMER REVENUE
    # ============================================================

    def get_customer_revenue(self, year=None):
        """Выручка и активность каждого клиента."""

        rows = self.repository.customer_revenue(year)

        df = self._to_dataframe(
            rows,
            [
                "customer_id",
                "name",
                "orders_count",
                "units_bought",
                "revenue",
            ]
        )

        if df.empty:
            return df

        df = self._numeric(
            df,
            [
                "orders_count",
                "units_bought",
                "revenue",
            ]
        )

        total_revenue = df["revenue"].sum()

        df["revenue_share_percent"] = np.where(
            total_revenue != 0,
            df["revenue"]
            / total_revenue
            * 100,
            0,
        )

        df["average_order_value"] = np.where(
            df["orders_count"] != 0,
            df["revenue"]
            / df["orders_count"],
            0,
        )

        return df

    def get_top_customers_by_revenue(
        self,
        limit=10,
        year=None
    ):
        """Топ клиентов по выручке."""

        rows = self.repository.top_customers_by_revenue(
            limit=limit,
            year=year
        )

        df = self._to_dataframe(
            rows,
            [
                "customer_id",
                "name",
                "orders_count",
                "revenue",
            ]
        )

        if df.empty:
            return df

        df = self._numeric(
            df,
            [
                "orders_count",
                "revenue",
            ]
        )

        return df

    # ============================================================
    # AVERAGE CHECK
    # ============================================================

    def get_customer_average_check(
        self,
        year=None
    ):
        """Средний чек каждого клиента."""

        rows = self.repository.customer_average_check(
            year
        )

        df = self._to_dataframe(
            rows,
            [
                "customer_id",
                "name",
                "orders_count",
                "average_check",
                "total_revenue",
            ]
        )

        if df.empty:
            return df

        df = self._numeric(
            df,
            [
                "orders_count",
                "average_check",
                "total_revenue",
            ]
        )

        global_average = df["average_check"].mean()

        df["above_global_average"] = (
            df["average_check"]
            > global_average
        )

        df["check_difference_percent"] = np.where(
            global_average != 0,
            (
                df["average_check"]
                / global_average
                - 1
            ) * 100,
            0,
        )

        return df

    def get_customers_above_average_check(
        self,
        year=None
    ):
        """Клиенты со средним чеком выше среднего."""

        rows = (
            self.repository
            .customers_above_average_check(year)
        )

        df = self._to_dataframe(
            rows,
            [
                "customer_id",
                "name",
                "average_check",
                "global_average_check",
            ]
        )

        if df.empty:
            return df

        df = self._numeric(
            df,
            [
                "average_check",
                "global_average_check",
            ]
        )

        df["difference_percent"] = np.where(
            df["global_average_check"] != 0,
            (
                df["average_check"]
                / df["global_average_check"]
                - 1
            ) * 100,
            0,
        )

        return df

    # ============================================================
    # REPEAT CUSTOMERS
    # ============================================================

    def get_repeat_customers(self, year=None):
        """Клиенты с повторными покупками."""

        rows = self.repository.repeat_customers(year)

        df = self._to_dataframe(
            rows,
            [
                "customer_id",
                "name",
                "orders_count",
            ]
        )

        if df.empty:
            return df

        df = self._numeric(
            df,
            ["orders_count"]
        )

        df["customer_type"] = np.select(
            [
                df["orders_count"] >= 10,
                df["orders_count"] >= 5,
                df["orders_count"] >= 2,
            ],
            [
                "loyal",
                "regular",
                "repeat",
            ],
            default="unknown",
        )

        return df

    def get_one_time_customers(self, year=None):
        """Клиенты, совершившие одну покупку."""

        rows = self.repository.one_time_customers(year)

        return self._to_dataframe(
            rows,
            [
                "customer_id",
                "name",
            ]
        )

    # ============================================================
    # PURCHASE FREQUENCY
    # ============================================================

    def get_purchase_frequency(self):
        """Средний интервал между покупками."""

        rows = self.repository.customer_purchase_frequency()

        df = self._to_dataframe(
            rows,
            [
                "customer_id",
                "name",
                "orders_count",
                "average_days_between_orders",
            ]
        )

        if df.empty:
            return df

        df = self._numeric(
            df,
            [
                "orders_count",
                "average_days_between_orders",
            ]
        )

        df["purchase_frequency_class"] = np.select(
            [
                df["average_days_between_orders"] <= 7,
                df["average_days_between_orders"] <= 30,
                df["average_days_between_orders"] <= 90,
                df["average_days_between_orders"] > 90,
            ],
            [
                "very_frequent",
                "frequent",
                "occasional",
                "rare",
            ],
            default="unknown",
        )

        return df

    # ============================================================
    # RFM
    # ============================================================

    def get_rfm_dataset(self):
        """
        Базовый RFM DataFrame.

        R — Recency
        F — Frequency
        M — Monetary
        """

        rows = self.repository.rfm_dataset()

        df = self._to_dataframe(
            rows,
            [
                "customer_id",
                "name",
                "recency",
                "frequency",
                "monetary",
            ]
        )

        if df.empty:
            return df

        df = self._numeric(
            df,
            [
                "recency",
                "frequency",
                "monetary",
            ]
        )

        return df

    def get_rfm_analysis(self):
        """
        Полный RFM-анализ.

        Каждому клиенту присваивается
        score от 1 до 5 по каждому показателю.
        """

        df = self.get_rfm_dataset()

        if df.empty:
            return df

        # Recency:
        # меньше дней = лучше.
        df["r_score"] = pd.qcut(
            df["recency"],
            q=5,
            labels=[5, 4, 3, 2, 1],
            duplicates="drop"
        )

        # Frequency:
        # больше заказов = лучше.
        df["f_score"] = pd.qcut(
            df["frequency"]
            .rank(method="first"),
            q=5,
            labels=[1, 2, 3, 4, 5],
            duplicates="drop"
        )

        # Monetary:
        # больше денег = лучше.
        df["m_score"] = pd.qcut(
            df["monetary"]
            .rank(method="first"),
            q=5,
            labels=[1, 2, 3, 4, 5],
            duplicates="drop"
        )

        df["r_score"] = pd.to_numeric(
            df["r_score"]
        )

        df["f_score"] = pd.to_numeric(
            df["f_score"]
        )

        df["m_score"] = pd.to_numeric(
            df["m_score"]
        )

        df["rfm_score"] = (
            df["r_score"]
            + df["f_score"]
            + df["m_score"]
        )

        df["rfm_segment"] = np.select(
            [
                (
                    (df["r_score"] >= 4)
                    & (df["f_score"] >= 4)
                    & (df["m_score"] >= 4)
                ),

                (
                    (df["r_score"] >= 4)
                    & (df["f_score"] >= 3)
                ),

                (
                    (df["r_score"] <= 2)
                    & (df["f_score"] >= 4)
                ),

                (
                    (df["r_score"] <= 2)
                    & (df["f_score"] <= 2)
                ),

                (
                    df["m_score"] >= 4
                ),
            ],
            [
                "champions",
                "loyal_customers",
                "at_risk",
                "lost",
                "high_value",
            ],
            default="potential",
        )

        return df

    def get_rfm_segment_summary(self):
        """Сводка клиентов по RFM-сегментам."""

        df = self.get_rfm_analysis()

        if df.empty:
            return pd.DataFrame(
                columns=[
                    "rfm_segment",
                    "customers_count",
                    "revenue",
                    "average_monetary",
                    "average_recency",
                ]
            )

        summary = (
            df
            .groupby(
                "rfm_segment",
                as_index=False
            )
            .agg(
                customers_count=(
                    "customer_id",
                    "count"
                ),
                revenue=(
                    "monetary",
                    "sum"
                ),
                average_monetary=(
                    "monetary",
                    "mean"
                ),
                average_recency=(
                    "recency",
                    "mean"
                ),
            )
        )

        total_customers = (
            summary["customers_count"].sum()
        )

        summary["customer_share_percent"] = np.where(
            total_customers != 0,
            summary["customers_count"]
            / total_customers
            * 100,
            0,
        )

        return summary

    # ============================================================
    # LIFETIME VALUE
    # ============================================================

    def get_customer_lifetime_value(self):
        """Исторический LTV клиента."""

        rows = (
            self.repository
            .customer_lifetime_value()
        )

        df = self._to_dataframe(
            rows,
            [
                "customer_id",
                "name",
                "first_order_date",
                "last_order_date",
                "orders_count",
                "lifetime_value",
            ]
        )

        if df.empty:
            return df

        df["first_order_date"] = pd.to_datetime(
            df["first_order_date"],
            errors="coerce"
        )

        df["last_order_date"] = pd.to_datetime(
            df["last_order_date"],
            errors="coerce"
        )

        df = self._numeric(
            df,
            [
                "orders_count",
                "lifetime_value",
            ]
        )

        df["customer_lifetime_days"] = (
            df["last_order_date"]
            - df["first_order_date"]
        ).dt.days

        df["average_order_value"] = np.where(
            df["orders_count"] != 0,
            df["lifetime_value"]
            / df["orders_count"],
            0,
        )

        return df

    # ============================================================
    # PROFITABILITY
    # ============================================================

    def get_customer_profitability(self):
        """Выручка, себестоимость и прибыль клиента."""

        rows = self.repository.customer_profitability()

        df = self._to_dataframe(
            rows,
            [
                "customer_id",
                "name",
                "revenue",
                "cost",
                "profit",
            ]
        )

        if df.empty:
            return df

        df = self._numeric(
            df,
            [
                "revenue",
                "cost",
                "profit",
            ]
        )

        df["margin_percent"] = np.where(
            df["revenue"] != 0,
            df["profit"]
            / df["revenue"]
            * 100,
            0,
        )

        df["profit_class"] = np.select(
            [
                df["profit"] > 0,
                df["profit"] == 0,
                df["profit"] < 0,
            ],
            [
                "profitable",
                "break_even",
                "loss",
            ],
            default="unknown",
        )

        return df

    # ============================================================
    # PRODUCT / CATEGORY PREFERENCES
    # ============================================================

    def get_customer_favorite_categories(self):
        """Самая прибыльная/популярная категория клиента."""

        rows = (
            self.repository
            .customer_favorite_categories()
        )

        df = self._to_dataframe(
            rows,
            [
                "customer_id",
                "customer",
                "category",
                "units_bought",
                "revenue",
            ]
        )

        if df.empty:
            return df

        df = self._numeric(
            df,
            [
                "units_bought",
                "revenue",
            ]
        )

        return df

    # ============================================================
    # COHORT ANALYSIS
    # ============================================================

    def get_customer_cohorts(self):
        """Базовые данные когортного анализа."""

        rows = self.repository.customer_cohorts()

        df = self._to_dataframe(
            rows,
            [
                "cohort_month",
                "order_month",
                "active_customers",
            ]
        )

        if df.empty:
            return df

        df["cohort_month"] = pd.to_datetime(
            df["cohort_month"]
        )

        df["order_month"] = pd.to_datetime(
            df["order_month"]
        )

        df = self._numeric(
            df,
            ["active_customers"]
        )

        df["month_number"] = (
            (
                df["order_month"].dt.year
                - df["cohort_month"].dt.year
            ) * 12
            +
            (
                df["order_month"].dt.month
                - df["cohort_month"].dt.month
            )
        )

        return df

    def get_cohort_retention(self):
        """Retention по когортам."""

        rows = self.repository.cohort_retention()

        df = self._to_dataframe(
            rows,
            [
                "cohort_month",
                "month_number",
                "active_customers",
                "cohort_size",
                "retention_percent",
            ]
        )

        if df.empty:
            return df

        df["cohort_month"] = pd.to_datetime(
            df["cohort_month"]
        )

        df = self._numeric(
            df,
            [
                "month_number",
                "active_customers",
                "cohort_size",
                "retention_percent",
            ]
        )

        return df

    # ============================================================
    # CUSTOMER GROWTH
    # ============================================================

    def get_monthly_active_customers(self):
        """Активные клиенты по месяцам."""

        rows = (
            self.repository
            .monthly_active_customers()
        )

        df = self._to_dataframe(
            rows,
            [
                "month",
                "active_customers",
            ]
        )

        if df.empty:
            return df

        df["month"] = pd.to_datetime(
            df["month"]
        )

        df = self._numeric(
            df,
            ["active_customers"]
        )

        df["previous_month"] = (
            df["active_customers"]
            .shift(1)
        )

        df["growth_percent"] = np.where(
            df["previous_month"] != 0,
            (
                df["active_customers"]
                / df["previous_month"]
                - 1
            ) * 100,
            np.nan,
        )

        return df

    def get_new_customers_by_month(self):
        """Новые клиенты по месяцам."""

        rows = (
            self.repository
            .new_customers_by_month()
        )

        df = self._to_dataframe(
            rows,
            [
                "month",
                "new_customers",
            ]
        )

        if df.empty:
            return df

        df["month"] = pd.to_datetime(
            df["month"]
        )

        df = self._numeric(
            df,
            ["new_customers"]
        )

        return df

    # ============================================================
    # CHURN
    # ============================================================

    def get_customer_last_purchase(self):
        """Последняя покупка каждого клиента."""

        rows = (
            self.repository
            .customer_last_purchase()
        )

        df = self._to_dataframe(
            rows,
            [
                "customer_id",
                "name",
                "last_order_date",
                "days_since_purchase",
            ]
        )

        if df.empty:
            return df

        df["last_order_date"] = pd.to_datetime(
            df["last_order_date"],
            errors="coerce"
        )

        df = self._numeric(
            df,
            ["days_since_purchase"]
        )

        return df

    def get_churn_candidates(
        self,
        days=90
    ):
        """Клиенты с высоким риском оттока."""

        rows = self.repository.churn_candidates(
            days
        )

        df = self._to_dataframe(
            rows,
            [
                "customer_id",
                "name",
                "last_order_date",
                "days_since_purchase",
            ]
        )

        if df.empty:
            return df

        df["last_order_date"] = pd.to_datetime(
            df["last_order_date"],
            errors="coerce"
        )

        df = self._numeric(
            df,
            ["days_since_purchase"]
        )

        df["churn_risk"] = np.select(
            [
                df["days_since_purchase"] > 365,
                df["days_since_purchase"] > 180,
                df["days_since_purchase"] > days,
            ],
            [
                "critical",
                "high",
                "medium",
            ],
            default="low",
        )

        return df

    # ============================================================
    # CUSTOMER RANKING
    # ============================================================

    def get_customer_revenue_rank(self):
        """Рейтинг клиентов по выручке."""

        rows = (
            self.repository
            .customer_revenue_rank()
        )

        df = self._to_dataframe(
            rows,
            [
                "customer_id",
                "name",
                "revenue",
                "revenue_rank",
                "revenue_share_percent",
            ]
        )

        if df.empty:
            return df

        df = self._numeric(
            df,
            [
                "revenue",
                "revenue_rank",
                "revenue_share_percent",
            ]
        )

        df["cumulative_revenue_share"] = (
            df["revenue_share_percent"]
            .cumsum()
        )

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
    # UNIVERSAL CUSTOMER DATASET
    # ============================================================

    def get_customer_analytics_dataset(self):
        """
        Большой универсальный датасет клиента.

        Основная точка входа для:
        - pandas;
        - numpy;
        - RFM;
        - clustering;
        - customer segmentation;
        - LTV analysis.
        """

        rows = (
            self.repository
            .customer_analytics_dataset()
        )

        df = self._to_dataframe(
            rows,
            [
                "customer_id",
                "name",
                "first_order_date",
                "last_order_date",
                "recency_days",
                "frequency",
                "monetary",
                "units_bought",
                "average_check",
                "customer_age_days",
            ]
        )

        if df.empty:
            return df

        df["first_order_date"] = pd.to_datetime(
            df["first_order_date"],
            errors="coerce"
        )

        df["last_order_date"] = pd.to_datetime(
            df["last_order_date"],
            errors="coerce"
        )

        df = self._numeric(
            df,
            [
                "recency_days",
                "frequency",
                "monetary",
                "units_bought",
                "average_check",
                "customer_age_days",
            ]
        )

        # Средняя покупка в месяц жизни клиента.
        customer_age_months = (
            df["customer_age_days"] / 30
        )

        df["monthly_revenue"] = np.where(
            customer_age_months > 0,
            df["monetary"]
            / customer_age_months,
            df["monetary"],
        )

        # Среднее количество заказов в месяц.
        df["orders_per_month"] = np.where(
            customer_age_months > 0,
            df["frequency"]
            / customer_age_months,
            df["frequency"],
        )

        return df

    # ============================================================
    # CUSTOMER SEGMENTATION
    # ============================================================

    def get_customer_segments(self):
        """
        Быстрая сегментация клиентов.

        Это не полноценный ML-кластеринг.
        Для первой версии используется
        бизнес-сегментация на основе RFM/LTV.
        """

        df = self.get_customer_analytics_dataset()

        if df.empty:
            return df

        # Квантили распределения.
        monetary_q75 = df["monetary"].quantile(0.75)
        monetary_q50 = df["monetary"].quantile(0.50)

        frequency_q75 = df["frequency"].quantile(0.75)
        frequency_q50 = df["frequency"].quantile(0.50)

        df["segment"] = np.select(
            [
                (
                    (df["monetary"] >= monetary_q75)
                    & (df["frequency"] >= frequency_q75)
                    & (df["recency_days"] <= 30)
                ),

                (
                    (df["monetary"] >= monetary_q50)
                    & (df["frequency"] >= frequency_q50)
                    & (df["recency_days"] <= 90)
                ),

                (
                    (df["monetary"] >= monetary_q75)
                    & (df["recency_days"] > 90)
                ),

                (
                    df["recency_days"] > 180
                ),

                (
                    df["monetary"] < monetary_q50
                    & (df["frequency"] < frequency_q50)
                ),
            ],
            [
                "champions",
                "loyal",
                "high_value_at_risk",
                "lost",
                "low_value",
            ],
            default="potential",
        )

        return df

    def get_segment_summary(self):
        """Сводка клиентских сегментов."""

        df = self.get_customer_segments()

        if df.empty:
            return pd.DataFrame()

        summary = (
            df
            .groupby(
                "segment",
                as_index=False
            )
            .agg(
                customers_count=(
                    "customer_id",
                    "count"
                ),
                revenue=(
                    "monetary",
                    "sum"
                ),
                average_revenue=(
                    "monetary",
                    "mean"
                ),
                average_check=(
                    "average_check",
                    "mean"
                ),
                average_frequency=(
                    "frequency",
                    "mean"
                ),
                average_recency=(
                    "recency_days",
                    "mean"
                ),
            )
        )

        total_revenue = summary["revenue"].sum()

        summary["revenue_share_percent"] = np.where(
            total_revenue != 0,
            summary["revenue"]
            / total_revenue
            * 100,
            0,
        )

        return summary

    # ============================================================
    # DASHBOARD
    # ============================================================

    def get_dashboard_data(self, year=None):
        """
        Основной набор данных для customer dashboard.
        """

        summary = self.get_customer_summary(
            year
        )

        revenue = self.get_customer_revenue(
            year
        )

        top_customers = (
            self.get_top_customers_by_revenue(
                limit=10,
                year=year
            )
        )

        rfm = self.get_rfm_analysis()

        segments = self.get_segment_summary()

        cohorts = self.get_cohort_retention()

        churn = self.get_churn_candidates()

        return {
            "summary": summary,
            "customer_revenue": revenue,
            "top_customers": top_customers,
            "rfm": rfm,
            "segments": segments,
            "cohorts": cohorts,
            "churn": churn,
        }

    # ============================================================
    # DATA QUALITY
    # ============================================================

    def validate_customer_data(self):
        """
        Базовая проверка качества данных клиентов.
        """

        checks = {}

        checks["orders_without_customer"] = (
            self._fetch_scalar(
                """
                SELECT COUNT(*)
                FROM orders o
                LEFT JOIN customers c
                    ON c.customer_id =
                       o.customer_id
                WHERE c.customer_id IS NULL
                """
            )
        )

        checks["duplicate_customer_names"] = (
            self._fetch_scalar(
                """
                SELECT COUNT(*)
                FROM (
                    SELECT
                        name,
                        COUNT(*) AS cnt
                    FROM customers
                    GROUP BY name
                    HAVING COUNT(*) > 1
                ) duplicates
                """
            )
        )

        checks["orders_without_items"] = (
            self._fetch_scalar(
                """
                SELECT COUNT(*)
                FROM orders o
                LEFT JOIN order_items oi
                    ON oi.order_id =
                       o.order_id
                WHERE oi.order_id IS NULL
                """
            )
        )

        checks["negative_order_values"] = (
            self._fetch_scalar(
                """
                SELECT COUNT(*)
                FROM order_items
                WHERE
                    quantity < 0
                    OR price < 0
                """
            )
        )

        return checks

    # ============================================================
    # DATABASE HELPERS
    # ============================================================

    def _fetch_scalar(
        self,
        query,
        params=None
    ):
        """
        Выполнить SELECT,
        возвращающий одно значение.
        """

        row = self.repository._fetch_one(
            query,
            params
        )

        if row is None:
            return 0

        return row[0] or 0