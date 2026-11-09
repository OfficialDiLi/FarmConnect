from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime
import pickle
import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.neighbors import NearestNeighbors
import openfoodfacts

app = Flask(__name__)
app.config['SECRET_KEY'] = 'put-your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'farm_marketplace.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Load recommendation model
def load_recommendation_model():
    try:
        model_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'model.pkl')
        with open(model_path, 'rb') as file:
            model_data = pickle.load(file)
        return model_data
    except FileNotFoundError:
        print("Model file not found. Please run ml_model.py to train the model.")
        return None

# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'farmer' or 'buyer'
    location = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    
    # Relationships
    products = db.relationship('Product', backref='farmer_user', lazy=True)
    interactions = db.relationship('Interaction', backref='user', lazy=True)
    transactions = db.relationship('Transaction', foreign_keys='Transaction.buyer_id', backref='buyer', lazy=True)

# Product model
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    crop_type = db.Column(db.String(100), nullable=False)
    quantity_kg = db.Column(db.Integer, nullable=False)  # quantity available
    price_per_kg = db.Column(db.Float, nullable=False)
    harvest_date = db.Column(db.Date, nullable=False)
    quality = db.Column(db.String(10), nullable=False)  # A, B, C
    description = db.Column(db.Text)
    image_url = db.Column(db.String(200), default='https://placehold.co/600x400?text=Crop+Image')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    interactions = db.relationship('Interaction', backref='product', lazy=True)
    transactions = db.relationship('Transaction', backref='product', lazy=True)

# Interaction model
class Interaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    event_type = db.Column(db.String(20), nullable=False)  # 'view', 'click', 'buy'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Transaction model
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity_bought = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')  # pending, completed, cancelled

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    # Get featured products
    products = Product.query.limit(8).all()
    return render_template('index.html', products=products)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        location = request.form['location']
        
        # Check if user already exists
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already registered')
            return redirect(url_for('register'))
        
        # Create new user
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(name=name, email=email, password=hashed_password, role=role, location=location)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'farmer':
        products = Product.query.filter_by(farmer_id=current_user.id).all()
        return render_template('farmer_dashboard.html', products=products)
    else:  # buyer
        # Get recommended products for the buyer
        recommendations = get_recommendations_for_user(current_user.id)
        return render_template('buyer_dashboard.html', recommendations=recommendations)

@app.route('/products')
def products():
    # Get query parameters for search and filtering
    search_query = request.args.get('search', '')
    crop_type = request.args.get('crop_type', '')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    quality = request.args.get('quality', '')
    
    # Start with all products
    query = Product.query
    
    # Apply search filter - search in crop_type field
    if search_query:
        query = query.filter(Product.crop_type.ilike(f'%{search_query}%'))
    
    # Apply crop type filter
    if crop_type:
        query = query.filter(Product.crop_type == crop_type)
    
    # Apply price filters
    if min_price is not None:
        query = query.filter(Product.price_per_kg >= min_price)
    if max_price is not None:
        query = query.filter(Product.price_per_kg <= max_price)
    
    # Apply quality filter
    if quality:
        query = query.filter(Product.quality == quality)
    
    # Execute query
    filtered_products = query.all()
    
    # Get unique crop types for the filter dropdown
    crop_types = [result[0] for result in db.session.query(Product.crop_type).distinct().all()]
    
    return render_template('products.html', products=filtered_products, crop_types=crop_types, search_query=search_query, crop_type_selected=crop_type, min_price=min_price, max_price=max_price, quality_selected=quality)

@app.route('/search')
def search():
    search_query = request.args.get('q', '')
    if search_query:
        # Search in both crop_type and description fields
        products = Product.query.filter(
            db.or_(
                Product.crop_type.ilike(f'%{search_query}%'),
                Product.description.ilike(f'%{search_query}%')
            )
        ).all()
    else:
        products = Product.query.all()
    
    # Get unique crop types for the filter dropdown
    crop_types = [result[0] for result in db.session.query(Product.crop_type).distinct().all()]
    return render_template('products.html', products=products, crop_types=crop_types, search_query=search_query, crop_type_selected='', min_price=None, max_price=None, quality_selected='')

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    
    # Fetch nutrition info from Open Food Facts
    nutrition_info = get_product_nutrition_info(product.crop_type)
    
    # Record the view interaction
    if current_user.is_authenticated:
        interaction = Interaction(user_id=current_user.id, product_id=product_id, event_type='view')
        db.session.add(interaction)
        db.session.commit()
    
    return render_template('product_detail.html', product=product, nutrition_info=nutrition_info)

@app.route('/buy/<int:product_id>', methods=['POST'])
@login_required
def buy_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    # Get quantity from form
    quantity = int(request.form.get('quantity', 1))
    
    # Check if enough quantity is available
    if quantity > product.quantity_kg:
        flash(f'Not enough quantity available. Only {product.quantity_kg} kg available.')
        return redirect(url_for('product_detail', product_id=product_id))
    
    # Calculate total price
    total_price = quantity * product.price_per_kg
    
    # Create transaction
    transaction = Transaction(
        buyer_id=current_user.id,
        product_id=product_id,
        quantity_bought=quantity,
        total_price=total_price
    )
    
    db.session.add(transaction)
    
    # Update product quantity
    product.quantity_kg -= quantity
    
    # If product quantity becomes 0, optionally mark as sold out or remove
    if product.quantity_kg <= 0:
        # For now, we'll just keep it but could add status field later
        pass
    
    db.session.commit()
    
    # Record the purchase interaction
    interaction = Interaction(
        user_id=current_user.id,
        product_id=product_id,
        event_type='buy'
    )
    db.session.add(interaction)
    db.session.commit()
    
    flash('Purchase completed successfully!')
    return redirect(url_for('product_detail', product_id=product_id))

def get_product_nutrition_info(crop_type):
    """Fetch nutrition and product information from Open Food Facts API"""
    try:
        # Clean the crop type to be more search-friendly
        search_term = crop_type.lower().strip()
        
        # Search for the product in Open Food Facts
        result = openfoodfacts.products.text_search(search_term)
        
        if result and 'products' in result and len(result['products']) > 0:
            # Get the first matching product
            product = result['products'][0]
            
            # Extract relevant information
            nutrition_info = {
                'product_name': product.get('product_name', crop_type),
                'generic_name': product.get('generic_name', ''),
                'brands': product.get('brands', 'Unknown'),
                'nutriments': product.get('nutriments', {}),
                'ingredients_text': product.get('ingredients_text', ''),
                'image_url': product.get('image_url', ''),
                'categories': product.get('categories', ''),
                'nutriscore_grade': product.get('nutriscore_grade', ''),
            }
            return nutrition_info
    except Exception as e:
        print(f"Error fetching nutrition info for {crop_type}: {e}")
        # Return None or default values in case of error
        pass
    
    return None

@app.route('/recommendations')
@login_required
def recommendations():
    # Get recommendations for current user
    recs = get_recommendations_for_user(current_user.id)
    return render_template('recommendations.html', recommendations=recs)

@app.route('/api/recommendations/<int:user_id>')
@login_required
def api_recommendations(user_id):
    """API endpoint to get recommendations for a user"""
    if current_user.id != user_id and current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    recommendations = get_recommendations_for_user(user_id)
    return jsonify({'recommendations': recommendations})

def get_recommendations_for_user(user_id):
    """Get product recommendations for a specific user using the ML model"""
    model_data = load_recommendation_model()
    
    # Get the user's interaction history
    user_interactions = Interaction.query.filter_by(user_id=user_id).all()
    
    # If no history, return popular products
    if not user_interactions:
        return get_popular_products()
    
    # If model is not available, use interaction-based recommendations
    if not model_data:
        print("Model file not found or invalid, using interaction-based recommendations")
        return get_interaction_based_recommendations(user_interactions)
    
    # Prepare data for recommendation
    try:
        # Get user's index in the model
        user_idx = model_data['user_to_index'].get(user_id)
        
        recommendations = set()
        
        # If user exists in the model, try to get recommendations
        if user_idx is not None:
            # Get the trained model and matrices
            model = model_data['model']
            user_item_matrix = model_data['user_item_matrix']
            
            # Get the user's interaction vector
            user_vector = user_item_matrix[user_idx]
            
            # Find items the user has interacted with (non-zero entries)
            user_interacted_item_indices = user_vector.nonzero()[1]
            
            if len(user_interacted_item_indices) > 0:
                # Get the item-user matrix for similarity calculation
                item_user_matrix = user_item_matrix.T.tocsr()
                
                # For each item the user interacted with, find similar items
                for item_idx in user_interacted_item_indices:
                    # Get similar items based on item-item similarity
                    # The model was trained on item-user matrix, so we find similar items
                    if item_idx < item_user_matrix.shape[0]:  # Check bounds
                        item_vector = item_user_matrix[item_idx]
                        
                        # Find similar items using the model
                        # Reshape the item vector if it has only one feature
                        if hasattr(item_vector, 'toarray'):
                            item_vector_array = item_vector.toarray().flatten()
                            if len(item_vector_array) == 1:
                                item_vector_reshaped = item_vector_array.reshape(1, -1)
                            else:
                                item_vector_reshaped = item_vector_array.reshape(1, -1)
                        else:
                            item_vector_reshaped = item_vector.reshape(1, -1)
                        
                        # Find similar items using the model
                        distances, indices = model.kneighbors(item_vector_reshaped, n_neighbors=min(10, item_user_matrix.shape[0]))
                        
                        # Add similar items to recommendations (excluding items the user already interacted with)
                        for idx in indices[0]:
                            if idx < len(model_data['index_to_product']):  # Check bounds
                                original_product_id = model_data['index_to_product'].get(idx)
                                if original_product_id and original_product_id not in [ui.product_id for ui in user_interactions]:
                                    recommendations.add(original_product_id)
        
        # Convert to product objects if we got model-based recommendations
        if recommendations:
            recommended_products = []
            for prod_id in list(recommendations)[:10]:  # Limit to 10
                product = Product.query.get(prod_id)
                if product:
                    recommended_products.append(product)
            
            # If we have recommendations from the model, return them
            if recommended_products:
                return [{'id': p.id, 'name': p.crop_type, 'price': p.price_per_kg, 'quantity': p.quantity_kg, 'quality': p.quality, 'description': p.description[:100] + '...' if p.description and len(p.description) > 100 else (p.description or ''), 'image_url': p.image_url} for p in recommended_products]
        
        # If user not in model or no recommendations from model, use content-based approach
        return get_interaction_based_recommendations(user_interactions)
        
    except Exception as e:
        print(f"Error in recommendation: {e}")
        import traceback
        traceback.print_exc()
        return get_popular_products()

def get_interaction_based_recommendations(user_interactions):
    """Get recommendations based on user interaction history when model is not available or user is new"""
    user_product_ids = [interaction.product_id for interaction in user_interactions]
    
    if user_product_ids:
        # Get the first product the user interacted with to find similar products
        sample_interaction = user_interactions[0]
        sample_product = Product.query.get(sample_interaction.product_id)
        
        if sample_product:
            # Find products of the same crop type or similar price range
            similar_products = Product.query.filter(
                Product.crop_type == sample_product.crop_type,
                Product.id.notin_(user_product_ids)
            ).limit(10).all()
            
            if similar_products:
                return [{'id': p.id, 'name': p.crop_type, 'price': p.price_per_kg, 'quantity': p.quantity_kg, 'quality': p.quality, 'description': p.description[:100] + '...' if p.description and len(p.description) > 100 else (p.description or ''), 'image_url': p.image_url} for p in similar_products]
    
    # Fallback to popular products
    return get_popular_products()

def get_popular_products():
    """Get popular products based on number of transactions or interactions"""
    # More sophisticated approach: rank by interactions and transactions
    from sqlalchemy import func
    
    # Get products with the most interactions
    popular_product_ids = db.session.query(
        Interaction.product_id, 
        func.count(Interaction.id).label('interaction_count')
    ).group_by(Interaction.product_id).order_by(func.count(Interaction.id).desc()).limit(20).all()
    
    product_ids = [pid[0] for pid in popular_product_ids]
    
    # Get the actual products, with fallback to all products if not enough popular ones
    if product_ids:
        products = Product.query.filter(Product.id.in_(product_ids)).all()
        # Sort by the order in popular_product_ids to maintain ranking
        products.sort(key=lambda p: product_ids.index(p.id))
    else:
        # If no interaction data, return latest products
        products = Product.query.order_by(Product.created_at.desc()).limit(10).all()
    
    return [{'id': p.id, 'name': p.crop_type, 'price': p.price_per_kg, 'quantity': p.quantity_kg, 'quality': p.quality, 'description': p.description[:100] + '...' if p.description and len(p.description) > 100 else (p.description or ''), 'image_url': p.image_url} for p in products]

@app.route('/sell', methods=['GET', 'POST'])
@login_required
def sell():
    if current_user.role != 'farmer':
        flash('Only farmers can sell products')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        crop_type = request.form['crop_type']
        quantity_kg = int(request.form['quantity_kg'])
        price_per_kg = float(request.form['price_per_kg'])
        harvest_date = datetime.strptime(request.form['harvest_date'], '%Y-%m-%d').date()
        quality = request.form['quality']
        description = request.form.get('description', '')
        image_url = request.form.get('image_url', f'https://placehold.co/600x400?text={crop_type}')
        
        new_product = Product(
            farmer_id=current_user.id,
            crop_type=crop_type,
            quantity_kg=quantity_kg,
            price_per_kg=price_per_kg,
            harvest_date=harvest_date,
            quality=quality,
            description=description,
            image_url=image_url
        )
        
        db.session.add(new_product)
        db.session.commit()
        
        flash('Product added successfully')
        return redirect(url_for('dashboard'))
    
    return render_template('sell.html')

@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    # Check if the current user is the farmer who owns this product
    if current_user.id != product.farmer_id or current_user.role != 'farmer':
        flash('You are not authorized to edit this product')
        return redirect(url_for('product_detail', product_id=product_id))
    
    if request.method == 'POST':
        # Update product details
        product.crop_type = request.form['crop_type']
        product.quantity_kg = int(request.form['quantity_kg'])
        product.price_per_kg = float(request.form['price_per_kg'])
        product.harvest_date = datetime.strptime(request.form['harvest_date'], '%Y-%m-%d').date()
        product.quality = request.form['quality']
        product.description = request.form.get('description', '')
        product.image_url = request.form.get('image_url', product.image_url)  # Keep existing if not provided
        
        db.session.commit()
        flash('Product updated successfully')
        return redirect(url_for('dashboard'))
    
    return render_template('sell.html', product=product)  # Reuse the sell template with product data

@app.route('/delete_product/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    # Check if the current user is the farmer who owns this product
    if current_user.id != product.farmer_id or current_user.role != 'farmer':
        flash('You are not authorized to delete this product')
        return redirect(url_for('product_detail', product_id=product_id))
    
    # Delete associated interactions and transactions first (due to foreign key constraints)
    Interaction.query.filter_by(product_id=product_id).delete()
    Transaction.query.filter_by(product_id=product_id).delete()
    
    # Now delete the product
    db.session.delete(product)
    db.session.commit()
    
    flash('Product deleted successfully')
    return redirect(url_for('dashboard'))

# Create tables
with app.app_context():
    db.create_all()
    
    # Check if we have sample data
    if User.query.count() == 0:
        # Add sample users if database is empty
        sample_farmer = User(
            name='John Farmer',
            email='farmer@example.com',
            password=generate_password_hash('password', method='pbkdf2:sha256'),
            role='farmer',
            location='Lagos'
        )
        sample_buyer = User(
            name='Jane Buyer',
            email='buyer@example.com',
            password=generate_password_hash('password', method='pbkdf2:sha256'),
            role='buyer',
            location='Abuja'
        )
        
        db.session.add(sample_farmer)
        db.session.add(sample_buyer)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)
