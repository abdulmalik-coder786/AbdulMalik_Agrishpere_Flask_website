# models/consultation_models.py
from models import db
from datetime import datetime

class Consultation(db.Model):
    __tablename__='consultations'
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    consultant_id = db.Column(db.Integer, db.ForeignKey('consultants.id'), nullable=False)
    topic = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, completed, cancelled
    consultation_type = db.Column(db.String(50), default='general')
    scheduled_date = db.Column(db.DateTime, nullable=True)
    duration = db.Column(db.Integer, default=60)  # minutes
    fee = db.Column(db.Float, default=0.0)
    payment_status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Consultation results
    consultant_notes = db.Column(db.Text)
    recommendations = db.Column(db.Text)
    client_rating = db.Column(db.Integer)
    client_feedback = db.Column(db.Text)

