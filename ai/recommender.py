import sqlite3
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
import os

# 1. Define Database Path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'instance', 'dokan.db')

def recommend_products(product_name):
    """
    Recommends similar products based on Name and Category using TF-IDF.
    """
    try:
        # 2. Connect to Database and fetch Inventory
        conn = sqlite3.connect(DB_PATH)
        # We need the product name and category to find similarities
        df = pd.read_sql_query("SELECT * FROM product", conn)
        conn.close()
    except Exception as e:
        print(f"Error fetching data: {e}")
        return []

    if df.empty:
        return []

    # 3. Preprocessing
    # Ensure text columns are strings and fill missing values
    df['name'] = df['name'].fillna('')
    df['category'] = df['category'].fillna('')
    
    # Create a 'content' column combining name and category for better matching
    df['content'] = df['name'] + ' ' + df['category']

    # 4. TF-IDF Vectorization
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(df['content'])

    # 5. Calculate Cosine Similarity
    cosine_sim = linear_kernel(tfidf_matrix, tfidf_matrix)

    # 6. Find the index of the product matching the input name
    # We use lowercase for case-insensitive matching
    # Create a mapping of Name -> Index
    indices = pd.Series(df.index, index=df['name'].str.lower()).drop_duplicates()
    
    product_name_lower = product_name.lower()
    
    if product_name_lower not in indices:
        return []

    idx = indices[product_name_lower]

    # Get similarity scores for this product
    sim_scores = list(enumerate(cosine_sim[idx]))

    # Sort the products based on similarity scores
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)

    # Get the scores of the 3 most similar products (ignoring itself at index 0)
    sim_scores = sim_scores[1:4]

    # Get the product indices
    product_indices = [i[0] for i in sim_scores]

    # Return the names of the recommended products
    return df['name'].iloc[product_indices].tolist()