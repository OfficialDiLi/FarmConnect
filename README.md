# FarmConnect - Web-based Recommendation System for Farmers & Buyers

A web application that connects small/medium farmers and buyers (markets, aggregators, retailers) and provides personalized recommendations using machine learning.

## 🌾 Features

### For Farmers:
- User registration and authentication
- Product listing (crop type, quantity, price, quality, harvest date)
- Edit and delete product functionality
- Dashboard to manage products
- Personalized recommendations for buyers to target

### For Buyers:
- User registration and authentication
- Product browsing and search functionality
- Advanced filtering options (crop type, price range, quality)
- Product detail pages with nutritional information
- Purchase functionality
- Personalized product recommendations

### Recommendation System:
- Collaborative filtering based on user interactions
- Content-based recommendations
- Popular products fallback
- Integration with Open Food Facts API for nutritional data

## 🛠️ Tech Stack

- **Backend**: Python Flask
- **Frontend**: HTML, CSS (Bootstrap), JavaScript
- **Database**: SQLite
- **ML Library**: scikit-learn (Nearest Neighbors)
- **API**: Open Food Facts API

## 📋 Prerequisites

- Python 3.7+
- pip (Python package installer)

## 🚀 Installation

1. Clone the repository:
```bash
git clone https://github.com/OfficialDiLi/FarmConnect.git
cd FarmConnect
```

2. Create a virtual environment:
```bash
python -m venv .venv
# On Linux/Mac:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Generate the recommendation model:
```bash
python ml_model.py
```

5. Start the application:
```bash
python main.py
```

The application will be accessible at `http://localhost:5000`

## ⚠️ Platform Specific Notes

### Windows Users:
- Make sure you have Python 3.7+ installed
- Use PowerShell or Command Prompt for the installation steps
- Virtual environment activation command: `.venv\Scripts\activate`
- If you encounter issues with `openfoodfacts` package on Windows, you might need to install Microsoft C++ Build Tools

### Linux/Mac Users:
- Use the standard installation commands as listed above
- Virtual environment activation command: `source .venv/bin/activate`

## 🏗️ Project Structure

```
farm/
├── main.py                 # Flask application
├── ml_model.py             # ML model training
├── model.pkl               # Trained model file
├── requirements.txt        # Python dependencies
├── Project.md              # Original project specification
├── .env                    # Environment variables
├── datasets/
│   ├── data.py             # Data generation script
│   ├── interactions.csv    # Sample interaction data
│   ├── products.csv        # Sample product data
│   ├── transactions.csv    # Sample transaction data
│   └── users.csv           # Sample user data
├── templates/              # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── products.html
│   ├── product_detail.html
│   ├── recommendations.html
│   ├── login.html
│   ├── register.html
│   ├── farmer_dashboard.html
│   ├── buyer_dashboard.html
│   └── sell.html
└── instance/
```

## 🔧 Usage

### For Farmers:
1. Register as a farmer
2. Login to your account
3. Click "Add New Product" to list your crops
4. Manage your products using "Edit" or "Delete" options
5. Check your dashboard for recommendations and product performance

### For Buyers:
1. Register as a buyer
2. Browse products using search and filters
3. View detailed product information including nutritional data
4. Purchase products directly
5. Get personalized recommendations based on your behavior

## 🤖 Recommendation System Details

The recommendation system uses multiple approaches:

1. **Collaborative Filtering**: Based on user interaction history
2. **Content-Based**: Based on crop types and attributes
3. **Popularity-Based**: Fallback for users with no interaction history

The system tracks:
- Product views
- Purchases
- User preferences

## 📊 Data Model

- `User`: Farmer/Buyer accounts with roles
- `Product`: Crop listings with details (type, quantity, price, quality)
- `Interaction`: User-product interactions (views, clicks, purchases)
- `Transaction`: Purchase records

## 🌐 API Endpoints

- `GET /` - Home page
- `POST /register` - User registration
- `POST /login` - User authentication
- `GET /dashboard` - User dashboard
- `GET /products` - Product listings with filters
- `GET /product/<id>` - Product details
- `POST /buy/<id>` - Purchase products
- `GET /sell` - List new products (farmers only)
- `GET /edit_product/<id>` - Edit product (farmers only)
- `POST /delete_product/<id>` - Delete product (farmers only)
- `GET /recommendations` - Personalized recommendations

## 🧪 Testing

To test the recommendation system:
1. Create multiple user accounts
2. As a buyer, interact with various products (view, purchase)
3. Check recommendations to see personalized suggestions
4. As a farmer, add products and monitor their performance

## 📈 Future Improvements

- Migration to PostgreSQL and FastAPI
- Redis caching for recommendations
- Elasticsearch for advanced search
- Mobile-responsive improvements
- More sophisticated ML algorithms
- Real-time recommendation updates
- Seller/buyer ratings and reviews
- Location-based recommendations
- Seasonal crop recommendations

## 📄 License

This project is open source and available under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 🐛 Known Issues

- The recommendation model requires sufficient interaction data to provide accurate suggestions
- SQLite may have performance limitations with large datasets

## 📞 Support

For support, please open an issue in the GitHub repository.
