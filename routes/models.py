from datetime import datetime
from .extensions import db
from flask_login import UserMixin

class Rank(db.Model):
    __tablename__ = 'ranks'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    level = db.Column(db.Integer, nullable=False, default=0)

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    age = db.Column(db.Integer)

    email = db.Column(db.String(120), unique=True)
    phone = db.Column(db.String(20))
    language = db.Column(db.String(5), default='fr')
    theme = db.Column(db.String(10), default='light')

    profile_picture_url = db.Column(db.String(255))

    rank_id = db.Column(db.Integer, db.ForeignKey('ranks.id'))
    rank = db.relationship('Rank', backref=db.backref('users', lazy=True))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = db.Column(db.DateTime)
    def is_in_project(self, project_id):
        return any(m.group_id == project_id for m in self.group_memberships)

    def role_in_project(self, project_id):
        membership = next((m for m in self.group_memberships if m.group_id == project_id), None)
        return membership.role_in_group if membership else None
        
class Group(db.Model):
    __tablename__ = 'groups'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship('User', backref=db.backref('created_groups', lazy=True))

class GroupMembership(db.Model):
    __tablename__ = 'group_memberships'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    role_in_group = db.Column(
        db.Enum('chef', 'trésorier', 'messager', 'membre', name='group_roles'),
        default='membre'
    )

    user = db.relationship('User', backref=db.backref('group_memberships', lazy=True))
    group = db.relationship('Group', backref=db.backref('memberships', lazy=True))

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    edited_at = db.Column(db.DateTime)
    discussion_id = db.Column(db.Integer, db.ForeignKey('discussions.id'), nullable=False)

    sender = db.relationship('User', backref=db.backref('sent_messages', lazy=True))
    group = db.relationship('Group', backref=db.backref('messages', lazy=True))
    
class Discussion(db.Model):
    __tablename__ = 'discussions'
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    group = db.relationship('Group', backref='discussions')
    creator = db.relationship('User', foreign_keys=[created_by])
    admin = db.relationship('User', foreign_keys=[admin_id])


class File(db.Model):
    __tablename__ = 'files'
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey('messages.id'), nullable=False)
    file_url = db.Column(db.Text, nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    message = db.relationship('Message', backref=db.backref('files', lazy=True))

class MessageReaction(db.Model):
    __tablename__ = 'message_reactions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message_id = db.Column(db.Integer, db.ForeignKey('messages.id'), nullable=False)
    emoji = db.Column(db.String(10), nullable=False)
    reacted_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('reactions', lazy=True))
    message = db.relationship('Message', backref=db.backref('reactions', lazy=True))

class UserSession(db.Model):
    __tablename__ = 'user_sessions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_token = db.Column(db.String(255), unique=True, nullable=False)
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)

    user = db.relationship('User', backref=db.backref('sessions', lazy=True))

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(255), nullable=False)
    details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('audit_logs', lazy=True))

class MindMap(db.Model):
    __tablename__ = 'mind_maps'
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("groups.id"), nullable=False)
    title = db.Column(db.String(255), default="Carte Mentale")
    data = db.Column(db.Text, default="{}")  # JSON brut
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    group = db.relationship("Group", backref="mind_map", lazy=True)
    
class MindMapNode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mind_map_id = db.Column(db.Integer, db.ForeignKey('mind_maps.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('mind_map_node.id'), nullable=True)
    content = db.Column(db.Text, nullable=False)
    pos_x = db.Column(db.Float, default=0.0)
    pos_y = db.Column(db.Float, default=0.0)
    bg_color = db.Column(db.String(20), default="#ffffff")
    text_color = db.Column(db.String(20), default="#000000")
    type = db.Column(db.String(20), default="descriptive")  # <--- AJOUT ICI

    parent = db.relationship('MindMapNode', remote_side=[id], backref='children')
