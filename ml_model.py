import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.neighbors import NearestNeighbors
import pickle
import numpy as np

# --- 1. Load Data ---
try:
    # We focus on interactions to build the recommendation engine
    interactions_df = pd.read_csv('datasets/interactions.csv')
    products_df = pd.read_csv('datasets/products.csv')
    print("Data loaded successfully.")
except FileNotFoundError:
    print("Error: Could not find datasets/interactions.csv or datasets/products.csv.")
    print("Please ensure you have run the 'datasets/data.py' script first to generate the CSV files.")
    exit()

# --- 2. Data Preprocessing & Feature Engineering ---

# Create a unique list of user and product IDs
user_ids = interactions_df['user_id'].unique()
product_ids = interactions_df['product_id'].unique()

# Map IDs to contiguous indices for the matrix
user_to_index = {user_id: idx for idx, user_id in enumerate(user_ids)}
product_to_index = {product_id: idx for idx, product_id in enumerate(product_ids)}

# Create a relevance score for the Interaction Matrix
# We will count how many times a user interacted with a product
interaction_counts = interactions_df.groupby(['user_id', 'product_id']).size().reset_index(name='count')

# --- 3. Build User-Item Interaction Matrix ---
# The matrix will have users as rows and products as columns
num_users = len(user_ids)
num_products = len(product_ids)

user_item_matrix = np.zeros((num_users, num_products), dtype=np.int32)

for row in interaction_counts.itertuples():
    user_idx = user_to_index[row.user_id]
    product_idx = product_to_index[row.product_id]
    user_item_matrix[user_idx, product_idx] = row.count # Use interaction count as score

# Convert to a Compressed Sparse Row matrix for efficient computation
user_item_sparse_matrix = csr_matrix(user_item_matrix)
print(f"User-Item Matrix built: {user_item_sparse_matrix.shape}")


# --- 4. Train Item-Based Collaborative Filter Model ---
# We transpose the matrix to get Item-User matrix. We train the model
# on items to find which products are 'closest' (most similar) to each other.
item_user_sparse_matrix = user_item_sparse_matrix.T.tocsr()

# Use NearestNeighbors for Item-Item Similarity (Cosine distance)
model_knn = NearestNeighbors(
    metric='cosine', 
    algorithm='brute', 
    n_neighbors=20, # Number of similar products to find
    n_jobs=-1
)

print("Training kNN model...")
model_knn.fit(item_user_sparse_matrix)
print("Training complete.")


# --- 5. Save Model Assets ---
# We save the model, the product mappings, and the original interactions/products data
# for the FastAPI application to use.
model_assets = {
    'model': model_knn,
    'product_to_index': product_to_index,
    'index_to_product': {v: k for k, v in product_to_index.items()},
    'user_to_index': user_to_index,
    'index_to_user': {v: k for k, v in user_to_index.items()},
    'product_details': products_df.set_index('product_id').to_dict('index'),
    'user_item_matrix': user_item_sparse_matrix, # Keep the matrix for finding user history
}

with open('model.pkl', 'wb') as file:
    pickle.dump(model_assets, file)

print("\n--- ML Model Training Success ---")
print("Model assets saved to 'model.pkl'.")
print("You can now run 'main.py' to start the Flask service.")
