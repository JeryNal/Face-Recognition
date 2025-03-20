from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from flask import render_template, jsonify

def register_error_handlers(app):
    @app.errorhandler(Exception)
    def handle_exception(e):
        # Log the error
        log_error(e, "Unhandled exception")
        
        # Handle SQLAlchemy errors
        if isinstance(e, SQLAlchemyError):
            db.session.rollback()
            return render_template('errors/database.html'), 500
            
        # Handle HTTP errors
        if isinstance(e, HTTPException):
            return render_template(f'errors/{e.code}.html'), e.code
            
        # Handle API errors
        if request.is_json:
            return jsonify({
                'error': 'Internal server error',
                'message': str(e)
            }), 500
            
        # Default error handling
        return render_template('errors/500.html'), 500

    @app.errorhandler(404)
    def not_found_error(e):
        if request.is_json:
            return jsonify({'error': 'Not found'}), 404
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden_error(e):
        if request.is_json:
            return jsonify({'error': 'Forbidden'}), 403
        return render_template('errors/403.html'), 403 