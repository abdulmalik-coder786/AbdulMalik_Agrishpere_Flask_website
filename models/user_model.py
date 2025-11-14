from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from models import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='customer')  # customer, farmer, vendor, admin, consultant
    is_verified = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    is_trusted_seller = db.Column(db.Boolean, default=False)
    
    # Consultant-specific fields
    expertise = db.Column(db.String(200))  # e.g., "Rose Cultivation, Organic Farming"
    qualifications = db.Column(db.Text)    # Certifications, degrees
    experience_years = db.Column(db.Integer, default=0)
    consultation_fee = db.Column(db.Float, default=0.0)  # Per hour or per session
    bio = db.Column(db.Text)               # Professional background
    availability = db.Column(db.String(50), default='weekdays')  # weekdays, weekends, flexible
    rating = db.Column(db.Float, default=0.0)  # Average consultant rating
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    profile_picture = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    # Add these to your existing fields
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(20))
    location = db.Column(db.String(100))  # City, State
    profile_complete = db.Column(db.Boolean, default=False)
    business_name = db.Column(db.String(200))
    business_type = db.Column(db.String(100))  # nursery, farm, retailer, etc.
    business_description = db.Column(db.Text)
    business_address = db.Column(db.Text)
    business_phone = db.Column(db.String(20))
    business_website = db.Column(db.String(200))
    farm_size = db.Column(db.String(50))  # small, medium, large
    crop_types = db.Column(db.String(300))  # comma-separated
    farming_method = db.Column(db.String(100))  # organic, conventional, hydroponic
    vendor_type = db.Column(db.String(100))  # wholesaler, retailer, exporter
    product_categories = db.Column(db.String(300))
    delivery_areas = db.Column(db.Text)
    
    # Customer-specific fields
    interests = db.Column(db.String(300))  # Agricultural interests (comma-separated)
    preferred_contact = db.Column(db.String(20), default='email')  # email, phone, both

    # Password reset token
    reset_token = db.Column(db.String(100), unique=True)
    reset_token_expires = db.Column(db.DateTime)

    # ✅ One-directional relationship
    posts = db.relationship('Post', backref='author', lazy=True)

    # Relationships
    products = db.relationship('Product', backref='vendor', lazy=True)
    cart_items = db.relationship('Cart', backref='user', lazy=True)
    orders = db.relationship('Order', backref='user', lazy=True)
    reviews = db.relationship('Review', backref='user', lazy=True)
    consultation_requests = db.relationship('Consultation', backref='client', lazy=True, foreign_keys='Consultation.client_id')
    consultant = db.relationship('Consultant', backref='user', uselist=False, lazy=True)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)
    def get_required_profile_fields(self):
        """Return required fields based on role"""
        base_fields = ['phone', 'address', 'bio']
    
        if self.role == 'farmer':
            return base_fields + ['business_name', 'crop_types', 'farm_size']
        elif self.role == 'vendor':
            return base_fields + ['business_name', 'vendor_type', 'product_categories']
        elif self.role == 'consultant':
            return base_fields + ['expertise', 'qualifications', 'experience_years']
        else:  # customer
            return base_fields

    @property
    def is_consultant(self):
        return self.role == 'consultant'

    @property
    def is_admin(self):
        return self.role == 'admin'

    def __repr__(self):
        return f'<User {self.email}>'
