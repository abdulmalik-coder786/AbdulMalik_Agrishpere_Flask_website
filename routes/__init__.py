from flask import Flask
from routes import auth_routes, forum_routes, blog_routes, shop_routes, admin_routes, profile_routes, consultant_routes,admin_routes

def create_app():
    app = Flask(__name__)

    # Secret key for sessions and flash messages
    app.secret_key = "supersecretkey"

    # ✅ Register all blueprints
    app.register_blueprint(auth_routes.bp)
    app.register_blueprint(forum_routes.bp)
    app.register_blueprint(blog_routes.bp)
    app.register_blueprint(shop_routes.bp)
    app.register_blueprint(admin_routes.bp)
    app.register_blueprint(profile_routes.bp)
    app.register_blueprint(consultant_routes.bp)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
