import argparse

from services.sales_service import SalesService
from services.customer_service import CustomerService
from services.inventory_service import InventoryService
from services.logistics_service import LogisticsService

from visualization.logistics_charts import LogisticsCharts
from visualization.sales_charts import SalesCharts

# ============================================================
# ANALYTICS
# ============================================================

def run_sales_charts():
    from matplotlib.ticker import FuncFormatter

    service = SalesService()
    charts = SalesCharts()

    # ============================================================
    # ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ДЛЯ ОФОРМЛЕНИЯ ГРАФИКОВ
    # ============================================================

    def prepare_chart(fig):
        ax = fig.axes[0]

        # Убираем подписи значений с каждого столбца.
        # Иначе при большом количестве товаров получается каша.
        for text in ax.texts:
            text.remove()

        def format_value(value, _):
            value = abs(value)

            if value >= 1_000_000:
                return f"{value / 1_000_000:.0f} млн"

            if value >= 1_000:
                return f"{value / 1_000:.0f} тыс"

            return f"{value:.0f}"

        ax.xaxis.set_major_formatter(
            FuncFormatter(format_value)
        )

        ax.grid(
            axis="x",
            alpha=0.2
        )

        ax.set_axisbelow(True)

        fig.tight_layout()

        return fig


    # ============================================================
    # 1. ПРОДАЖИ — ТОП-20 ТОВАРОВ ПО ВЫРУЧКЕ
    # ============================================================

    products = service.get_product_profitability()

    sales_fig = charts.top_products(
        products,
        name_column="name",
        value_column="revenue",
        title="Топ-20 товаров по выручке",
        limit=20,
        horizontal=True,
        show=False,
    )

    sales_fig.set_size_inches(
        14,
        9
    )

    sales_fig = prepare_chart(
        sales_fig
    )

    charts.save_figure(
        sales_fig,
        "output/sales.png",
    )

    charts.close(
        sales_fig
    )


    # ============================================================
    # 2. ПРИБЫЛЬ — ТОП-20 ТОВАРОВ
    # ============================================================

    profit_fig = charts.profit_by_product(
        products,
        name_column="name",
        profit_column="profit",
        title="Топ-20 товаров по прибыли",
        limit=20,
        show=False,
    )

    profit_fig.set_size_inches(
        14,
        9
    )

    profit_fig = prepare_chart(
        profit_fig
    )

    charts.save_figure(
        profit_fig,
        "output/profit.png",
    )

    charts.close(
        profit_fig
    )


    # ============================================================
    # 3. ПРОДАЖИ — ВСЕ КАТЕГОРИИ
    # ============================================================

    categories = service.get_category_performance()

    categories_sales_fig = charts.category_revenue(
        categories,
        category_column="category",
        revenue_column="revenue",
        title="Выручка по категориям",
        limit=None,
        show=False,
    )

    categories_sales_fig.set_size_inches(
        14,
        8
    )

    categories_sales_fig = prepare_chart(
        categories_sales_fig
    )

    charts.save_figure(
        categories_sales_fig,
        "output/categories_sales.png",
    )

    charts.close(
        categories_sales_fig
    )


    # ============================================================
    # 4. ПРИБЫЛЬ — ВСЕ КАТЕГОРИИ
    # ============================================================

    categories_profit_fig = charts.category_profit(
        categories,
        category_column="category",
        profit_column="profit",
        title="Прибыль по категориям",
        limit=None,
        show=False,
    )

    categories_profit_fig.set_size_inches(
        14,
        8
    )

    categories_profit_fig = prepare_chart(
        categories_profit_fig
    )

    charts.save_figure(
        categories_profit_fig,
        "output/categories_profit.png",
    )

    charts.close(
        categories_profit_fig
    )


    # ============================================================
    # РЕЗУЛЬТАТ
    # ============================================================

    print("\n=== SALES CHARTS ===")
    print("Created:")
    print("  output/sales.png")
    print("  output/profit.png")
    print("  output/categories_sales.png")
    print("  output/categories_profit.png")


def run_sales():
    service = SalesService()

    result = service.get_sales_summary()

    print("\n=== SALES ===")

    for key, value in result.items():
        print(f"{key}: {value}")


def run_customers():
    service = CustomerService()

    result = service.get_customer_summary()

    print("\n=== CUSTOMERS ===")

    for key, value in result.items():
        print(f"{key}: {value}")


def run_inventory():
    service = InventoryService()

    result = service.get_inventory_summary()

    print("\n=== INVENTORY ===")

    for key, value in result.items():
        print(f"{key}: {value}")


def run_logistics():
    service = LogisticsService()

    result = service.get_logistics_summary()

    print("\n=== LOGISTICS ===")

    for key, value in result.items():
        print(f"{key}: {value}")


def run_all():
    print("\n=== SALES ===")

    try:
        result = SalesService().get_sales_summary()

        for key, value in result.items():
            print(f"{key}: {value}")

    except Exception as e:
        print(f"ERROR: {e}")


    print("\n=== CUSTOMERS ===")

    try:
        result = CustomerService().get_customer_summary()

        for key, value in result.items():
            print(f"{key}: {value}")

    except Exception as e:
        print(f"ERROR: {e}")


    print("\n=== INVENTORY ===")

    try:
        result = InventoryService().get_inventory_summary()

        for key, value in result.items():
            print(f"{key}: {value}")

    except Exception as e:
        print(f"ERROR: {e}")


    print("\n=== LOGISTICS ===")

    try:
        result = LogisticsService().get_logistics_summary()

        for key, value in result.items():
            print(f"{key}: {value}")

    except Exception as e:
        print(f"ERROR: {e}")


# ============================================================
# LOGISTICS CHARTS
# ============================================================

def run_logistics_charts():
    service = LogisticsService()
    charts = LogisticsCharts()


    # ========================================================
    # 1. ДИНАМИКА ДОСТАВОК
    # ========================================================

    monthly = service.get_monthly_logistics()

    charts.deliveries_by_period(
        monthly,
        date_column="date",
        count_column="shipments_count",
        title="Количество поставок по месяцам",
    )


    # ========================================================
    # 2. СРЕДНЕЕ ВРЕМЯ ДОСТАВКИ
    # ========================================================

    monthly_delivery = (
        service.get_monthly_delivery_time()
    )

    charts.delivery_time(
        monthly_delivery,
        date_column="date",
        time_column="average_delivery_days",
        title="Среднее время доставки",
    )


    # ========================================================
    # 3. РАСПРЕДЕЛЕНИЕ ДИСТАНЦИЙ
    # ========================================================

    distance = (
        service.get_distance_distribution()
    )

    charts.distance_distribution(
        distance,
        distance_column="average_distance",
        title="Распределение дистанций",
    )


    # ========================================================
    # 4. ЗАДЕРЖКИ
    # ========================================================

    delays = (
        service.get_delayed_shipments(
            expected_days=7
        )
    )

    charts.delay_distribution(
        delays,
        delay_column="delay_days",
        title="Распределение задержек",
    )


    # ========================================================
    # 5. СКЛАДЫ
    # ========================================================

    warehouses = (
        service.get_warehouse_performance()
    )

    charts.region_performance(
        warehouses,
        region_column="warehouse",
        value_column="shipments_count",
        title="Количество поставок по складам",
    )


    # ========================================================
    # 6. ТРАНСПОРТ
    # ========================================================

    vehicles = (
        service.get_vehicle_performance()
    )

    charts.carrier_performance(
        vehicles,
        carrier_column="vehicle_id",
        value_column="shipments_count",
        title="Загрузка транспорта",
    )


# ============================================================
# ALL CHARTS
# ============================================================

def run_all_charts():
    """
    Генерирует все доступные графики проекта.
    """

    print("\n=== GENERATING CHARTS ===")

    try:
        run_logistics_charts()

        print("\nAll charts generated successfully.")

    except Exception as e:
        print(f"\nERROR: {e}")


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Business Analytics Service"
    )

    parser.add_argument(
        "command",
        choices=[
            "sales",
            "customers",
            "inventory",
            "logistics",
            "all",
            "all_images",
            "sales_images",
        ],
        help="Analytics domain or chart generation",
    )

    args = parser.parse_args()


    commands = {
        "sales": run_sales,
        "customers": run_customers,
        "inventory": run_inventory,
        "logistics": run_logistics,
        "all": run_all,
        "all_images": run_all_charts,
        "sales_images": run_sales_charts,
    }


    commands[args.command]()


if __name__ == "__main__":
    main()