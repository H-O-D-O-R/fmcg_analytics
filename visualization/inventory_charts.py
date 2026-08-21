from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


class InventoryCharts:
    """
    Visualization layer для складской аналитики.

    Получает готовые pandas.DataFrame из InventoryService.
    SQL и бизнес-логику здесь не содержит.

    Основные графики:

        - остатки;
        - стоимость запасов;
        - продажи и остатки;
        - оборачиваемость;
        - дни запаса;
        - дефицит;
        - излишки;
        - stockout rate;
        - ABC-анализ;
        - XYZ-анализ;
        - ABC/XYZ матрица;
        - товары с критическими остатками;
        - прогноз потребности;
        - динамика склада;
        - поставщики;
        - складские категории;
        - корреляции;
        - dashboard.
    """

    def __init__(
        self,
        figsize=(12, 6),
        dpi=110,
    ):
        self.figsize = figsize
        self.dpi = dpi

    # ============================================================
    # HELPERS
    # ============================================================

    def _create_figure(
        self,
        figsize=None,
    ):
        if figsize is None:
            figsize = self.figsize

        return plt.subplots(
            figsize=figsize,
            dpi=self.dpi,
        )

    @staticmethod
    def _check_columns(
        df,
        required,
    ):
        if not isinstance(
            df,
            pd.DataFrame,
        ):
            raise TypeError(
                "df должен быть pandas.DataFrame"
            )

        missing = [
            column
            for column in required
            if column not in df.columns
        ]

        if missing:
            raise ValueError(
                f"Отсутствуют колонки: {missing}"
            )

    @staticmethod
    def _numeric(
        df,
        columns,
    ):
        result = df.copy()

        for column in columns:
            if column in result.columns:
                result[column] = pd.to_numeric(
                    result[column],
                    errors="coerce",
                )

        return result

    @staticmethod
    def _format(
        ax,
        title=None,
        xlabel=None,
        ylabel=None,
        grid=True,
    ):
        if title:
            ax.set_title(
                title,
                fontsize=14,
                fontweight="bold",
            )

        if xlabel:
            ax.set_xlabel(xlabel)

        if ylabel:
            ax.set_ylabel(ylabel)

        if grid:
            ax.grid(
                True,
                alpha=0.25,
            )

        return ax

    @staticmethod
    def _add_values(
        ax,
        bars,
        fmt="{:.0f}",
    ):
        for bar in bars:
            value = bar.get_height()

            if pd.isna(value):
                continue

            ax.annotate(
                fmt.format(value),
                xy=(
                    bar.get_x()
                    + bar.get_width() / 2,
                    value,
                ),
                xytext=(0, 4),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=9,
            )

    @staticmethod
    def _finish(
        fig,
        show=True,
    ):
        fig.tight_layout()

        if show:
            plt.show()

        return fig

    @staticmethod
    def save_figure(
        fig,
        path,
        dpi=200,
    ):
        path = Path(path)

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        fig.savefig(
            path,
            dpi=dpi,
            bbox_inches="tight",
        )

        return path

    # ============================================================
    # STOCK LEVEL
    # ============================================================

    def stock_levels(
        self,
        df,
        name_column="name",
        stock_column="stock",
        title="Остатки товаров",
        limit=15,
        show=True,
    ):
        """
        Топ товаров по текущему остатку.
        """

        self._check_columns(
            df,
            [
                name_column,
                stock_column,
            ],
        )

        data = self._numeric(
            df,
            [stock_column],
        )

        data = (
            data
            .sort_values(
                stock_column,
                ascending=False,
            )
            .head(limit)
            .sort_values(
                stock_column,
            )
        )

        fig, ax = self._create_figure()

        bars = ax.barh(
            data[name_column].astype(str),
            data[stock_column],
        )

        self._add_values(
            ax,
            bars,
            "{:,.0f}",
        )

        self._format(
            ax,
            title=title,
            xlabel="Количество",
            ylabel="Товар",
        )

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # LOW STOCK
    # ============================================================

    def low_stock(
        self,
        df,
        name_column="name",
        stock_column="stock",
        reorder_point_column="reorder_point",
        title="Товары с критическим остатком",
        limit=15,
        show=True,
    ):
        """
        Товары, где остаток ниже точки заказа.
        """

        self._check_columns(
            df,
            [
                name_column,
                stock_column,
                reorder_point_column,
            ],
        )

        data = self._numeric(
            df,
            [
                stock_column,
                reorder_point_column,
            ],
        )

        data = data[
            data[stock_column]
            < data[reorder_point_column]
        ].copy()

        data["deficit"] = (
            data[reorder_point_column]
            - data[stock_column]
        )

        data = (
            data
            .sort_values(
                "deficit",
                ascending=False,
            )
            .head(limit)
            .sort_values(
                "deficit",
            )
        )

        fig, ax = self._create_figure()

        bars = ax.barh(
            data[name_column].astype(str),
            data["deficit"],
        )

        self._add_values(
            ax,
            bars,
            "{:,.0f}",
        )

        self._format(
            ax,
            title=title,
            xlabel="Дефицит",
            ylabel="Товар",
        )

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # EXCESS STOCK
    # ============================================================

    def excess_stock(
        self,
        df,
        name_column="name",
        stock_column="stock",
        max_stock_column="max_stock",
        title="Избыточные запасы",
        limit=15,
        show=True,
    ):
        """
        Товары, где остаток превышает максимальный запас.
        """

        self._check_columns(
            df,
            [
                name_column,
                stock_column,
                max_stock_column,
            ],
        )

        data = self._numeric(
            df,
            [
                stock_column,
                max_stock_column,
            ],
        )

        data = data[
            data[stock_column]
            > data[max_stock_column]
        ].copy()

        data["excess"] = (
            data[stock_column]
            - data[max_stock_column]
        )

        data = (
            data
            .sort_values(
                "excess",
                ascending=False,
            )
            .head(limit)
            .sort_values(
                "excess",
            )
        )

        fig, ax = self._create_figure()

        bars = ax.barh(
            data[name_column].astype(str),
            data["excess"],
        )

        self._add_values(
            ax,
            bars,
            "{:,.0f}",
        )

        self._format(
            ax,
            title=title,
            xlabel="Излишек",
            ylabel="Товар",
        )

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # INVENTORY VALUE
    # ============================================================

    def inventory_value(
        self,
        df,
        name_column="name",
        stock_column="stock",
        cost_column="cost_price",
        title="Стоимость запасов",
        limit=15,
        show=True,
    ):
        """
        Стоимость текущих запасов:

            stock * cost_price
        """

        self._check_columns(
            df,
            [
                name_column,
                stock_column,
                cost_column,
            ],
        )

        data = self._numeric(
            df,
            [
                stock_column,
                cost_column,
            ],
        )

        data["inventory_value"] = (
            data[stock_column]
            * data[cost_column]
        )

        data = (
            data
            .sort_values(
                "inventory_value",
                ascending=False,
            )
            .head(limit)
            .sort_values(
                "inventory_value",
            )
        )

        fig, ax = self._create_figure()

        bars = ax.barh(
            data[name_column].astype(str),
            data["inventory_value"],
        )

        self._add_values(
            ax,
            bars,
            "{:,.0f}",
        )

        self._format(
            ax,
            title=title,
            xlabel="Стоимость",
            ylabel="Товар",
        )

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # INVENTORY VALUE BY CATEGORY
    # ============================================================

    def inventory_value_by_category(
        self,
        df,
        category_column="category",
        value_column="inventory_value",
        title="Стоимость запасов по категориям",
        limit=15,
        show=True,
    ):
        """Стоимость запасов по категориям."""

        self._check_columns(
            df,
            [
                category_column,
                value_column,
            ],
        )

        data = (
            df
            .groupby(category_column)[
                value_column
            ]
            .sum()
            .reset_index()
            .sort_values(
                value_column,
                ascending=False,
            )
            .head(limit)
            .sort_values(
                value_column,
            )
        )

        fig, ax = self._create_figure()

        bars = ax.barh(
            data[category_column].astype(str),
            data[value_column],
        )

        self._add_values(
            ax,
            bars,
            "{:,.0f}",
        )

        self._format(
            ax,
            title=title,
            xlabel="Стоимость запасов",
            ylabel="Категория",
        )

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # STOCK DYNAMICS
    # ============================================================

    def stock_dynamics(
        self,
        df,
        date_column="date",
        stock_column="stock",
        title="Динамика запасов",
        show=True,
    ):
        """Изменение общего остатка во времени."""

        self._check_columns(
            df,
            [
                date_column,
                stock_column,
            ],
        )

        data = df.copy()

        data[date_column] = pd.to_datetime(
            data[date_column],
            errors="coerce",
        )

        data[stock_column] = pd.to_numeric(
            data[stock_column],
            errors="coerce",
        )

        data = (
            data
            .dropna(
                subset=[
                    date_column,
                    stock_column,
                ]
            )
            .sort_values(date_column)
        )

        fig, ax = self._create_figure()

        ax.plot(
            data[date_column],
            data[stock_column],
            marker="o",
            linewidth=2,
        )

        self._format(
            ax,
            title=title,
            xlabel="Дата",
            ylabel="Остаток",
        )

        fig.autofmt_xdate()

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # STOCK VS SALES
    # ============================================================

    def stock_vs_sales(
        self,
        df,
        name_column="name",
        stock_column="stock",
        sales_column="sales",
        title="Остатки и продажи",
        show=True,
    ):
        """
        Scatter:

            X = продажи
            Y = остаток
        """

        self._check_columns(
            df,
            [
                name_column,
                stock_column,
                sales_column,
            ],
        )

        data = self._numeric(
            df,
            [
                stock_column,
                sales_column,
            ],
        ).dropna(
            subset=[
                stock_column,
                sales_column,
            ]
        )

        fig, ax = self._create_figure()

        ax.scatter(
            data[sales_column],
            data[stock_column],
            alpha=0.7,
        )

        self._format(
            ax,
            title=title,
            xlabel="Продажи",
            ylabel="Остаток",
        )

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # TURNOVER
    # ============================================================

    def turnover(
        self,
        df,
        name_column="name",
        turnover_column="turnover",
        title="Оборачиваемость запасов",
        limit=15,
        show=True,
    ):
        """
        Рейтинг товаров по оборачиваемости.
        """

        self._check_columns(
            df,
            [
                name_column,
                turnover_column,
            ],
        )

        data = self._numeric(
            df,
            [turnover_column],
        )

        data = (
            data
            .sort_values(
                turnover_column,
                ascending=False,
            )
            .head(limit)
            .sort_values(
                turnover_column,
            )
        )

        fig, ax = self._create_figure()

        bars = ax.barh(
            data[name_column].astype(str),
            data[turnover_column],
        )

        self._add_values(
            ax,
            bars,
            "{:.2f}",
        )

        self._format(
            ax,
            title=title,
            xlabel="Обороты",
            ylabel="Товар",
        )

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # DAYS OF INVENTORY
    # ============================================================

    def days_of_inventory(
        self,
        df,
        name_column="name",
        days_column="days_of_inventory",
        title="Дни запаса",
        limit=15,
        show=True,
    ):
        """
        Сколько дней текущего спроса
        покрывает запас.
        """

        self._check_columns(
            df,
            [
                name_column,
                days_column,
            ],
        )

        data = self._numeric(
            df,
            [days_column],
        )

        data = (
            data
            .sort_values(
                days_column,
                ascending=False,
            )
            .head(limit)
            .sort_values(
                days_column,
            )
        )

        fig, ax = self._create_figure()

        bars = ax.barh(
            data[name_column].astype(str),
            data[days_column],
        )

        self._add_values(
            ax,
            bars,
            "{:.1f}",
        )

        self._format(
            ax,
            title=title,
            xlabel="Дни",
            ylabel="Товар",
        )

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # STOCK TURNOVER DYNAMICS
    # ============================================================

    def turnover_dynamics(
        self,
        df,
        date_column="date",
        turnover_column="turnover",
        title="Динамика оборачиваемости",
        show=True,
    ):
        """Изменение оборачиваемости во времени."""

        self._check_columns(
            df,
            [
                date_column,
                turnover_column,
            ],
        )

        data = df.copy()

        data[date_column] = pd.to_datetime(
            data[date_column],
            errors="coerce",
        )

        data[turnover_column] = pd.to_numeric(
            data[turnover_column],
            errors="coerce",
        )

        data = (
            data
            .dropna(
                subset=[
                    date_column,
                    turnover_column,
                ]
            )
            .sort_values(date_column)
        )

        fig, ax = self._create_figure()

        ax.plot(
            data[date_column],
            data[turnover_column],
            marker="o",
        )

        ax.axhline(
            data[turnover_column].mean(),
            linestyle="--",
            label="Среднее",
        )

        ax.legend()

        self._format(
            ax,
            title=title,
            xlabel="Дата",
            ylabel="Оборачиваемость",
        )

        fig.autofmt_xdate()

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # STOCKOUT RATE
    # ============================================================

    def stockout_rate(
        self,
        df,
        date_column="date",
        stockout_column="stockout_rate",
        title="Доля дефицита",
        show=True,
    ):
        """Динамика stockout rate."""

        self._check_columns(
            df,
            [
                date_column,
                stockout_column,
            ],
        )

        data = df.copy()

        data[date_column] = pd.to_datetime(
            data[date_column],
            errors="coerce",
        )

        data[stockout_column] = pd.to_numeric(
            data[stockout_column],
            errors="coerce",
        )

        data = (
            data
            .dropna(
                subset=[
                    date_column,
                    stockout_column,
                ]
            )
            .sort_values(date_column)
        )

        fig, ax = self._create_figure()

        ax.plot(
            data[date_column],
            data[stockout_column],
            marker="o",
        )

        self._format(
            ax,
            title=title,
            xlabel="Дата",
            ylabel="Stockout, %",
        )

        fig.autofmt_xdate()

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # STOCKOUT BY CATEGORY
    # ============================================================

    def stockout_by_category(
        self,
        df,
        category_column="category",
        stockout_column="stockout_rate",
        title="Дефицит по категориям",
        limit=15,
        show=True,
    ):
        """Средний stockout rate по категориям."""

        self._check_columns(
            df,
            [
                category_column,
                stockout_column,
            ],
        )

        data = (
            df
            .groupby(category_column)[
                stockout_column
            ]
            .mean()
            .reset_index()
            .sort_values(
                stockout_column,
                ascending=False,
            )
            .head(limit)
            .sort_values(
                stockout_column,
            )
        )

        fig, ax = self._create_figure()

        bars = ax.barh(
            data[category_column].astype(str),
            data[stockout_column],
        )

        self._add_values(
            ax,
            bars,
            "{:.1f}%",
        )

        self._format(
            ax,
            title=title,
            xlabel="Stockout, %",
            ylabel="Категория",
        )

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # REORDER POINT
    # ============================================================

    def reorder_point_comparison(
        self,
        df,
        name_column="name",
        stock_column="stock",
        reorder_column="reorder_point",
        title="Остаток и точка заказа",
        limit=15,
        show=True,
    ):
        """
        Сравнение:

            текущий остаток
            reorder point
        """

        self._check_columns(
            df,
            [
                name_column,
                stock_column,
                reorder_column,
            ],
        )

        data = self._numeric(
            df,
            [
                stock_column,
                reorder_column,
            ],
        )

        data = data.head(limit)

        data = data.sort_values(
            stock_column,
        )

        fig, ax = self._create_figure()

        y = np.arange(
            len(data)
        )

        height = 0.35

        ax.barh(
            y - height / 2,
            data[stock_column],
            height,
            label="Остаток",
        )

        ax.barh(
            y + height / 2,
            data[reorder_column],
            height,
            label="Точка заказа",
        )

        ax.set_yticks(y)

        ax.set_yticklabels(
            data[name_column].astype(str)
        )

        ax.legend()

        self._format(
            ax,
            title=title,
            xlabel="Количество",
            ylabel="Товар",
        )

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # DEMAND FORECAST
    # ============================================================

    def demand_forecast(
        self,
        df,
        date_column="date",
        actual_column="demand",
        forecast_column="forecast",
        title="Фактический и прогнозируемый спрос",
        show=True,
    ):
        """
        Сравнение фактического спроса
        с прогнозом.
        """

        self._check_columns(
            df,
            [
                date_column,
                actual_column,
                forecast_column,
            ],
        )

        data = df.copy()

        data[date_column] = pd.to_datetime(
            data[date_column],
            errors="coerce",
        )

        data = self._numeric(
            data,
            [
                actual_column,
                forecast_column,
            ],
        )

        data = (
            data
            .dropna(
                subset=[
                    date_column,
                ]
            )
            .sort_values(date_column)
        )

        fig, ax = self._create_figure()

        ax.plot(
            data[date_column],
            data[actual_column],
            marker="o",
            label="Факт",
        )

        ax.plot(
            data[date_column],
            data[forecast_column],
            linestyle="--",
            linewidth=2,
            label="Прогноз",
        )

        ax.legend()

        self._format(
            ax,
            title=title,
            xlabel="Дата",
            ylabel="Спрос",
        )

        fig.autofmt_xdate()

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # DEMAND VS STOCK
    # ============================================================

    def demand_vs_stock(
        self,
        df,
        name_column="name",
        demand_column="demand",
        stock_column="stock",
        title="Спрос и складской запас",
        show=True,
    ):
        """
        Матрица:

            X = спрос
            Y = запас
        """

        self._check_columns(
            df,
            [
                name_column,
                demand_column,
                stock_column,
            ],
        )

        data = self._numeric(
            df,
            [
                demand_column,
                stock_column,
            ],
        ).dropna(
            subset=[
                demand_column,
                stock_column,
            ]
        )

        demand_median = (
            data[demand_column].median()
        )

        stock_median = (
            data[stock_column].median()
        )

        fig, ax = self._create_figure()

        ax.scatter(
            data[demand_column],
            data[stock_column],
            alpha=0.7,
        )

        ax.axvline(
            demand_median,
            linestyle="--",
        )

        ax.axhline(
            stock_median,
            linestyle="--",
        )

        self._format(
            ax,
            title=title,
            xlabel="Спрос",
            ylabel="Остаток",
        )

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # SUPPLIER PERFORMANCE
    # ============================================================

    def supplier_performance(
        self,
        df,
        supplier_column="supplier",
        value_column="purchase_value",
        title="Поставщики",
        limit=15,
        show=True,
    ):
        """Стоимость закупок по поставщикам."""

        self._check_columns(
            df,
            [
                supplier_column,
                value_column,
            ],
        )

        data = (
            df
            .groupby(supplier_column)[
                value_column
            ]
            .sum()
            .reset_index()
            .sort_values(
                value_column,
                ascending=False,
            )
            .head(limit)
            .sort_values(
                value_column,
            )
        )

        fig, ax = self._create_figure()

        bars = ax.barh(
            data[supplier_column].astype(str),
            data[value_column],
        )

        self._add_values(
            ax,
            bars,
            "{:,.0f}",
        )

        self._format(
            ax,
            title=title,
            xlabel="Стоимость закупок",
            ylabel="Поставщик",
        )

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # ABC ANALYSIS
    # ============================================================

    def abc_distribution(
        self,
        df,
        class_column="abc_class",
        value_column="inventory_value",
        title="ABC-анализ запасов",
        show=True,
    ):
        """
        Вклад классов A/B/C
        в стоимость запасов.
        """

        self._check_columns(
            df,
            [
                class_column,
                value_column,
            ],
        )

        data = (
            df
            .groupby(class_column)[
                value_column
            ]
            .sum()
            .reindex(
                ["A", "B", "C"],
                fill_value=0,
            )
        )

        fig, ax = self._create_figure()

        bars = ax.bar(
            data.index,
            data.values,
        )

        self._add_values(
            ax,
            bars,
            "{:,.0f}",
        )

        self._format(
            ax,
            title=title,
            xlabel="ABC-класс",
            ylabel="Стоимость запасов",
        )

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # ABC SHARE
    # ============================================================

    def abc_share(
        self,
        df,
        class_column="abc_class",
        value_column="inventory_value",
        title="Доля стоимости запасов по ABC",
        show=True,
    ):
        """Процент стоимости запасов каждого класса."""

        self._check_columns(
            df,
            [
                class_column,
                value_column,
            ],
        )

        data = (
            df
            .groupby(class_column)[
                value_column
            ]
            .sum()
            .reindex(
                ["A", "B", "C"],
                fill_value=0,
            )
        )

        total = data.sum()

        if total != 0:
            share = (
                data / total * 100
            )
        else:
            share = data * 0

        fig, ax = self._create_figure()

        bars = ax.bar(
            share.index,
            share.values,
        )

        self._add_values(
            ax,
            bars,
            "{:.1f}%",
        )

        self._format(
            ax,
            title=title,
            xlabel="ABC-класс",
            ylabel="Доля, %",
        )

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # XYZ DISTRIBUTION
    # ============================================================

    def xyz_distribution(
        self,
        df,
        class_column="xyz_class",
        title="XYZ-анализ спроса",
        show=True,
    ):
        """Количество товаров в X/Y/Z классах."""

        self._check_columns(
            df,
            [class_column],
        )

        data = (
            df[class_column]
            .value_counts()
            .reindex(
                ["X", "Y", "Z"],
                fill_value=0,
            )
        )

        fig, ax = self._create_figure()

        bars = ax.bar(
            data.index,
            data.values,
        )

        self._add_values(
            ax,
            bars,
            "{:.0f}",
        )

        self._format(
            ax,
            title=title,
            xlabel="XYZ-класс",
            ylabel="Количество товаров",
        )

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # ABC XYZ MATRIX
    # ============================================================

    def abc_xyz_matrix(
        self,
        df,
        abc_column="abc_class",
        xyz_column="xyz_class",
        title="ABC/XYZ матрица",
        show=True,
    ):
        """
        Матрица количества товаров:

              X   Y   Z
            A
            B
            C
        """

        self._check_columns(
            df,
            [
                abc_column,
                xyz_column,
            ],
        )

        matrix = pd.crosstab(
            df[abc_column],
            df[xyz_column],
        )

        abc_order = [
            "A",
            "B",
            "C",
        ]

        xyz_order = [
            "X",
            "Y",
            "Z",
        ]

        matrix = matrix.reindex(
            index=abc_order,
            columns=xyz_order,
            fill_value=0,
        )

        fig, ax = self._create_figure(
            figsize=(8, 7)
        )

        image = ax.imshow(
            matrix.values,
            aspect="auto",
        )

        fig.colorbar(
            image,
            ax=ax,
        )

        ax.set_xticks(
            np.arange(
                len(matrix.columns)
            )
        )

        ax.set_yticks(
            np.arange(
                len(matrix.index)
            )
        )

        ax.set_xticklabels(
            matrix.columns
        )

        ax.set_yticklabels(
            matrix.index
        )

        for i in range(
            len(matrix.index)
        ):
            for j in range(
                len(matrix.columns)
            ):
                ax.text(
                    j,
                    i,
                    str(
                        matrix.iloc[i, j]
                    ),
                    ha="center",
                    va="center",
                    fontsize=12,
                )

        self._format(
            ax,
            title=title,
            xlabel="XYZ-класс",
            ylabel="ABC-класс",
            grid=False,
        )

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # STOCK VALUE DISTRIBUTION
    # ============================================================

    def inventory_value_distribution(
        self,
        df,
        value_column="inventory_value",
        bins=20,
        title="Распределение стоимости запасов",
        show=True,
    ):
        """Распределение стоимости запасов."""

        self._check_columns(
            df,
            [value_column],
        )

        values = pd.to_numeric(
            df[value_column],
            errors="coerce",
        ).dropna()

        fig, ax = self._create_figure()

        ax.hist(
            values,
            bins=bins,
        )

        ax.axvline(
            values.mean(),
            linestyle="--",
            linewidth=2,
            label="Среднее",
        )

        ax.axvline(
            values.median(),
            linestyle=":",
            linewidth=2,
            label="Медиана",
        )

        ax.legend()

        self._format(
            ax,
            title=title,
            xlabel="Стоимость",
            ylabel="Количество товаров",
        )

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # CORRELATION
    # ============================================================

    def correlation_heatmap(
        self,
        df,
        columns=None,
        title="Корреляция складских показателей",
        show=True,
    ):
        """
        Heatmap корреляций.
        Используется только matplotlib.
        """

        if columns is None:
            data = df.select_dtypes(
                include=[np.number]
            ).copy()
        else:
            self._check_columns(
                df,
                columns,
            )

            data = df[
                columns
            ].copy()

        correlation = data.corr()

        fig, ax = self._create_figure(
            figsize=(10, 8)
        )

        image = ax.imshow(
            correlation,
            aspect="auto",
        )

        fig.colorbar(
            image,
            ax=ax,
        )

        ax.set_xticks(
            np.arange(
                len(correlation.columns)
            )
        )

        ax.set_yticks(
            np.arange(
                len(correlation.columns)
            )
        )

        ax.set_xticklabels(
            correlation.columns,
            rotation=45,
            ha="right",
        )

        ax.set_yticklabels(
            correlation.columns,
        )

        for i in range(
            len(correlation.columns)
        ):
            for j in range(
                len(correlation.columns)
            ):

                value = correlation.iloc[
                    i,
                    j,
                ]

                if pd.notna(value):
                    ax.text(
                        j,
                        i,
                        f"{value:.2f}",
                        ha="center",
                        va="center",
                        fontsize=9,
                    )

        self._format(
            ax,
            title=title,
            grid=False,
        )

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # ROLLING STOCK
    # ============================================================

    def rolling_stock(
        self,
        df,
        date_column="date",
        stock_column="stock",
        window=7,
        title="Скользящая средняя запасов",
        show=True,
    ):
        """Фактические остатки + MA."""

        self._check_columns(
            df,
            [
                date_column,
                stock_column,
            ],
        )

        data = df.copy()

        data[date_column] = pd.to_datetime(
            data[date_column],
            errors="coerce",
        )

        data[stock_column] = pd.to_numeric(
            data[stock_column],
            errors="coerce",
        )

        data = (
            data
            .dropna(
                subset=[
                    date_column,
                    stock_column,
                ]
            )
            .sort_values(date_column)
        )

        data["rolling_mean"] = (
            data[stock_column]
            .rolling(window)
            .mean()
        )

        fig, ax = self._create_figure()

        ax.plot(
            data[date_column],
            data[stock_column],
            alpha=0.5,
            label="Остаток",
        )

        ax.plot(
            data[date_column],
            data["rolling_mean"],
            linewidth=3,
            label=f"MA {window}",
        )

        ax.legend()

        self._format(
            ax,
            title=title,
            xlabel="Дата",
            ylabel="Остаток",
        )

        fig.autofmt_xdate()

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # INVENTORY EFFICIENCY MATRIX
    # ============================================================

    def inventory_efficiency_matrix(
        self,
        df,
        turnover_column="turnover",
        stock_value_column="inventory_value",
        title="Матрица эффективности запасов",
        show=True,
    ):
        """
        X = стоимость запасов
        Y = оборачиваемость

        Позволяет находить:

            высокий запас + высокая оборачиваемость
            высокий запас + низкая оборачиваемость
            низкий запас + высокая оборачиваемость
            низкий запас + низкая оборачиваемость
        """

        self._check_columns(
            df,
            [
                turnover_column,
                stock_value_column,
            ],
        )

        data = self._numeric(
            df,
            [
                turnover_column,
                stock_value_column,
            ],
        ).dropna(
            subset=[
                turnover_column,
                stock_value_column,
            ]
        )

        turnover_median = (
            data[turnover_column].median()
        )

        value_median = (
            data[stock_value_column].median()
        )

        fig, ax = self._create_figure()

        ax.scatter(
            data[stock_value_column],
            data[turnover_column],
            alpha=0.7,
        )

        ax.axvline(
            value_median,
            linestyle="--",
        )

        ax.axhline(
            turnover_median,
            linestyle="--",
        )

        self._format(
            ax,
            title=title,
            xlabel="Стоимость запасов",
            ylabel="Оборачиваемость",
        )

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # INVENTORY DASHBOARD
    # ============================================================

    def dashboard(
        self,
        summary,
        stock_df,
        abc_df=None,
        category_df=None,
        show=True,
    ):
        """
        Общий dashboard склада.

        summary:
            dict с KPI.

        stock_df:
            динамика запасов.

        abc_df:
            ABC-аналитика.

        category_df:
            категории.
        """

        fig = plt.figure(
            figsize=(16, 10),
            dpi=self.dpi,
        )

        grid = fig.add_gridspec(
            2,
            2,
            hspace=0.35,
            wspace=0.25,
        )

        # --------------------------------------------------------
        # STOCK DYNAMICS
        # --------------------------------------------------------

        ax1 = fig.add_subplot(
            grid[0, 0]
        )

        if (
            stock_df is not None
            and not stock_df.empty
        ):

            data = stock_df.copy()

            date_column = (
                "date"
                if "date" in data.columns
                else "month"
            )

            data[date_column] = pd.to_datetime(
                data[date_column],
                errors="coerce",
            )

            if "stock" in data.columns:

                data["stock"] = pd.to_numeric(
                    data["stock"],
                    errors="coerce",
                )

                data = data.dropna(
                    subset=[
                        date_column,
                        "stock",
                    ]
                )

                ax1.plot(
                    data[date_column],
                    data["stock"],
                    marker="o",
                )

                ax1.set_title(
                    "Динамика запасов",
                    fontweight="bold",
                )

                ax1.grid(
                    True,
                    alpha=0.25,
                )

        # --------------------------------------------------------
        # ABC
        # --------------------------------------------------------

        ax2 = fig.add_subplot(
            grid[0, 1]
        )

        if (
            abc_df is not None
            and not abc_df.empty
        ):

            if (
                "abc_class" in abc_df.columns
                and "inventory_value"
                in abc_df.columns
            ):

                data = (
                    abc_df
                    .groupby("abc_class")[
                        "inventory_value"
                    ]
                    .sum()
                    .reindex(
                        [
                            "A",
                            "B",
                            "C",
                        ],
                        fill_value=0,
                    )
                )

                ax2.bar(
                    data.index,
                    data.values,
                )

                ax2.set_title(
                    "ABC-анализ",
                    fontweight="bold",
                )

                ax2.grid(
                    True,
                    axis="y",
                    alpha=0.25,
                )

        # --------------------------------------------------------
        # CATEGORY
        # --------------------------------------------------------

        ax3 = fig.add_subplot(
            grid[1, 0]
        )

        if (
            category_df is not None
            and not category_df.empty
        ):

            if (
                "category"
                in category_df.columns
                and "inventory_value"
                in category_df.columns
            ):

                data = (
                    category_df
                    .groupby("category")[
                        "inventory_value"
                    ]
                    .sum()
                    .reset_index()
                    .sort_values(
                        "inventory_value",
                        ascending=False,
                    )
                    .head(10)
                    .sort_values(
                        "inventory_value",
                    )
                )

                ax3.barh(
                    data["category"].astype(str),
                    data["inventory_value"],
                )

                ax3.set_title(
                    "Категории",
                    fontweight="bold",
                )

                ax3.grid(
                    True,
                    axis="x",
                    alpha=0.25,
                )

        # --------------------------------------------------------
        # KPI
        # --------------------------------------------------------

        ax4 = fig.add_subplot(
            grid[1, 1]
        )

        ax4.axis("off")

        if isinstance(
            summary,
            dict,
        ):

            total_stock = summary.get(
                "total_stock",
                0,
            )

            inventory_value = summary.get(
                "inventory_value",
                0,
            )

            turnover = summary.get(
                "turnover",
                0,
            )

            stockout_rate = summary.get(
                "stockout_rate",
                0,
            )

            excess_value = summary.get(
                "excess_stock_value",
                0,
            )

            ax4.text(
                0.5,
                0.82,
                "INVENTORY KPI",
                ha="center",
                fontsize=18,
                fontweight="bold",
            )

            ax4.text(
                0.5,
                0.66,
                f"Остаток: {total_stock:,.0f}",
                ha="center",
                fontsize=14,
            )

            ax4.text(
                0.5,
                0.51,
                f"Стоимость: {inventory_value:,.0f}",
                ha="center",
                fontsize=14,
            )

            ax4.text(
                0.5,
                0.36,
                f"Оборачиваемость: {turnover:.2f}",
                ha="center",
                fontsize=14,
            )

            ax4.text(
                0.5,
                0.21,
                f"Stockout: {stockout_rate:.1f}%",
                ha="center",
                fontsize=14,
            )

            ax4.text(
                0.5,
                0.06,
                f"Излишки: {excess_value:,.0f}",
                ha="center",
                fontsize=14,
            )

        fig.suptitle(
            "Inventory Analytics Dashboard",
            fontsize=20,
            fontweight="bold",
        )

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # SAVE
    # ============================================================

    def save(
        self,
        fig,
        path,
        dpi=200,
    ):
        """Сохранить Figure."""

        return self.save_figure(
            fig,
            path,
            dpi=dpi,
        )

    # ============================================================
    # CLOSE
    # ============================================================

    @staticmethod
    def close(
        fig=None,
    ):
        """Закрыть один график или все."""

        if fig is None:
            plt.close("all")
        else:
            plt.close(fig)