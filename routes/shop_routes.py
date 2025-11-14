from flask import Blueprint, render_template, request, url_for, flash, redirect, jsonify
from flask_login import login_required, current_user
from models.product_model import Product, Review, ProductImage
from models.order_model import Cart, Order, OrderItem, Payment
from models import db
from sqlalchemy import func
import os
import base64
from utils.email_utils import send_email_if_configured

# ✅ Create blueprint instance
bp = Blueprint('shop', __name__, url_prefix='/shop')
@bp.route('/')
def index():
    # Filters: q, category, min_price, max_price, rating, sort
    q = request.args.get('q')
    category = request.args.get('category')
    min_price = request.args.get('min_price')
    max_price = request.args.get('max_price')
    sort = request.args.get('sort')  # price_asc, price_desc, date, popularity

    query = Product.query.filter(Product.is_active == True)
    if q:
        query = query.filter((Product.name.ilike(f"%{q}%")) | (Product.description.ilike(f"%{q}%")))
    if category:
        query = query.filter(Product.category == category)
    if min_price:
        try:
            query = query.filter(Product.price >= float(min_price))
        except ValueError:
            pass
    if max_price:
        try:
            query = query.filter(Product.price <= float(max_price))
        except ValueError:
            pass

    products = query.all()

    # calculate average rating and popularity (order items count)
    prod_ids = [p.id for p in products]
    ratings = {}
    if prod_ids:
        rows = db.session.query(Review.product_id, func.avg(Review.rating)).filter(Review.product_id.in_(prod_ids), Review.is_approved==True).group_by(Review.product_id).all()
        ratings = {r[0]: float(r[1]) for r in rows}

    # popularity by order items
    popularity = {}
    if prod_ids:
        rows = db.session.query(OrderItem.product_id, func.count(OrderItem.id)).filter(OrderItem.product_id.in_(prod_ids)).group_by(OrderItem.product_id).all()
        popularity = {r[0]: int(r[1]) for r in rows}

    for p in products:
        p.avg_rating = ratings.get(p.id, 0)
        p.popularity = popularity.get(p.id, 0)

    if sort == 'price_asc':
        products.sort(key=lambda x: x.price)
    elif sort == 'price_desc':
        products.sort(key=lambda x: x.price, reverse=True)
    elif sort == 'popularity':
        products.sort(key=lambda x: x.popularity, reverse=True)
    else:  # default date
        products.sort(key=lambda x: x.created_at, reverse=True)

    # gather categories for filter UI
    categories = [c[0] for c in db.session.query(Product.category).distinct().all() if c[0]]
    return render_template("marketplace.html", products=products, categories=categories, q=q, category=category, min_price=min_price, max_price=max_price, sort=sort)

#View single Product
@bp.route('/product/<int:product_id>')
def view_product(product_id):
    product = Product.query.get_or_404(product_id)
    # Get images from ProductImage table
    product_images = ProductImage.query.filter_by(product_id=product_id).order_by(ProductImage.created_at).all()
    images = [img.img_data for img in product_images]
    # approved reviews
    reviews = [r for r in product.reviews if getattr(r, 'is_approved', True)]
    avg_rating = None
    if reviews:
        avg_rating = sum(r.rating for r in reviews) / len(reviews)

    return render_template("product_detail.html", product=product, images=images, reviews=reviews, avg_rating=avg_rating)


@bp.route('/sell')
def sell():
    # Public link — if not logged in, send to login; if logged in, send to add product
    if not current_user.is_authenticated:
        # send to login with next pointing back to shop.sell
        return redirect(url_for('auth.login', next=url_for('shop.sell')))
    # If user is logged in, send to add product page (which itself checks admin)
    return redirect(url_for('shop.add_product'))

#Add product (only admin)
@bp.route('/add',methods=['GET','POST'])
@login_required
def add_product():
    # Only allow admin, vendor, or farmer roles to add products
    if current_user.role not in ['admin', 'vendor', 'farmer']:
        flash("Only vendors, farmers, or admins can add products!", "danger")
        return redirect(url_for('shop.index'))
    
    if request.method == 'POST':
        try:
            product = Product(
                name=request.form['name'],
                description=request.form['description'],
                price=float(request.form['price']),
                category=request.form['category'],
                sub_category=request.form.get('sub_category'),
                img_url='',  # Will be set to first image or empty
                quantity=int(request.form['quantity']),
                vendor_id=current_user.id
            )
            db.session.add(product)
            db.session.commit()

            # Handle multiple image uploads - require at least 2 images
            images = request.files.getlist('images')
            valid_images = [img for img in images if img and img.filename]

            if len(valid_images) < 2:
                db.session.rollback()
                flash('Please upload at least 2 images for the product.', 'danger')
                return redirect(url_for('shop.add_product'))

            first_img_data = None
            for image_file in valid_images:
                # Convert to base64
                img_data = base64.b64encode(image_file.read()).decode('utf-8')
                if first_img_data is None:
                    first_img_data = img_data
                product_image = ProductImage(
                    product_id=product.id,
                    img_data=img_data
                )
                db.session.add(product_image)
            db.session.commit()

            # Set primary image URL to first image
            if first_img_data:
                product.img_url = f"data:image/jpeg;base64,{first_img_data}"
                db.session.commit()

            flash('Product added successfully!', 'success')
            return redirect(url_for('shop.view_product', product_id=product.id))
        except Exception as e:
            db.session.rollback()
            flash('Error adding product. Please try again.', 'danger')
            return redirect(url_for('shop.add_product'))
            
    return render_template('add_product.html')

@bp.route('/product/<int:product_id>/review', methods=['POST'])
@login_required
def add_review(product_id):
    product = Product.query.get_or_404(product_id)
    
    try:
        review = Review(
            product_id=product.id,
            user_id=current_user.id,
            rating=int(request.form['rating']),
            comment=request.form['comment']
        )
        db.session.add(review)
        db.session.commit()
        flash('Review added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error adding review. Please try again.', 'danger')
    
    return redirect(url_for('shop.view_product', product_id=product.id))

@bp.route('/cart/add', methods=['POST'])
@login_required
def add_to_cart():
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = int(data.get('quantity', 1))
    
    try:
        product = Product.query.get_or_404(product_id)
        if not product.in_stock or product.quantity < quantity:
            return jsonify({'success': False, 'error': 'Not enough stock'})

        # if an item exists, update quantity
        cart_item = Cart.query.filter_by(user_id=current_user.id, product_id=product_id).first()
        if cart_item:
            cart_item.quantity = min(product.quantity, cart_item.quantity + quantity)
        else:
            cart_item = Cart(user_id=current_user.id, product_id=product_id, quantity=quantity)
            db.session.add(cart_item)

        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/cart')
@login_required
def view_cart():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    subtotal = sum(item.product.price * item.quantity for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, subtotal=subtotal)

@bp.route('/cart/update/<int:item_id>', methods=['POST'])
@login_required
def update_cart(item_id):
    data = request.get_json()
    action = data.get('action')
    
    cart_item = Cart.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
    
    if action == 'increase':
        cart_item.quantity += 1
    elif action == 'decrease':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
        else:
            db.session.delete(cart_item)
            db.session.commit()
            return jsonify({'success': True})
    
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/cart/remove/<int:item_id>', methods=['POST'])
@login_required
def remove_from_cart(item_id):
    cart_item = Cart.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
    db.session.delete(cart_item)
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    # Show checkout form with address information
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        flash('Your cart is empty', 'warning')
        return redirect(url_for('shop.index'))

    subtotal = sum(item.product.price * item.quantity for item in cart_items)
    if request.method == 'POST':
        # collect address fields
        address = request.form.get('address') or current_user.address
        shipping_address = address

        # create order
        order = Order(user_id=current_user.id, total_amount=subtotal, status='pending', shipping_address=shipping_address)
        db.session.add(order)
        db.session.commit()

        # create order items and reduce inventory
        for item in cart_items:
            oi = OrderItem(order_id=order.id, product_id=item.product_id, quantity=item.quantity, price=item.product.price)
            db.session.add(oi)
            # decrement product stock
            p = item.product
            try:
                p.quantity = max(0, p.quantity - item.quantity)
                if p.quantity == 0:
                    p.in_stock = False
            except Exception:
                pass

        # create payment record placeholder
        payment = Payment(order_id=order.id, amount=subtotal, status='pending')
        db.session.add(payment)

        # clear cart
        Cart.query.filter_by(user_id=current_user.id).delete()

        db.session.commit()

        # send confirmation email if configured
        try:
            send_email_if_configured(current_user.email, 'Order placed', f'Your order #{order.id} was placed. Total: {subtotal}')
        except Exception:
            pass

        return redirect(url_for('shop.payment', order_id=order.id))

    subtotal = sum(item.product.price * item.quantity for item in cart_items)
    return render_template('checkout.html', cart_items=cart_items, subtotal=subtotal)


@bp.route('/payment/<int:order_id>')
@login_required
def payment(order_id):
    order = Order.query.get_or_404(order_id)
    # show simple payment page; integration with Stripe/other can be added if env keys present
    stripe_key = os.environ.get('STRIPE_PUBLISHABLE_KEY')
    return render_template('payment.html', order=order, stripe_key=stripe_key)


@bp.route('/payment/<int:order_id>/complete', methods=['POST'])
@login_required
def complete_payment(order_id):
    order = Order.query.get_or_404(order_id)
    # mark paid (in real app verify via gateway)
    order.payment_status = 'paid'
    order.status = 'confirmed'
    db.session.commit()
    try:
        send_email_if_configured(order.user.email, 'Payment received', f'Payment received for order #{order.id}. Thank you!')
    except Exception:
        pass
    flash('Payment completed. Order confirmed.', 'success')
    return redirect(url_for('shop.index'))
        