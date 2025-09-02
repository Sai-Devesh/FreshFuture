import pandas as pd
import joblib
from sklearn.ensemble import RandomForestRegressor
from datetime import datetime
import os

# --- Define Paths ---
MODEL_DIR = 'models'
DATA_DIR = 'data'

STOCK_MODEL_FILE = os.path.join(MODEL_DIR, 'stock_model.joblib')
WASTE_MODEL_FILE = os.path.join(MODEL_DIR, 'waste_model.joblib')
SELL_THROUGH_MODEL_FILE = os.path.join(MODEL_DIR, 'sell_through_model.joblib')

# --- Global Model Storage ---
MODELS = { "stock": None, "waste": None, "sell_through": None }
MODELS_LOADED = False

def load_models():
    """Loads all available models into memory and updates status."""
    global MODELS, MODELS_LOADED
    
    try:
        MODELS['stock'] = joblib.load(STOCK_MODEL_FILE)
        MODELS['waste'] = joblib.load(WASTE_MODEL_FILE)
    except FileNotFoundError:
        print("🟡 Strategic model files not found. They may need to be trained.")
        MODELS['stock'], MODELS['waste'] = None, None
    
    try:
        MODELS['sell_through'] = joblib.load(SELL_THROUGH_MODEL_FILE)
    except FileNotFoundError:
        print("🟡 Tactical model file not found. It may need to be trained.")
        MODELS['sell_through'] = None

    # Update global status if all models are present
    MODELS_LOADED = all(model is not None for model in MODELS.values())
    if MODELS_LOADED:
        print("✅ All AI models loaded successfully.")
    else:
        print("✅ Model loading complete. Some models may be pending training.")

# --- 1. STRATEGIC AI FUNCTIONS ---
def train_strategic_models():
    """Trains and saves the stock and waste prediction models."""
    try:
        df = pd.read_csv(os.path.join(DATA_DIR, 'historical_data.csv'))
        df = pd.get_dummies(df, columns=['product_name'], drop_first=True)
        features = [col for col in df.columns if col not in ['historical_stock', 'historical_waste']]
        X = df[features]
        
        stock_model = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=10)
        stock_model.fit(X, df['historical_stock'])
        joblib.dump(stock_model, STOCK_MODEL_FILE)

        waste_model = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=10)
        waste_model.fit(X, df['historical_waste'])
        joblib.dump(waste_model, WASTE_MODEL_FILE)
        
        return True, "Strategic models trained."
    except Exception as e:
        return False, str(e)

def run_strategic_prediction(products, target_month, target_year):
    if not MODELS['stock'] or not MODELS['waste']:
        return pd.DataFrame()

    data_to_predict = [{"month": target_month, "year": target_year, "promotions": 0, "local_event": 0, "seasonality_indicator": 1.1, "product_name": p} for p in products]
    df_predict = pd.DataFrame(data_to_predict)
    df_predict_encoded = pd.get_dummies(df_predict, columns=['product_name'])
    
    training_cols = MODELS['stock'].feature_names_in_
    df_predict_encoded = df_predict_encoded.reindex(columns=training_cols, fill_value=0)

    predicted_stock = MODELS['stock'].predict(df_predict_encoded)
    predicted_waste = MODELS['waste'].predict(df_predict_encoded)

    return pd.DataFrame({
        "Product": products,
        "Recommended Stock (Units)": [int(p) for p in predicted_stock],
        "Predicted Waste (Units)": [int(p) for p in predicted_waste]
    })

# --- 2. TACTICAL AI FUNCTIONS ---
def train_tactical_model():
    """Trains and saves the sell-through prediction model."""
    try:
        df = pd.read_csv(os.path.join(DATA_DIR, 'tactical_training_data.csv'))
        X = df[['days_until_expiry', 'stock_to_sales_ratio']]
        y = df['sell_through_rate']
        model = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=5)
        model.fit(X, y)
        joblib.dump(model, SELL_THROUGH_MODEL_FILE)
        return True, "Tactical model trained."
    except Exception as e:
        return False, str(e)

def get_tactical_discount(days_left, stock, avg_sales):
    if days_left < 0 or stock <= 0 or avg_sales <= 0 or not MODELS['sell_through']:
        return 0

    stock_ratio = stock / avg_sales
    input_data = pd.DataFrame([[days_left, stock_ratio]], columns=['days_until_expiry', 'stock_to_sales_ratio'])
    predicted_sell_through = MODELS['sell_through'].predict(input_data)[0]

    discount = 0.0
    if predicted_sell_through < 0.30: discount = 0.75
    elif predicted_sell_through < 0.60: discount = 0.50
    elif predicted_sell_through < 0.85: discount = 0.25

    return 0 if days_left > 7 else round(discount, 2)

def run_tactical_analysis(df_inventory):
    today = pd.Timestamp.now().normalize()
    df_inventory['expiry_date'] = pd.to_datetime(df_inventory['expiry_date'])
    df_inventory['days_until_expiry'] = (df_inventory['expiry_date'] - today).dt.days

    df_inventory['discount_rate'] = df_inventory.apply(lambda row: get_tactical_discount(row['days_until_expiry'], row['current_stock'], row['avg_daily_sales']), axis=1)
    df_inventory['recovered_revenue'] = df_inventory['current_stock'] * df_inventory['price'] * (1 - df_inventory['discount_rate'])

    flash_sale_items = df_inventory[(df_inventory['discount_rate'] > 0) & (df_inventory['days_until_expiry'] > 2)].copy()
    donation_items = df_inventory[df_inventory['days_until_expiry'] <= 2].copy()
    
    return flash_sale_items, donation_items

# --- Load any existing models on application startup ---
load_models()