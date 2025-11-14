from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models.consultant_model import Consultant
from models.specialization_model import ConsultantSpecialization
from models.consultation_models import Consultation
from models import db, User
from datetime import datetime
from forms.consultant import ConsultantRegistrationForm, ConsultationRequestForm

bp = Blueprint('consultant', __name__, url_prefix='/consultant')

@bp.route('/')
def index():
    # Show users with role consultant who are active
    consultants = User.query.filter_by(role='consultant', is_active=True).all()
    return render_template('consultant.html', consultants=consultants)

@bp.route('/profile/<int:consultant_id>')
def view_profile(consultant_id):
    # consultant_id here refers to User.id for the consultant
    user = User.query.get_or_404(consultant_id)
    if user.role != 'consultant':
        flash('Consultant not found.', 'danger')
        return redirect(url_for('consultant.index'))

    # Prefer the Consultant record if it exists, otherwise use user fields
    consultant = user.consultant if hasattr(user, 'consultant') and user.consultant else None
    if consultant:
        # Ensure img_url is set to user's profile picture if not set
        if not consultant.img_url:
            consultant.img_url = user.profile_picture
    if not consultant:
        # Create a lightweight proxy object with expected attributes for the template
        class Proxy:
            pass
        p = Proxy()
        p.id = None
        p.name = user.name
        p.email = user.email
        p.phone = user.phone
        p.expertise = user.expertise
        p.experience_years = user.experience_years
        p.bio = user.bio
        p.img_url = getattr(user, 'profile_picture', None)
        p.qualifications = user.qualifications
        p.consultation_fee = user.consultation_fee
        p.availability = user.availability
        p.rating = user.rating
        p.specializations = []
        p.consultations = []
        consultant = p

    return render_template('consultant_profile.html', consultant=consultant)

@bp.route('/book/<int:consultant_id>', methods=['GET', 'POST'])
@login_required
def book_consultation(consultant_id):
    # consultant_id refers to User.id; find associated Consultant record
    user = User.query.get_or_404(consultant_id)
    if user.role != 'consultant':
        flash('Consultant not found.', 'danger')
        return redirect(url_for('consultant.index'))

    # Prevent booking yourself
    if current_user.id == user.id:
        flash('You cannot book a consultation with yourself.', 'danger')
        return redirect(url_for('consultant.view_profile', consultant_id=user.id))

    # Ensure Consultant record exists, create if missing
    if not user.consultant:
        consultant = Consultant(
            name=user.name,
            email=user.email,
            phone=user.phone,
            expertise=user.expertise or '',
            experience_years=user.experience_years or 0,
            bio=user.bio,
            user_id=user.id,
            qualifications=user.qualifications,
            consultation_fee=user.consultation_fee or 4.0,
            availability=user.availability or 'weekdays',
            rating=user.rating or 0.0,
            is_verified=user.is_verified,
            is_active=True
        )
        db.session.add(consultant)
        db.session.commit()
    else:
        consultant = user.consultant

    # Ensure img_url is set
    if not consultant.img_url:
        consultant.img_url = user.profile_picture

    form = ConsultationRequestForm()

    if form.validate_on_submit():
        try:
            scheduled_date = datetime.strptime(form.preferred_date.data, '%Y-%m-%dT%H:%M') if form.preferred_date.data else None
        except ValueError:
            flash('Invalid date format. Please try again.', 'danger')
            return render_template('book_consultation.html', form=form, consultant=consultant)

        consultation = Consultation(
            client_id=current_user.id,
            consultant_id=consultant.id,
            topic=form.topic.data,
            description=form.description.data,
            consultation_type=form.consultation_type.data,
            scheduled_date=scheduled_date,
            fee=consultant.consultation_fee
        )

        try:
            db.session.add(consultation)
            db.session.commit()
            flash('Consultation booked successfully!', 'success')
            return redirect(url_for('consultant.view_profile', consultant_id=user.id))
        except Exception as e:
            db.session.rollback()
            flash('Error booking consultation. Please try again.', 'danger')

    return render_template('book_consultation.html', form=form, consultant=consultant)

@bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'consultant':
        flash('Access denied. Consultant privileges required.', 'danger')
        return redirect(url_for('home'))

    # Ensure Consultant record exists and is up to date
    if not current_user.consultant:
        consultant = Consultant(
            name=current_user.name,
            email=current_user.email,
            phone=current_user.phone,
            expertise=current_user.expertise or '',
            experience_years=current_user.experience_years or 0,
            bio=current_user.bio,
            user_id=current_user.id,
            qualifications=current_user.qualifications,
            consultation_fee=current_user.consultation_fee or 4.0,
            availability=current_user.availability or 'weekdays',
            rating=current_user.rating or 0.0,
            is_verified=current_user.is_verified,
            is_active=True
        )
        db.session.add(consultant)
    else:
        # Update existing consultant with current user data
        current_user.consultant.name = current_user.name
        current_user.consultant.email = current_user.email
        current_user.consultant.phone = current_user.phone
        current_user.consultant.expertise = current_user.expertise or ''
        current_user.consultant.experience_years = current_user.experience_years or 0
        current_user.consultant.bio = current_user.bio
        current_user.consultant.qualifications = current_user.qualifications
        current_user.consultant.consultation_fee = current_user.consultation_fee or 4.0
        current_user.consultant.availability = current_user.availability or 'weekdays'
        current_user.consultant.rating = current_user.rating or 0.0
        current_user.consultant.is_verified = current_user.is_verified
        current_user.consultant.is_active = True
    db.session.commit()

    my_consultations = Consultation.query.filter_by(consultant_id=current_user.consultant.id).order_by(Consultation.scheduled_date.desc()).all()
    return render_template('consultant_dashboard.html', consultations=my_consultations)

@bp.route('/accept/<int:consultation_id>', methods=['POST'])
@login_required
def accept_consultation(consultation_id):
    if current_user.role != 'consultant':
        flash('Access denied.', 'danger')
        return redirect(url_for('consultant.dashboard'))

    consultation = Consultation.query.get_or_404(consultation_id)
    if consultation.consultant_id != current_user.consultant.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('consultant.dashboard'))

    if consultation.status != 'pending':
        flash('Consultation is not pending.', 'warning')
        return redirect(url_for('consultant.dashboard'))

    consultation.status = 'accepted'
    db.session.commit()
    flash('Consultation accepted successfully!', 'success')
    return redirect(url_for('consultant.dashboard'))

@bp.route('/decline/<int:consultation_id>', methods=['POST'])
@login_required
def decline_consultation(consultation_id):
    if current_user.role != 'consultant':
        flash('Access denied.', 'danger')
        return redirect(url_for('consultant.dashboard'))

    consultation = Consultation.query.get_or_404(consultation_id)
    if consultation.consultant_id != current_user.consultant.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('consultant.dashboard'))

    if consultation.status != 'pending':
        flash('Consultation is not pending.', 'warning')
        return redirect(url_for('consultant.dashboard'))

    consultation.status = 'cancelled'
    db.session.commit()
    flash('Consultation declined.', 'info')
    return redirect(url_for('consultant.dashboard'))

@bp.route('/start_meeting/<int:consultation_id>', methods=['POST'])
@login_required
def start_meeting(consultation_id):
    if current_user.role != 'consultant':
        flash('Access denied.', 'danger')
        return redirect(url_for('consultant.dashboard'))

    consultation = Consultation.query.get_or_404(consultation_id)
    if consultation.consultant_id != current_user.consultant.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('consultant.dashboard'))

    if consultation.status != 'accepted':
        flash('Consultation must be accepted first.', 'warning')
        return redirect(url_for('consultant.dashboard'))

    # For now, just flash a message. In a real app, this could integrate with video call API
    flash('Meeting started! (Integration with video call service needed)', 'success')
    return redirect(url_for('consultant.dashboard'))

@bp.route('/view_details/<int:consultation_id>')
@login_required
def view_consultation_details(consultation_id):
    if current_user.role != 'consultant':
        flash('Access denied.', 'danger')
        return redirect(url_for('consultant.dashboard'))

    consultation = Consultation.query.get_or_404(consultation_id)
    if consultation.consultant_id != current_user.consultant.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('consultant.dashboard'))

    return render_template('consultation_details.html', consultation=consultation)
