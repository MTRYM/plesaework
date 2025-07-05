# routes/dashboard/forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField, FileField, IntegerField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Length, Email, Optional, Regexp, EqualTo, NumberRange
from flask_wtf.file import FileField, FileAllowed

class GroupForm(FlaskForm):
    name = StringField('Nom du projet', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[DataRequired()])
    chef_id = SelectField('Chef de projet', coerce=int, validators=[DataRequired()])
    submit_group = SubmitField('Créer le projet')

class UserForm(FlaskForm):
    username = StringField('Nom d’utilisateur', validators=[DataRequired(), Length(min=3, max=50)])
    password = PasswordField('Mot de passe', validators=[DataRequired(), Length(min=6)])
    first_name = StringField('Prénom', validators=[DataRequired()])
    last_name = StringField('Nom', validators=[DataRequired()])
    age = IntegerField('Âge', validators=[NumberRange(min=10, max=100)])
    
    email = StringField('Adresse e-mail', validators=[Optional(), Email()])
    phone = StringField('Numéro de téléphone', validators=[
        Optional(),
        Regexp(r'^\+?\d{7,15}$', message="Numéro invalide")
    ])
    
    rank_id = SelectField('Rang', coerce=int, validators=[DataRequired()])
    submit_user = SubmitField('Créer utilisateur')

class DiscussionForm(FlaskForm):
    title = StringField("Titre de la discussion", validators=[DataRequired()])
    group_id = SelectField("Projet", coerce=int, validators=[DataRequired()])
    admin_id = SelectField("Admin destinataire", coerce=int, validators=[DataRequired()])
    submit = SubmitField("Créer")
    
class MemberSearchForm(FlaskForm):
    query = StringField('Recherche', validators=[Optional()])

class EditUserForm(FlaskForm):
    username = StringField('Nom d’utilisateur', validators=[Optional(), Length(min=3, max=50)])
    first_name = StringField('Prénom', validators=[Optional(), Length(max=50)])
    last_name = StringField('Nom', validators=[Optional(), Length(max=50)])
    age = IntegerField('Âge', validators=[Optional(), NumberRange(min=10, max=100)])
    email = StringField('Email', validators=[Optional(), Email()])
    phone = StringField('Téléphone', validators=[Optional(), Length(max=20)])
    rank_id = SelectField('Rôle', coerce=int, validators=[Optional()])

    profile_picture = FileField('Photo de profil', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images uniquement !')
    ])
    
    delete_account = BooleanField("Supprimer le compte")

class BaseSettingsForm(FlaskForm):
    username = StringField('Nom d’utilisateur', validators=[Optional(), Length(min=3, max=50)])
    email = StringField('Email', validators=[Optional(), Email()])
    phone = StringField('Téléphone', validators=[Optional(), Length(max=20)])
    age = IntegerField('Âge', validators=[Optional(), NumberRange(min=10, max=100)])
    submit = SubmitField('Enregistrer')


class PasswordForm(FlaskForm):
    current_password = PasswordField('Mot de passe actuel', validators=[Optional()])
    new_password = PasswordField('Nouveau mot de passe', validators=[
        Optional(), Length(min=6),
        EqualTo('confirm_password', message='Les mots de passe doivent correspondre.')
    ])
    confirm_password = PasswordField('Confirmer le mot de passe', validators=[Optional()])
    submit = SubmitField('Changer le mot de passe')


class PreferencesForm(FlaskForm):
    profile_picture = FileField('Photo de profil', validators=[Optional()])
    theme = SelectField('Thème', choices=[('light', 'Clair'), ('dark', 'Sombre')], validators=[Optional()])
    language = SelectField('Langue', choices=[('fr', 'Français'), ('en', 'Anglais')], validators=[Optional()])
    submit = SubmitField('Enregistrer')


class DeleteAccountForm(FlaskForm):
    delete_account = SubmitField('Supprimer mon compte')
