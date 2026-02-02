import sqlite3
import pandas as pd
import os

# 1. Define the path to the database
# (Goes up one level from 'ai/' to root, then into 'instance/dokan.db')
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'instance', 'dokan.db')

def get_sales_data():
    """Helper to fetch sales data from SQLite"""
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT * FROM sale", conn)
        conn.close()
        return df
    except Exception as e:
        print(f"❌ Database Error: {e}")
        return pd.DataFrame()

def predict_stockout(items):
    stockout_predictions = []

    # 2. Load data from DB instead of CSV
    sales_data = get_sales_data()
    
    if sales_data.empty:
        return []

    # Iterate over each item in the provided list
    for item in items:
        try:
            item_id = item.get('id')
            stock = float(item.get('stock', 0))

            # Filter sales data for the item
            # Note: In CSV it was 'item_id', in DB it is also 'item_id' (we matched the schema)
            item_sales = sales_data[sales_data['item_id'] == item_id]

            # If no sales data for the item, skip it
            if item_sales.empty or stock <= 0:
                continue

            # Ensure sales column is numeric and handle errors
            item_sales['sales'] = pd.to_numeric(item_sales['sales'], errors='coerce').fillna(0)

            # Calculate average daily sales (mean of daily sales)
            # Group by 'date' string. (SQLite stores dates as strings)
            daily_sales = item_sales.groupby('date')['sales'].sum().mean()

            if daily_sales > 0:
                # Calculate days until stockout
                days_until_stockout = int(stock / daily_sales)
                stockout_predictions.append({
                    'item': item['name'],
                    'days_until_stockout': days_until_stockout
                })
                # print(f"Prediction for {item['name']}: {days_until_stockout} days") 

        except Exception as e:
            print(f"⚠️ Error processing item '{item.get('name')}': {e}")

    return stockout_predictions