from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, session
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from models import db, User
from forms.profile import ProfileCompletionForm

bp = Blueprint('profile', __name__)

def save_profile_picture(file):
    if file and file.filename:
        filename = secure_filename(file.filename)
        # Create unique filename to avoid conflicts
        unique_filename = f"{current_user.id}_{filename}"
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'profiles', unique_filename)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        file.save(file_path)
        return f"uploads/profiles/{unique_filename}"
    return None

@bp.route('/complete-profile', methods=['GET', 'POST'])
@login_required
def complete_profile():
    # Carry next parameter so we can return after completion
    next_url = request.args.get('next') or request.form.get('next')

    # Allow skipping via a POSTed 'skip' value (sets session flag)
    if request.method == 'POST' and request.form.get('skip'):
        session['profile_skipped'] = True
        flash('Profile completion skipped for now. You can complete it later from your profile.', 'info')
        return redirect(next_url or url_for('home'))

    # Skip if profile already complete
    if current_user.profile_complete:
        flash('Your profile is already complete!', 'info')
        return redirect(url_for('home'))
    
    form = ProfileCompletionForm()
    
    if form.validate_on_submit():
        try:
            # Update personal information
            current_user.phone = form.phone.data
            current_user.address = form.address.data
            current_user.location = form.location.data
            current_user.bio = form.bio.data
            current_user.date_of_birth = form.date_of_birth.data
            current_user.gender = form.gender.data
            
            # Handle profile picture upload
            if form.profile_picture.data:
                picture_path = save_profile_picture(form.profile_picture.data)
                if picture_path:
                    current_user.profile_picture = picture_path
            
            # Update role-specific fields based on user's role
            # Update common business fields for business roles
            if current_user.role in ['farmer', 'vendor', 'consultant']:
                current_user.business_name = form.business_name.data
                current_user.business_description = form.business_description.data
                current_user.business_address = form.business_address.data
                current_user.business_phone = form.business_phone.data
                current_user.business_website = form.business_website.data

            # Update role-specific fields
            if current_user.role == 'farmer':
                current_user.farm_size = form.farm_size.data
                current_user.crop_types = form.crop_types.data
                current_user.farming_method = form.farming_method.data
            
            elif current_user.role == 'vendor':
                current_user.business_type = form.business_type.data
                current_user.vendor_type = form.vendor_type.data
                current_user.product_categories = form.product_categories.data
                current_user.delivery_areas = form.delivery_areas.data
            
            elif current_user.role == 'consultant':
                current_user.expertise = form.expertise.data
                current_user.qualifications = form.qualifications.data
                current_user.experience_years = form.experience_years.data
                current_user.consultation_fee = form.consultation_fee.data
                current_user.availability = form.availability.data
            
            elif current_user.role == 'customer':
                current_user.interests = form.interests.data
                current_user.preferred_contact = form.preferred_contact.data
            
            # Mark profile as complete
            current_user.profile_complete = True
            # Clear any session-skip flag when user actually completes their profile
            session.pop('profile_skipped', None)
            
            db.session.commit()

            # Update Consultant record if user is consultant
            if current_user.role == 'consultant':
                from models.consultant_model import Consultant
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

            flash('Profile completed successfully!', 'success')
            return redirect(next_url or url_for('home'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error updating profile. Please try again.', 'danger')
    
    # Pre-populate form with existing data
    elif request.method == 'GET':
        # Basic information
        form.phone.data = current_user.phone
        form.address.data = current_user.address
        form.location.data = current_user.location
        form.bio.data = current_user.bio
        form.date_of_birth.data = current_user.date_of_birth
        form.gender.data = current_user.gender

        # Business role fields
        if current_user.role in ['farmer', 'vendor', 'consultant']:
            form.business_name.data = current_user.business_name
            form.business_description.data = current_user.business_description
            form.business_address.data = current_user.business_address
            form.business_phone.data = current_user.business_phone
            form.business_website.data = current_user.business_website

        # Role-specific fields
        if current_user.role == 'farmer':
            form.farm_size.data = current_user.farm_size
            form.crop_types.data = current_user.crop_types
            form.farming_method.data = current_user.farming_method

        elif current_user.role == 'vendor':
            form.business_type.data = current_user.business_type
            form.vendor_type.data = current_user.vendor_type
            form.product_categories.data = current_user.product_categories
            form.delivery_areas.data = current_user.delivery_areas

        elif current_user.role == 'consultant':
            form.expertise.data = current_user.expertise
            form.qualifications.data = current_user.qualifications
            form.experience_years.data = current_user.experience_years
            form.consultation_fee.data = current_user.consultation_fee
            form.availability.data = current_user.availability

        elif current_user.role == 'customer':
            form.interests.data = current_user.interests
            form.preferred_contact.data = current_user.preferred_contact
    
    return render_template('complete_profile.html', form=form, user=current_user, next=next_url)

@bp.route('/profile')
@login_required
def view_profile():
    return render_template('profile_view.html', user=current_user)

@bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = ProfileCompletionForm()

    if form.validate_on_submit():
        try:
            current_user.phone = form.phone.data
            current_user.address = form.address.data
            current_user.location = form.location.data
            current_user.bio = form.bio.data
            current_user.date_of_birth = form.date_of_birth.data
            current_user.gender = form.gender.data

            if form.profile_picture.data:
                picture_path = save_profile_picture(form.profile_picture.data)
                if picture_path:
                    current_user.profile_picture = picture_path

            # Role-specific updates (don't toggle profile_complete)
            if current_user.role in ['farmer', 'vendor', 'consultant']:
                current_user.business_name = form.business_name.data
                current_user.business_description = form.business_description.data
                current_user.business_address = form.business_address.data
                current_user.business_phone = form.business_phone.data
                current_user.business_website = form.business_website.data

            if current_user.role == 'farmer':
                current_user.farm_size = form.farm_size.data
                current_user.crop_types = form.crop_types.data
                current_user.farming_method = form.farming_method.data
            elif current_user.role == 'vendor':
                current_user.business_type = form.business_type.data
                current_user.vendor_type = form.vendor_type.data
                current_user.product_categories = form.product_categories.data
                current_user.delivery_areas = form.delivery_areas.data
            elif current_user.role == 'consultant':
                current_user.expertise = form.expertise.data
                current_user.qualifications = form.qualifications.data
                current_user.experience_years = form.experience_years.data
                current_user.consultation_fee = form.consultation_fee.data
                current_user.availability = form.availability.data
            elif current_user.role == 'customer':
                current_user.interests = form.interests.data
                current_user.preferred_contact = form.preferred_contact.data

            db.session.commit()

            # Update Consultant record if user is consultant
            if current_user.role == 'consultant':
                if not current_user.consultant:
                    from models.consultant_model import Consultant
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

            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile.view_profile'))
        except Exception:
            db.session.rollback()
            flash('Error updating profile. Please try again.', 'danger')

    # Pre-populate form with current data
    form.phone.data = current_user.phone
    form.address.data = current_user.address
    form.location.data = current_user.location
    form.bio.data = current_user.bio
    form.date_of_birth.data = current_user.date_of_birth
    form.gender.data = current_user.gender

    if current_user.role in ['farmer', 'vendor', 'consultant']:
        form.business_name.data = current_user.business_name
        form.business_description.data = current_user.business_description
        form.business_address.data = current_user.business_address
        form.business_phone.data = current_user.business_phone
        form.business_website.data = current_user.business_website

    if current_user.role == 'farmer':
        form.farm_size.data = current_user.farm_size
        form.crop_types.data = current_user.crop_types
        form.farming_method.data = current_user.farming_method
    elif current_user.role == 'vendor':
        form.business_type.data = current_user.business_type
        form.vendor_type.data = current_user.vendor_type
        form.product_categories.data = current_user.product_categories
        form.delivery_areas.data = current_user.delivery_areas
    elif current_user.role == 'consultant':
        form.expertise.data = current_user.expertise
        form.qualifications.data = current_user.qualifications
        form.experience_years.data = current_user.experience_years
        form.consultation_fee.data = current_user.consultation_fee
        form.availability.data = current_user.availability
    elif current_user.role == 'customer':
        form.interests.data = current_user.interests
        form.preferred_contact.data = current_user.preferred_contact

    return render_template('profile/edit.html', form=form, user=current_user)

# NOTE: Removed global before_app_request enforcement so public pages stay accessible.
# Protected routes use @login_required where needed.
