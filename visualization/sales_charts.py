from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


class SalesCharts:
    """
    Visualization layer для аналитики продаж.

    Вход:
        pandas.DataFrame

    Выход:
        matplotlib Figure / Axes

    Класс не работает с БД и не содержит SQL.

    Основные графики:
        - выручка по месяцам;
        - выручка по годам;
        - динамика продаж;
        - рост продаж;
        - топ товаров;
        - прибыль товаров;
        - прибыльность;
        - категории;
        - бренды;
        - ABC-анализ;
        - Pareto;
        - сравнение выручки и прибыли;
        - распределения;
        - rolling average;
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
        """Создать Figure и Axes."""

        if figsize is None:
            figsize = self.figsize

        fig, ax = plt.subplots(
            figsize=figsize,
            dpi=self.dpi,
        )

        return fig, ax

    @staticmethod
    def _prepare_numeric(
        df,
        columns,
    ):
        """Привести выбранные колонки к числовому типу."""

        result = df.copy()

        for column in columns:
            if column in result.columns:
                result[column] = pd.to_numeric(
                    result[column],
                    errors="coerce",
                )

        return result

    @staticmethod
    def _check_columns(
        df,
        required,
    ):
        """Проверить наличие колонок."""

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
    def _format_axis(
        ax,
        title=None,
        xlabel=None,
        ylabel=None,
        grid=True,
    ):
        """Общая настройка графика."""

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
        """Добавить значения над столбцами."""

        for bar in bars:
            height = bar.get_height()

            if pd.isna(height):
                continue

            ax.annotate(
                fmt.format(height),
                xy=(
                    bar.get_x()
                    + bar.get_width() / 2,
                    height,
                ),
                xytext=(
                    0,
                    4,
                ),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=9,
            )

    @staticmethod
    def _save(
        fig,
        path,
        dpi=200,
    ):
        """Сохранить Figure."""

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
    # REVENUE BY MONTH
    # ============================================================

    def revenue_by_month(
        self,
        df,
        date_column="date",
        value_column="revenue",
        title="Выручка по месяцам",
        show=True,
    ):
        """
        Линейный график месячной выручки.
        """

        self._check_columns(
            df,
            [
                date_column,
                value_column,
            ],
        )

        data = df.copy()

        data[date_column] = pd.to_datetime(
            data[date_column],
            errors="coerce",
        )

        data[value_column] = pd.to_numeric(
            data[value_column],
            errors="coerce",
        )

        data = (
            data
            .dropna(
                subset=[
                    date_column,
                    value_column,
                ]
            )
            .sort_values(date_column)
        )

        fig, ax = self._create_figure()

        ax.plot(
            data[date_column],
            data[value_column],
            marker="o",
            linewidth=2,
        )

        self._format_axis(
            ax,
            title=title,
            xlabel="Дата",
            ylabel="Выручка",
        )

        fig.autofmt_xdate()

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # REVENUE BY YEAR
    # ============================================================

    def revenue_by_year(
        self,
        df,
        year_column="year",
        value_column="revenue",
        title="Выручка по годам",
        show=True,
    ):
        """Столбчатый график годовой выручки."""

        self._check_columns(
            df,
            [
                year_column,
                value_column,
            ],
        )

        data = (
            df.copy()
            .sort_values(year_column)
        )

        data = self._prepare_numeric(
            data,
            [
                year_column,
                value_column,
            ],
        )

        fig, ax = self._create_figure()

        bars = ax.bar(
            data[year_column].astype(str),
            data[value_column],
        )

        self._add_values(
            ax,
            bars,
            fmt="{:,.0f}",
        )

        self._format_axis(
            ax,
            title=title,
            xlabel="Год",
            ylabel="Выручка",
        )

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # SALES DYNAMICS
    # ============================================================

    def sales_dynamics(
        self,
        df,
        date_column="month",
        value_column="revenue",
        title="Динамика продаж",
        show=True,
    ):
        """
        Динамика выручки + линия среднего.
        """

        self._check_columns(
            df,
            [
                date_column,
                value_column,
            ],
        )

        data = df.copy()

        data[date_column] = pd.to_datetime(
            data[date_column],
            errors="coerce",
        )

        data[value_column] = pd.to_numeric(
            data[value_column],
            errors="coerce",
        )

        data = (
            data
            .dropna(
                subset=[
                    date_column,
                    value_column,
                ]
            )
            .sort_values(date_column)
        )

        fig, ax = self._create_figure()

        ax.plot(
            data[date_column],
            data[value_column],
            marker="o",
            label="Выручка",
        )

        mean_value = data[
            value_column
        ].mean()

        ax.axhline(
            mean_value,
            linestyle="--",
            label="Среднее",
        )

        ax.legend()

        self._format_axis(
            ax,
            title=title,
            xlabel="Дата",
            ylabel="Выручка",
        )

        fig.autofmt_xdate()

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # GROWTH
    # ============================================================

    def growth_chart(
        self,
        df,
        date_column="month",
        growth_column="growth_percent",
        title="Рост продаж",
        show=True,
    ):
        """График процентного изменения."""

        self._check_columns(
            df,
            [
                date_column,
                growth_column,
            ],
        )

        data = df.copy()

        data[date_column] = pd.to_datetime(
            data[date_column],
            errors="coerce",
        )

        data[growth_column] = pd.to_numeric(
            data[growth_column],
            errors="coerce",
        )

        data = data.dropna(
            subset=[
                date_column,
                growth_column,
            ]
        )

        fig, ax = self._create_figure()

        ax.axhline(
            0,
            linestyle="--",
            linewidth=1,
        )

        ax.plot(
            data[date_column],
            data[growth_column],
            marker="o",
        )

        self._format_axis(
            ax,
            title=title,
            xlabel="Дата",
            ylabel="Изменение, %",
        )

        fig.autofmt_xdate()

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # TOP PRODUCTS
    # ============================================================

    def top_products(
        self,
        df,
        name_column="name",
        value_column="revenue",
        title="Топ товаров",
        limit=None,
        horizontal=True,
        show=True,
    ):
        """
        Топ товаров по выбранному показателю.

        Например:
            revenue
            profit
            units_sold
        """

        self._check_columns(
            df,
            [
                name_column,
                value_column,
            ],
        )

        data = (
            df.copy()
            .sort_values(
                value_column,
                ascending=False,
            )
        )

        if limit is not None:
            data = data.head(limit)

        data = data.sort_values(
            value_column,
            ascending=True,
        )

        fig, ax = self._create_figure()

        if horizontal:

            bars = ax.barh(
                data[name_column].astype(str),
                data[value_column],
            )

        else:

            bars = ax.bar(
                data[name_column].astype(str),
                data[value_column],
            )

            plt.xticks(
                rotation=45,
                ha="right",
            )

        self._add_values(
            ax,
            bars,
            fmt="{:,.0f}",
        )

        self._format_axis(
            ax,
            title=title,
            ylabel=(
                "Товар"
                if horizontal
                else value_column
            ),
            xlabel=(
                value_column
                if horizontal
                else "Товар"
            ),
        )

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # PROFIT BY PRODUCT
    # ============================================================

    def profit_by_product(
        self,
        df,
        name_column="name",
        profit_column="profit",
        title="Прибыль по товарам",
        limit=15,
        show=True,
    ):
        """Прибыль по товарам."""

        self._check_columns(
            df,
            [
                name_column,
                profit_column,
            ],
        )

        data = (
            df.copy()
            .sort_values(
                profit_column,
                ascending=False,
            )
            .head(limit)
            .sort_values(
                profit_column
            )
        )

        fig, ax = self._create_figure()

        bars = ax.barh(
            data[name_column].astype(str),
            data[profit_column],
        )

        self._add_values(
            ax,
            bars,
            fmt="{:,.0f}",
        )

        ax.axvline(
            0,
            linewidth=1,
        )

        self._format_axis(
            ax,
            title=title,
            xlabel="Прибыль",
            ylabel="Товар",
        )

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # REVENUE VS PROFIT
    # ============================================================

    def revenue_vs_profit(
        self,
        df,
        revenue_column="revenue",
        profit_column="profit",
        name_column="name",
        title="Выручка и прибыль товаров",
        show=True,
    ):
        """
        Scatter plot:

            X = revenue
            Y = profit

        Размер точек зависит от величины выручки.
        """

        self._check_columns(
            df,
            [
                name_column,
                revenue_column,
                profit_column,
            ],
        )

        data = self._prepare_numeric(
            df,
            [
                revenue_column,
                profit_column,
            ],
        )

        data = data.dropna(
            subset=[
                revenue_column,
                profit_column,
            ]
        )

        fig, ax = self._create_figure()

        sizes = (
            np.maximum(
                data[revenue_column],
                0
            )
            + 1
        )

        ax.scatter(
            data[revenue_column],
            data[profit_column],
            s=sizes,
            alpha=0.7,
        )

        ax.axhline(
            0,
            linestyle="--",
            linewidth=1,
        )

        ax.axvline(
            data[revenue_column].median(),
            linestyle="--",
            linewidth=1,
        )

        self._format_axis(
            ax,
            title=title,
            xlabel="Выручка",
            ylabel="Прибыль",
        )

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # PROFIT MARGIN
    # ============================================================

    def profit_margin(
        self,
        df,
        name_column="name",
        margin_column="margin_percent",
        title="Рентабельность товаров",
        limit=15,
        show=True,
    ):
        """Рентабельность товаров."""

        self._check_columns(
            df,
            [
                name_column,
                margin_column,
            ],
        )

        data = (
            df.copy()
            .sort_values(
                margin_column,
                ascending=False,
            )
            .head(limit)
            .sort_values(
                margin_column
            )
        )

        fig, ax = self._create_figure()

        bars = ax.barh(
            data[name_column].astype(str),
            data[margin_column],
        )

        self._add_values(
            ax,
            bars,
            fmt="{:.1f}%",
        )

        ax.axvline(
            0,
            linewidth=1,
        )

        self._format_axis(
            ax,
            title=title,
            xlabel="Маржа, %",
            ylabel="Товар",
        )

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # CATEGORY PERFORMANCE
    # ============================================================

    def category_revenue(
        self,
        df,
        category_column="category",
        revenue_column="revenue",
        title="Выручка по категориям",
        limit=None,
        show=True,
    ):
        """Выручка по категориям."""

        self._check_columns(
            df,
            [
                category_column,
                revenue_column,
            ],
        )

        data = (
            df.copy()
            .sort_values(
                revenue_column,
                ascending=False,
            )
        )

        if limit is not None:
            data = data.head(limit)

        data = data.sort_values(
            revenue_column
        )

        fig, ax = self._create_figure()

        bars = ax.barh(
            data[category_column].astype(str),
            data[revenue_column],
        )

        self._add_values(
            ax,
            bars,
            fmt="{:,.0f}",
        )

        self._format_axis(
            ax,
            title=title,
            xlabel="Выручка",
            ylabel="Категория",
        )

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # CATEGORY PROFIT
    # ============================================================

    def category_profit(
        self,
        df,
        category_column="category",
        profit_column="profit",
        title="Прибыль по категориям",
        limit=None,
        show=True,
    ):
        """Прибыль по категориям."""

        self._check_columns(
            df,
            [
                category_column,
                profit_column,
            ],
        )

        data = (
            df.copy()
            .sort_values(
                profit_column,
                ascending=False,
            )
        )

        if limit is not None:
            data = data.head(limit)

        data = data.sort_values(
            profit_column
        )

        fig, ax = self._create_figure()

        bars = ax.barh(
            data[category_column].astype(str),
            data[profit_column],
        )

        self._add_values(
            ax,
            bars,
            fmt="{:,.0f}",
        )

        ax.axvline(
            0,
            linewidth=1,
        )

        self._format_axis(
            ax,
            title=title,
            xlabel="Прибыль",
            ylabel="Категория",
        )

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # BRAND PERFORMANCE
    # ============================================================

    def brand_revenue(
        self,
        df,
        brand_column="brand",
        revenue_column="revenue",
        title="Выручка по брендам",
        limit=15,
        show=True,
    ):
        """Выручка по брендам."""

        self._check_columns(
            df,
            [
                brand_column,
                revenue_column,
            ],
        )

        data = (
            df.copy()
            .sort_values(
                revenue_column,
                ascending=False,
            )
            .head(limit)
            .sort_values(
                revenue_column
            )
        )

        fig, ax = self._create_figure()

        bars = ax.barh(
            data[brand_column].astype(str),
            data[revenue_column],
        )

        self._add_values(
            ax,
            bars,
            fmt="{:,.0f}",
        )

        self._format_axis(
            ax,
            title=title,
            xlabel="Выручка",
            ylabel="Бренд",
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
        value_column="value",
        title="ABC-анализ",
        show=True,
    ):
        """
        Показывает вклад классов A/B/C
        в общий показатель.
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
            fmt="{:,.0f}",
        )

        self._format_axis(
            ax,
            title=title,
            xlabel="ABC-класс",
            ylabel="Значение",
        )

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # ABC VALUE SHARE
    # ============================================================

    def abc_value_share(
        self,
        df,
        class_column="abc_class",
        value_column="value",
        title="Доля результата по ABC-классам",
        show=True,
    ):
        """Процент результата каждого ABC-класса."""

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
            fmt="{:.1f}%",
        )

        self._format_axis(
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
    # PARETO
    # ============================================================

    def pareto(
        self,
        df,
        item_column="name",
        value_column="revenue",
        title="Pareto-анализ",
        limit=None,
        show=True,
    ):
        """
        Pareto-график:

            столбцы = значение товара;
            линия = накопительная доля.
        """

        self._check_columns(
            df,
            [
                item_column,
                value_column,
            ],
        )

        data = (
            df.copy()
            .sort_values(
                value_column,
                ascending=False,
            )
        )

        if limit is not None:
            data = data.head(limit)

        data[value_column] = pd.to_numeric(
            data[value_column],
            errors="coerce",
        )

        data = data.dropna(
            subset=[value_column]
        )

        total = data[value_column].sum()

        if total != 0:
            data["cumulative_share"] = (
                data[value_column]
                .cumsum()
                / total
                * 100
            )
        else:
            data["cumulative_share"] = 0

        fig, ax = self._create_figure()

        x = np.arange(
            len(data)
        )

        ax.bar(
            x,
            data[value_column],
        )

        ax.set_xticks(x)
        ax.set_xticklabels(
            data[item_column].astype(str),
            rotation=45,
            ha="right",
        )

        ax2 = ax.twinx()

        ax2.plot(
            x,
            data["cumulative_share"],
            marker="o",
            linewidth=2,
        )

        ax2.axhline(
            80,
            linestyle="--",
            linewidth=1,
        )

        ax2.set_ylabel(
            "Накопительная доля, %"
        )

        ax2.set_ylim(
            0,
            105,
        )

        self._format_axis(
            ax,
            title=title,
            xlabel="Товар",
            ylabel="Значение",
        )

        fig.tight_layout()

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # SALES DISTRIBUTION
    # ============================================================

    def revenue_distribution(
        self,
        df,
        revenue_column="revenue",
        bins=20,
        title="Распределение выручки",
        show=True,
    ):
        """Гистограмма распределения выручки."""

        self._check_columns(
            df,
            [revenue_column],
        )

        values = pd.to_numeric(
            df[revenue_column],
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

        self._format_axis(
            ax,
            title=title,
            xlabel="Выручка",
            ylabel="Количество",
        )

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # PROFIT DISTRIBUTION
    # ============================================================

    def profit_distribution(
        self,
        df,
        profit_column="profit",
        bins=20,
        title="Распределение прибыли",
        show=True,
    ):
        """Гистограмма распределения прибыли."""

        self._check_columns(
            df,
            [profit_column],
        )

        values = pd.to_numeric(
            df[profit_column],
            errors="coerce",
        ).dropna()

        fig, ax = self._create_figure()

        ax.hist(
            values,
            bins=bins,
        )

        ax.axvline(
            0,
            linestyle="--",
            linewidth=2,
        )

        self._format_axis(
            ax,
            title=title,
            xlabel="Прибыль",
            ylabel="Количество",
        )

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # REVENUE VS UNITS
    # ============================================================

    def revenue_vs_units(
        self,
        df,
        units_column="units_sold",
        revenue_column="revenue",
        title="Количество продаж и выручка",
        show=True,
    ):
        """
        Scatter:

            X = количество единиц;
            Y = выручка.
        """

        self._check_columns(
            df,
            [
                units_column,
                revenue_column,
            ],
        )

        data = self._prepare_numeric(
            df,
            [
                units_column,
                revenue_column,
            ],
        )

        data = data.dropna(
            subset=[
                units_column,
                revenue_column,
            ]
        )

        fig, ax = self._create_figure()

        ax.scatter(
            data[units_column],
            data[revenue_column],
            alpha=0.7,
        )

        self._format_axis(
            ax,
            title=title,
            xlabel="Продано единиц",
            ylabel="Выручка",
        )

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # ROLLING REVENUE
    # ============================================================

    def rolling_revenue(
        self,
        df,
        date_column="month",
        revenue_column="revenue",
        window=3,
        title="Скользящая средняя выручки",
        show=True,
    ):
        """
        Фактическая выручка +
        скользящее среднее.
        """

        self._check_columns(
            df,
            [
                date_column,
                revenue_column,
            ],
        )

        data = df.copy()

        data[date_column] = pd.to_datetime(
            data[date_column],
            errors="coerce",
        )

        data[revenue_column] = pd.to_numeric(
            data[revenue_column],
            errors="coerce",
        )

        data = (
            data
            .dropna(
                subset=[
                    date_column,
                    revenue_column,
                ]
            )
            .sort_values(date_column)
        )

        data["rolling_mean"] = (
            data[revenue_column]
            .rolling(window)
            .mean()
        )

        fig, ax = self._create_figure()

        ax.plot(
            data[date_column],
            data[revenue_column],
            marker="o",
            label="Выручка",
        )

        ax.plot(
            data[date_column],
            data["rolling_mean"],
            linewidth=3,
            label=f"MA {window}",
        )

        ax.legend()

        self._format_axis(
            ax,
            title=title,
            xlabel="Дата",
            ylabel="Выручка",
        )

        fig.autofmt_xdate()

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # YEAR COMPARISON
    # ============================================================

    def compare_years(
        self,
        df,
        month_column="month",
        year_column="year",
        value_column="revenue",
        title="Сравнение продаж по годам",
        show=True,
    ):
        """
        Сравнить месячную выручку нескольких лет.
        """

        self._check_columns(
            df,
            [
                month_column,
                year_column,
                value_column,
            ],
        )

        data = self._prepare_numeric(
            df,
            [
                month_column,
                year_column,
                value_column,
            ],
        )

        fig, ax = self._create_figure()

        for year, group in data.groupby(
            year_column
        ):
            group = group.sort_values(
                month_column
            )

            ax.plot(
                group[month_column],
                group[value_column],
                marker="o",
                label=str(int(year)),
            )

        ax.legend()

        self._format_axis(
            ax,
            title=title,
            xlabel="Месяц",
            ylabel="Выручка",
        )

        ax.set_xticks(
            range(1, 13)
        )

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # PRODUCT MATRIX
    # ============================================================

    def product_performance_matrix(
        self,
        df,
        revenue_column="revenue",
        profit_column="profit",
        title="Матрица эффективности товаров",
        show=True,
    ):
        """
        Матрица:

            X = выручка
            Y = прибыль

        Позволяет увидеть:

            высокий revenue + высокий profit
            высокий revenue + низкий profit
            низкий revenue + высокий profit
            низкий revenue + низкий profit
        """

        self._check_columns(
            df,
            [
                revenue_column,
                profit_column,
            ],
        )

        data = self._prepare_numeric(
            df,
            [
                revenue_column,
                profit_column,
            ],
        )

        data = data.dropna(
            subset=[
                revenue_column,
                profit_column,
            ]
        )

        revenue_median = (
            data[revenue_column].median()
        )

        profit_median = (
            data[profit_column].median()
        )

        fig, ax = self._create_figure()

        ax.scatter(
            data[revenue_column],
            data[profit_column],
            alpha=0.7,
        )

        ax.axvline(
            revenue_median,
            linestyle="--",
            linewidth=1,
        )

        ax.axhline(
            profit_median,
            linestyle="--",
            linewidth=1,
        )

        self._format_axis(
            ax,
            title=title,
            xlabel="Выручка",
            ylabel="Прибыль",
        )

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # KPI CARD
    # ============================================================

    def kpi_figure(
        self,
        title,
        value,
        subtitle=None,
        show=True,
    ):
        """
        Создать простую KPI-карточку
        средствами matplotlib.
        """

        fig = plt.figure(
            figsize=(6, 3),
            dpi=self.dpi,
        )

        ax = fig.add_axes(
            [
                0,
                0,
                1,
                1,
            ]
        )

        ax.axis("off")

        ax.text(
            0.5,
            0.65,
            str(title),
            ha="center",
            va="center",
            fontsize=15,
            fontweight="bold",
        )

        ax.text(
            0.5,
            0.40,
            str(value),
            ha="center",
            va="center",
            fontsize=28,
        )

        if subtitle:
            ax.text(
                0.5,
                0.18,
                str(subtitle),
                ha="center",
                va="center",
                fontsize=10,
            )

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # SALES DASHBOARD
    # ============================================================

    def dashboard(
        self,
        summary,
        monthly_df,
        top_products_df,
        category_df=None,
        show=True,
    ):
        """
        Создать общий sales dashboard.

        ВАЖНО:
        dashboard использует несколько Axes,
        в отличие от обычных методов класса.
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
        # REVENUE
        # --------------------------------------------------------

        ax1 = fig.add_subplot(
            grid[0, 0]
        )

        if not monthly_df.empty:

            data = monthly_df.copy()

            if "date" in data.columns:
                date_column = "date"
            else:
                date_column = "month"

            data[date_column] = pd.to_datetime(
                data[date_column],
                errors="coerce",
            )

            data["revenue"] = pd.to_numeric(
                data["revenue"],
                errors="coerce",
            )

            data = data.dropna(
                subset=[
                    date_column,
                    "revenue",
                ]
            )

            ax1.plot(
                data[date_column],
                data["revenue"],
                marker="o",
            )

            ax1.set_title(
                "Динамика выручки",
                fontweight="bold",
            )

            ax1.grid(
                True,
                alpha=0.25,
            )

        # --------------------------------------------------------
        # TOP PRODUCTS
        # --------------------------------------------------------

        ax2 = fig.add_subplot(
            grid[0, 1]
        )

        if not top_products_df.empty:

            data = (
                top_products_df
                .copy()
                .sort_values(
                    "revenue"
                )
            )

            ax2.barh(
                data["name"].astype(str),
                data["revenue"],
            )

            ax2.set_title(
                "Топ товаров",
                fontweight="bold",
            )

            ax2.grid(
                True,
                axis="x",
                alpha=0.25,
            )

        # --------------------------------------------------------
        # CATEGORIES
        # --------------------------------------------------------

        ax3 = fig.add_subplot(
            grid[1, 0]
        )

        if (
            category_df is not None
            and not category_df.empty
        ):

            data = (
                category_df
                .copy()
                .sort_values(
                    "revenue",
                    ascending=False,
                )
                .head(10)
                .sort_values(
                    "revenue"
                )
            )

            ax3.barh(
                data["category"].astype(str),
                data["revenue"],
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
            dict
        ):

            revenue = summary.get(
                "revenue",
                0,
            )

            orders = summary.get(
                "orders",
                0,
            )

            units = summary.get(
                "units_sold",
                0,
            )

            average_check = summary.get(
                "average_order_value",
                0,
            )

            ax4.text(
                0.5,
                0.82,
                "SALES KPI",
                ha="center",
                fontsize=18,
                fontweight="bold",
            )

            ax4.text(
                0.5,
                0.65,
                f"Выручка: {revenue:,.0f}",
                ha="center",
                fontsize=15,
            )

            ax4.text(
                0.5,
                0.50,
                f"Заказы: {orders:,.0f}",
                ha="center",
                fontsize=15,
            )

            ax4.text(
                0.5,
                0.35,
                f"Продано: {units:,.0f}",
                ha="center",
                fontsize=15,
            )

            ax4.text(
                0.5,
                0.20,
                f"Средний чек: {average_check:,.0f}",
                ha="center",
                fontsize=15,
            )

        fig.suptitle(
            "Sales Analytics Dashboard",
            fontsize=20,
            fontweight="bold",
        )

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # SAVE MULTIPLE FIGURES
    # ============================================================

    def save_figure(
        self,
        fig,
        path,
        dpi=200,
    ):
        """Сохранить готовый matplotlib Figure."""

        return self._save(
            fig,
            path,
            dpi=dpi,
        )

    # ============================================================
    # FINISH
    # ============================================================

    @staticmethod
    def _finish(
        fig,
        show=True,
    ):
        """
        Завершить построение.

        Возвращает Figure,
        чтобы его можно было:
            - показать;
            - сохранить;
            - встроить в GUI/dashboard.
        """

        fig.tight_layout()

        if show:
            plt.show()

        return fig

    # ============================================================
    # CLOSE
    # ============================================================

    @staticmethod
    def close(fig=None):
        """
        Закрыть Figure.

        Полезно при генерации большого количества
        графиков в batch-режиме.
        """

        if fig is None:
            plt.close("all")
        else:
            plt.close(fig)