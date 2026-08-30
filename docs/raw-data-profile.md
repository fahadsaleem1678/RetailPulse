# Raw Data Profile: Cosmetics Ecommerce Events

Source: https://www.kaggle.com/datasets/mkechinov/ecommerce-events-history-in-cosmetics-shop

## Files

| File | Rows | Date Range | Size Bytes | Duplicate Rows |
| --- | ---: | --- | ---: | ---: |
| 2019-Dec.csv | 3533286 | 2019-12-01 00:00:00 to 2019-12-31 23:59:57 | 415302972 | 183860 |
| 2019-Nov.csv | 4635837 | 2019-11-01 00:00:02 to 2019-11-30 23:59:58 | 545839412 | 246693 |
| 2019-Oct.csv | 4102283 | 2019-10-01 00:00:00 to 2019-10-31 23:59:54 | 482542278 | 213155 |
| 2020-Feb.csv | 4156682 | 2020-02-01 00:00:01 to 2020-02-29 23:59:59 | 488799986 | 240290 |
| 2020-Jan.csv | 4264752 | 2020-01-01 00:00:00 to 2020-01-31 23:59:58 | 501792804 | 225100 |

## Header Check

Required columns: `event_time`, `event_type`, `product_id`, `category_id`, `category_code`, `brand`, `price`, `user_id`, `user_session`

| File | Missing Required Columns | Unexpected Columns |
| --- | --- | --- |
| 2019-Dec.csv | None | None |
| 2019-Nov.csv | None | None |
| 2019-Oct.csv | None | None |
| 2020-Feb.csv | None | None |
| 2020-Jan.csv | None | None |

## Event Type Distribution

| Event Type | Rows | Share |
| --- | ---: | ---: |
| cart | 5768333 | 27.88% |
| purchase | 1287007 | 6.22% |
| remove_from_cart | 3979679 | 19.23% |
| view | 9657821 | 46.67% |

Unexpected event types: None

## Null and Blank Rates

| Field | Missing Rows | Missing Share |
| --- | ---: | ---: |
| category_code | 20339246 | 98.29% |
| brand | 8757117 | 42.32% |
| user_session | 4598 | 0.02% |
| price | 0 | 0.00% |

## Price Quality

Minimum parsed price: -79.37
Maximum parsed price: 327.78
Unparseable price rows: 0
Negative price rows: 131

## Cardinality

| File | Distinct Users | Distinct Sessions |
| --- | ---: | ---: |
| 2019-Dec.csv | 370154 | 839812 |
| 2019-Nov.csv | 368232 | 942022 |
| 2019-Oct.csv | 399664 | 873960 |
| 2020-Feb.csv | 391055 | 931668 |
| 2020-Jan.csv | 410073 | 965351 |

## Phase 1 Gate

- Required headers are present for every profiled file.
- Event types are checked against `view`, `cart`, `remove_from_cart`, and `purchase`.
- Date coverage, duplicate rows, key null rates, price quality, users, and sessions are reported.
