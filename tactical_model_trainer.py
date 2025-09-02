import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import joblib
import os

print("--- Training Tactical Model (Sell-Through Rate) ---")

# Define paths
DATA_DIR = 'data'
MODEL_DIR = 'models'
DATA_FILE = os.path.join(DATA_DIR, 'tactical_training_data.csv')
MODEL_FILE = os.path.join(MODEL_DIR, 'sell_through_model.joblib')

# Create directories if they don't exist
os.makedirs(MODEL_DIR, exist_ok=True)

# 1. Load Data
try:
    df = pd.read_csv(DATA_FILE)
except FileNotFoundError:
    print(f"Error: '{DATA_FILE}' not found. Please run generate_data.py first.")
    exit()

# 2. Define Features and Target
X = df[['days_until_expiry', 'stock_to_sales_ratio']]
y = df['sell_through_rate']

# 3. Train the Model
print("Training Sell-Through Rate model...")
model = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=5)
model.fit(X, y)
joblib.dump(model, MODEL_FILE)
print(f"✅ Saved '{MODEL_FILE}'")

print("\nTactical model training complete.")