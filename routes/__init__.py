from flask import Flask
from .auth import auth_bp
from .dashboard import dashboard_bp
from .public import public_bp

def create_routes(app: Flask):
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(public_bp)
