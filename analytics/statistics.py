import numpy as np
import pandas as pd


class RFMAnalysis:
    """
    RFM-анализ клиентов.

    RFM состоит из:

        R — Recency
            сколько времени прошло с последней покупки.

        F — Frequency
            как часто клиент покупает.

        M — Monetary
            сколько денег клиент потратил.

    Класс не работает с БД напрямую.
    На вход получает pandas.DataFrame.

    Основные возможности:

        - расчет R/F/M;
        - RFM scoring 1-5;
        - RFM score;
        - сегментация клиентов;
        - сводка сегментов;
        - доля выручки сегментов;
        - поиск лучших клиентов;
        - поиск клиентов под риском;
        - сравнение сегментов;
        - расчет потенциально потерянной выручки.
    """

    def __init__(
        self,
        data: pd.DataFrame,
        customer_column: str = "customer_id",
        recency_column: str = "recency",
        frequency_column: str = "frequency",
        monetary_column: str = "monetary",
        current_date=None,
        quantiles: int = 5,
    ):
        self.data = data.copy()

        self.customer_column = customer_column
        self.recency_column = recency_column
        self.frequency_column = frequency_column
        self.monetary_column = monetary_column

        self.current_date = (
            pd.Timestamp(current_date)
            if current_date is not None
            else pd.Timestamp.today().normalize()
        )

        self.quantiles = quantiles

        self._validate()

    # ============================================================
    # VALIDATION
    # ============================================================

    def _validate(self):
        """Проверка входного DataFrame."""

        if not isinstance(
            self.data,
            pd.DataFrame
        ):
            raise TypeError(
                "data должен быть pandas.DataFrame"
            )

        required_columns = [
            self.customer_column,
            self.recency_column,
            self.frequency_column,
            self.monetary_column,
        ]

        missing_columns = [
            column
            for column in required_columns
            if column not in self.data.columns
        ]

        if missing_columns:
            raise ValueError(
                f"Отсутствуют колонки: {missing_columns}"
            )

        if self.quantiles < 2:
            raise ValueError(
                "quantiles должен быть >= 2"
            )

    # ============================================================
    # PREPARATION
    # ============================================================

    def prepare_data(self):
        """
        Подготовить исходные данные.

        Удаляются строки без customer_id.
        R/F/M приводятся к числовому типу.
        """

        df = self.data.copy()

        numeric_columns = [
            self.recency_column,
            self.frequency_column,
            self.monetary_column,
        ]

        for column in numeric_columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

        df = df.dropna(
            subset=[
                self.customer_column,
                *numeric_columns,
            ]
        )

        # Recency не может быть отрицательным.
        df = df[
            df[self.recency_column] >= 0
        ]

        # Frequency не может быть отрицательной.
        df = df[
            df[self.frequency_column] >= 0
        ]

        return df

    # ============================================================
    # RFM CALCULATION
    # ============================================================

    def calculate(self):
        """
        Выполнить полный RFM-анализ.

        Возвращает DataFrame:

            customer_id
            recency
            frequency
            monetary

            r_score
            f_score
            m_score

            rfm_score
            rfm_code
            segment
        """

        df = self.prepare_data()

        if df.empty:
            return pd.DataFrame(
                columns=[
                    self.customer_column,
                    self.recency_column,
                    self.frequency_column,
                    self.monetary_column,
                    "r_score",
                    "f_score",
                    "m_score",
                    "rfm_score",
                    "rfm_code",
                    "segment",
                ]
            )

        # Если один клиент встречается несколько раз,
        # приводим его к одной строке.
        df = (
            df
            .groupby(
                self.customer_column,
                as_index=False
            )
            .agg(
                {
                    self.recency_column: "min",
                    self.frequency_column: "sum",
                    self.monetary_column: "sum",
                }
            )
        )

        # --------------------------------------------------------
        # SCORING
        # --------------------------------------------------------

        df["r_score"] = self._recency_score(
            df[self.recency_column]
        )

        df["f_score"] = self._frequency_score(
            df[self.frequency_column]
        )

        df["m_score"] = self._monetary_score(
            df[self.monetary_column]
        )

        # --------------------------------------------------------
        # TOTAL SCORE
        # --------------------------------------------------------

        df["rfm_score"] = (
            df["r_score"]
            + df["f_score"]
            + df["m_score"]
        )

        # Например:
        #
        # R=5 F=5 M=5
        #
        # код будет 555.
        df["rfm_code"] = (
            df["r_score"].astype(str)
            + df["f_score"].astype(str)
            + df["m_score"].astype(str)
        )

        # --------------------------------------------------------
        # SEGMENTATION
        # --------------------------------------------------------

        df["segment"] = self._assign_segments(
            df
        )

        return df

    # ============================================================
    # RECENCY SCORE
    # ============================================================

    def _recency_score(
        self,
        series: pd.Series
    ):
        """
        Recency scoring.

        Меньше дней с последней покупки
        = лучший score.

        5 — лучший клиент
        1 — худший клиент
        """

        return self._quantile_score(
            series,
            reverse=True
        )

    # ============================================================
    # FREQUENCY SCORE
    # ============================================================

    def _frequency_score(
        self,
        series: pd.Series
    ):
        """
        Frequency scoring.

        Больше покупок
        = лучший score.
        """

        return self._quantile_score(
            series,
            reverse=False
        )

    # ============================================================
    # MONETARY SCORE
    # ============================================================

    def _monetary_score(
        self,
        series: pd.Series
    ):
        """
        Monetary scoring.

        Больше потрачено
        = лучший score.
        """

        return self._quantile_score(
            series,
            reverse=False
        )

    # ============================================================
    # QUANTILE SCORE
    # ============================================================

    def _quantile_score(
        self,
        series: pd.Series,
        reverse: bool = False
    ):
        """
        Универсальное разбиение значения
        на quantiles.

        Используется rank(method="first"),
        чтобы qcut не ломался при большом
        количестве одинаковых значений.
        """

        ranked = series.rank(
            method="first"
        )

        scores = pd.qcut(
            ranked,
            q=self.quantiles,
            labels=False,
            duplicates="drop"
        )

        scores = scores + 1

        if reverse:
            scores = (
                self.quantiles + 1 - scores
            )

        return scores.astype(int)

    # ============================================================
    # SEGMENTATION
    # ============================================================

    def _assign_segments(
        self,
        df: pd.DataFrame
    ):
        """
        Бизнес-сегментация клиентов.

        Основные сегменты:

            Champions
            Loyal Customers
            Potential Loyalists
            New Customers
            Promising
            At Risk
            Can't Lose Them
            Hibernating
            Lost
        """

        r = df["r_score"]
        f = df["f_score"]
        m = df["m_score"]

        conditions = [
            # ----------------------------------------------------
            # CHAMPIONS
            # ----------------------------------------------------
            (
                (r >= 4)
                & (f >= 4)
                & (m >= 4)
            ),

            # ----------------------------------------------------
            # LOYAL CUSTOMERS
            # ----------------------------------------------------
            (
                (r >= 3)
                & (f >= 4)
                & (m >= 3)
            ),

            # ----------------------------------------------------
            # POTENTIAL LOYALISTS
            # ----------------------------------------------------
            (
                (r >= 4)
                & (f >= 2)
                & (f <= 3)
                & (m >= 2)
            ),

            # ----------------------------------------------------
            # NEW CUSTOMERS
            # ----------------------------------------------------
            (
                (r >= 4)
                & (f <= 2)
                & (m <= 3)
            ),

            # ----------------------------------------------------
            # PROMISING
            # ----------------------------------------------------
            (
                (r >= 3)
                & (f >= 2)
                & (m >= 2)
            ),

            # ----------------------------------------------------
            # AT RISK
            # ----------------------------------------------------
            (
                (r <= 2)
                & (f >= 3)
                & (m >= 3)
            ),

            # ----------------------------------------------------
            # CAN'T LOSE THEM
            # ----------------------------------------------------
            (
                (r <= 2)
                & (f >= 4)
                & (m >= 4)
            ),

            # ----------------------------------------------------
            # HIBERNATING
            # ----------------------------------------------------
            (
                (r <= 2)
                & (f <= 2)
                & (m >= 2)
            ),

            # ----------------------------------------------------
            # LOST
            # ----------------------------------------------------
            (
                (r <= 2)
                & (f <= 2)
                & (m <= 2)
            ),
        ]

        choices = [
            "champions",
            "loyal_customers",
            "potential_loyalists",
            "new_customers",
            "promising",
            "at_risk",
            "cant_lose_them",
            "hibernating",
            "lost",
        ]

        return np.select(
            conditions,
            choices,
            default="other"
        )

    # ============================================================
    # SEGMENT SUMMARY
    # ============================================================

    def segment_summary(self):
        """
        Сводка по сегментам.

        Показывает:

            количество клиентов;
            выручку;
            среднюю выручку;
            средний R;
            средний F;
            средний M;
            долю клиентов;
            долю выручки.
        """

        df = self.calculate()

        if df.empty:
            return pd.DataFrame(
                columns=[
                    "segment",
                    "customers_count",
                    "revenue",
                    "average_revenue",
                    "average_recency",
                    "average_frequency",
                    "average_monetary",
                    "customer_share_percent",
                    "revenue_share_percent",
                ]
            )

        summary = (
            df
            .groupby(
                "segment",
                as_index=False
            )
            .agg(
                customers_count=(
                    self.customer_column,
                    "count"
                ),
                revenue=(
                    self.monetary_column,
                    "sum"
                ),
                average_revenue=(
                    self.monetary_column,
                    "mean"
                ),
                average_recency=(
                    self.recency_column,
                    "mean"
                ),
                average_frequency=(
                    self.frequency_column,
                    "mean"
                ),
                average_monetary=(
                    self.monetary_column,
                    "mean"
                ),
            )
        )

        total_customers = (
            summary["customers_count"]
            .sum()
        )

        total_revenue = (
            summary["revenue"]
            .sum()
        )

        summary["customer_share_percent"] = np.where(
            total_customers != 0,
            summary["customers_count"]
            / total_customers
            * 100,
            0,
        )

        summary["revenue_share_percent"] = np.where(
            total_revenue != 0,
            summary["revenue"]
            / total_revenue
            * 100,
            0,
        )

        return summary.sort_values(
            "revenue",
            ascending=False
        ).reset_index(
            drop=True
        )

    # ============================================================
    # TOP CUSTOMERS
    # ============================================================

    def top_customers(
        self,
        n: int = 10
    ):
        """N лучших клиентов по RFM score."""

        if n <= 0:
            raise ValueError(
                "n должен быть больше 0"
            )

        df = self.calculate()

        return (
            df
            .sort_values(
                [
                    "rfm_score",
                    self.monetary_column,
                ],
                ascending=[
                    False,
                    False,
                ]
            )
            .head(n)
            .reset_index(drop=True)
        )

    # ============================================================
    # BEST MONETARY CUSTOMERS
    # ============================================================

    def top_customers_by_revenue(
        self,
        n: int = 10
    ):
        """N клиентов с максимальными расходами."""

        if n <= 0:
            raise ValueError(
                "n должен быть больше 0"
            )

        df = self.calculate()

        return (
            df
            .sort_values(
                self.monetary_column,
                ascending=False
            )
            .head(n)
            .reset_index(drop=True)
        )

    # ============================================================
    # BEST FREQUENCY
    # ============================================================

    def top_customers_by_frequency(
        self,
        n: int = 10
    ):
        """N клиентов с максимальным количеством покупок."""

        if n <= 0:
            raise ValueError(
                "n должен быть больше 0"
            )

        df = self.calculate()

        return (
            df
            .sort_values(
                self.frequency_column,
                ascending=False
            )
            .head(n)
            .reset_index(drop=True)
        )

    # ============================================================
    # BEST RECENCY
    # ============================================================

    def most_recent_customers(
        self,
        n: int = 10
    ):
        """N клиентов с самой свежей покупкой."""

        if n <= 0:
            raise ValueError(
                "n должен быть больше 0"
            )

        df = self.calculate()

        return (
            df
            .sort_values(
                self.recency_column,
                ascending=True
            )
            .head(n)
            .reset_index(drop=True)
        )

    # ============================================================
    # AT RISK
    # ============================================================

    def get_at_risk_customers(self):
        """Клиенты, находящиеся под риском."""

        df = self.calculate()

        return (
            df[
                df["segment"].isin(
                    [
                        "at_risk",
                        "cant_lose_them",
                    ]
                )
            ]
            .sort_values(
                "monetary",
                ascending=False
            )
            .reset_index(drop=True)
        )

    # ============================================================
    # LOST
    # ============================================================

    def get_lost_customers(self):
        """Потерянные клиенты."""

        df = self.calculate()

        return (
            df[
                df["segment"] == "lost"
            ]
            .sort_values(
                self.monetary_column,
                ascending=False
            )
            .reset_index(drop=True)
        )

    # ============================================================
    # LOYAL
    # ============================================================

    def get_loyal_customers(self):
        """Лояльные клиенты."""

        df = self.calculate()

        return (
            df[
                df["segment"].isin(
                    [
                        "champions",
                        "loyal_customers",
                    ]
                )
            ]
            .sort_values(
                self.monetary_column,
                ascending=False
            )
            .reset_index(drop=True)
        )

    # ============================================================
    # REVENUE AT RISK
    # ============================================================

    def revenue_at_risk(self):
        """
        Оценка выручки клиентов,
        находящихся под риском.

        Это не прогноз потерь,
        а текущая историческая стоимость
        клиентов из risky-сегментов.
        """

        df = self.get_at_risk_customers()

        if df.empty:
            return {
                "customers_count": 0,
                "revenue_at_risk": 0,
                "revenue_share_percent": 0,
            }

        all_customers = self.calculate()

        total_revenue = (
            all_customers[
                self.monetary_column
            ].sum()
        )

        risk_revenue = (
            df[
                self.monetary_column
            ].sum()
        )

        revenue_share = (
            risk_revenue
            / total_revenue
            * 100
            if total_revenue != 0
            else 0
        )

        return {
            "customers_count": len(df),
            "revenue_at_risk": risk_revenue,
            "revenue_share_percent": revenue_share,
        }

    # ============================================================
    # CUSTOMER SCORE
    # ============================================================

    def calculate_customer_score(
        self,
        recency_weight: float = 0.30,
        frequency_weight: float = 0.30,
        monetary_weight: float = 0.40,
    ):
        """
        Рассчитать взвешенный клиентский score.

        По умолчанию:

            R = 30%
            F = 30%
            M = 40%

        В отличие от простого RFM score,
        здесь можно задать собственные веса.
        """

        weights_sum = (
            recency_weight
            + frequency_weight
            + monetary_weight
        )

        if not np.isclose(
            weights_sum,
            1.0
        ):
            raise ValueError(
                "Сумма весов должна быть равна 1"
            )

        df = self.calculate()

        if df.empty:
            return df

        df["customer_score"] = (
            df["r_score"]
            / self.quantiles
            * recency_weight
            +

            df["f_score"]
            / self.quantiles
            * frequency_weight
            +

            df["m_score"]
            / self.quantiles
            * monetary_weight
        ) * 100

        df["score_class"] = np.select(
            [
                df["customer_score"] >= 80,
                df["customer_score"] >= 60,
                df["customer_score"] >= 40,
                df["customer_score"] < 40,
            ],
            [
                "excellent",
                "good",
                "average",
                "poor",
            ],
            default="unknown",
        )

        return df.sort_values(
            "customer_score",
            ascending=False
        ).reset_index(
            drop=True
        )

    # ============================================================
    # SEGMENT COUNTS
    # ============================================================

    def segment_distribution(self):
        """Распределение клиентов по сегментам."""

        df = self.calculate()

        if df.empty:
            return pd.DataFrame(
                columns=[
                    "segment",
                    "customers_count",
                    "share_percent",
                ]
            )

        distribution = (
            df
            .groupby(
                "segment",
                as_index=False
            )
            .size()
            .rename(
                columns={
                    "size": "customers_count"
                }
            )
        )

        total = (
            distribution["customers_count"]
            .sum()
        )

        distribution["share_percent"] = np.where(
            total != 0,
            distribution["customers_count"]
            / total
            * 100,
            0,
        )

        return distribution.sort_values(
            "customers_count",
            ascending=False
        ).reset_index(
            drop=True
        )

    # ============================================================
    # RFM MATRIX
    # ============================================================

    def rfm_matrix(self):
        """
        Матрица R × F.

        Показывает количество клиентов
        для каждой комбинации R и F.
        """

        df = self.calculate()

        if df.empty:
            return pd.DataFrame()

        matrix = pd.pivot_table(
            df,
            index="r_score",
            columns="f_score",
            values=self.customer_column,
            aggfunc="count",
            fill_value=0,
        )

        return matrix.sort_index(
            ascending=False
        )

    # ============================================================
    # MONETARY DISTRIBUTION
    # ============================================================

    def monetary_statistics(self):
        """Статистика денежного вклада клиентов."""

        df = self.calculate()

        if df.empty:
            return {}

        monetary = df[
            self.monetary_column
        ]

        return {
            "mean": monetary.mean(),
            "median": monetary.median(),
            "std": monetary.std(),
            "min": monetary.min(),
            "max": monetary.max(),
            "q25": monetary.quantile(0.25),
            "q75": monetary.quantile(0.75),
        }

    # ============================================================
    # RECENCY DISTRIBUTION
    # ============================================================

    def recency_statistics(self):
        """Статистика давности покупок."""

        df = self.calculate()

        if df.empty:
            return {}

        recency = df[
            self.recency_column
        ]

        return {
            "mean": recency.mean(),
            "median": recency.median(),
            "std": recency.std(),
            "min": recency.min(),
            "max": recency.max(),
            "q25": recency.quantile(0.25),
            "q75": recency.quantile(0.75),
        }

    # ============================================================
    # FREQUENCY DISTRIBUTION
    # ============================================================

    def frequency_statistics(self):
        """Статистика частоты покупок."""

        df = self.calculate()

        if df.empty:
            return {}

        frequency = df[
            self.frequency_column
        ]

        return {
            "mean": frequency.mean(),
            "median": frequency.median(),
            "std": frequency.std(),
            "min": frequency.min(),
            "max": frequency.max(),
            "q25": frequency.quantile(0.25),
            "q75": frequency.quantile(0.75),
        }

    # ============================================================
    # CUSTOM SEGMENTS
    # ============================================================

    def filter_segment(
        self,
        segment: str
    ):
        """Получить клиентов определенного сегмента."""

        df = self.calculate()

        return (
            df[
                df["segment"] == segment
            ]
            .reset_index(drop=True)
        )

    # ============================================================
    # COMPARISON
    # ============================================================

    def compare_segments(
        self,
        segment_a: str,
        segment_b: str
    ):
        """
        Сравнить два сегмента.

        Возвращает таблицу
        со средними показателями.
        """

        df = self.calculate()

        selected = df[
            df["segment"].isin(
                [
                    segment_a,
                    segment_b,
                ]
            )
        ]

        if selected.empty:
            return pd.DataFrame()

        comparison = (
            selected
            .groupby(
                "segment",
                as_index=False
            )
            .agg(
                customers_count=(
                    self.customer_column,
                    "count"
                ),
                average_recency=(
                    self.recency_column,
                    "mean"
                ),
                average_frequency=(
                    self.frequency_column,
                    "mean"
                ),
                average_monetary=(
                    self.monetary_column,
                    "mean"
                ),
                total_revenue=(
                    self.monetary_column,
                    "sum"
                ),
            )
        )

        return comparison

    # ============================================================
    # DASHBOARD
    # ============================================================

    def dashboard_data(self):
        """
        Все основные данные для customer dashboard.
        """

        rfm = self.calculate()

        return {
            "rfm": rfm,
            "segment_summary": self.segment_summary(),
            "segment_distribution": (
                self.segment_distribution()
            ),
            "top_customers": (
                self.top_customers(10)
            ),
            "top_by_revenue": (
                self.top_customers_by_revenue(10)
            ),
            "at_risk": (
                self.get_at_risk_customers()
            ),
            "lost": (
                self.get_lost_customers()
            ),
            "loyal": (
                self.get_loyal_customers()
            ),
            "revenue_at_risk": (
                self.revenue_at_risk()
            ),
            "rfm_matrix": (
                self.rfm_matrix()
            ),
            "monetary_statistics": (
                self.monetary_statistics()
            ),
            "recency_statistics": (
                self.recency_statistics()
            ),
            "frequency_statistics": (
                self.frequency_statistics()
            ),
        }

    # ============================================================
    # FACTORY
    # ============================================================

    @classmethod
    def from_customer_service(
        cls,
        df: pd.DataFrame
    ):
        """
        Создать RFMAnalysis из DataFrame,
        который возвращает CustomerService.

        Ожидаемые колонки:

            customer_id
            recency
            frequency
            monetary
        """

        return cls(
            data=df,
            customer_column="customer_id",
            recency_column="recency",
            frequency_column="frequency",
            monetary_column="monetary",
        )