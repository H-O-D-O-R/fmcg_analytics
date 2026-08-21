import numpy as np
import pandas as pd


class ABCAnalysis:
    """
    ABC-анализ товаров.

    Класс работает с DataFrame и не зависит от БД.

    ABC-анализ позволяет разделить товары по их
    вкладу в общий показатель:

        A — товары, формирующие основную долю результата;
        B — товары со средним вкладом;
        C — товары с небольшим вкладом.

    По умолчанию используется классическая схема:

        A <= 80%
        B <= 95%
        C > 95%

    Класс можно использовать для:
        - выручки;
        - прибыли;
        - стоимости запасов;
        - количества продаж;
        - других числовых показателей.
    """

    def __init__(
        self,
        data: pd.DataFrame,
        value_column: str,
        item_column: str = "name",
        a_limit: float = 0.80,
        b_limit: float = 0.95,
    ):
        self.data = data.copy()
        self.value_column = value_column
        self.item_column = item_column

        self.a_limit = a_limit
        self.b_limit = b_limit

        self._validate()

    # ============================================================
    # VALIDATION
    # ============================================================

    def _validate(self):
        """Проверить корректность входных данных."""

        if not isinstance(self.data, pd.DataFrame):
            raise TypeError(
                "data должен быть pandas.DataFrame"
            )

        required_columns = [
            self.item_column,
            self.value_column,
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

        if not (
            0 < self.a_limit < self.b_limit <= 1
        ):
            raise ValueError(
                "Должно выполняться: "
                "0 < a_limit < b_limit <= 1"
            )

    # ============================================================
    # PREPARATION
    # ============================================================

    def prepare_data(self):
        """
        Подготовить данные к ABC-анализу.

        Удаляются:
        - NaN;
        - отрицательные значения.

        Показатель приводится к числовому типу.
        """

        df = self.data.copy()

        df[self.value_column] = pd.to_numeric(
            df[self.value_column],
            errors="coerce",
        )

        df = df.dropna(
            subset=[
                self.item_column,
                self.value_column,
            ]
        )

        df = df[
            df[self.value_column] >= 0
        ].copy()

        return df

    # ============================================================
    # MAIN ANALYSIS
    # ============================================================

    def calculate(self):
        """
        Выполнить полный ABC-анализ.

        Возвращает DataFrame с:

            value
            value_share
            cumulative_share
            abc_class
            rank
        """

        df = self.prepare_data()

        if df.empty:
            return pd.DataFrame(
                columns=[
                    self.item_column,
                    "value",
                    "value_share",
                    "cumulative_share",
                    "abc_class",
                    "rank",
                ]
            )

        # Если один товар встречается несколько раз,
        # объединяем его значения.
        df = (
            df
            .groupby(
                self.item_column,
                as_index=False
            )[self.value_column]
            .sum()
        )

        df = df.rename(
            columns={
                self.value_column: "value"
            }
        )

        # Сортировка от самого значимого товара
        # к самому незначительному.
        df = df.sort_values(
            "value",
            ascending=False
        ).reset_index(drop=True)

        total_value = df["value"].sum()

        if total_value == 0:
            df["value_share"] = 0.0
            df["cumulative_share"] = 0.0
        else:
            df["value_share"] = (
                df["value"]
                / total_value
            )

            df["cumulative_share"] = (
                df["value_share"]
                .cumsum()
            )

        # --------------------------------------------------------
        # ABC CLASS
        # --------------------------------------------------------

        df["abc_class"] = np.select(
            [
                df["cumulative_share"]
                <= self.a_limit,

                df["cumulative_share"]
                <= self.b_limit,
            ],
            [
                "A",
                "B",
            ],
            default="C",
        )

        # Первый товар, который пересекает
        # границу A, логически должен остаться A.
        #
        # Например:
        # 70%
        # 20% -> cumulative 90%
        #
        # Второй товар всё равно относится
        # к A, потому что именно он пересек
        # границу 80%.

        df = self._fix_boundary_classes(df)

        df["rank"] = np.arange(
            1,
            len(df) + 1
        )

        df["value_share_percent"] = (
            df["value_share"] * 100
        )

        df["cumulative_share_percent"] = (
            df["cumulative_share"] * 100
        )

        return df

    # ============================================================
    # BOUNDARY CORRECTION
    # ============================================================

    def _fix_boundary_classes(
        self,
        df: pd.DataFrame
    ):
        """
        Исправить пограничные товары.

        Если товар пересек границу 80%,
        он всё равно относится к A,
        потому что именно он сформировал
        переход через порог.

        Аналогично для B.
        """

        if df.empty:
            return df

        classes = []

        previous_share = 0.0

        for cumulative_share in (
            df["cumulative_share"]
        ):
            if previous_share < self.a_limit:
                classes.append("A")

            elif previous_share < self.b_limit:
                classes.append("B")

            else:
                classes.append("C")

            previous_share = cumulative_share

        df = df.copy()
        df["abc_class"] = classes

        return df

    # ============================================================
    # SUMMARY
    # ============================================================

    def summary(self):
        """
        Сводка ABC-классов.

        Возвращает:

            class
            products_count
            total_value
            value_share_percent
            average_value
        """

        df = self.calculate()

        if df.empty:
            return pd.DataFrame(
                columns=[
                    "abc_class",
                    "products_count",
                    "total_value",
                    "value_share_percent",
                    "average_value",
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
                    self.item_column,
                    "count"
                ),
                total_value=(
                    "value",
                    "sum"
                ),
                average_value=(
                    "value",
                    "mean"
                ),
            )
        )

        total_value = summary[
            "total_value"
        ].sum()

        summary["value_share_percent"] = np.where(
            total_value != 0,
            summary["total_value"]
            / total_value
            * 100,
            0,
        )

        return summary

    # ============================================================
    # CLASS A
    # ============================================================

    def get_class_a(self):
        """Получить только товары класса A."""

        df = self.calculate()

        return df[
            df["abc_class"] == "A"
        ].reset_index(drop=True)

    # ============================================================
    # CLASS B
    # ============================================================

    def get_class_b(self):
        """Получить только товары класса B."""

        df = self.calculate()

        return df[
            df["abc_class"] == "B"
        ].reset_index(drop=True)

    # ============================================================
    # CLASS C
    # ============================================================

    def get_class_c(self):
        """Получить только товары класса C."""

        df = self.calculate()

        return df[
            df["abc_class"] == "C"
        ].reset_index(drop=True)

    # ============================================================
    # TOP PRODUCTS
    # ============================================================

    def top_products(
        self,
        n: int = 10
    ):
        """Получить N наиболее значимых товаров."""

        if n <= 0:
            raise ValueError(
                "n должен быть больше 0"
            )

        df = self.calculate()

        return df.head(n).reset_index(
            drop=True
        )

    # ============================================================
    # BOTTOM PRODUCTS
    # ============================================================

    def bottom_products(
        self,
        n: int = 10
    ):
        """Получить N наименее значимых товаров."""

        if n <= 0:
            raise ValueError(
                "n должен быть больше 0"
            )

        df = self.calculate()

        return df.tail(n).sort_values(
            "value",
            ascending=True
        ).reset_index(
            drop=True
        )

    # ============================================================
    # PARETO ANALYSIS
    # ============================================================

    def pareto_point(self):
        """
        Найти минимальное количество товаров,
        формирующих заданную долю результата.

        Например:

            80% выручки формируют 23% товаров.
        """

        df = self.calculate()

        if df.empty:
            return {
                "items_count": 0,
                "total_items": 0,
                "items_percent": 0,
                "target_percent": self.a_limit * 100,
            }

        mask = (
            df["cumulative_share"]
            >= self.a_limit
        )

        if not mask.any():
            items_count = len(df)
        else:
            items_count = (
                mask.idxmax() + 1
            )

        total_items = len(df)

        items_percent = (
            items_count
            / total_items
            * 100
        )

        return {
            "items_count": items_count,
            "total_items": total_items,
            "items_percent": items_percent,
            "target_percent": self.a_limit * 100,
        }

    # ============================================================
    # CLASS DISTRIBUTION
    # ============================================================

    def class_distribution(self):
        """
        Распределение количества товаров
        по ABC-классам.
        """

        df = self.calculate()

        if df.empty:
            return pd.DataFrame(
                columns=[
                    "abc_class",
                    "products_count",
                    "products_share_percent",
                ]
            )

        distribution = (
            df
            .groupby(
                "abc_class",
                as_index=False
            )
            .size()
            .rename(
                columns={
                    "size": "products_count"
                }
            )
        )

        total_products = (
            distribution["products_count"]
            .sum()
        )

        distribution[
            "products_share_percent"
        ] = np.where(
            total_products != 0,
            distribution["products_count"]
            / total_products
            * 100,
            0,
        )

        return distribution

    # ============================================================
    # CUSTOM THRESHOLDS
    # ============================================================

    def recalculate(
        self,
        a_limit: float,
        b_limit: float
    ):
        """
        Пересчитать ABC с другими порогами.

        Например:

            A = 70%
            B = 90%
            C = 10%
        """

        if not (
            0 < a_limit < b_limit <= 1
        ):
            raise ValueError(
                "Должно выполняться: "
                "0 < a_limit < b_limit <= 1"
            )

        analyzer = ABCAnalysis(
            data=self.data,
            value_column=self.value_column,
            item_column=self.item_column,
            a_limit=a_limit,
            b_limit=b_limit,
        )

        return analyzer.calculate()

    # ============================================================
    # COMPARISON
    # ============================================================

    def compare(
        self,
        other: "ABCAnalysis"
    ):
        """
        Сравнить два ABC-анализа.

        Полезно, например:

            ABC по выручке
            vs
            ABC по прибыли.
        """

        if not isinstance(
            other,
            ABCAnalysis
        ):
            raise TypeError(
                "other должен быть ABCAnalysis"
            )

        first = self.calculate()
        second = other.calculate()

        first = first[
            [
                self.item_column,
                "value",
                "abc_class",
            ]
        ].rename(
            columns={
                "value": "value_first",
                "abc_class": "class_first",
            }
        )

        second = second[
            [
                other.item_column,
                "value",
                "abc_class",
            ]
        ].rename(
            columns={
                other.item_column:
                    self.item_column,
                "value":
                    "value_second",
                "abc_class":
                    "class_second",
            }
        )

        result = first.merge(
            second,
            on=self.item_column,
            how="outer"
        )

        result["class_changed"] = (
            result["class_first"]
            != result["class_second"]
        )

        return result

    # ============================================================
    # FACTORY METHODS
    # ============================================================

    @classmethod
    def from_sales(
        cls,
        df: pd.DataFrame,
        value_column: str = "revenue",
        item_column: str = "name",
    ):
        """
        Удобный запуск ABC для продаж.
        """

        return cls(
            data=df,
            value_column=value_column,
            item_column=item_column,
        )


    @classmethod
    def from_inventory(
        cls,
        df: pd.DataFrame,
        value_column: str = "stock_value",
        item_column: str = "name",
    ):
        """
        Удобный запуск ABC для запасов.
        """

        return cls(
            data=df,
            value_column=value_column,
            item_column=item_column,
        )