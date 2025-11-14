from flask import Blueprint, render_template, redirect, url_for, request, flash
from datetime import datetime, timedelta
import secrets
from forms.login import LoginForm
from forms.register import RegistrationForm
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from models.user_model import User, db
from models.consultant_model import Consultant
from utils.email_utils import send_email_if_configured

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login',methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Logged in successfully!', 'success')
            next_page = request.args.get('next')
            # Respect next parameter first
            if next_page:
                return redirect(next_page)
            # Otherwise, consultants go to their dashboard
            if user.role == 'consultant':
                return redirect(url_for('consultant.dashboard'))
            return redirect(url_for('home'))
        flash('Invalid email or password.', 'danger')
    return render_template('login.html', form=form)

@bp.route('/register', methods=['GET','POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Email already registered. Please login.', 'danger')
            return redirect(url_for('auth.login'))

        # ✅ CHECK IF NO ADMIN EXISTS - MAKE THIS USER ADMIN
        admin_exists = User.query.filter_by(role='admin').first()
        user_role = 'admin' if not admin_exists else form.role.data

        hashed_password = generate_password_hash(form.password.data)
        new_user = User(
            name=form.name.data,
            email=form.email.data,
            password=hashed_password,
            role=user_role
        )
        
        db.session.add(new_user)
        db.session.commit()

        # If the new user registered as a consultant, create a Consultant entry (if not exists)
        if user_role == 'consultant':
            try:
                existing = Consultant.query.filter_by(user_id=new_user.id).first()
                if not existing:
                    consultant = Consultant(
                        name=new_user.name,
                        email=new_user.email,
                        phone=new_user.phone or '',
                        expertise=new_user.expertise or '',
                        experience_years=new_user.experience_years or 0,
                        bio=new_user.bio or '',
                        user_id=new_user.id,
                        qualifications=new_user.qualifications or '',
                        consultation_fee=new_user.consultation_fee or 0.0,
                        availability=new_user.availability or 'weekdays',
                        is_verified=new_user.is_verified,
                        is_active=True
                    )
                    db.session.add(consultant)
                    db.session.commit()
            except Exception:
                db.session.rollback()
        
        if not admin_exists:
            flash('🎉 Admin user created successfully!', 'success')
        else:
            flash('Registration successful! You can login via the navbar.', 'success')

        return redirect(url_for('home'))
    
    return render_template('register.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))

@bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()

        if user:
            # Generate reset token
            token = secrets.token_urlsafe(32)
            user.reset_token = token
            user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
            db.session.commit()

            # Send reset email
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            subject = 'Password Reset Request - AgriSphere'
            body = f'''Hello {user.name},

You requested a password reset for your AgriSphere account.

Click the following link to reset your password:
{reset_url}

This link will expire in 1 hour.

If you didn't request this reset, please ignore this email.

Best regards,
AgriSphere Team
'''

            if send_email_if_configured(user.email, subject, body):
                flash('Password reset instructions have been sent to your email.', 'success')
            else:
                flash('Password reset token generated. Please contact support if email is not configured.', 'info')
                # For development/testing, show the reset URL
                flash(f'Development mode - Reset URL: {reset_url}', 'info')
        else:
            # Don't reveal if email exists or not for security
            flash('If an account with that email exists, password reset instructions have been sent.', 'info')

        return redirect(url_for('auth.login'))

    return render_template('forgot_password.html')

@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    user = User.query.filter_by(reset_token=token).first()

    if not user or (user.reset_token_expires and user.reset_token_expires < datetime.utcnow()):
        flash('Invalid or expired reset token.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('reset_password.html', token=token)

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('reset_password.html', token=token)

        # Update password and clear reset token
        user.set_password(password)
        user.reset_token = None
        user.reset_token_expires = None
        db.session.commit()

        flash('Your password has been reset successfully. You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('reset_password.html', token=token)


