import sys
import os
import joblib

# Ensure we can import from the 'ai' folder
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai'))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, 'models')

print("--- STARTING AI SERIALIZATION TEST ---\n")

# 1. Check if Model Files Exist
print(f"Checking for models in {MODELS_DIR}...")
files = os.listdir(MODELS_DIR)
if 'sales_model.pkl' in files and 'categorizer_model.pkl' in files:
    print("✅ Model files found on disk.")
else:
    print(f"❌ Missing model files. Found: {files}")

# 2. Test Sales Forecast Loading
print("\nTesting Sales Forecast (Should load from disk)...")
try:
    from ai.sales_forecast import forecast_sales
    # Run a prediction
    result = forecast_sales()
    if result:
        print("✅ Sales Forecast functionality: OK")
    else:
        print("⚠️ Sales Forecast returned empty (might be low data, but didn't crash).")
except Exception as e:
    print(f"❌ Sales Forecast FAILED: {e}")

# 3. Test Categorizer Loading
print("\nTesting Categorizer (Should load from disk)...")
try:
    from ai.categorizer import predict_category
    # Check if the global cache was populated
    from ai.categorizer import _cached_model
    
    # Trigger the load
    cat = predict_category("Test Product")
    
    if _cached_model is not None:
        print("✅ Categorizer loaded from CACHE (Success!)")
    else:
        print("⚠️ Categorizer used Fallback (Training on the fly).")
        
    print(f"   Prediction for 'Test Product': {cat}")

except Exception as e:
    print(f"❌ Categorizer FAILED: {e}")

print("\n--- TEST COMPLETE ---")