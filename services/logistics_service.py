import numpy as np
import pandas as pd

from repositories.logistics_repository import LogisticsRepository


class LogisticsService:
    """
    Service layer для аналитики логистики.

    Repository:
        SQL + получение данных.

    Service:
        pandas + numpy + бизнес-метрики.

    Visualization:
        matplotlib.
    """

    def __init__(self):
        self.repository = LogisticsRepository()

    # ============================================================
    # HELPERS
    # ============================================================

    @staticmethod
    def _to_dataframe(rows, columns):
        return pd.DataFrame(rows, columns=columns)

    @staticmethod
    def _numeric(df, columns):
        for column in columns:
            if column in df.columns:
                df[column] = pd.to_numeric(
                    df[column],
                    errors="coerce",
                )

        return df

    # ============================================================
    # BASIC METRICS
    # ============================================================

    def get_total_shipments(self, year=None):
        row = self.repository.total_shipments(year)

        if row is None:
            return 0

        return int(row[0] or 0)

    def get_total_distance(self, year=None):
        row = self.repository.total_distance(year)

        if row is None:
            return 0.0

        return float(row[0] or 0)

    def get_average_distance(self, year=None):
        row = self.repository.average_distance(year)

        if row is None:
            return 0.0

        return float(row[0] or 0)

    def get_average_delivery_time(self, year=None):
        row = self.repository.average_delivery_time(year)

        if row is None:
            return 0.0

        return float(row[0] or 0)

    def get_delay_rate(
        self,
        expected_days=7,
        year=None,
    ):
        row = self.repository.delay_rate(
            expected_days=expected_days,
            year=year,
        )

        if row is None:
            return {
                "total_shipments": 0,
                "delayed_shipments": 0,
                "delay_rate_percent": 0.0,
            }

        return {
            "total_shipments": int(row[0] or 0),
            "delayed_shipments": int(row[1] or 0),
            "delay_rate_percent": float(row[2] or 0),
        }

    # ============================================================
    # LOGISTICS SUMMARY
    # ============================================================

    def get_logistics_summary(self, year=None):
        shipments = self.get_total_shipments(year)
        distance = self.get_total_distance(year)
        average_distance = self.get_average_distance(year)
        average_delivery = self.get_average_delivery_time(year)

        delay = self.get_delay_rate(year=year)

        return {
            "shipments": shipments,
            "total_distance": distance,
            "average_distance": average_distance,
            "average_delivery_days": average_delivery,
            "delayed_shipments": delay[
                "delayed_shipments"
            ],
            "delay_rate_percent": delay[
                "delay_rate_percent"
            ],
        }

    # ============================================================
    # SHIPMENT ANALYSIS
    # ============================================================

    def get_delivery_time_by_shipment(
        self,
        year=None,
    ):
        rows = self.repository.delivery_time_by_shipment(
            year
        )

        df = self._to_dataframe(
            rows,
            [
                "shipment_id",
                "order_id",
                "warehouse_id",
                "vehicle_id",
                "driver_id",
                "departure_date",
                "arrival_date",
                "distance",
                "delivery_days",
            ],
        )

        if df.empty:
            return df

        df["departure_date"] = pd.to_datetime(
            df["departure_date"],
            errors="coerce",
        )

        df["arrival_date"] = pd.to_datetime(
            df["arrival_date"],
            errors="coerce",
        )

        df = self._numeric(
            df,
            [
                "distance",
                "delivery_days",
            ],
        )

        df["speed_per_day"] = np.where(
            df["delivery_days"] > 0,
            df["distance"] / df["delivery_days"],
            np.nan,
        )

        return df

    # ============================================================
    # DELAYS
    # ============================================================

    def get_delayed_shipments(
        self,
        expected_days=7,
        year=None,
    ):
        rows = self.repository.delayed_shipments(
            expected_days=expected_days,
            year=year,
        )

        df = self._to_dataframe(
            rows,
            [
                "shipment_id",
                "order_id",
                "warehouse_id",
                "vehicle_id",
                "driver_id",
                "departure_date",
                "arrival_date",
                "distance",
                "delivery_days",
                "delay_days",
            ],
        )

        if df.empty:
            return df

        df["departure_date"] = pd.to_datetime(
            df["departure_date"],
            errors="coerce",
        )

        df["arrival_date"] = pd.to_datetime(
            df["arrival_date"],
            errors="coerce",
        )

        df = self._numeric(
            df,
            [
                "distance",
                "delivery_days",
                "delay_days",
            ],
        )

        df["delay_level"] = np.select(
            [
                df["delay_days"] <= 2,
                df["delay_days"] <= 5,
                df["delay_days"] > 5,
            ],
            [
                "minor",
                "moderate",
                "critical",
            ],
            default="unknown",
        )

        return df

    # ============================================================
    # MONTHLY ANALYSIS
    # ============================================================

    def get_monthly_logistics(
        self,
        year=None,
    ):
        rows = self.repository.monthly_logistics(
            year
        )

        df = self._to_dataframe(
            rows,
            [
                "year",
                "month",
                "shipments_count",
                "total_distance",
                "average_distance",
                "average_delivery_days",
            ],
        )

        if df.empty:
            return df

        df = self._numeric(
            df,
            [
                "year",
                "month",
                "shipments_count",
                "total_distance",
                "average_distance",
                "average_delivery_days",
            ],
        )

        df["year"] = df["year"].astype(int)
        df["month"] = df["month"].astype(int)

        df["date"] = pd.to_datetime(
            dict(
                year=df["year"],
                month=df["month"],
                day=1,
            )
        )

        df["distance_growth_percent"] = (
            df["total_distance"]
            .pct_change()
            .mul(100)
        )

        df["shipment_growth_percent"] = (
            df["shipments_count"]
            .pct_change()
            .mul(100)
        )

        df["delivery_time_change"] = (
            df["average_delivery_days"]
            .diff()
        )

        return df

    def get_monthly_delivery_time(
        self,
        year=None,
    ):
        rows = self.repository.monthly_delivery_time(
            year
        )

        df = self._to_dataframe(
            rows,
            [
                "year",
                "month",
                "shipments_count",
                "average_delivery_days",
            ],
        )

        if df.empty:
            return df

        df = self._numeric(
            df,
            [
                "year",
                "month",
                "shipments_count",
                "average_delivery_days",
            ],
        )

        df["year"] = df["year"].astype(int)
        df["month"] = df["month"].astype(int)

        df["date"] = pd.to_datetime(
            dict(
                year=df["year"],
                month=df["month"],
                day=1,
            )
        )

        df["delivery_time_change"] = (
            df["average_delivery_days"]
            .diff()
        )

        df["delivery_time_growth_percent"] = (
            df["average_delivery_days"]
            .pct_change()
            .mul(100)
        )

        return df

    # ============================================================
    # DISTANCE ANALYSIS
    # ============================================================

    def get_distance_distribution(self):
        rows = self.repository.distance_distribution()

        df = self._to_dataframe(
            rows,
            [
                "distance_group",
                "shipments_count",
                "average_distance",
            ],
        )

        if df.empty:
            return df

        return self._numeric(
            df,
            [
                "shipments_count",
                "average_distance",
            ],
        )

    def get_monthly_distance_growth(self):
        rows = self.repository.monthly_distance_growth()

        df = self._to_dataframe(
            rows,
            [
                "month",
                "total_distance",
                "shipments_count",
                "previous_distance",
                "growth_percent",
            ],
        )

        if df.empty:
            return df

        df["month"] = pd.to_datetime(
            df["month"],
            errors="coerce",
        )

        return self._numeric(
            df,
            [
                "total_distance",
                "shipments_count",
                "previous_distance",
                "growth_percent",
            ],
        )

    # ============================================================
    # WAREHOUSES
    # ============================================================

    def get_warehouse_performance(
        self,
        year=None,
    ):
        rows = self.repository.warehouse_performance(
            year
        )

        df = self._to_dataframe(
            rows,
            [
                "warehouse_id",
                "warehouse",
                "shipments_count",
                "total_distance",
                "average_distance",
                "average_delivery_days",
            ],
        )

        if df.empty:
            return df

        return self._numeric(
            df,
            [
                "shipments_count",
                "total_distance",
                "average_distance",
                "average_delivery_days",
            ],
        )

    def get_top_warehouses(
        self,
        limit=10,
        year=None,
    ):
        rows = self.repository.top_warehouses_by_shipments(
            limit=limit,
            year=year,
        )

        return self._to_dataframe(
            rows,
            [
                "warehouse_id",
                "warehouse",
                "shipments_count",
                "total_distance",
            ],
        )

    def get_warehouse_ranking(
        self,
        year=None,
    ):
        rows = self.repository.warehouse_distance_ranking(
            year
        )

        df = self._to_dataframe(
            rows,
            [
                "warehouse_id",
                "warehouse",
                "shipments_count",
                "total_distance",
                "average_distance",
                "distance_rank",
                "volume_rank",
            ],
        )

        if df.empty:
            return df

        df = self._numeric(
            df,
            [
                "shipments_count",
                "total_distance",
                "average_distance",
                "distance_rank",
                "volume_rank",
            ],
        )

        df["overall_rank"] = (
            df["distance_rank"]
            + df["volume_rank"]
        )

        return df.sort_values(
            "overall_rank"
        ).reset_index(drop=True)

    # ============================================================
    # VEHICLES
    # ============================================================

    def get_vehicle_performance(
        self,
        year=None,
    ):
        rows = self.repository.vehicle_performance(
            year
        )

        df = self._to_dataframe(
            rows,
            [
                "vehicle_id",
                "shipments_count",
                "total_distance",
                "average_distance",
                "average_delivery_days",
            ],
        )

        if df.empty:
            return df

        return self._numeric(
            df,
            [
                "shipments_count",
                "total_distance",
                "average_distance",
                "average_delivery_days",
            ],
        )

    def get_top_vehicles(
        self,
        limit=10,
        year=None,
    ):
        rows = self.repository.top_vehicles_by_distance(
            limit=limit,
            year=year,
        )

        df = self._to_dataframe(
            rows,
            [
                "vehicle_id",
                "shipments_count",
                "total_distance",
                "average_distance",
            ],
        )

        return self._numeric(
            df,
            [
                "shipments_count",
                "total_distance",
                "average_distance",
            ],
        )

    def get_vehicle_ranking(
        self,
        year=None,
    ):
        rows = self.repository.vehicle_utilization_ranking(
            year
        )

        df = self._to_dataframe(
            rows,
            [
                "vehicle_id",
                "shipments_count",
                "total_distance",
                "average_distance",
                "volume_rank",
                "distance_rank",
            ],
        )

        if df.empty:
            return df

        df = self._numeric(
            df,
            [
                "shipments_count",
                "total_distance",
                "average_distance",
                "volume_rank",
                "distance_rank",
            ],
        )

        df["overall_rank"] = (
            df["volume_rank"]
            + df["distance_rank"]
        )

        return df.sort_values(
            "overall_rank"
        ).reset_index(drop=True)

    # ============================================================
    # DRIVERS
    # ============================================================

    def get_driver_performance(
        self,
        year=None,
    ):
        rows = self.repository.driver_performance(
            year
        )

        df = self._to_dataframe(
            rows,
            [
                "driver_id",
                "shipments_count",
                "total_distance",
                "average_distance",
                "average_delivery_days",
            ],
        )

        if df.empty:
            return df

        return self._numeric(
            df,
            [
                "shipments_count",
                "total_distance",
                "average_distance",
                "average_delivery_days",
            ],
        )

    def get_top_drivers(
        self,
        limit=10,
        year=None,
    ):
        rows = self.repository.top_drivers_by_distance(
            limit=limit,
            year=year,
        )

        df = self._to_dataframe(
            rows,
            [
                "driver_id",
                "shipments_count",
                "total_distance",
                "average_delivery_days",
            ],
        )

        return self._numeric(
            df,
            [
                "shipments_count",
                "total_distance",
                "average_delivery_days",
            ],
        )

    # ============================================================
    # ORDER / SHIPMENT ANALYSIS
    # ============================================================

    def get_shipment_order_statistics(
        self,
        year=None,
    ):
        row = self.repository.shipment_order_statistics(
            year
        )

        if row is None:
            return {
                "shipments_count": 0,
                "unique_orders": 0,
                "shipments_per_order": 0.0,
            }

        return {
            "shipments_count": int(row[0] or 0),
            "unique_orders": int(row[1] or 0),
            "shipments_per_order": float(
                row[2] or 0
            ),
        }

    def get_orders_with_multiple_shipments(
        self,
        limit=20,
    ):
        rows = self.repository.orders_with_multiple_shipments(
            limit
        )

        df = self._to_dataframe(
            rows,
            [
                "order_id",
                "shipments_count",
                "total_distance",
                "average_distance",
            ],
        )

        return self._numeric(
            df,
            [
                "shipments_count",
                "total_distance",
                "average_distance",
            ],
        )

    # ============================================================
    # ADVANCED ANALYTICS
    # ============================================================

    def get_logistics_efficiency(
        self,
        year=None,
    ):
        """
        Комплексная оценка эффективности логистики.

        Использует:
        - объем поставок;
        - среднюю дистанцию;
        - среднее время доставки;
        - долю задержек.
        """

        summary = self.get_logistics_summary(
            year
        )

        shipments = summary["shipments"]
        avg_distance = summary["average_distance"]
        avg_delivery = summary[
            "average_delivery_days"
        ]
        delay_rate = summary[
            "delay_rate_percent"
        ]

        if shipments == 0:
            return {
                "score": 0.0,
                "class": "unknown",
            }

        # Скорость.
        speed_score = np.clip(
            100 - avg_delivery * 10,
            0,
            100,
        )

        # Надежность.
        reliability_score = np.clip(
            100 - delay_rate,
            0,
            100,
        )

        # Эффективность дистанции.
        distance_score = np.clip(
            100 - avg_distance / 50,
            0,
            100,
        )

        score = (
            speed_score * 0.45
            + reliability_score * 0.40
            + distance_score * 0.15
        )

        if score >= 80:
            efficiency_class = "excellent"
        elif score >= 60:
            efficiency_class = "good"
        elif score >= 40:
            efficiency_class = "average"
        else:
            efficiency_class = "poor"

        return {
            "score": round(float(score), 2),
            "class": efficiency_class,
            "speed_score": round(
                float(speed_score),
                2,
            ),
            "reliability_score": round(
                float(reliability_score),
                2,
            ),
            "distance_score": round(
                float(distance_score),
                2,
            ),
        }

    # ============================================================
    # DASHBOARD
    # ============================================================

    def get_dashboard_data(
        self,
        year=None,
    ):
        """
        Единый набор данных для dashboard
        и visualization.
        """

        summary = self.get_logistics_summary(
            year
        )

        monthly = self.get_monthly_logistics(
            year
        )

        warehouses = self.get_warehouse_performance(
            year
        )

        vehicles = self.get_vehicle_performance(
            year
        )

        drivers = self.get_driver_performance(
            year
        )

        distance_distribution = (
            self.get_distance_distribution()
        )

        efficiency = self.get_logistics_efficiency(
            year
        )

        return {
            "summary": summary,
            "monthly": monthly,
            "warehouses": warehouses,
            "vehicles": vehicles,
            "drivers": drivers,
            "distance_distribution":
                distance_distribution,
            "efficiency": efficiency,
        }

    # ============================================================
    # DATA QUALITY
    # ============================================================

    def validate_logistics_data(self):
        """
        Проверка качества реальных данных shipments.
        """

        result = {}

        rows = self.repository._fetch_all(
            """
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
                    WHERE arrival_date < departure_date
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
        )

        if not rows:
            return result

        row = rows[0]

        result["negative_distance"] = int(
            row[0] or 0
        )

        result["missing_departure"] = int(
            row[1] or 0
        )

        result["missing_arrival"] = int(
            row[2] or 0
        )

        result["invalid_dates"] = int(
            row[3] or 0
        )

        result["missing_warehouse"] = int(
            row[4] or 0
        )

        result["missing_vehicle"] = int(
            row[5] or 0
        )

        result["missing_driver"] = int(
            row[6] or 0
        )

        return result