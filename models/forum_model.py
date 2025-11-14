from datetime import datetime
from models import db

class ForumTopic(db.Model):
    __tablename__ = 'forum_topics'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    slug = db.Column(db.String(200), unique=True, nullable=False)

    # Foreign key for author
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to messages
    messages = db.relationship('ForumMessage', backref='topic', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<ForumTopic {self.title}>'

    @property
    def message_count(self):
        return len(self.messages)

    @property
    def last_message_at(self):
        if self.messages:
            return max(msg.created_at for msg in self.messages)
        return self.created_at


class ForumMessage(db.Model):
    __tablename__ = 'forum_messages'

    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('forum_topics.id'), nullable=False)

    # Foreign key for author
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<ForumMessage {self.id}>'