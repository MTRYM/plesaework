from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
import os
from datetime import datetime, timedelta
import secrets

from routes.extensions import db, bcrypt
from routes.models import User, UserSession
from . import auth_bp
from .forms import LoginForm, RegisterForm
from .utils import authenticate

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(
            username=form.username.data,
            password_hash=hashed_pw,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            age=form.age.data,
            rank_id=5 
        )
        db.session.add(user)
        db.session.commit()
        flash('Compte créé avec succès. Vous pouvez maintenant vous connecter.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth.html', form=form, title="Inscription")

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = authenticate(form.username.data, form.password.data)
        if user:
            login_user(user)

            session_token = secrets.token_urlsafe(32)
            user_session = UserSession(
                user_id=user.id,
                session_token=session_token,
                ip_address=request.remote_addr,
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=30)
            )
            db.session.add(user_session)

            user.last_login_at = datetime.utcnow()
            db.session.commit()

            flash('Connexion réussie ✅', 'success')
            return redirect(request.args.get('next') or url_for('dashboard.projects'))
        else:
            flash('Identifiants invalides ❌', 'danger')
    return render_template('auth.html', form=form, title="Connexion")

@auth_bp.route('/logout')
@login_required
def logout():
    UserSession.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()

    logout_user()
    flash("Déconnexion réussie 👋", "info")
    return redirect(url_for('auth.login'))
