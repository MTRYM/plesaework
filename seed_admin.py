# seed_admin.py
import os
from flask import Flask
from routes.extensions import db, bcrypt
from routes.models import User, Rank

# --- Initialisation minimale ---
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://srxw6645:Yb6t-G6rz-zJT!@localhost/srxw6645_juniorAssociation'  # ou MySQL URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
bcrypt.init_app(app)

# --- Script de seed ---
with app.app_context():
    # Vérifie si le rang admin existe
    admin_rank = Rank.query.filter_by(name='admin').first()
    if not admin_rank:
        print("❌ Le rang 'admin' n'existe pas. Abandon.")
        exit()

    # Vérifie si un user admin existe déjà
    existing_user = User.query.filter_by(username='admin').first()
    if existing_user:
        print("ℹ️ Utilisateur 'admin' existe déjà.")
    else:
        hashed_pw = bcrypt.generate_password_hash("admin123").decode('utf-8')
        user = User(
            username='admin',
            password_hash=hashed_pw,
            first_name='Super',
            last_name='Admin',
            age=30,
            rank_id=admin_rank.id
        )
        db.session.add(user)
        db.session.commit()
        print("✅ Utilisateur admin créé avec succès.")
        print("🔑 Identifiants de test → username: admin | password: admin123")
