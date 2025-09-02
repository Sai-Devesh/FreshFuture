import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import joblib
import os

print("--- Training Strategic Models (Stock & Waste) ---")

# Define paths
DATA_DIR = 'data'
MODEL_DIR = 'models'
DATA_FILE = os.path.join(DATA_DIR, 'historical_data.csv')
STOCK_MODEL_FILE = os.path.join(MODEL_DIR, 'stock_model.joblib')
WASTE_MODEL_FILE = os.path.join(MODEL_DIR, 'waste_model.joblib')

# Create directories if they don't exist
os.makedirs(MODEL_DIR, exist_ok=True)

# 1. Load Data
try:
    df = pd.read_csv(DATA_FILE)
    df = pd.get_dummies(df, columns=['product_name'], drop_first=True)
except FileNotFoundError:
    print(f"Error: '{DATA_FILE}' not found. Please run generate_data.py first.")
    exit()

# 2. Define Features and Targets
features = [col for col in df.columns if col not in ['historical_stock', 'historical_waste']]
X = df[features]
y_stock = df['historical_stock']
y_waste = df['historical_waste']

# 3. Train Stock Prediction Model
print("Training Recommended Stock model...")
stock_model = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=10)
stock_model.fit(X, y_stock)
joblib.dump(stock_model, STOCK_MODEL_FILE)
print(f"✅ Saved '{STOCK_MODEL_FILE}'")

# 4. Train Waste Prediction Model
print("Training Predicted Waste model...")
waste_model = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=10)
waste_model.fit(X, y_waste)
joblib.dump(waste_model, WASTE_MODEL_FILE)
print(f"✅ Saved '{WASTE_MODEL_FILE}'")

print("\nStrategic model training complete.")