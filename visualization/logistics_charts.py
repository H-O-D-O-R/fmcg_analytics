from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


class LogisticsCharts:
    """
    Visualization layer для аналитики логистики.

    Не работает с БД и SQL.
    Получает готовые pandas.DataFrame из LogisticsService.

    Основные графики:

        - доставки по периодам;
        - время доставки;
        - расстояния;
        - стоимость логистики;
        - стоимость на км;
        - стоимость на заказ;
        - эффективность перевозчиков;
        - эффективность маршрутов;
        - регионы;
        - задержки;
        - выполнение SLA;
        - загрузка перевозчиков;
        - распределение времени доставки;
        - распределение расстояний;
        - корреляция;
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
    def _add_values(
        ax,
        bars,
        fmt="{:.1f}",
    ):
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
                xytext=(0, 4),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=9,
            )

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
    # DELIVERIES BY PERIOD
    # ============================================================

    def deliveries_by_period(
        self,
        df,
        date_column="date",
        count_column="deliveries",
        title="Количество доставок",
        show=True,
    ):
        """
        Динамика количества доставок.
        """

        self._check_columns(
            df,
            [
                date_column,
                count_column,
            ],
        )

        data = df.copy()

        data[date_column] = pd.to_datetime(
            data[date_column],
            errors="coerce",
        )

        data[count_column] = pd.to_numeric(
            data[count_column],
            errors="coerce",
        )

        data = (
            data
            .dropna(
                subset=[
                    date_column,
                    count_column,
                ]
            )
            .sort_values(date_column)
        )

        fig, ax = self._create_figure()

        ax.plot(
            data[date_column],
            data[count_column],
            marker="o",
            linewidth=2,
        )

        self._format(
            ax,
            title=title,
            xlabel="Дата",
            ylabel="Количество доставок",
        )

        fig.autofmt_xdate()

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # DELIVERY TIME
    # ============================================================

    def delivery_time(
        self,
        df,
        date_column="date",
        time_column="delivery_time",
        title="Среднее время доставки",
        show=True,
    ):
        """
        Динамика времени доставки.
        """

        self._check_columns(
            df,
            [
                date_column,
                time_column,
            ],
        )

        data = df.copy()

        data[date_column] = pd.to_datetime(
            data[date_column],
            errors="coerce",
        )

        data[time_column] = pd.to_numeric(
            data[time_column],
            errors="coerce",
        )

        data = (
            data
            .dropna(
                subset=[
                    date_column,
                    time_column,
                ]
            )
            .sort_values(date_column)
        )

        fig, ax = self._create_figure()

        ax.plot(
            data[date_column],
            data[time_column],
            marker="o",
        )

        ax.axhline(
            data[time_column].mean(),
            linestyle="--",
            label="Среднее",
        )

        ax.legend()

        self._format(
            ax,
            title=title,
            xlabel="Дата",
            ylabel="Время доставки",
        )

        fig.autofmt_xdate()

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # DELIVERY TIME DISTRIBUTION
    # ============================================================

    def delivery_time_distribution(
        self,
        df,
        time_column="delivery_time",
        bins=20,
        title="Распределение времени доставки",
        show=True,
    ):
        """
        Гистограмма времени доставки.
        """

        self._check_columns(
            df,
            [time_column],
        )

        values = pd.to_numeric(
            df[time_column],
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
            xlabel="Время доставки",
            ylabel="Количество",
        )

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # DISTANCE DISTRIBUTION
    # ============================================================

    def distance_distribution(
        self,
        df,
        distance_column="distance_km",
        bins=20,
        title="Распределение расстояний",
        show=True,
    ):
        """
        Распределение пройденных расстояний.
        """

        self._check_columns(
            df,
            [distance_column],
        )

        values = pd.to_numeric(
            df[distance_column],
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

        ax.legend()

        self._format(
            ax,
            title=title,
            xlabel="Расстояние, км",
            ylabel="Количество маршрутов",
        )

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # DISTANCE BY ROUTE
    # ============================================================

    def distance_by_route(
        self,
        df,
        route_column="route",
        distance_column="distance_km",
        title="Расстояние по маршрутам",
        limit=15,
        show=True,
    ):
        """
        Топ маршрутов по расстоянию.
        """

        self._check_columns(
            df,
            [
                route_column,
                distance_column,
            ],
        )

        data = (
            df.copy()
            .sort_values(
                distance_column,
                ascending=False,
            )
            .head(limit)
            .sort_values(
                distance_column
            )
        )

        fig, ax = self._create_figure()

        bars = ax.barh(
            data[route_column].astype(str),
            data[distance_column],
        )

        self._add_values(
            ax,
            bars,
            "{:.1f}",
        )

        self._format(
            ax,
            title=title,
            xlabel="Расстояние, км",
            ylabel="Маршрут",
        )

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # LOGISTICS COST
    # ============================================================

    def logistics_cost(
        self,
        df,
        date_column="date",
        cost_column="logistics_cost",
        title="Стоимость логистики",
        show=True,
    ):
        """
        Динамика затрат на логистику.
        """

        self._check_columns(
            df,
            [
                date_column,
                cost_column,
            ],
        )

        data = df.copy()

        data[date_column] = pd.to_datetime(
            data[date_column],
            errors="coerce",
        )

        data[cost_column] = pd.to_numeric(
            data[cost_column],
            errors="coerce",
        )

        data = (
            data
            .dropna(
                subset=[
                    date_column,
                    cost_column,
                ]
            )
            .sort_values(date_column)
        )

        fig, ax = self._create_figure()

        ax.plot(
            data[date_column],
            data[cost_column],
            marker="o",
        )

        self._format(
            ax,
            title=title,
            xlabel="Дата",
            ylabel="Стоимость",
        )

        fig.autofmt_xdate()

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # COST BY ROUTE
    # ============================================================

    def cost_by_route(
        self,
        df,
        route_column="route",
        cost_column="logistics_cost",
        title="Стоимость логистики по маршрутам",
        limit=15,
        show=True,
    ):
        """Стоимость логистики по маршрутам."""

        self._check_columns(
            df,
            [
                route_column,
                cost_column,
            ],
        )

        data = (
            df.copy()
            .sort_values(
                cost_column,
                ascending=False,
            )
            .head(limit)
            .sort_values(
                cost_column
            )
        )

        fig, ax = self._create_figure()

        bars = ax.barh(
            data[route_column].astype(str),
            data[cost_column],
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
            ylabel="Маршрут",
        )

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # COST PER KM
    # ============================================================

    def cost_per_km(
        self,
        df,
        route_column="route",
        cost_column="logistics_cost",
        distance_column="distance_km",
        title="Стоимость одного километра",
        limit=15,
        show=True,
    ):
        """
        Расчет и визуализация:

            cost_per_km =
            logistics_cost / distance_km
        """

        self._check_columns(
            df,
            [
                route_column,
                cost_column,
                distance_column,
            ],
        )

        data = self._numeric(
            df,
            [
                cost_column,
                distance_column,
            ],
        )

        data = data[
            data[distance_column] > 0
        ].copy()

        data["cost_per_km"] = (
            data[cost_column]
            / data[distance_column]
        )

        data = (
            data
            .groupby(route_column)
            ["cost_per_km"]
            .mean()
            .reset_index()
            .sort_values(
                "cost_per_km",
                ascending=False,
            )
            .head(limit)
            .sort_values(
                "cost_per_km"
            )
        )

        fig, ax = self._create_figure()

        bars = ax.barh(
            data[route_column].astype(str),
            data["cost_per_km"],
        )

        self._add_values(
            ax,
            bars,
            "{:.2f}",
        )

        self._format(
            ax,
            title=title,
            xlabel="Стоимость / км",
            ylabel="Маршрут",
        )

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # COST PER DELIVERY
    # ============================================================

    def cost_per_delivery(
        self,
        df,
        date_column="date",
        cost_column="logistics_cost",
        deliveries_column="deliveries",
        title="Стоимость одной доставки",
        show=True,
    ):
        """
        Средняя стоимость одной доставки.
        """

        self._check_columns(
            df,
            [
                date_column,
                cost_column,
                deliveries_column,
            ],
        )

        data = self._numeric(
            df,
            [
                cost_column,
                deliveries_column,
            ],
        )

        data[date_column] = pd.to_datetime(
            data[date_column],
            errors="coerce",
        )

        data = data[
            data[deliveries_column] > 0
        ].copy()

        data["cost_per_delivery"] = (
            data[cost_column]
            / data[deliveries_column]
        )

        data = data.dropna(
            subset=[date_column]
        ).sort_values(
            date_column
        )

        fig, ax = self._create_figure()

        ax.plot(
            data[date_column],
            data["cost_per_delivery"],
            marker="o",
        )

        self._format(
            ax,
            title=title,
            xlabel="Дата",
            ylabel="Стоимость доставки",
        )

        fig.autofmt_xdate()

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # CARRIER PERFORMANCE
    # ============================================================

    def carrier_performance(
        self,
        df,
        carrier_column="carrier",
        value_column="deliveries",
        title="Эффективность перевозчиков",
        limit=15,
        show=True,
    ):
        """
        Сравнение перевозчиков
        по выбранному показателю.
        """

        self._check_columns(
            df,
            [
                carrier_column,
                value_column,
            ],
        )

        data = (
            df
            .groupby(carrier_column)[
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
                value_column
            )
        )

        fig, ax = self._create_figure()

        bars = ax.barh(
            data[carrier_column].astype(str),
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
            xlabel=value_column,
            ylabel="Перевозчик",
        )

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # CARRIER COST
    # ============================================================

    def carrier_cost(
        self,
        df,
        carrier_column="carrier",
        cost_column="logistics_cost",
        title="Затраты по перевозчикам",
        limit=15,
        show=True,
    ):
        """Затраты на каждого перевозчика."""

        self._check_columns(
            df,
            [
                carrier_column,
                cost_column,
            ],
        )

        data = (
            df
            .groupby(carrier_column)[
                cost_column
            ]
            .sum()
            .reset_index()
            .sort_values(
                cost_column,
                ascending=False,
            )
            .head(limit)
            .sort_values(
                cost_column
            )
        )

        fig, ax = self._create_figure()

        bars = ax.barh(
            data[carrier_column].astype(str),
            data[cost_column],
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
            ylabel="Перевозчик",
        )

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # CARRIER DELIVERY TIME
    # ============================================================

    def carrier_delivery_time(
        self,
        df,
        carrier_column="carrier",
        time_column="delivery_time",
        title="Среднее время доставки перевозчиков",
        limit=15,
        show=True,
    ):
        """Среднее время доставки по перевозчикам."""

        self._check_columns(
            df,
            [
                carrier_column,
                time_column,
            ],
        )

        data = (
            df
            .groupby(carrier_column)[
                time_column
            ]
            .mean()
            .reset_index()
            .sort_values(
                time_column,
                ascending=False,
            )
            .head(limit)
            .sort_values(
                time_column
            )
        )

        fig, ax = self._create_figure()

        bars = ax.barh(
            data[carrier_column].astype(str),
            data[time_column],
        )

        self._add_values(
            ax,
            bars,
            "{:.1f}",
        )

        self._format(
            ax,
            title=title,
            xlabel="Время доставки",
            ylabel="Перевозчик",
        )

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # REGION PERFORMANCE
    # ============================================================

    def region_performance(
        self,
        df,
        region_column="region",
        value_column="deliveries",
        title="Доставки по регионам",
        limit=15,
        show=True,
    ):
        """Количество доставок по регионам."""

        self._check_columns(
            df,
            [
                region_column,
                value_column,
            ],
        )

        data = (
            df
            .groupby(region_column)[
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
                value_column
            )
        )

        fig, ax = self._create_figure()

        bars = ax.barh(
            data[region_column].astype(str),
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
            xlabel=value_column,
            ylabel="Регион",
        )

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # REGION COST
    # ============================================================

    def region_cost(
        self,
        df,
        region_column="region",
        cost_column="logistics_cost",
        title="Логистические затраты по регионам",
        limit=15,
        show=True,
    ):
        """Затраты по регионам."""

        self._check_columns(
            df,
            [
                region_column,
                cost_column,
            ],
        )

        data = (
            df
            .groupby(region_column)[
                cost_column
            ]
            .sum()
            .reset_index()
            .sort_values(
                cost_column,
                ascending=False,
            )
            .head(limit)
            .sort_values(
                cost_column
            )
        )

        fig, ax = self._create_figure()

        bars = ax.barh(
            data[region_column].astype(str),
            data[cost_column],
        )

        self._add_values(
            ax,
            bars,
            "{:,.0f}",
        )

        self._format(
            ax,
            title=title,
            xlabel="Затраты",
            ylabel="Регион",
        )

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # DELAY ANALYSIS
    # ============================================================

    def delays(
        self,
        df,
        date_column="date",
        delay_column="delay_minutes",
        title="Динамика задержек",
        show=True,
    ):
        """Средняя задержка во времени."""

        self._check_columns(
            df,
            [
                date_column,
                delay_column,
            ],
        )

        data = df.copy()

        data[date_column] = pd.to_datetime(
            data[date_column],
            errors="coerce",
        )

        data[delay_column] = pd.to_numeric(
            data[delay_column],
            errors="coerce",
        )

        data = (
            data
            .dropna(
                subset=[
                    date_column,
                    delay_column,
                ]
            )
            .sort_values(date_column)
        )

        fig, ax = self._create_figure()

        ax.plot(
            data[date_column],
            data[delay_column],
            marker="o",
        )

        ax.axhline(
            0,
            linestyle="--",
            linewidth=1,
        )

        self._format(
            ax,
            title=title,
            xlabel="Дата",
            ylabel="Задержка, мин",
        )

        fig.autofmt_xdate()

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # DELAY DISTRIBUTION
    # ============================================================

    def delay_distribution(
        self,
        df,
        delay_column="delay_minutes",
        bins=20,
        title="Распределение задержек",
        show=True,
    ):
        """Распределение задержек."""

        self._check_columns(
            df,
            [delay_column],
        )

        values = pd.to_numeric(
            df[delay_column],
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

        self._format(
            ax,
            title=title,
            xlabel="Задержка, мин",
            ylabel="Количество",
        )

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # SLA PERFORMANCE
    # ============================================================

    def sla_performance(
        self,
        df,
        status_column="sla_status",
        title="Выполнение SLA",
        show=True,
    ):
        """
        Распределение:

            on_time
            delayed
            critical
        """

        self._check_columns(
            df,
            [status_column],
        )

        data = (
            df[status_column]
            .value_counts()
        )

        fig, ax = self._create_figure()

        bars = ax.bar(
            data.index.astype(str),
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
            xlabel="Статус SLA",
            ylabel="Количество",
        )

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # SLA PERCENTAGE
    # ============================================================

    def sla_percentage(
        self,
        df,
        status_column="sla_status",
        title="Доля выполнения SLA",
        show=True,
    ):
        """Процент доставок в рамках SLA."""

        self._check_columns(
            df,
            [status_column],
        )

        counts = (
            df[status_column]
            .value_counts()
        )

        total = counts.sum()

        if total:
            percentages = (
                counts
                / total
                * 100
            )
        else:
            percentages = counts * 0

        fig, ax = self._create_figure()

        bars = ax.bar(
            percentages.index.astype(str),
            percentages.values,
        )

        self._add_values(
            ax,
            bars,
            "{:.1f}%",
        )

        self._format(
            ax,
            title=title,
            xlabel="Статус SLA",
            ylabel="Доля, %",
        )

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # LOAD BY CARRIER
    # ============================================================

    def carrier_load(
        self,
        df,
        carrier_column="carrier",
        deliveries_column="deliveries",
        title="Загрузка перевозчиков",
        limit=15,
        show=True,
    ):
        """Загрузка перевозчиков."""

        self._check_columns(
            df,
            [
                carrier_column,
                deliveries_column,
            ],
        )

        data = (
            df
            .groupby(carrier_column)[
                deliveries_column
            ]
            .sum()
            .reset_index()
            .sort_values(
                deliveries_column,
                ascending=False,
            )
            .head(limit)
            .sort_values(
                deliveries_column
            )
        )

        fig, ax = self._create_figure()

        bars = ax.barh(
            data[carrier_column].astype(str),
            data[deliveries_column],
        )

        self._add_values(
            ax,
            bars,
            "{:,.0f}",
        )

        self._format(
            ax,
            title=title,
            xlabel="Количество доставок",
            ylabel="Перевозчик",
        )

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # DISTANCE VS TIME
    # ============================================================

    def distance_vs_delivery_time(
        self,
        df,
        distance_column="distance_km",
        time_column="delivery_time",
        title="Расстояние и время доставки",
        show=True,
    ):
        """
        Проверить зависимость времени доставки
        от расстояния.
        """

        self._check_columns(
            df,
            [
                distance_column,
                time_column,
            ],
        )

        data = self._numeric(
            df,
            [
                distance_column,
                time_column,
            ],
        )

        data = data.dropna(
            subset=[
                distance_column,
                time_column,
            ]
        )

        fig, ax = self._create_figure()

        ax.scatter(
            data[distance_column],
            data[time_column],
            alpha=0.7,
        )

        self._format(
            ax,
            title=title,
            xlabel="Расстояние, км",
            ylabel="Время доставки",
        )

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # DISTANCE VS COST
    # ============================================================

    def distance_vs_cost(
        self,
        df,
        distance_column="distance_km",
        cost_column="logistics_cost",
        title="Расстояние и стоимость",
        show=True,
    ):
        """
        Зависимость стоимости
        от расстояния.
        """

        self._check_columns(
            df,
            [
                distance_column,
                cost_column,
            ],
        )

        data = self._numeric(
            df,
            [
                distance_column,
                cost_column,
            ],
        )

        data = data.dropna(
            subset=[
                distance_column,
                cost_column,
            ]
        )

        fig, ax = self._create_figure()

        ax.scatter(
            data[distance_column],
            data[cost_column],
            alpha=0.7,
        )

        self._format(
            ax,
            title=title,
            xlabel="Расстояние, км",
            ylabel="Стоимость",
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
        title="Корреляция логистических показателей",
        show=True,
    ):
        """
        Тепловая карта корреляций.

        Используется только matplotlib,
        без seaborn.
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

        matrix = ax.imshow(
            correlation,
            aspect="auto",
        )

        fig.colorbar(
            matrix,
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
    # ROLLING DELIVERY TIME
    # ============================================================

    def rolling_delivery_time(
        self,
        df,
        date_column="date",
        time_column="delivery_time",
        window=7,
        title="Скользящее среднее времени доставки",
        show=True,
    ):
        """Скользящее среднее времени доставки."""

        self._check_columns(
            df,
            [
                date_column,
                time_column,
            ],
        )

        data = df.copy()

        data[date_column] = pd.to_datetime(
            data[date_column],
            errors="coerce",
        )

        data[time_column] = pd.to_numeric(
            data[time_column],
            errors="coerce",
        )

        data = (
            data
            .dropna(
                subset=[
                    date_column,
                    time_column,
                ]
            )
            .sort_values(date_column)
        )

        data["rolling_mean"] = (
            data[time_column]
            .rolling(window)
            .mean()
        )

        fig, ax = self._create_figure()

        ax.plot(
            data[date_column],
            data[time_column],
            alpha=0.5,
            label="Фактическое",
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
            ylabel="Время доставки",
        )

        fig.autofmt_xdate()

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # ROUTE EFFICIENCY
    # ============================================================

    def route_efficiency(
        self,
        df,
        route_column="route",
        distance_column="distance_km",
        time_column="delivery_time",
        title="Эффективность маршрутов",
        limit=15,
        show=True,
    ):
        """
        Эффективность маршрута:

            distance / time

        Чем выше показатель,
        тем выше средняя скорость прохождения маршрута.
        """

        self._check_columns(
            df,
            [
                route_column,
                distance_column,
                time_column,
            ],
        )

        data = self._numeric(
            df,
            [
                distance_column,
                time_column,
            ],
        )

        data = data[
            data[time_column] > 0
        ].copy()

        data["route_efficiency"] = (
            data[distance_column]
            / data[time_column]
        )

        data = (
            data
            .groupby(route_column)[
                "route_efficiency"
            ]
            .mean()
            .reset_index()
            .sort_values(
                "route_efficiency",
                ascending=False,
            )
            .head(limit)
            .sort_values(
                "route_efficiency"
            )
        )

        fig, ax = self._create_figure()

        bars = ax.barh(
            data[route_column].astype(str),
            data["route_efficiency"],
        )

        self._add_values(
            ax,
            bars,
            "{:.2f}",
        )

        self._format(
            ax,
            title=title,
            xlabel="Эффективность",
            ylabel="Маршрут",
        )

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # ROUTE MATRIX
    # ============================================================

    def route_performance_matrix(
        self,
        df,
        distance_column="distance_km",
        cost_column="logistics_cost",
        time_column="delivery_time",
        title="Матрица эффективности маршрутов",
        show=True,
    ):
        """
        Матрица:

            X = расстояние
            Y = стоимость

        Размер точки = время доставки.
        """

        self._check_columns(
            df,
            [
                distance_column,
                cost_column,
                time_column,
            ],
        )

        data = self._numeric(
            df,
            [
                distance_column,
                cost_column,
                time_column,
            ],
        ).dropna(
            subset=[
                distance_column,
                cost_column,
                time_column,
            ]
        )

        sizes = (
            np.maximum(
                data[time_column],
                0,
            )
            + 1
        ) * 5

        fig, ax = self._create_figure()

        ax.scatter(
            data[distance_column],
            data[cost_column],
            s=sizes,
            alpha=0.65,
        )

        ax.set_xlabel(
            "Расстояние, км"
        )

        ax.set_ylabel(
            "Стоимость"
        )

        self._format(
            ax,
            title=title,
        )

        return self._finish(
            fig,
            show,
        )

    # ============================================================
    # KPI FIGURE
    # ============================================================

    def kpi_figure(
        self,
        title,
        value,
        subtitle=None,
        show=True,
    ):
        """Отдельная KPI-карточка."""

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
    # LOGISTICS DASHBOARD
    # ============================================================

    def dashboard(
        self,
        summary,
        monthly_df,
        carrier_df=None,
        region_df=None,
        show=True,
    ):
        """
        Общий dashboard логистики.

        summary:
            dict с KPI.

        monthly_df:
            дата + показатели.

        carrier_df:
            перевозчики.

        region_df:
            регионы.
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
        # DELIVERY TIME / DELIVERIES
        # --------------------------------------------------------

        ax1 = fig.add_subplot(
            grid[0, 0]
        )

        if (
            monthly_df is not None
            and not monthly_df.empty
        ):

            data = monthly_df.copy()

            date_column = (
                "date"
                if "date" in data.columns
                else "month"
            )

            data[date_column] = pd.to_datetime(
                data[date_column],
                errors="coerce",
            )

            if "deliveries" in data.columns:

                data["deliveries"] = pd.to_numeric(
                    data["deliveries"],
                    errors="coerce",
                )

                data = data.dropna(
                    subset=[
                        date_column,
                        "deliveries",
                    ]
                )

                ax1.plot(
                    data[date_column],
                    data["deliveries"],
                    marker="o",
                )

                ax1.set_title(
                    "Динамика доставок",
                    fontweight="bold",
                )

                ax1.grid(
                    True,
                    alpha=0.25,
                )

        # --------------------------------------------------------
        # CARRIER
        # --------------------------------------------------------

        ax2 = fig.add_subplot(
            grid[0, 1]
        )

        if (
            carrier_df is not None
            and not carrier_df.empty
        ):

            data = (
                carrier_df
                .copy()
                .sort_values(
                    "deliveries",
                    ascending=False,
                )
                .head(10)
                .sort_values(
                    "deliveries"
                )
            )

            ax2.barh(
                data["carrier"].astype(str),
                data["deliveries"],
            )

            ax2.set_title(
                "Перевозчики",
                fontweight="bold",
            )

            ax2.grid(
                True,
                axis="x",
                alpha=0.25,
            )

        # --------------------------------------------------------
        # REGION
        # --------------------------------------------------------

        ax3 = fig.add_subplot(
            grid[1, 0]
        )

        if (
            region_df is not None
            and not region_df.empty
        ):

            data = (
                region_df
                .copy()
                .sort_values(
                    "deliveries",
                    ascending=False,
                )
                .head(10)
                .sort_values(
                    "deliveries"
                )
            )

            ax3.barh(
                data["region"].astype(str),
                data["deliveries"],
            )

            ax3.set_title(
                "Регионы",
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

            deliveries = summary.get(
                "deliveries",
                0,
            )

            total_cost = summary.get(
                "logistics_cost",
                0,
            )

            avg_time = summary.get(
                "average_delivery_time",
                0,
            )

            avg_distance = summary.get(
                "average_distance",
                0,
            )

            sla = summary.get(
                "sla_percent",
                0,
            )

            ax4.text(
                0.5,
                0.82,
                "LOGISTICS KPI",
                ha="center",
                fontsize=18,
                fontweight="bold",
            )

            ax4.text(
                0.5,
                0.66,
                f"Доставки: {deliveries:,.0f}",
                ha="center",
                fontsize=14,
            )

            ax4.text(
                0.5,
                0.51,
                f"Затраты: {total_cost:,.0f}",
                ha="center",
                fontsize=14,
            )

            ax4.text(
                0.5,
                0.36,
                f"Среднее время: {avg_time:.1f}",
                ha="center",
                fontsize=14,
            )

            ax4.text(
                0.5,
                0.21,
                f"SLA: {sla:.1f}%",
                ha="center",
                fontsize=14,
            )

        fig.suptitle(
            "Logistics Analytics Dashboard",
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
        """Сохранить график."""

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
        """Закрыть один или все графики."""

        if fig is None:
            plt.close("all")
        else:
            plt.close(fig)