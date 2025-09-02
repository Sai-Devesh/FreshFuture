import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os # Import the 'os' module to handle file paths and directories

print("Starting data generation...")

# --- Configuration ---
PRODUCTS = ["Chicken Breast", "Organic Bananas", "Gallon Milk", "Bagged Salad", "Artisan Bread"]
START_DATE = datetime(2018, 1, 1)
MONTHS_OF_DATA = 5 * 12  # 5 years
DATA_DIR = 'data' # Define the directory name

# --- Create Data Directory if it Doesn't Exist ---
# This is the key change: it ensures the 'data' folder is available.
os.makedirs(DATA_DIR, exist_ok=True)
print(f"Ensured data directory exists at: '{DATA_DIR}/'")

# --- 1. Generate Strategic Historical Data (5 years) ---
data = []
for i in range(MONTHS_OF_DATA):
    current_date = START_DATE + timedelta(days=i*30)
    month = current_date.month
    year = current_date.year
    
    # Seasonality (e.g., higher demand in summer/holidays)
    seasonality = 1.0
    if month in [6, 7, 11, 12]:
        seasonality = np.random.uniform(1.1, 1.3)
        
    for product in PRODUCTS:
        base_stock = np.random.randint(500, 2000)
        base_sales = np.random.randint(400, base_stock)

        # Simulate effects
        promotions = np.random.choice([0, 1], p=[0.8, 0.2])
        stocked_amount = int(base_stock * seasonality)
        
        # Add a local event simulator
        local_event = 0
        if month in [5, 8, 10]: # Assume months with potential holidays/events
             if np.random.rand() > 0.85: # 15% chance of a major event
                local_event = 1
                stocked_amount *= 1.2 # Event boosts demand

        # Waste is a function of overstocking and lack of promotions
        # MODIFIED: Lowered the base waste percentage for more realistic numbers
        waste_percentage = np.random.uniform(0.01, 0.05) 
        # MODIFIED: Made the overstock condition stricter and penalty smaller
        if (stocked_amount > base_sales * 1.3) and promotions == 0:
            waste_percentage *= 1.2 
        wasted_amount = int(stocked_amount * waste_percentage)
        
        data.append({
            "product_name": product,
            "month": month,
            "year": year,
            "promotions": promotions,
            "local_event": local_event,
            "seasonality_indicator": round(seasonality, 2),
            "historical_stock": stocked_amount,
            "historical_waste": wasted_amount
        })

historical_df = pd.DataFrame(data)
# Use os.path.join to create the correct file path
historical_file_path = os.path.join(DATA_DIR, 'historical_data.csv')
historical_df.to_csv(historical_file_path, index=False)
print(f"✅ Generated '{historical_file_path}' with {len(historical_df)} rows.")

# --- 2. Generate Tactical Training Data (for sell-through model) ---
tactical_data = []
for days in [7, 6, 5, 4, 3, 2, 1]:
    for ratio in np.linspace(0.5, 8.0, 10):
        # Logic: sell-through drops sharply as expiry nears and overstock increases
        sell_through = 0.95 * (1 / (ratio**0.5)) * (days / 7)
        sell_through = max(0, min(sell_through - np.random.uniform(0, 0.1), 1.0))
        tactical_data.append({
            "days_until_expiry": days,
            "stock_to_sales_ratio": round(ratio, 2),
            "sell_through_rate": round(sell_through, 2)
        })

tactical_df = pd.DataFrame(tactical_data)
# Use os.path.join for this file too
tactical_file_path = os.path.join(DATA_DIR, 'tactical_training_data.csv')
tactical_df.to_csv(tactical_file_path, index=False)
print(f"✅ Generated '{tactical_file_path}' with {len(tactical_df)} rows.")


# --- 3. Generate Current Inventory Snapshot ---
today = datetime.now()
current_inventory = [
    # --- Items that will be marked for DONATION (Expires in <= 2 days) ---
    {'product_id': 105, 'product_name': 'Artisan Bread', 'category': 'Bakery', 'avg_daily_sales': 40, 'current_stock': 30, 'expiry_date': (today + timedelta(days=1)).strftime('%Y-%m-%d'), 'price': 5.50},
    {'product_id': 104, 'product_name': 'Bagged Salad', 'category': 'Produce', 'avg_daily_sales': 60, 'current_stock': 80, 'expiry_date': (today + timedelta(days=2)).strftime('%Y-%m-%d'), 'price': 3.00},

    # --- Items that will be marked for FLASH SALE to create a 75/50/25 split ---
    # High stock ratio, near expiry -> 75% discount
    {'product_id': 101, 'product_name': 'Chicken Breast', 'category': 'Meat', 'avg_daily_sales': 25, 'current_stock': 180, 'expiry_date': (today + timedelta(days=3)).strftime('%Y-%m-%d'), 'price': 12.50},
    # Medium stock ratio, mid expiry -> 50% discount
    {'product_id': 102, 'product_name': 'Organic Bananas', 'category': 'Produce', 'avg_daily_sales': 50, 'current_stock': 150, 'expiry_date': (today + timedelta(days=5)).strftime('%Y-%m-%d'), 'price': 1.50},
    # Lower stock ratio, far expiry -> 25% discount
    {'product_id': 106, 'product_name': 'Greek Yogurt', 'category': 'Dairy', 'avg_daily_sales': 70, 'current_stock': 100, 'expiry_date': (today + timedelta(days=6)).strftime('%Y-%m-%d'), 'price': 2.50},

    # --- Item that is safe (Expires far out) ---
    {'product_id': 103, 'product_name': 'Gallon Milk', 'category': 'Dairy', 'avg_daily_sales': 100, 'current_stock': 120, 'expiry_date': (today + timedelta(days=9)).strftime('%Y-%m-%d'), 'price': 4.25}
]
current_inventory_df = pd.DataFrame(current_inventory)
# And finally, for the inventory file
inventory_file_path = os.path.join(DATA_DIR, 'current_inventory.csv')
current_inventory_df.to_csv(inventory_file_path, index=False)
print(f"✅ Generated '{inventory_file_path}' for today.")

print("\nData generation complete!")