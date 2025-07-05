from flask_login import login_user
from routes.extensions import bcrypt
from routes.models import User

def authenticate(username, password):
    user = User.query.filter_by(username=username).first()
    if user and bcrypt.check_password_hash(user.password_hash, password):
        return user
    return None
