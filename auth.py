from functools import wraps
from flask import flash, redirect, url_for
from database import db_session, User
from flask_login import current_user, login_required as flask_login_required

# Use Flask-Login's login_required decorator instead of custom one
login_required = flask_login_required

def get_current_user():
    """
    Get the current user from Flask-Login.
    """
    if current_user and current_user.is_authenticated:
        return current_user
    return None 