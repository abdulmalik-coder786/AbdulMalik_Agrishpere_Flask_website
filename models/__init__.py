from flask_sqlalchemy import SQLAlchemy

# ✅ Single global db object
db = SQLAlchemy()

# ✅ Import models after db is created
from .user_model import User
from .post_model import Post,BlogComment
from .consultant_model import Consultant
from .consultation_models import Consultation
from .specialization_model import ConsultantSpecialization
from .product_model import Product, Review, ProductImage
from .order_model import Order, OrderItem, Cart, Payment, InventoryLog
from .forum_model import ForumTopic, ForumMessage

__all__ = ['User', 'Product', 'Review', 'ProductImage', 'Order', 'OrderItem', 'Cart', 'Payment', 'InventoryLog', 'Post', 'BlogComment', 'Consultant', 'Consultation', 'ConsultantSpecialization', 'ForumTopic', 'ForumMessage']
