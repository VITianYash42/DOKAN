import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np
import sqlite3
import os

# 1. Define Database Path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'instance', 'dokan.db')

def forecast_sales():
    """Predicts sales for the next 7 days using Linear Regression on DB data."""
    try:
        # 2. Connect to Database
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT date, sales FROM sale", conn)
        conn.close()
    except Exception as e:
        print(f"Error fetching data: {e}")
        return {}

    if df.empty:
        return {}

    # 3. Process Data
    # Convert string dates from DB to datetime objects
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date'])

    # Group by date to get total daily sales
    daily_sales = df.groupby(df['date'].dt.date)['sales'].sum().reset_index()
    
    # We need at least 2 days of data to make a trend line
    if len(daily_sales) < 2:
        return {}

    # Prepare data for Linear Regression (Dates must be numbers)
    daily_sales['date_ordinal'] = pd.to_datetime(daily_sales['date']).apply(lambda x: x.toordinal())
    
    X = daily_sales[['date_ordinal']]
    y = daily_sales['sales']

    # 4. Train Model
    model = LinearRegression()
    model.fit(X, y)

    # 5. Predict Next 7 Days
    last_date = pd.to_datetime(daily_sales['date'].max())
    future_dates = [last_date + pd.Timedelta(days=i) for i in range(1, 8)]
    future_ordinals = np.array([d.toordinal() for d in future_dates]).reshape(-1, 1)
    
    predictions = model.predict(future_ordinals)

    # Return result as a dictionary { 'YYYY-MM-DD': predicted_value }
    forecast = {str(date.date()): round(pred, 2) for date, pred in zip(future_dates, predictions)}
    
    return forecast