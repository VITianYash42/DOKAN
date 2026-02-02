import sqlite3
import pandas as pd
import os
import joblib
from sklearn.naive_bayes import MultinomialNB
from sklearn.feature_extraction.text import CountVectorizer

# 1. Define Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'instance', 'dokan.db')
MODEL_PATH = os.path.join(BASE_DIR, 'models', 'categorizer_model.pkl')
VECTORIZER_PATH = os.path.join(BASE_DIR, 'models', 'vectorizer.pkl')

# Global cache to allow "Singleton" behavior (load once per app restart)
_cached_model = None
_cached_vectorizer = None

def load_resources():
    """Loads model and vectorizer from disk into memory."""
    global _cached_model, _cached_vectorizer
    
    if _cached_model and _cached_vectorizer:
        return _cached_model, _cached_vectorizer
        
    if os.path.exists(MODEL_PATH) and os.path.exists(VECTORIZER_PATH):
        try:
            _cached_model = joblib.load(MODEL_PATH)
            _cached_vectorizer = joblib.load(VECTORIZER_PATH)
            # print("✅ Loaded Categorizer from disk")
            return _cached_model, _cached_vectorizer
        except Exception as e:
            print(f"⚠️ Error loading resources: {e}")
            return None, None
    return None, None

def train_fallback():
    """Trains a temporary model if disk files are missing."""
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT name, category FROM product", conn)
        conn.close()
        
        if df.empty: return None, None
        
        df = df.dropna(subset=['name', 'category'])
        if len(df) < 2: return None, None

        vectorizer = CountVectorizer()
        X_vectorized = vectorizer.fit_transform(df['name'])
        model = MultinomialNB()
        model.fit(X_vectorized, df['category'])
        
        return model, vectorizer
    except:
        return None, None

def predict_category(product_name):
    """
    Predicts category using cached model -> disk model -> training fallback.
    """
    # 1. Try loading cached/disk resources
    model, vectorizer = load_resources()

    # 2. Fallback: Train on the fly
    if not model or not vectorizer:
        # print("⚠️ Cache miss. Training fallback...")
        model, vectorizer = train_fallback()

    if not model or not vectorizer:
        return "General"

    # 3. Predict
    try:
        input_vector = vectorizer.transform([product_name])
        prediction = model.predict(input_vector)
        return prediction[0]
    except Exception as e:
        print(f"Prediction error: {e}")
        return "General"