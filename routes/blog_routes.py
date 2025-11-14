from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models.post_model import Post
from models.user_model import db
from datetime import datetime

bp = Blueprint('blog', __name__, url_prefix='/blog')

@bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.created_at.desc()).paginate(page=page, per_page=5)
    return render_template('blog.html', posts=posts)

@bp.route('/post/<int:post_id>')
def view_post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('blog_post.html', post=post)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        summary = request.form.get('summary')
        image_url = request.form.get('image_url')

        if not title or not content:
            flash('Title and content are required.', 'danger')
            return redirect(url_for('blog.create_post'))

        post = Post(
            title=title,
            content=content,
            summary=summary,
            image_url=image_url,
            author_id=current_user.id
        )

        try:
            db.session.add(post)
            db.session.commit()
            flash('Post created successfully!', 'success')
            return redirect(url_for('blog.view_post', post_id=post.id))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while creating the post.', 'danger')
            return redirect(url_for('blog.create_post'))

    return render_template('create_post.html')

@bp.route('/edit/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    if post.author_id != current_user.id and not current_user.is_admin:
        flash('You do not have permission to edit this post.', 'danger')
        return redirect(url_for('blog.view_post', post_id=post.id))

    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        summary = request.form.get('summary')
        image_url = request.form.get('image_url')

        if not title or not content:
            flash('Title and content are required.', 'danger')
            return redirect(url_for('blog.edit_post', post_id=post.id))

        try:
            post.title = title
            post.content = content
            post.summary = summary
            post.image_url = image_url
            post.updated_at = datetime.utcnow()
            db.session.commit()
            flash('Post updated successfully!', 'success')
            return redirect(url_for('blog.view_post', post_id=post.id))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating the post.', 'danger')
            return redirect(url_for('blog.edit_post', post_id=post.id))

    return render_template('edit_post.html', post=post)

@bp.route('/delete/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    if post.author_id != current_user.id and not current_user.is_admin:
        flash('You do not have permission to delete this post.', 'danger')
        return redirect(url_for('blog.view_post', post_id=post.id))

    try:
        db.session.delete(post)
        db.session.commit()
        flash('Post deleted successfully!', 'success')
        return redirect(url_for('blog.index'))
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the post.', 'danger')
        return redirect(url_for('blog.view_post', post_id=post.id))