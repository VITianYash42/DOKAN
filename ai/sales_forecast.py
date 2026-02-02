import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np
import sqlite3
import os
import joblib  # Added for loading models

# 1. Define Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'instance', 'dokan.db')
MODEL_PATH = os.path.join(BASE_DIR, 'models', 'sales_model.pkl')

def get_latest_date():
    """Helper to get the last recorded sale date from DB."""
    try:
        conn = sqlite3.connect(DB_PATH)
        # We only need the MAX date, which is very fast
        df = pd.read_sql_query("SELECT MAX(date) as last_date FROM sale", conn)
        conn.close()
        
        if not df.empty and df['last_date'].iloc[0]:
            return pd.to_datetime(df['last_date'].iloc[0])
    except Exception as e:
        print(f"DB Error: {e}")
    
    return pd.Timestamp.now() # Fallback to today

def forecast_sales():
    """
    Predicts sales for the next 7 days.
    Strategy: Load cached model -> Fallback to training if missing.
    """
    model = None
    
    # --- STRATEGY 1: LOAD SAVED MODEL (FAST) ---
    if os.path.exists(MODEL_PATH):
        try:
            model = joblib.load(MODEL_PATH)
            # print("✅ Using cached Sales Model")
        except Exception as e:
            print(f"⚠️ Error loading model: {e}")

    # --- STRATEGY 2: TRAIN ON THE FLY (FALLBACK) ---
    if model is None:
        # print("⚠️ Cached model not found. Training on the fly...")
        try:
            conn = sqlite3.connect(DB_PATH)
            df = pd.read_sql_query("SELECT date, sales FROM sale", conn)
            conn.close()

            if df.empty: return {}

            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            df = df.dropna(subset=['date'])
            daily_sales = df.groupby(df['date'].dt.date)['sales'].sum().reset_index()

            if len(daily_sales) < 2: return {}

            daily_sales['date_ordinal'] = pd.to_datetime(daily_sales['date']).apply(lambda x: x.toordinal())
            X = daily_sales[['date_ordinal']]
            y = daily_sales['sales']

            model = LinearRegression()
            model.fit(X, y)
        except Exception as e:
            print(f"❌ Training failed: {e}")
            return {}

    # --- PREDICTION PHASE ---
    try:
        # We predict starting from the day AFTER the last recorded sale
        last_date = get_latest_date()
        future_dates = [last_date + pd.Timedelta(days=i) for i in range(1, 8)]
        
        # Convert future dates to the format the model understands (ordinals)
        future_ordinals = np.array([d.toordinal() for d in future_dates]).reshape(-1, 1)
        
        predictions = model.predict(future_ordinals)
        
        # Format: { 'YYYY-MM-DD': 150.25 }
        forecast = {str(date.date()): round(pred, 2) for date, pred in zip(future_dates, predictions)}
        return forecast
        
    except Exception as e:
        print(f"❌ Prediction logic failed: {e}")
        return {}