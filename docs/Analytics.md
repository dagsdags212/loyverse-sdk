# Analytics

The analytics layer runs SQL queries over the local DuckDB warehouse produced by
[[DuckDB-Export]]. You can use it two ways:

- **Python:** `AnalyticsEngine` returns [Polars](https://pola.rs/) DataFrames you
  can analyze, plot, or export.
- **CLI:** `loyverse analytics <command>` prints the same metrics to the terminal
  (see [[CLI]]).

Both read from a DuckDB database, so **export your data first**:

```python
await client.export_to_duckdb("loyverse.duckdb")
```

## AnalyticsEngine

```python
from loyverse_sdk.analytics import AnalyticsEngine

engine = AnalyticsEngine("loyverse.duckdb")   # read-only by default

# Revenue over the last 30 days
df = engine.revenue.daily_revenue(days=30)

# RFM customer segmentation
rfm = engine.customers.rfm_analysis()

engine.close()
```

`AnalyticsEngine` opens the database read-only and raises `FileNotFoundError` if
the path does not exist (export first). It is also a context manager:

```python
with AnalyticsEngine("loyverse.duckdb") as engine:
    top = engine.products.top_items(limit=10)
```

The engine exposes eight typed modules, each returning Polars DataFrames.

### `engine.revenue`

| Method | Description |
|---|---|
| `daily_revenue(days=...)` | Revenue per day |
| `revenue_by_store(...)` | Revenue broken down by store |
| `revenue_growth(...)` | Period-over-period growth |
| `total_revenue(...)` | Aggregate revenue for a window |
| `total_revenue_by_month(...)` | Monthly revenue totals |
| `refund_rate(...)` | Share of refunded transactions |

### `engine.products`

| Method | Description |
|---|---|
| `revenue_by_category(...)` | Revenue grouped by category |
| `top_items(limit=...)` | Best-selling items |
| `items_per_transaction(...)` | Basket size / composition |
| `category_mix_trend(...)` | Category share over time |

### `engine.customers`

| Method | Description |
|---|---|
| `new_vs_returning(...)` | New vs. returning customer split |
| `rfm_analysis()` | Recency / Frequency / Monetary segmentation |
| `top_customers(...)` | Highest-spending customers |
| `unique_customers(...)` | Distinct customer counts |
| `retention_rate(...)` | Customer retention |
| `customer_visit_distribution(...)` | Visit-frequency distribution |

### `engine.employees`

| Method | Description |
|---|---|
| `revenue_by_employee(...)` | Revenue attributed per employee |
| `employee_daily_summary(...)` | Daily per-employee totals |
| `tip_by_employee(...)` | Tips collected per employee |

### `engine.operations`

| Method | Description |
|---|---|
| `peak_hours(...)` | Busiest hours of the day |
| `peak_days(...)` | Busiest days |
| `payment_method_split(...)` | Sales by payment method |
| `discount_analysis(...)` | Discount usage and impact |
| `tip_analysis(...)` | Tip totals and rates |
| `dining_option_split(...)` | Sales by dining option |

### `engine.time_series`

| Method | Description |
|---|---|
| `moving_average_revenue(...)` | Smoothed revenue trend |
| `week_over_week_growth(...)` | WoW growth |
| `monthly_summary(...)` | Monthly rollup |
| `day_over_day(...)` | DoD change |

### `engine.profitability`

| Method | Description |
|---|---|
| `gross_profit(...)` | Gross profit (requires item cost data) |
| `profit_by_category(...)` | Profit grouped by category |
| `profit_margins(...)` | Margins per item/category |
| `margin_trend(...)` | Margin over time |
| `overall_margin(...)` | Blended margin |
| `items_without_cost(...)` | Items missing cost data (skew profit metrics) |

### `engine.inventory`

| Method | Description |
|---|---|
| `turnover(...)` | Inventory turnover ratio |
| `stock_value(...)` | Current stock value |
| `total_inventory_value(...)` | Aggregate inventory value |
| `stock_value_by_store(...)` | Stock value per store |
| `low_stock(...)` | Items below a threshold |
| `items_never_sold(...)` | Dead stock |

## Working with results

Methods return Polars DataFrames, so you can chain Polars operations or hand the
data to other tools:

```python
df = engine.revenue.daily_revenue(days=90)

df.write_csv("daily_revenue.csv")        # to CSV
total = df["revenue"].sum()              # aggregate
recent = df.tail(7)                       # last 7 rows
```

## CLI equivalents

Every module maps to a `loyverse analytics` subcommand. Flags select the metric:

```bash
loyverse analytics revenue --days 30
loyverse analytics revenue --by-month --days 365
loyverse analytics products --top-n 10
loyverse analytics customers --rfm
loyverse analytics operations --payments
loyverse analytics profitability --margins
loyverse analytics inventory --low-stock
loyverse analytics time-series --monthly
```

Add `--format json` or `--format csv` to pipe results elsewhere. The database
path defaults to `LOYVERSE_DB_PATH`; pass `--db-path` to override. See [[CLI]]
for the full command tree.

## See also

- [[DuckDB-Export]] — populate the warehouse the engine reads from
- [[CLI]] — the `loyverse analytics` command reference
- [[Flat-File-Export]] — export raw query results instead of computed metrics
