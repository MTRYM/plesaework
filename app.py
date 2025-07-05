import os
import logging
from flask import Flask, render_template
from dotenv import load_dotenv

from routes import create_routes
from routes.extensions import db, bcrypt
from routes.config import ProdConfig

from flask_login import LoginManager
from routes.models import User

load_dotenv()

app = Flask(__name__)
app.config.from_object(ProdConfig)

db.init_app(app)
bcrypt.init_app(app)

logging.basicConfig(
    filename='logs/app.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

app.logger.info("Flask a démarré")

with app.app_context():
    db.create_all()

create_routes(app)

@app.route('/')
def home():
    return render_template('index.html')
@app.route('/testcontact')
def test_contact_page():
    return render_template('contact.html')

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", message="Page non trouvée"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template("error.html", message="Erreur serveur"), 500

application = app

if __name__ == '__main__':
    app.run()
