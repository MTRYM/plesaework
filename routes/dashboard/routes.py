# routes/dashboard/routes.py

from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user, logout_user
from sqlalchemy import or_
from routes.extensions import db, bcrypt
from routes.models import Group, User, GroupMembership
from . import dashboard_bp
from .forms import GroupForm, UserForm, MemberSearchForm, BaseSettingsForm, PasswordForm, PreferencesForm, DeleteAccountForm
from .utils import get_chefs_de_groupe, get_all_ranks
from flask import jsonify
from werkzeug.utils import secure_filename
import os
import uuid
import json

@dashboard_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_group():
    if not current_user.rank or current_user.rank.name != 'admin':
        flash("Accès réservé aux administrateurs.", "danger")
        return redirect(url_for('dashboard.projects'))
    print("run create group")
    group_form = GroupForm()
    group_form.chef_id.choices = [(u.id, f"{u.first_name} {u.last_name}") for u in get_chefs_de_groupe()]

    user_form = UserForm()
    user_form.rank_id.choices = [
        (r.id, r.name.capitalize()) for r in get_all_ranks() if r.name in ['admin', 'membre']
    ]


    if 'submit_group' in request.form and group_form.validate_on_submit():
        group = Group(
            name=group_form.name.data,
            description=group_form.description.data,
            created_by=group_form.chef_id.data
        )
        db.session.add(group)
        db.session.commit()
        membership = GroupMembership(
        group_id=group.id,
            user_id=group.created_by,
            role_in_group='chef'
        )
        db.session.add(membership)
        db.session.commit()

        flash("Projet créé avec succès", "success")
        return redirect(url_for('dashboard.create_group'))

    if 'submit_user' in request.form and user_form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(user_form.password.data).decode('utf-8')
        user = User(
            username=user_form.username.data,
            password_hash=hashed_pw,
            first_name=user_form.first_name.data,
            last_name=user_form.last_name.data,
            age=user_form.age.data,
            rank_id=user_form.rank_id.data,
            email=user_form.email.data or None,
            phone=user_form.phone.data or None
        )
        db.session.add(user)
        db.session.commit()
        flash("Utilisateur créé avec succès", "success")
        return redirect(url_for('dashboard.create_group'))

    return render_template('dashboard/create.html', group_form=group_form, user_form=user_form, user=current_user)

@dashboard_bp.route('/add-user-to-group', methods=['POST'])
@login_required
def add_user_to_group():
    from routes.models import GroupMembership, Group, User

    group_id = request.form.get('group_id')
    user_id = request.form.get('user_id')
    role = request.form.get('role')

    group = Group.query.get_or_404(group_id)
    user = User.query.get_or_404(user_id)

    if not current_user.rank or current_user.rank.name not in ['admin', 'chef_de_groupe']:
        flash("Accès refusé. Seuls les admins et chefs peuvent ajouter des membres.", "danger")
        return redirect(url_for('dashboard.project_view', project_id=group.id))

    existing = GroupMembership.query.filter_by(group_id=group.id, user_id=user.id).first()
    
    allowed_roles = ['chef', 'trésorier', 'messager', 'membre']

    if existing:
        flash("Cet utilisateur est déjà dans le projet.", "warning")
    else:
        if role not in allowed_roles:
            flash("Rôle de projet invalide.", "danger")
            return redirect(url_for('dashboard.project_view', project_id=group.id))

        membership = GroupMembership(
            group_id=group.id,
            user_id=user.id,
            role_in_group=role
        )
        db.session.add(membership)
        db.session.commit()
        flash(f"{user.first_name} a été ajouté au projet comme {role}.", "success")

    return redirect(url_for('dashboard.project_view', project_id=group.id))


    return redirect(url_for('dashboard.project_view', project_id=group.id))

@dashboard_bp.route('/remove-user-from-group/<int:group_id>/<int:user_id>', methods=['POST'])
@login_required
def remove_user_from_group(group_id, user_id):
    group = Group.query.get_or_404(group_id)
    user_to_remove = User.query.get_or_404(user_id)

    membership = GroupMembership.query.filter_by(group_id=group.id, user_id=user_id).first()
    if not membership:
        flash("Utilisateur non trouvé dans ce projet.", "warning")
        return redirect(url_for('dashboard.project_view', project_id=group.id))

    is_admin = current_user.rank and current_user.rank.name == 'admin'
    is_chef = current_user.id == group.created_by

    if not (is_admin or is_chef):
        flash("Action interdite.", "danger")
        return redirect(url_for('dashboard.project_view', project_id=group.id))

    if user_to_remove.id == group.created_by and not is_admin:
        flash("Seul un admin peut gérer le chef de groupe.", "warning")
        return redirect(url_for('dashboard.project_view', project_id=group.id))

    user_rank = user_to_remove.rank.name if user_to_remove.rank else "membre"

    if user_rank in ["trésorier", "messager"]:
        from routes.models import Rank
        new_rank = Rank.query.filter_by(name="membre").first()
        user_to_remove.rank = new_rank
        db.session.commit()
        flash(f"{user_to_remove.username} est redevenu membre.", "info")
    elif user_rank == "membre":
        db.session.delete(membership)
        db.session.commit()
        flash(f"{user_to_remove.username} a été retiré du projet.", "info")
    elif user_rank == "chef":
        flash("Impossible de supprimer un chef de groupe (sauf admin).", "danger")

    return redirect(url_for('dashboard.project_view', project_id=group.id))


@dashboard_bp.route('/projects')
@login_required
def projects():
    from routes.models import Group, GroupMembership, Rank

    search_query = request.args.get('search')

    is_admin = current_user.rank and current_user.rank.name == 'admin'

    if is_admin:
        base_query = Group.query
    else:
        base_query = Group.query.filter(
            or_(
                Group.created_by == current_user.id,
                Group.memberships.any(GroupMembership.user_id == current_user.id)
            )
        )

    if search_query:
        user_projects = base_query.filter(Group.name.ilike(f'%{search_query}%')).all()
    else:
        user_projects = base_query.all()

    return render_template(
        'dashboard/projects.html',
        projects=user_projects,
        user=current_user
    )


@dashboard_bp.route('/project/<int:project_id>')
@login_required
def project_view(project_id):
    group = Group.query.get_or_404(project_id)

    memberships = GroupMembership.query.filter_by(group_id=group.id).all()
    member_ids = [m.user_id for m in memberships]

    users_by_rank = {
        'chef': [],
        'trésorier': [],
        'messager': [],
        'membre': []
    }


    for m in memberships:
        role = m.role_in_group or 'membre'
        if role not in users_by_rank:
            users_by_rank['membre'].append(m.user)  # fallback si erreur
        else:
            users_by_rank[role].append(m.user)



    treasurers_list = users_by_rank.get('trésorier', [])
    tresorier_user = treasurers_list[0] if treasurers_list else None

    all_users = User.query.filter(User.id.notin_(member_ids)).all()

    return render_template(
        'dashboard/project-view.html',
        group=group,
        users_by_rank=users_by_rank,
        all_users=all_users,
        user=current_user,
        tresorier=tresorier_user
    )


@dashboard_bp.route('/messages')
@login_required
def messages():
    from routes.models import GroupMembership, Discussion, Group, User, Rank
    from routes.dashboard.forms import DiscussionForm
    from sqlalchemy import or_

    memberships = GroupMembership.query.filter_by(user_id=current_user.id, role_in_group='messager').all()
    group_ids = [m.group_id for m in memberships]

    discussions = Discussion.query.filter(
        or_(
            Discussion.created_by == current_user.id,
            Discussion.admin_id == current_user.id,
            Discussion.group_id.in_(group_ids)
        )
    ).order_by(Discussion.created_at.desc()).all()

    # Préparer les groupes pour le formulaire si utilisateur est messager
    groups = Group.query.filter(Group.id.in_(group_ids)).all()

    admin_rank = Rank.query.filter_by(name='admin').first()
    admins = User.query.filter_by(rank_id=admin_rank.id).all() if admin_rank else []

    discussion_form = DiscussionForm()
    discussion_form.group_id.choices = [(g.id, g.name) for g in groups]
    discussion_form.admin_id.choices = [(a.id, f"{a.first_name} {a.last_name}") for a in admins]

    user_in_group = GroupMembership.query.filter_by(
        user_id=current_user.id
    ).first()

    return render_template(
        'dashboard/messages.html',
        groups=groups,
        discussions=discussions,
        user=current_user,
        group_admins=admins,
        discussion_form=discussion_form,
        user_in_group=user_in_group
    )

    
@dashboard_bp.route('/create-discussion', methods=['POST'])
@login_required
def create_discussion():
    from routes.dashboard.forms import DiscussionForm
    from routes.models import Discussion, GroupMembership, Group, User, Rank

    form = DiscussionForm()

    # Groupes où le current_user est messager
    memberships = GroupMembership.query.filter_by(user_id=current_user.id, role_in_group='messager').all()
    group_ids = [m.group_id for m in memberships]
    groups = Group.query.filter(Group.id.in_(group_ids)).all()

    admin_rank = Rank.query.filter_by(name='admin').first()

    admin_users = User.query.filter_by(rank_id=admin_rank.id).all() if admin_rank else []

    if current_user.rank and current_user.rank.name == 'admin':
        messager_user_ids = db.session.query(GroupMembership.user_id).filter_by(role_in_group='messager').distinct()
        messager_users = User.query.filter(User.id.in_(messager_user_ids)).all()
        print(messager_users)
        # Fusionne les deux listes sans doublons
        all_recipients = {u.id: f"{u.first_name} {u.last_name}" for u in admin_users + messager_users}
    else:
        # Sinon, seulement les admins visibles
        all_recipients = {a.id: f"{a.first_name} {a.last_name}" for a in admin_users}

    # Injecte les choices dans le form
    form.group_id.choices = [(g.id, g.name) for g in groups]
    form.admin_id.choices = list(all_recipients.items())

    if not form.validate_on_submit():
        flash("Erreur dans le formulaire.", "danger")
        return redirect(url_for('dashboard.messages'))

    group_id = form.group_id.data
    admin_id = form.admin_id.data
    title = form.title.data

    # Vérifie que current_user est bien messager dans ce groupe
    membership = GroupMembership.query.filter_by(
        user_id=current_user.id,
        group_id=group_id,
        role_in_group='messager'
    ).first()

    if not membership:
        flash("Vous n'êtes pas messager dans ce groupe.", "danger")
        return redirect(url_for('dashboard.messages'))

    discussion = Discussion(
        title=title,
        group_id=group_id,
        created_by=current_user.id,
        admin_id=admin_id
    )
    db.session.add(discussion)
    db.session.commit()
    flash("Discussion créée avec succès.", "success")
    return redirect(url_for('dashboard.messages'))
    
    
@dashboard_bp.route('/get-messages/<int:discussion_id>')
@login_required
def get_messages(discussion_id):
    from routes.models import Message, Discussion, GroupMembership
    from sqlalchemy import and_

    after_id = request.args.get("after_id", type=int)

    discussion = Discussion.query.get_or_404(discussion_id)

    is_creator = discussion.created_by == current_user.id
    is_admin = discussion.admin_id == current_user.id
    membership = GroupMembership.query.filter_by(
        user_id=current_user.id,
        group_id=discussion.group_id
    ).first()

    if not (is_creator or is_admin or membership):
        return {"error": "Accès refusé."}, 403

    query = Message.query.filter_by(discussion_id=discussion.id)
    if after_id:
        query = query.filter(Message.id > after_id)

    messages = query.order_by(Message.sent_at.asc()).all()

    return {
        "discussion_title": discussion.title,
        "messages": [
            {
                "id": m.id,
                "content": m.content,
                "sent_at": m.sent_at.strftime("%d/%m/%Y %H:%M"),
                "from_current_user": m.sender_id == current_user.id,
                "sender_name": f"{m.sender.first_name} {m.sender.last_name}"
            } for m in messages
        ]
    }


@dashboard_bp.route('/send-message', methods=['POST'])
@login_required
def send_message():
    from routes.models import Message, Discussion

    data = request.get_json()
    discussion_id = data.get('discussion_id')
    content = data.get('content')

    discussion = Discussion.query.get_or_404(discussion_id)

    # Vérifie accès
    if current_user.id not in [discussion.created_by, discussion.admin_id]:
        return {"error": "Accès refusé."}, 403

    new_msg = Message(
        sender_id=current_user.id,
        group_id=discussion.group_id,
        content=content,
        discussion_id=discussion.id
    )
    db.session.add(new_msg)
    db.session.commit()

    return {
        "id": new_msg.id,
        "content": new_msg.content,
        "sent_at": new_msg.sent_at.strftime("%d/%m/%Y %H:%M"),
        "from_current_user": True,
        "sender_name": f"{current_user.first_name} {current_user.last_name}"
    }
    
@dashboard_bp.route('/members', methods=['GET', 'POST'])
@login_required
def members():
    if not current_user.rank or current_user.rank.name != 'admin':
        flash("Accès réservé aux administrateurs.", "danger")
        return redirect(url_for('dashboard.projects'))

    form = MemberSearchForm()
    query = form.query.data or ""

    members_query = User.query

    if query:
        # Recherche sur username ou prénom
        members_query = members_query.filter(
            or_(
                User.username.ilike(f"%{query}%"),
                User.first_name.ilike(f"%{query}%")
            )
        )

    members = members_query.order_by(User.first_name.asc()).all()

    return render_template("dashboard/members.html", form=form, members=members, user=current_user)
    
@dashboard_bp.route('/edit-member/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_member(user_id):
    from routes.models import User
    from .forms import EditUserForm

    if not current_user.rank or current_user.rank.name != 'admin':
        flash("Accès réservé aux administrateurs.", "danger")
        return redirect(url_for('dashboard.members'))

    user = User.query.get_or_404(user_id)
    form = EditUserForm(obj=user)
    form.rank_id.choices = [(r.id, r.name.capitalize()) for r in get_all_ranks()]

    if form.validate_on_submit():
        user.username = form.username.data
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.age = form.age.data
        user.email = form.email.data
        user.phone = form.phone.data
        user.rank_id = form.rank_id.data

        if form.profile_picture.data:
            picture = form.profile_picture.data
            filename = secure_filename(picture.filename)
            ext = filename.rsplit('.', 1)[-1].lower()
            if ext in ['png', 'jpg', 'jpeg', 'gif']:
                unique_filename = f"{user.id}_{uuid.uuid4().hex}.{ext}"
                upload_folder = os.path.join('static', 'images/user_image/')
                os.makedirs(upload_folder, exist_ok=True)
                path = os.path.join(upload_folder, unique_filename)
                picture.save(path)
                user.profile_picture_url = f"/static/images/user_image/{unique_filename}"

        if form.delete_account.data:
            db.session.delete(user)
            db.session.commit()
            flash("Compte utilisateur supprimé.", "info")
            return redirect(url_for('dashboard.members'))

        db.session.commit()
        flash("Informations mises à jour avec succès.", "success")
        return redirect(url_for('dashboard.members'))

    return render_template('dashboard/edit_member.html', form=form, user=user)
    
@dashboard_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    base_form = BaseSettingsForm(obj=current_user)
    password_form = PasswordForm()
    preferences_form = PreferencesForm()
    delete_form = DeleteAccountForm()

    if "submit_base" in request.form and base_form.validate_on_submit():
        print("[DEBUG] Mise à jour infos de base.")
        current_user.username = base_form.username.data
        current_user.email = base_form.email.data
        current_user.phone = base_form.phone.data
        current_user.age = base_form.age.data
        db.session.commit()
        flash("Informations mises à jour", "success")
        return redirect(url_for('dashboard.settings'))

    if "submit_password" in request.form and password_form.validate_on_submit():
        print("[DEBUG] Changement mot de passe")
        if bcrypt.check_password_hash(current_user.password_hash, password_form.current_password.data):
            current_user.password_hash = bcrypt.generate_password_hash(password_form.new_password.data).decode('utf-8')
            db.session.commit()
            flash("Mot de passe mis à jour", "success")
        else:
            flash("Mot de passe actuel incorrect", "danger")
        return redirect(url_for('dashboard.settings'))

    if "submit_preferences" in request.form and preferences_form.validate_on_submit():
        print("[DEBUG] Préférences soumises")
        current_user.theme = preferences_form.theme.data
        current_user.language = preferences_form.language.data

        picture = preferences_form.profile_picture.data
        if picture:
            print("[DEBUG] Nouvelle image détectée")
            filename = secure_filename(picture.filename)
            ext = filename.rsplit('.', 1)[-1].lower()
            if ext in ['png', 'jpg', 'jpeg', 'gif']:
                unique_filename = f"{current_user.id}_{uuid.uuid4().hex}.{ext}"
                upload_folder = os.path.join('static', 'images/user_image/')
                os.makedirs(upload_folder, exist_ok=True)
                path = os.path.join(upload_folder, unique_filename)
                picture.save(path)
                current_user.profile_picture_url = f"/static/images/user_image/{unique_filename}"
                print("[DEBUG] Image sauvegardée")
            else:
                print("[DEBUG] Extension non autorisée :", ext)

        db.session.commit()
        flash("Préférences mises à jour", "success")
        return redirect(url_for('dashboard.settings'))
    
    if "delete_account" in request.form and delete_form.validate_on_submit():
        print("[DEBUG] Compte supprimé")
        db.session.delete(current_user)
        db.session.commit()
        flash("Compte supprimé", "info")
        return redirect(url_for('auth.logout'))

    return render_template("dashboard/settings.html", 
        user=current_user,
        base_form=base_form,
        password_form=password_form,
        preferences_form=preferences_form,
        delete_form=delete_form
    )
    
    
@dashboard_bp.route('/project/<int:project_id>/mind-map')
@login_required
def mind_map(project_id):
    from routes.models import Group, MindMap

    print("\n--- [DEBUG] Entrée route /mind-map ---")
    group = Group.query.get_or_404(project_id)
    print(f"[DEBUG] Groupe trouvé : {group.name} (ID={group.id})")

    mindmap = MindMap.query.filter_by(group_id=project_id).first()

    if not mindmap:
        print("[DEBUG] Aucune mindmap existante, création en cours...")
        default_data = {
            "nodeData": {
                "id": "root",
                "topic": group.name,
                "children": [],
                "root": True  # <-- 🔥 AJOUT CRITIQUE
            },
            "linkData": {},
            "noteData": {},
            "expand": {}
        }
        mindmap = MindMap(
            group_id=project_id,
            title="Carte Mentale",
            data=json.dumps(default_data)
        )
        db.session.add(mindmap)
        db.session.commit()
        print("[DEBUG] Mindmap créée et ajoutée à la DB.")


    print("[DEBUG] Données de la mindmap :")
    print(mindmap.data)
    print("--- [DEBUG] Fin route /mind-map ---\n")

    return render_template(
        "dashboard/mind_map.html",
        project=group,
        mindmap=mindmap,
        user=current_user
    )


@dashboard_bp.route('/project/<int:project_id>/mind-map/save', methods=['POST'])
@login_required
def save_mind_map(project_id):
    from routes.models import MindMap
    group = Group.query.get_or_404(project_id)

    if current_user.role_in_project(project_id) not in ['chef', 'trésorier']:
        print(f"[ERROR] Accès refusé à l'utilisateur {current_user.username}")
        return jsonify(error="Accès refusé"), 403

    data = request.get_json()
    print(f"[DEBUG] Données reçues pour sauvegarde : {data}")

    mind_map = MindMap.query.filter_by(group_id=project_id).first_or_404()
    mind_map.data = json.dumps(data)
    db.session.commit()
    print("[DEBUG] Mindmap sauvegardée avec succès.")
    return jsonify(success=True)
