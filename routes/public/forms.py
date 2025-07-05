from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Email, Length

class ContactForm(FlaskForm):
    email = StringField("Votre adresse e-mail", validators=[
        DataRequired(), Email(), Length(max=120)
    ])
    submit = SubmitField("Envoyer")
