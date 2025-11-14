from datetime import datetime
from models import db

class Post(db.Model):
    __tablename__ = "blog_posts"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    summary = db.Column(db.String(300))
    image_url = db.Column(db.String(200))
    
    # ✅ ADDED: Foreign key for author relationship
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    comments = db.relationship('BlogComment', backref='post', lazy=True)

    def __repr__(self):
        return f'<Post {self.title}>'

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'summary': self.summary,
            'image_url': self.image_url,
            'author_id': self.author_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class BlogComment(db.Model):
    __tablename__ = 'blog_comments'
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('blog_posts.id'), nullable=False)
    
    # ✅ FIXED: Only one user foreign key
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    content = db.Column(db.Text, nullable=False)
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<BlogComment {self.id}>'