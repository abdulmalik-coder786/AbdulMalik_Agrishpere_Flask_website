from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from models import db, User, Product, Order, Consultant, ProductImage
from datetime import datetime, timedelta
from sqlalchemy import func
import base64

# ✅ Main admin blueprint
bp = Blueprint('admin', __name__,url_prefix='/admin')

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

# ✅ Admin Dashboard
@bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    # Admin statistics
    total_users = User.query.count()
    total_products = Product.query.count() if hasattr(Product, 'query') else 0
    total_orders = Order.query.count() if hasattr(Order, 'query') else 0
    total_consultants = Consultant.query.count() if hasattr(Consultant, 'query') else 0
    
    # Recent activities
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all() if hasattr(Order, 'query') else []
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         total_products=total_products,
                         total_orders=total_orders,
                         total_consultants=total_consultants,
                         recent_users=recent_users,
                         recent_orders=recent_orders)

# ✅ Admin Index (redirect to dashboard)
@bp.route('/')
@login_required
@admin_required
def index():
    return redirect(url_for('admin.dashboard'))

# ✅ User Management
@bp.route('/users')
@login_required
@admin_required
def manage_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

# ✅ Update User Role
@bp.route('/update-user-role/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def update_user_role(user_id):
    user = User.query.get_or_404(user_id)
    new_role = request.json.get('role')
    
    if new_role in ['customer', 'farmer', 'vendor', 'consultant', 'admin']:
        user.role = new_role
        db.session.commit()
        return {'success': True, 'new_role': new_role}
    
    return {'success': False, 'error': 'Invalid role'}

# ✅ Verify User
@bp.route('/verify-user/<int:user_id>')
@login_required
@admin_required
def verify_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_verified = not user.is_verified
    db.session.commit()
    
    status = "verified" if user.is_verified else "unverified"
    flash(f'User {status} successfully!', 'success')
    return redirect(url_for('admin.manage_users'))


# -----------------------------
# Product Management
# -----------------------------
@bp.route('/products')
@login_required
@admin_required
def manage_products():
    q = request.args.get('q')
    category = request.args.get('category')
    status = request.args.get('status')

    query = Product.query
    if q:
        query = query.filter(Product.name.ilike(f"%{q}%"))
    if category:
        query = query.filter(Product.category == category)
    if status == 'active':
        query = query.filter(Product.is_active == True)
    elif status == 'disabled':
        query = query.filter(Product.is_active == False)

    products = query.order_by(Product.created_at.desc()).all()

    # gather categories
    categories = [c[0] for c in db.session.query(Product.category).distinct().all() if c[0]]
    return render_template('admin/products.html', products=products, categories=categories, q=q, category=category, status=status)


@bp.route('/product/<int:product_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_product(product_id):
    p = Product.query.get_or_404(product_id)
    p.is_active = not p.is_active
    db.session.commit()
    flash(f'Product "{p.name}" updated.', 'success')
    return redirect(url_for('admin.manage_products'))


@bp.route('/product/<int:product_id>/edit', methods=['GET','POST'])
@login_required
@admin_required
def edit_product(product_id):
    p = Product.query.get_or_404(product_id)
    if request.method == 'POST':
        p.name = request.form.get('name')
        p.description = request.form.get('description')
        p.price = float(request.form.get('price') or p.price)
        p.category = request.form.get('category') or None
        p.quantity = int(request.form.get('quantity') or p.quantity)
        p.min_quantity = int(request.form.get('min_quantity') or p.min_quantity)
        p.in_stock = bool(request.form.get('in_stock'))

        # Handle image uploads - replace existing images (require at least 2 if uploading)
        images = request.files.getlist('images')
        valid_images = [img for img in images if img and img.filename]

        if valid_images:
            if len(valid_images) < 2:
                flash('Please upload at least 2 images for the product.', 'danger')
                return redirect(url_for('admin.edit_product', product_id=product_id))

            # Delete existing images
            ProductImage.query.filter_by(product_id=product_id).delete()
            first_img_data = None
            for image_file in valid_images:
                img_data = base64.b64encode(image_file.read()).decode('utf-8')
                if first_img_data is None:
                    first_img_data = img_data
                product_image = ProductImage(product_id=product_id, img_data=img_data)
                db.session.add(product_image)
            if first_img_data:
                p.img_url = f"data:image/jpeg;base64,{first_img_data}"

        db.session.commit()
        flash('Product updated.', 'success')
        return redirect(url_for('admin.manage_products'))

    categories = [c[0] for c in db.session.query(Product.category).distinct().all() if c[0]]
    return render_template('admin/edit_product.html', product=p, categories=categories)


@bp.route('/categories', methods=['GET','POST'])
@login_required
@admin_required
def manage_categories():
    # View categories and allow rename/delete via POST
    categories = [c[0] for c in db.session.query(Product.category).distinct().all() if c[0]]
    if request.method == 'POST':
        action = request.form.get('action')
        src = request.form.get('src')
        if action == 'delete':
            # remove category from products
            Product.query.filter(Product.category == src).update({Product.category: None})
            db.session.commit()
            flash(f'Category "{src}" removed from products.', 'success')
        elif action == 'rename':
            dst = request.form.get('dst')
            Product.query.filter(Product.category == src).update({Product.category: dst})
            db.session.commit()
            flash(f'Category "{src}" renamed to "{dst}".', 'success')
        return redirect(url_for('admin.manage_categories'))

    return render_template('admin/categories.html', categories=categories)


# -----------------------------
# Consultant Management
# -----------------------------
@bp.route('/consultants')
@login_required
@admin_required
def manage_consultants():
    # Prefer Consultant table but also include Users with role consultant
    consultants = Consultant.query.order_by(Consultant.created_at.desc()).all()
    # supplement missing consultants from User table
    user_consults = User.query.filter_by(role='consultant').all()
    return render_template('admin/consultants.html', consultants=consultants, user_consults=user_consults)


@bp.route('/consultant/<int:consultant_id>/toggle_verify')
@login_required
@admin_required
def toggle_consultant_verify(consultant_id):
    c = Consultant.query.get_or_404(consultant_id)
    c.is_verified = not c.is_verified
    db.session.commit()
    flash('Consultant verification status updated.', 'success')
    return redirect(url_for('admin.manage_consultants'))


@bp.route('/consultant/<int:consultant_id>/toggle_active')
@login_required
@admin_required
def toggle_consultant_active(consultant_id):
    c = Consultant.query.get_or_404(consultant_id)
    c.is_active = not c.is_active
    db.session.commit()
    flash('Consultant active status updated.', 'success')
    return redirect(url_for('admin.manage_consultants'))


@bp.route('/consultant/<int:consultant_id>/requests')
@login_required
@admin_required
def consultant_requests(consultant_id):
    from models import Consultation
    requests = Consultation.query.filter_by(consultant_id=consultant_id).order_by(Consultation.created_at.desc()).all()
    return render_template('admin/consultation_requests.html', requests=requests)


# -----------------------------
# Order Management
# -----------------------------
@bp.route('/orders')
@login_required
@admin_required
def manage_orders():
    status = request.args.get('status')
    q = request.args.get('q')
    query = Order.query
    if status:
        query = query.filter(Order.status == status)
    if q:
        query = query.join(User).filter(User.email.ilike(f"%{q}%"))
    orders = query.order_by(Order.created_at.desc()).all()
    return render_template('admin/orders.html', orders=orders, status=status, q=q)


@bp.route('/order/<int:order_id>/update', methods=['POST'])
@login_required
@admin_required
def update_order_status(order_id):
    o = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')
    if new_status:
        o.status = new_status
        db.session.commit()
        flash('Order status updated.', 'success')
    return redirect(url_for('admin.manage_orders'))


# Enhance dashboard with sales stats
@bp.route('/dashboard/stats')
@login_required
@admin_required
def dashboard_stats():
    # last 30 days sales
    today = datetime.utcnow()
    since = today - timedelta(days=30)
    sales_q = db.session.query(func.date(Order.created_at).label('day'), func.coalesce(func.sum(Order.total_amount),0).label('total'))
    sales_q = sales_q.filter(Order.created_at >= since).group_by(func.date(Order.created_at)).order_by(func.date(Order.created_at)).all()
    data = [{'day': str(r[0]), 'total': float(r[1])} for r in sales_q]
    total_sales = db.session.query(func.coalesce(func.sum(Order.total_amount),0)).scalar() or 0
    return {'total_sales': float(total_sales), 'sales_by_day': data}