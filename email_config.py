from flask import url_for
from flask_mail import Mail, Message
import os
import logging

mail_settings = {
    "MAIL_SERVER": 'smtp.gmail.com',
    "MAIL_PORT": 587,
    "MAIL_USE_TLS": True,
    "MAIL_USE_SSL": False,
    "MAIL_USERNAME": os.getenv('EMAIL_USER', 'your-email@gmail.com'),
    "MAIL_PASSWORD": os.getenv('EMAIL_PASSWORD', 'your-app-specific-password')
}

def init_mail(app):
    app.config.update(mail_settings)
    return Mail(app)

def send_verification_email(mail, email, token):
    msg = Message(
        'Verify Your Email - Face Recognition System',
        sender=mail_settings["MAIL_USERNAME"],
        recipients=[email]
    )
    msg.body = f'''To verify your email, visit the following link:
{url_for('verify_email', token=token, _external=True)}

If you did not make this request, please ignore this email.
'''
    mail.send(msg)

def send_reset_password_email(mail, email, token):
    msg = Message(
        'Password Reset Request - Face Recognition System',
        sender=mail_settings["MAIL_USERNAME"],
        recipients=[email]
    )
    msg.body = f'''To reset your password, visit the following link:
{url_for('reset_password', token=token, _external=True)}

If you did not make this request, please ignore this email.
'''
    mail.send(msg) 