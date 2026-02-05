import sqlite3
import pandas as pd
from textblob import TextBlob
import os

# 1. Define Database Path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'instance', 'dokan.db')

def analyze_sentiment():
    """
    Fetches customer feedback messages from the SQLite database
    and calculates the average sentiment polarity.
    """
    try:
        # 2. Connect to Database and fetch Feedback
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT message FROM feedback", conn)
        conn.close()
    except Exception as e:
        print(f"Error fetching feedback: {e}")
        return {"status": "Error", "score": 0}

    if df.empty:
        return {"status": "No Feedback", "score": 0}

    # 3. Analyze Sentiment using TextBlob
    # (Polarity ranges from -1.0 to 1.0)
    def get_polarity(text):
        try:
            return TextBlob(text).sentiment.polarity
        except:
            return 0.0

    df['polarity'] = df['message'].apply(get_polarity)
    
    # Calculate average
    avg_score = df['polarity'].mean()
    
    # Determine status label
    if avg_score > 0.1:
        status = "Positive"
    elif avg_score < -0.1:
        status = "Negative"
    else:
        status = "Neutral"

    return {
        "status": status, 
        "score": round(avg_score, 2),
        "count": len(df)
    }