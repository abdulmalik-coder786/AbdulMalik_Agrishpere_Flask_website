from models import db
from datetime import datetime

class ConsultantSpecialization(db.Model):
    __tablename__='consultant_specializations'
    id = db.Column(db.Integer, primary_key=True)
    consultant_id = db.Column(db.Integer, db.ForeignKey('consultants.id'), nullable=False)
    specialization = db.Column(db.String(100), nullable=False)
    
    def __repr__(self):
        return f"<Specialization {self.specialization}>"