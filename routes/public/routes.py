import os
import smtplib
import ssl
from email.message import EmailMessage
from flask import Blueprint, render_template, request, jsonify
from . import public_bp

@public_bp.route("/contact", methods=["GET"])
def contact_page():
    return render_template("contact.html")


@public_bp.route("/contact/send", methods=["POST"])
def send_contact_message():
    data = request.get_json()
    user_email = data.get("email")
    message_html = data.get("message")

    if not user_email or not message_html:
        return jsonify({"success": False, "error": "Champs manquants"}), 400

    try:
        smtp_server = os.environ.get('SMTP_SERVER')
        smtp_port = int(os.environ.get('SMTP_PORT', 465))
        smtp_username = os.environ.get('SMTP_USERNAME')
        smtp_password = os.environ.get('SMTP_PASSWORD')
        receiver_email = os.environ.get('FEEDBACK_RECEIVER')

        msg = EmailMessage()
        msg['Subject'] = f"Message depuis le formulaire contact ({user_email})"
        msg['From'] = smtp_username
        msg['To'] = receiver_email
        msg.set_content("Message au format HTML.", subtype="plain")
        msg.add_alternative(message_html, subtype="html")

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
            server.login(smtp_username, smtp_password)
            server.send_message(msg)

        return jsonify({"success": True}), 200

    except Exception as e:
        print("Erreur d'envoi :", e)
        return jsonify({"success": False, "error": "Erreur serveur"}), 500
