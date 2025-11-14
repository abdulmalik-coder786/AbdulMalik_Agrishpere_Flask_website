# models/consultant_model.py
from models import db
from datetime import datetime

class Consultant(db.Model):
    __tablename__='consultants'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    expertise = db.Column(db.String(120), nullable=False)
    experience_years = db.Column(db.Integer, default=0)
    bio = db.Column(db.Text, nullable=True)
    img_url = db.Column(db.String(300), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Add these new fields for enhanced functionality
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Link to User account
    qualifications = db.Column(db.Text, nullable=True)
    consultation_fee = db.Column(db.Float, default=0.0)
    availability = db.Column(db.String(50), default='weekdays')
    rating = db.Column(db.Float, default=0.0)
    is_verified = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    consultations = db.relationship('Consultation', backref='consultant', lazy=True)
    specializations = db.relationship('ConsultantSpecialization', backref='consultant', lazy=True)
    
    def __repr__(self):
        return f"<Consultant {self.name}>"