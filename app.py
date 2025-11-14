import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from routes import forum_routes, auth_routes, blog_routes, shop_routes, admin_routes, profile_routes, consultant_routes
from models.user_model import User
from models import db
from config import Config
from models.post_model import Post, BlogComment
from models.product_model import Product, Review
from models.consultant_model import Consultant
from models.consultation_models import Consultation
from models.specialization_model import ConsultantSpecialization

migrate = Migrate()
def create_app():
    app = Flask(__name__, instance_relative_config=True)
    # Load config based on environment
    env = os.environ.get('FLASK_ENV', 'development')
    if env == 'production':
        app.config.from_object('config.ProductionConfig')
    elif env == 'testing':
        app.config.from_object('config.TestingConfig')
    else:
        app.config.from_object('config.DevelopmentConfig')
    
    # Handle cookie compatibility
    from flask import Response
    original_set_cookie = Response.set_cookie
    def set_cookie_wrapper(self, *args, **kwargs):
        if 'partitioned' in kwargs:
            del kwargs['partitioned']
        return original_set_cookie(self, *args, **kwargs)
    Response.set_cookie = set_cookie_wrapper

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db, render_as_batch=True)  # Enable SQLite batch migrations
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Create database tables
    with app.app_context():
        db.create_all()

        # Ensure `is_active` column exists on users table (backwards-compatibility)
        from sqlalchemy import text
        try:
            cols = db.session.execute(text("PRAGMA table_info('users')")).fetchall()
            col_names = [c[1] for c in cols]
            if 'is_active' not in col_names:
                # Add the column with a default of 1 (True)
                try:
                    db.session.execute(text("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1"))
                    db.session.commit()
                    print('Patched users table: added is_active column')
                except Exception as e:
                    db.session.rollback()
                    print('Could not add is_active column automatically:', e)
        except Exception:
            # pragma may fail on some DBs; ignore and proceed
            pass

        # ✅ CREATE DEFAULT ADMIN IF NO USERS EXIST (Backup)
        from models.user_model import User
        if User.query.count() == 0:
            admin_user = User(
                name='System Administrator',
                email='admin@agrifarma.com',
                role='admin',
                is_verified=True,
                profile_complete=True
            )
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            db.session.commit()
            print("✅ Default admin user created!")
    
    # Create upload directories
        upload_dirs = ['profiles', 'products', 'blog']
        for directory in upload_dirs:
            dir_path = os.path.join(app.config['UPLOAD_FOLDER'], directory)
            os.makedirs(dir_path, exist_ok=True)
            print(f"Created directory: {dir_path}")  # Optional: for verification


    # Register blueprints
    
    app.register_blueprint(forum_routes.bp)
    app.register_blueprint(auth_routes.bp)
    app.register_blueprint(blog_routes.bp)
    app.register_blueprint(shop_routes.bp)
    app.register_blueprint(admin_routes.bp)
    app.register_blueprint(profile_routes.bp)
    app.register_blueprint(consultant_routes.bp)
    
    @app.context_processor
    def inject_now():
        from datetime import datetime
        return {'now': datetime.utcnow()}

    # Middleware: encourage profile completion but do not force browsing
    @app.before_request
    def encourage_profile_completion():
        from flask import request, session, flash, redirect, url_for
        from flask_login import current_user

        endpoint = request.endpoint or ''
        # Skip static, favicon, and auth routes, profile routes themselves, and public blueprints
        public_allowed = (
            'static',
            'favicon',
            'home',
            'auth.',
            'blog.',
            'shop.index',
            'shop.view_product',
            'consultant.index',
            'consultant.view_profile',
            'profile.complete_profile',
        )

        # If endpoint is None or starts with any public prefix, skip
        if not endpoint:
            return
        if any(endpoint == p or endpoint.startswith(p) for p in public_allowed):
            return

        # Only act for authenticated users
        if not current_user.is_authenticated:
            return

        # If profile already complete, nothing to do
        if getattr(current_user, 'profile_complete', False):
            return

        # Gentle reminder: show once per session
        if not session.get('profile_reminder_shown'):
            flash('Complete your profile to unlock more features (you can skip for now).', 'info')
            session['profile_reminder_shown'] = True

        # Endpoints that require a completed profile to proceed
        require_complete = set([
            'shop.add_product',                # adding products (vendors/farmers)
            'consultant.book_consultation',
            'consultant.dashboard',    # consultant dashboard
        ])

        if endpoint in require_complete:
            # redirect to profile completion, preserve next param
            return redirect(url_for('profile.complete_profile', next=request.url))

    @app.route('/')
    def home():
        return render_template("index.html")

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)