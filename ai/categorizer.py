import sqlite3
import pandas as pd
import os
from sklearn.naive_bayes import MultinomialNB
from sklearn.feature_extraction.text import CountVectorizer

# 1. Define Database Path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'instance', 'dokan.db')

def predict_category(product_name):
    """
    Predicts the category of a product name using a simple Naive Bayes classifier
    trained on existing database data.
    """
    try:
        # 2. Connect to Database
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT name, category FROM product", conn)
        conn.close()
    except Exception as e:
        print(f"Error fetching data: {e}")
        return "Uncategorized"

    if df.empty:
        return "General"

    # 3. Prepare Data
    # Drop rows where category or name is missing
    df = df.dropna(subset=['name', 'category'])
    
    if len(df) < 2:
        return "General"

    X = df['name']
    y = df['category']

    # 4. Train Model (Simple NLP)
    vectorizer = CountVectorizer()
    X_vectorized = vectorizer.fit_transform(X)

    model = MultinomialNB()
    model.fit(X_vectorized, y)

    # 5. Predict
    input_vector = vectorizer.transform([product_name])
    prediction = model.predict(input_vector)

    return prediction[0]