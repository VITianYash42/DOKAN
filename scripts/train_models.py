import sys
import os
import sqlite3
import pandas as pd
import joblib
from sklearn.linear_model import LinearRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.feature_extraction.text import CountVectorizer
import numpy as np

# Setup paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'instance', 'dokan.db')
MODELS_DIR = os.path.join(BASE_DIR, 'models')

# Ensure models directory exists
os.makedirs(MODELS_DIR, exist_ok=True)

def train_sales_forecast():
    print("⏳ Training Sales Forecaster...")
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT date, sales FROM sale", conn)
        conn.close()

        if df.empty or len(df) < 2:
            print("⚠️ Not enough data to train Sales Forecaster.")
            return

        # Preprocessing
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.dropna(subset=['date'])
        daily_sales = df.groupby(df['date'].dt.date)['sales'].sum().reset_index()
        
        if len(daily_sales) < 2:
            print("⚠️ Not enough daily data points.")
            return

        # Features
        daily_sales['date_ordinal'] = pd.to_datetime(daily_sales['date']).apply(lambda x: x.toordinal())
        X = daily_sales[['date_ordinal']]
        y = daily_sales['sales']

        # Train
        model = LinearRegression()
        model.fit(X, y)

        # Save
        joblib.dump(model, os.path.join(MODELS_DIR, 'sales_model.pkl'))
        print("✅ Sales Forecaster saved to models/sales_model.pkl")

    except Exception as e:
        print(f"❌ Error training Sales Forecaster: {e}")

def train_categorizer():
    print("⏳ Training Categorizer...")
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT name, category FROM product", conn)
        conn.close()

        if df.empty:
            print("⚠️ No product data to train Categorizer.")
            return

        df = df.dropna(subset=['name', 'category'])
        X = df['name']
        y = df['category']

        # Vectorize
        vectorizer = CountVectorizer()
        X_vectorized = vectorizer.fit_transform(X)

        # Train
        model = MultinomialNB()
        model.fit(X_vectorized, y)

        # Save BOTH the model and the vectorizer (we need both to predict)
        joblib.dump(model, os.path.join(MODELS_DIR, 'categorizer_model.pkl'))
        joblib.dump(vectorizer, os.path.join(MODELS_DIR, 'vectorizer.pkl'))
        print("✅ Categorizer saved to models/")

    except Exception as e:
        print(f"❌ Error training Categorizer: {e}")

if __name__ == "__main__":
    print("🚀 Starting Model Training...")
    train_sales_forecast()
    train_categorizer()
    print("✨ Training Complete.")