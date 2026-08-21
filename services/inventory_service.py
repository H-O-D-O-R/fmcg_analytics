import numpy as np
import pandas as pd

from repositories.inventory_repository import InventoryRepository


class InventoryService:
    """
    Service layer для аналитики складских запасов.

    Repository:
        SQL + получение данных.

    Service:
        pandas + numpy + бизнес-метрики.

    Analytics:
        прогнозирование, статистические модели,
        более сложные расчеты.

    Visualization:
        matplotlib.
    """

    def __init__(self):
        self.repository = InventoryRepository()

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
    def _numeric(
        df,
        columns
    ):
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

    def get_total_stock(self):
        """Общее количество единиц на складах."""

        row = self.repository.total_stock()

        if row is None:
            return 0

        return int(row[0] or 0)


    def get_total_stock_value(self):
        """Общая стоимость текущих запасов."""

        row = self.repository.total_stock_value()

        if row is None:
            return 0.0

        return float(row[0] or 0)


    def get_products_count_in_stock(self):
        """Количество товаров с положительным остатком."""

        row = self.repository.products_count_in_stock()

        if row is None:
            return 0

        return int(row[0] or 0)


    def get_inventory_summary(self):
        """Общая сводка склада."""

        total_stock = self.get_total_stock()
        stock_value = self.get_total_stock_value()
        products_count = self.get_products_count_in_stock()

        average_stock_value = (
            stock_value / products_count
            if products_count
            else 0
        )

        return {
            "total_units": total_stock,
            "stock_value": stock_value,
            "products_count": products_count,
            "average_stock_value": average_stock_value,
        }

    # ============================================================
    # CURRENT STOCK
    # ============================================================

    def get_current_stock(self):
        """
        Полный текущий остаток.

        Возвращает DataFrame:
        product
        category
        brand
        warehouse
        quantity
        """

        rows = self.repository.current_stock()

        df = self._to_dataframe(
            rows,
            [
                "product_id",
                "product",
                "category",
                "brand",
                "warehouse_id",
                "warehouse",
                "quantity",
            ]
        )

        if df.empty:
            return df

        df = self._numeric(
            df,
            ["quantity"]
        )

        return df


    def get_stock_by_product(self):
        """Суммарный остаток каждого товара."""

        rows = self.repository.stock_by_product()

        df = self._to_dataframe(
            rows,
            [
                "product_id",
                "name",
                "total_stock",
            ]
        )

        if df.empty:
            return df

        df = self._numeric(
            df,
            ["total_stock"]
        )

        total_stock = df["total_stock"].sum()

        df["stock_share_percent"] = np.where(
            total_stock != 0,
            df["total_stock"]
            / total_stock
            * 100,
            0,
        )

        return df


    def get_stock_by_category(self):
        """Остатки по категориям."""

        rows = self.repository.stock_by_category()

        df = self._to_dataframe(
            rows,
            [
                "category_id",
                "category",
                "products_count",
                "total_stock",
            ]
        )

        if df.empty:
            return df

        df = self._numeric(
            df,
            [
                "products_count",
                "total_stock",
            ]
        )

        total_stock = df["total_stock"].sum()

        df["stock_share_percent"] = np.where(
            total_stock != 0,
            df["total_stock"]
            / total_stock
            * 100,
            0,
        )

        return df

    # ============================================================
    # LOW STOCK
    # ============================================================

    def get_low_stock_products(
        self,
        threshold=10
    ):
        """Товары с остатком ниже порога."""

        rows = self.repository.low_stock_products(
            threshold
        )

        df = self._to_dataframe(
            rows,
            [
                "product_id",
                "name",
                "current_stock",
            ]
        )

        if df.empty:
            return df

        df = self._numeric(
            df,
            ["current_stock"]
        )

        df["stock_status"] = np.select(
            [
                df["current_stock"] <= 0,
                df["current_stock"] <= threshold / 2,
                df["current_stock"] <= threshold,
            ],
            [
                "out_of_stock",
                "critical",
                "low",
            ],
            default="normal",
        )

        return df


    def get_out_of_stock_products(self):
        """Товары, которых полностью нет на складе."""

        rows = self.repository.out_of_stock_products()

        return self._to_dataframe(
            rows,
            [
                "product_id",
                "name",
            ]
        )

    # ============================================================
    # DEAD / INACTIVE STOCK
    # ============================================================

    def get_dead_stock(self):
        """Товары без единой продажи."""

        rows = self.repository.dead_stock_products()

        df = self._to_dataframe(
            rows,
            [
                "product_id",
                "name",
                "stock_quantity",
            ]
        )

        if df.empty:
            return df

        df = self._numeric(
            df,
            ["stock_quantity"]
        )

        return df


    def get_inactive_stock(
        self,
        days=90
    ):
        """
        Товары, которые давно не продавались.
        """

        rows = self.repository.inactive_stock(
            days
        )

        df = self._to_dataframe(
            rows,
            [
                "product_id",
                "name",
                "stock_quantity",
                "last_sale_date",
                "days_since_sale",
            ]
        )

        if df.empty:
            return df

        df["last_sale_date"] = pd.to_datetime(
            df["last_sale_date"],
            errors="coerce"
        )

        df = self._numeric(
            df,
            [
                "stock_quantity",
                "days_since_sale",
            ]
        )

        df["inactivity_level"] = np.select(
            [
                df["days_since_sale"].isna(),
                df["days_since_sale"] > 365,
                df["days_since_sale"] > 180,
                df["days_since_sale"] > days,
            ],
            [
                "never_sold",
                "critical",
                "high",
                "medium",
            ],
            default="normal",
        )

        return df

    # ============================================================
    # STOCK VALUE
    # ============================================================

    def get_stock_value_by_product(self):
        """Стоимость запасов по товарам."""

        rows = self.repository.stock_value_by_product()

        df = self._to_dataframe(
            rows,
            [
                "product_id",
                "name",
                "stock_quantity",
                "cost_price",
                "stock_value",
            ]
        )

        if df.empty:
            return df

        df = self._numeric(
            df,
            [
                "stock_quantity",
                "cost_price",
                "stock_value",
            ]
        )

        total_value = df["stock_value"].sum()

        df["value_share_percent"] = np.where(
            total_value != 0,
            df["stock_value"]
            / total_value
            * 100,
            0,
        )

        return df


    def get_stock_value_by_category(self):
        """Стоимость запасов по категориям."""

        rows = self.repository.stock_value_by_category()

        df = self._to_dataframe(
            rows,
            [
                "category_id",
                "category",
                "stock_value",
            ]
        )

        if df.empty:
            return df

        df = self._numeric(
            df,
            ["stock_value"]
        )

        total_value = df["stock_value"].sum()

        df["value_share_percent"] = np.where(
            total_value != 0,
            df["stock_value"]
            / total_value
            * 100,
            0,
        )

        return df

    # ============================================================
    # SALES VS STOCK
    # ============================================================

    def get_stock_and_sales(
        self,
        year=None
    ):
        """
        Объединяет:
        - продажи;
        - выручку;
        - текущий остаток.

        Основной DataFrame для дальнейшего
        анализа эффективности запасов.
        """

        rows = self.repository.stock_and_sales(
            year
        )

        df = self._to_dataframe(
            rows,
            [
                "product_id",
                "name",
                "units_sold",
                "revenue",
                "stock_quantity",
            ]
        )

        if df.empty:
            return df

        df = self._numeric(
            df,
            [
                "units_sold",
                "revenue",
                "stock_quantity",
            ]
        )

        # Продажи на одну единицу текущего запаса.
        df["sales_to_stock_ratio"] = np.where(
            df["stock_quantity"] > 0,
            df["units_sold"]
            / df["stock_quantity"],
            np.nan,
        )

        # Простейшая классификация.
        df["stock_efficiency"] = np.select(
            [
                df["sales_to_stock_ratio"] >= 10,
                df["sales_to_stock_ratio"] >= 5,
                df["sales_to_stock_ratio"] >= 1,
                df["sales_to_stock_ratio"] < 1,
            ],
            [
                "excellent",
                "good",
                "average",
                "poor",
            ],
            default="unknown",
        )

        return df

    # ============================================================
    # INVENTORY TURNOVER
    # ============================================================

    def get_inventory_turnover(
        self,
        year=None
    ):
        """
        Оборачиваемость запасов.

        SQL возвращает базовую метрику,
        service добавляет классификацию.
        """

        rows = self.repository.inventory_turnover(
            year
        )

        df = self._to_dataframe(
            rows,
            [
                "product_id",
                "name",
                "units_sold",
                "stock_quantity",
                "turnover",
            ]
        )

        if df.empty:
            return df

        df = self._numeric(
            df,
            [
                "units_sold",
                "stock_quantity",
                "turnover",
            ]
        )

        df["turnover_class"] = np.select(
            [
                df["turnover"] >= 10,
                df["turnover"] >= 5,
                df["turnover"] >= 1,
                df["turnover"] < 1,
            ],
            [
                "very_fast",
                "fast",
                "normal",
                "slow",
            ],
            default="unknown",
        )

        return df

    # ============================================================
    # STOCK COVERAGE
    # ============================================================

    def get_stock_coverage(
        self,
        year=None
    ):
        """
        Сколько дней примерно хватит
        текущего запаса.
        """

        rows = self.repository.stock_coverage(
            year
        )

        df = self._to_dataframe(
            rows,
            [
                "product_id",
                "name",
                "stock_quantity",
                "units_sold",
                "active_days",
                "estimated_days_left",
            ]
        )

        if df.empty:
            return df

        df = self._numeric(
            df,
            [
                "stock_quantity",
                "units_sold",
                "active_days",
                "estimated_days_left",
            ]
        )

        df["coverage_status"] = np.select(
            [
                df["estimated_days_left"] < 7,
                df["estimated_days_left"] < 30,
                df["estimated_days_left"] < 90,
                df["estimated_days_left"] >= 90,
            ],
            [
                "critical",
                "low",
                "normal",
                "excess",
            ],
            default="unknown",
        )

        return df

    # ============================================================
    # ABC ANALYSIS
    # ============================================================

    def get_abc_stock_analysis(self):
        """
        ABC-анализ запасов по стоимости.
        """

        rows = self.repository.abc_stock_analysis()

        df = self._to_dataframe(
            rows,
            [
                "product_id",
                "name",
                "stock_quantity",
                "stock_value",
                "cumulative_share",
                "abc_class",
            ]
        )

        if df.empty:
            return df

        df = self._numeric(
            df,
            [
                "stock_quantity",
                "stock_value",
                "cumulative_share",
            ]
        )

        total_value = df["stock_value"].sum()

        df["value_share_percent"] = np.where(
            total_value != 0,
            df["stock_value"]
            / total_value
            * 100,
            0,
        )

        return df


    def get_abc_stock_summary(self):
        """Сводка ABC-классов склада."""

        df = self.get_abc_stock_analysis()

        if df.empty:
            return pd.DataFrame(
                columns=[
                    "abc_class",
                    "products_count",
                    "stock_value",
                    "value_share_percent",
                ]
            )

        summary = (
            df
            .groupby(
                "abc_class",
                as_index=False
            )
            .agg(
                products_count=(
                    "product_id",
                    "count"
                ),
                stock_value=(
                    "stock_value",
                    "sum"
                ),
            )
        )

        total_value = summary["stock_value"].sum()

        summary["value_share_percent"] = np.where(
            total_value != 0,
            summary["stock_value"]
            / total_value
            * 100,
            0,
        )

        return summary

    # ============================================================
    # WAREHOUSES
    # ============================================================

    def get_warehouse_load(self):
        """Загрузка складов."""

        rows = self.repository.warehouse_load()

        df = self._to_dataframe(
            rows,
            [
                "warehouse_id",
                "warehouse",
                "products_count",
                "total_units",
            ]
        )

        if df.empty:
            return df

        df = self._numeric(
            df,
            [
                "products_count",
                "total_units",
            ]
        )

        total_units = df["total_units"].sum()

        df["stock_share_percent"] = np.where(
            total_units != 0,
            df["total_units"]
            / total_units
            * 100,
            0,
        )

        df["load_class"] = np.select(
            [
                df["stock_share_percent"] >= 40,
                df["stock_share_percent"] >= 25,
                df["stock_share_percent"] >= 10,
            ],
            [
                "high",
                "medium",
                "low",
            ],
            default="very_low",
        )

        return df


    def get_warehouse_stock_value(self):
        """Стоимость запасов по складам."""

        rows = self.repository.warehouse_stock_value()

        df = self._to_dataframe(
            rows,
            [
                "warehouse_id",
                "warehouse",
                "stock_value",
            ]
        )

        if df.empty:
            return df

        df = self._numeric(
            df,
            ["stock_value"]
        )

        total_value = df["stock_value"].sum()

        df["value_share_percent"] = np.where(
            total_value != 0,
            df["stock_value"]
            / total_value
            * 100,
            0,
        )

        return df


    def get_warehouse_distribution(self):
        """
        Распределение товаров между складами.
        """

        rows = self.repository.warehouse_product_distribution()

        df = self._to_dataframe(
            rows,
            [
                "warehouse",
                "product",
                "quantity",
            ]
        )

        if df.empty:
            return df

        df = self._numeric(
            df,
            ["quantity"]
        )

        df["warehouse_total"] = (
            df
            .groupby("warehouse")["quantity"]
            .transform("sum")
        )

        df["stock_share_percent"] = np.where(
            df["warehouse_total"] != 0,
            df["quantity"]
            / df["warehouse_total"]
            * 100,
            0,
        )

        return df

    # ============================================================
    # RISK ANALYSIS
    # ============================================================

    def get_inventory_risk_dataset(
        self,
        year=None
    ):
        """
        Формирует датасет для оценки риска товара.

        Итоговый risk score рассчитывается
        в numpy/pandas.
        """

        rows = self.repository.inventory_risk_dataset(
            year
        )

        df = self._to_dataframe(
            rows,
            [
                "product_id",
                "name",
                "stock_quantity",
                "units_sold",
                "orders_count",
                "last_sale_date",
                "days_since_sale",
            ]
        )

        if df.empty:
            return df

        df["last_sale_date"] = pd.to_datetime(
            df["last_sale_date"],
            errors="coerce"
        )

        df = self._numeric(
            df,
            [
                "stock_quantity",
                "units_sold",
                "orders_count",
                "days_since_sale",
            ]
        )

        # Нормализация признаков.
        stock_risk = (
            df["stock_quantity"]
            .rank(pct=True)
        )

        inactivity_risk = (
            df["days_since_sale"]
            .fillna(
                df["days_since_sale"].max()
            )
            .rank(pct=True)
        )

        sales_risk = (
            1 -
            df["units_sold"]
            .rank(pct=True)
        )

        # Итоговый риск.
        df["risk_score"] = (
            stock_risk * 0.35
            + inactivity_risk * 0.40
            + sales_risk * 0.25
        ) * 100

        df["risk_class"] = np.select(
            [
                df["risk_score"] >= 75,
                df["risk_score"] >= 50,
                df["risk_score"] >= 25,
            ],
            [
                "critical",
                "high",
                "medium",
            ],
            default="low",
        )

        return df.sort_values(
            "risk_score",
            ascending=False
        ).reset_index(drop=True)

    # ============================================================
    # STOCK OPTIMIZATION DATASET
    # ============================================================

    def get_stock_optimization_dataset(
        self,
        year=None
    ):
        """
        Универсальный датасет для последующего
        прогнозирования и оптимизации запасов.

        На его основе можно делать:
        - reorder point;
        - safety stock;
        - demand forecasting;
        - EOQ;
        - ABC/XYZ.
        """

        stock_sales = self.get_stock_and_sales(
            year
        )

        coverage = self.get_stock_coverage(
            year
        )

        turnover = self.get_inventory_turnover(
            year
        )

        if stock_sales.empty:
            return pd.DataFrame()

        result = stock_sales.copy()

        if not coverage.empty:
            result = result.merge(
                coverage[
                    [
                        "product_id",
                        "estimated_days_left",
                        "coverage_status",
                    ]
                ],
                on="product_id",
                how="left",
            )

        if not turnover.empty:
            result = result.merge(
                turnover[
                    [
                        "product_id",
                        "turnover",
                        "turnover_class",
                    ]
                ],
                on="product_id",
                how="left",
            )

        # Средние продажи в день.
        result["average_daily_sales"] = np.where(
            result["units_sold"] > 0,
            result["units_sold"] / 365,
            0,
        )

        # Примерный reorder point.
        result["estimated_reorder_point"] = (
            result["average_daily_sales"]
            * 14
        )

        result["reorder_required"] = (
            result["stock_quantity"]
            <= result["estimated_reorder_point"]
        )

        return result

    # ============================================================
    # DASHBOARD
    # ============================================================

    def get_dashboard_data(
        self,
        year=None
    ):
        """
        Основной набор данных для dashboard.
        """

        summary = self.get_inventory_summary()

        stock = self.get_stock_by_product()

        low_stock = self.get_low_stock_products()

        abc = self.get_abc_stock_summary()

        warehouses = self.get_warehouse_load()

        turnover = self.get_inventory_turnover(
            year
        )

        risk = self.get_inventory_risk_dataset(
            year
        )

        return {
            "summary": summary,
            "stock": stock,
            "low_stock": low_stock,
            "abc": abc,
            "warehouses": warehouses,
            "turnover": turnover,
            "risk": risk,
        }

    # ============================================================
    # DATA QUALITY
    # ============================================================

    def validate_inventory_data(self):
        """
        Базовая проверка качества складских данных.
        """

        checks = {}

        checks["negative_stock"] = (
            self._fetch_scalar(
                """
                SELECT COUNT(*)
                FROM inventory
                WHERE quantity < 0
                """
            )
        )

        checks["missing_products"] = (
            self._fetch_scalar(
                """
                SELECT COUNT(*)
                FROM inventory i
                LEFT JOIN products p
                    ON p.product_id =
                       i.product_id
                WHERE p.product_id IS NULL
                """
            )
        )

        checks["missing_warehouses"] = (
            self._fetch_scalar(
                """
                SELECT COUNT(*)
                FROM inventory i
                LEFT JOIN warehouses w
                    ON w.warehouse_id =
                       i.warehouse_id
                WHERE w.warehouse_id IS NULL
                """
            )
        )

        checks["duplicate_product_warehouse"] = (
            self._fetch_scalar(
                """
                SELECT COUNT(*)
                FROM (
                    SELECT
                        product_id,
                        warehouse_id,
                        COUNT(*) AS cnt
                    FROM inventory
                    GROUP BY
                        product_id,
                        warehouse_id
                    HAVING COUNT(*) > 1
                ) duplicates
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