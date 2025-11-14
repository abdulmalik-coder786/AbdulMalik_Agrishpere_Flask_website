from models import db
from datetime import datetime

class Product(db.Model):
    __tablename__= 'products'
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(100),nullable=False)
    description = db.Column(db.Text,nullable=True)
    price = db.Column(db.Float,nullable=False)
    category = db.Column(db.String(50),nullable=True)
    sub_category = db.Column(db.String(50))
    img_url = db.Column(db.String(300),nullable=False)
    in_stock = db.Column(db.Boolean, default=True)
    quantity = db.Column(db.Integer, default=0)
    min_quantity = db.Column(db.Integer, default=5)  # Low stock threshold
    vendor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    

    # Relationships
    reviews = db.relationship('Review', backref='product', lazy=True)
    order_items = db.relationship('OrderItem', backref='product', lazy=True)

    def __repr__(self):
        return f"<Product {self.name}>"

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_approved = db.Column(db.Boolean, default=False)

class ProductImage(db.Model):
    __tablename__ = 'product_images'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    img_data = db.Column(db.Text, nullable=False)  # Base64 encoded image data
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship back to product
    product = db.relationship('Product', backref='images', lazy=True)

    def __repr__(self):
        return f"<ProductImage {self.id} for Product {self.product_id}>"
