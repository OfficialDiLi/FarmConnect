CREATE DATABASE farm_recommendations;

USE farm_recommendations;

CREATE TABLE users (
    user_id INT PRIMARY KEY,
    name VARCHAR(255),
    role VARCHAR(50),
    location VARCHAR(255),
    email VARCHAR(255),
    password VARCHAR(255)
);

CREATE TABLE products (
    product_id INT PRIMARY KEY,
    farmer_id INT,
    crop_type VARCHAR(255),
    quantity_kg INT,
    price_per_kg INT,
    harvest_date DATE,
    quality VARCHAR(10),
    FOREIGN KEY (farmer_id) REFERENCES users(user_id)
);

CREATE TABLE interactions (
    interaction_id INT PRIMARY KEY,
    user_id INT,
    product_id INT,
    event_type VARCHAR(50),
    timestamp DATETIME,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE TABLE transactions (
    transaction_id INT PRIMARY KEY,
    buyer_id INT,
    product_id INT,
    quantity_bought INT,
    total_price INT,
    date DATE,
    FOREIGN KEY (buyer_id) REFERENCES users(user_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);