# services/db_service.py

# Library Setup
import os
import sqlite3
import pandas as pd

# Automatic resolve absolute path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "BubbleTeaDB_2026.db")


# Fetches hourly order counts grouped by sales channel
def get_rush_hours_data() -> pd.DataFrame:
    # Code your query here
    # day_type: strftime('%w') returns the weekday as '0' (Sunday) .. '6' (Saturday),
    # so '0' and '6' are labelled 'Weekend' and every other day 'Weekday'.
    # It is added to GROUP BY so the dashboard callback can filter by it.
    query = """
        SELECT
            strftime('%H:00', order_time) AS hour_of_day,
            channel,
            CASE WHEN strftime('%w', order_time) IN ('0', '6')
                 THEN 'Weekend' ELSE 'Weekday' END AS day_type,
            COUNT(order_id) AS total_order
        FROM Orders
        GROUP BY hour_of_day, channel, day_type
        ORDER BY hour_of_day, channel, day_type;
    """

    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query(query, conn)
    return df


# Counts how many calendar days of each day_type have orders recorded.
# Used to show the denominator next to the chart: 6 weeks contain more
# weekdays than weekend days, so raw totals are not directly comparable.
def get_day_counts() -> pd.DataFrame:
    query = """
        SELECT
            CASE WHEN strftime('%w', order_time) IN ('0', '6')
                 THEN 'Weekend' ELSE 'Weekday' END AS day_type,
            COUNT(DISTINCT date(order_time)) AS n_days
        FROM Orders
        GROUP BY day_type;
    """

    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query(query, conn)
    return df
