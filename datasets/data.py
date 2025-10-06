import pandas as pd
import numpy as np
from faker import Faker
import random
from datetime import datetime, timedelta
import os

# Initialize Faker for generating fake data
fake = Faker('en_NG') # Use Nigerian locale for more relevant names and locations

# Number of rows to generate
NUM_ROWS = 400

#
# 1. Users Table (users.csv)
#
users_data = {
    'user_id': range(1, NUM_ROWS + 1),
    'name': [fake.name() for _ in range(NUM_ROWS)],
    'role': [random.choice(['farmer', 'buyer']) for _ in range(NUM_ROWS)],
    'location': [fake.city() for _ in range(NUM_ROWS)],
    'email': [fake.email() for _ in range(NUM_ROWS)],
    'password': ['password123' for _ in range(NUM_ROWS)]
}
users_df = pd.DataFrame(users_data)
users_df.to_csv(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'datasets', 'users.csv'), index=False)
print("Generated users.csv with 400 rows.")


#
# 2. Products Table (products.csv)
#
products_data = {
    'product_id': range(1001, 1001 + NUM_ROWS),
    'farmer_id': [random.randint(1, NUM_ROWS) for _ in range(NUM_ROWS)],
    'crop_type': [random.choice(['maize', 'rice', 'yam', 'beans', 'cassava', 'millet', 'sorghum', 'potatoes']) for _ in range(NUM_ROWS)],
    'quantity_kg': [random.randint(50, 1000) for _ in range(NUM_ROWS)],
    'price_per_kg': [random.choice([150, 180, 200, 250, 300, 350, 400]) for _ in range(NUM_ROWS)],
    'harvest_date': [fake.date_between(start_date='-60d', end_date='-10d') for _ in range(NUM_ROWS)],
    'quality': [random.choice(['A', 'B', 'C']) for _ in range(NUM_ROWS)]
}
products_df = pd.DataFrame(products_data)
products_df.to_csv(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'datasets', 'products.csv'), index=False)
print("Generated products.csv with 400 rows.")


#
# 3. Interactions Table (interactions.csv)
#
interactions_data = {
    'interaction_id': range(1, NUM_ROWS + 1),
    'user_id': [random.randint(1, NUM_ROWS) for _ in range(NUM_ROWS)],
    'product_id': [random.randint(1001, 1001 + NUM_ROWS) for _ in range(NUM_ROWS)],
    'event_type': [random.choice(['view', 'view', 'view', 'click', 'buy']) for _ in range(NUM_ROWS)], # More views and clicks than buys
    'timestamp': [fake.date_time_between(start_date='-30d', end_date='now') for _ in range(NUM_ROWS)]
}
interactions_df = pd.DataFrame(interactions_data)
interactions_df.to_csv(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'datasets', 'interactions.csv'), index=False)
print("Generated interactions.csv with 400 rows.")


#
# 4. Transactions Table (transactions.csv)
#
# Create a valid list of buyers and products to ensure data integrity
buyers = users_df[users_df['role'] == 'buyer']['user_id'].tolist()
products = products_df['product_id'].tolist()

transactions_data = []
for i in range(1, NUM_ROWS + 1):
    buyer_id = random.choice(buyers)
    product_id = random.choice(products)
    quantity = random.randint(1, 50)
    
    # Look up the price_per_kg for the chosen product
    price_per_kg = products_df[products_df['product_id'] == product_id]['price_per_kg'].iloc[0]
    
    total_price = quantity * price_per_kg
    date = fake.date_between(start_date='-15d', end_date='now')
    
    transactions_data.append({
        'transaction_id': i,
        'buyer_id': buyer_id,
        'product_id': product_id,
        'quantity_bought': quantity,
        'total_price': total_price,
        'date': date
    })

transactions_df = pd.DataFrame(transactions_data)
transactions_df.to_csv(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'datasets', 'transactions.csv'), index=False)
print("Generated transactions.csv with 400 rows.")