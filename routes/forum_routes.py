from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, ForumTopic, ForumMessage, User
import re

# ✅ Create blueprint instance
bp = Blueprint('forum', __name__, url_prefix='/forum')

# ✅ Define routes
@bp.route('/')
def index():
    topics = ForumTopic.query.order_by(ForumTopic.created_at.desc()).all()
    return render_template('forum.html', topics=topics)

@bp.route('/discussion/<slug>')
def discussion(slug):
    topic = ForumTopic.query.filter_by(slug=slug).first_or_404()
    messages = ForumMessage.query.filter_by(topic_id=topic.id).order_by(ForumMessage.created_at.asc()).all()

    # Get author info for messages
    message_authors = {}
    for message in messages:
        author = User.query.get(message.author_id)
        message_authors[message.id] = author

    return render_template('discussion.html', topic=topic, messages=messages, message_authors=message_authors)

@bp.route('/create_topic', methods=['GET', 'POST'])
@login_required
def create_topic():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')

        if not title:
            flash('Title is required', 'error')
            return redirect(url_for('forum.create_topic'))

        # Create slug from title
        slug = re.sub(r'[^\w\s-]', '', title).strip().lower()
        slug = re.sub(r'[-\s]+', '-', slug)

        # Check if slug already exists
        existing_topic = ForumTopic.query.filter_by(slug=slug).first()
        if existing_topic:
            slug = f"{slug}-{ForumTopic.query.count() + 1}"

        new_topic = ForumTopic(
            title=title,
            description=description,
            slug=slug,
            author_id=current_user.id
        )

        db.session.add(new_topic)
        db.session.commit()

        flash('Topic created successfully!', 'success')
        return redirect(url_for('forum.discussion', slug=slug))

    return render_template('create_topic.html')

@bp.route('/discussion/<slug>/post_message', methods=['POST'])
@login_required
def post_message(slug):
    topic = ForumTopic.query.filter_by(slug=slug).first_or_404()
    content = request.form.get('content')

    if not content:
        flash('Message content is required', 'error')
        return redirect(url_for('forum.discussion', slug=slug))

    new_message = ForumMessage(
        topic_id=topic.id,
        author_id=current_user.id,
        content=content
    )

    db.session.add(new_message)
    db.session.commit()

    flash('Message posted successfully!', 'success')
    return redirect(url_for('forum.discussion', slug=slug))
