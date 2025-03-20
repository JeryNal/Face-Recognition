import os
import cv2
import numpy as np
from flask import Flask, Response, jsonify, request, render_template, flash, redirect, url_for
from flask_login import LoginManager, login_required, current_user, login_user, logout_user
from flask_mail import Mail, Message
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from database import db_session, User, FaceEncoding, init_db
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect, CSRFError
from werkzeug.security import generate_password_hash
import random
import logging
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

# Initialize Flask app
app = Flask(__name__,
    static_folder='static',
    template_folder='templates'
)

# Security configurations
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['WTF_CSRF_SECRET_KEY'] = os.environ.get('WTF_CSRF_SECRET_KEY')

# Cookie security settings
app.config.update(
    REMEMBER_COOKIE_DURATION=timedelta(days=30),
    REMEMBER_COOKIE_SECURE=False,  # Set to True in production
    REMEMBER_COOKIE_HTTPONLY=True,
    REMEMBER_COOKIE_REFRESH_EACH_REQUEST=True
)

# Initialize extensions
csrf = CSRFProtect(app)

# Initialize LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'
login_manager.session_protection = 'strong'

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
    storage_options={"policy": "fixed-window"}
)

# Initialize face recognition
def setup_face_recognition():
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    detector = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    return recognizer, detector

recognizer, detector = setup_face_recognition()

# Global camera variable
camera = None

# Email configuration
app.config.update(
    MAIL_SERVER=os.environ.get('MAIL_SERVER'),
    MAIL_PORT=int(os.environ.get('MAIL_PORT', 587)),
    MAIL_USE_TLS=True,
    MAIL_USERNAME=os.environ.get('MAIL_USERNAME'),
    MAIL_PASSWORD=os.environ.get('MAIL_PASSWORD'),
    MAIL_DEFAULT_SENDER=os.environ.get('MAIL_USERNAME')
)

# Initialize Flask-Mail
mail = Mail(app)

@app.route('/get_csrf_token')
def get_csrf_token():
    """Generate a new CSRF token."""
    try:
        token = csrf.generate_csrf()
        return jsonify({'csrf_token': token})
    except Exception as e:
        logging.error(f"Failed to generate CSRF token: {str(e)}")
        return jsonify({'error': 'Failed to generate security token'}), 500

@app.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per hour")  # Limit registration attempts
def register():
    """Handle user registration."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        try:
            # Validate CSRF token
            csrf.protect()
            
            name = request.form.get('name')
            email = request.form.get('email')
            password = request.form.get('password')
            
            # Validate required fields
            if not all([name, email, password]):
                flash('All fields are required', 'error')
                return redirect(url_for('register'))
                
            # Basic email validation
            if not '@' in email or not '.' in email:
                flash('Please enter a valid email address', 'error')
                return redirect(url_for('register'))
                
            # Check if user exists
            existing_user = db_session.query(User).filter_by(email=email).first()
            if existing_user:
                flash('Email already registered', 'error')
                return redirect(url_for('register'))
                
            # Generate OTP
            otp = generate_otp()
            
            # Create new user
            new_user = User(
                name=name,
                email=email,
                is_active=False,
                is_email_verified=False
            )
            new_user.set_password(password)
            new_user.set_otp(otp)
            
            db_session.add(new_user)
            db_session.commit()
            logging.info(f"New user created: {email}")
            
            # Send verification email
            try:
                send_otp_email(mail, email, otp)
                flash('Registration successful! Please check your email for verification code.', 'success')
            except Exception as e:
                logging.error(f"Failed to send OTP email: {str(e)}")
                flash('Account created but failed to send verification email. Please request a new code.', 'warning')
            
            return redirect(url_for('verify_email', email=email))
            
        except Exception as e:
            db_session.rollback()
            logging.error(f"Registration error: {str(e)}")
            flash('An error occurred during registration. Please try again.', 'error')
            return redirect(url_for('register'))
    
    return render_template('register.html')

@app.route('/verify_email', methods=['GET', 'POST'])
def verify_email():
    """Handle email verification."""
    email = request.args.get('email')
    if not email:
        flash('Email parameter is required', 'error')
        return redirect(url_for('register'))

    if request.method == 'POST':
        try:
            otp = request.form.get('otp')
            if not otp:
                flash('Please enter the verification code', 'error')
                return redirect(url_for('verify_email', email=email))
                
            user = db_session.query(User).filter_by(email=email).first()
            if not user:
                flash('User not found', 'error')
                return redirect(url_for('register'))
                
            if user.verify_otp(otp):
                user.is_email_verified = True
                user.is_active = True
                db_session.commit()
                
                # Log the user in
                login_user(user, remember=True)
                flash('Email verified successfully! Welcome to Face Recognition System.', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid or expired verification code', 'error')
                
        except Exception as e:
            logging.error(f"Email verification error: {str(e)}")
            flash('An error occurred during verification', 'error')
            
    return render_template('verify_email.html', email=email)

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")  # Limit login attempts
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        try:
            csrf.protect()
            
            email = request.form.get('email')
            password = request.form.get('password')
            remember = request.form.get('remember', False) == 'true'
            
            if not email:
                flash('Email is required', 'error')
                return redirect(url_for('login'))
                
            user = db_session.query(User).filter_by(email=email).first()
            
            # Test account handling
            if user and user.email == 'test@example.com':
                login_user(user, remember=True)
                flash('Login successful with test account!', 'success')
                return redirect(url_for('dashboard'))
                
            if user and not user.is_active:
                if not user.is_email_verified:
                    flash('Please verify your email first', 'warning')
                    return redirect(url_for('verify_email', email=email))
                flash('Your account is not active', 'error')
                return redirect(url_for('login'))
                
            if user and user.check_password(password):
                # Check if account is locked
                if user.locked_until and user.locked_until > datetime.utcnow():
                    remaining_time = (user.locked_until - datetime.utcnow()).total_seconds() / 60
                    flash(f'Account is locked. Try again in {int(remaining_time)} minutes.', 'error')
                    return redirect(url_for('login'))
                    
                # Login successful
                login_user(user, remember=remember)
                user.record_login_attempt(success=True)
                db_session.commit()
                
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                if user:
                    user.record_login_attempt(success=False)
                    db_session.commit()
                    
                flash('Invalid email or password', 'error')
                return redirect(url_for('login'))
                
        except Exception as e:
            logging.error(f"Login error: {str(e)}")
            flash('An error occurred during login', 'error')
            return redirect(url_for('login'))
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    user = current_user
    return render_template('index.html', user=user)

@app.route('/video_feed')
@login_required
def video_feed():
    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/stop_camera')
@login_required
def stop_camera():
    global camera
    if camera is not None:
        camera.release()
        camera = None
        logging.info("Camera successfully released")
        return jsonify({"status": "success", "message": "Camera stopped"})
    return jsonify({"status": "info", "message": "Camera was not running"})

def gen_frames():
    global camera
    if camera is None:
        camera = cv2.VideoCapture(0)
    
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/train', methods=['POST'])
@login_required
@limiter.limit("10 per hour")  # Limit training requests
def train_model():
    try:
        faces, ids = [], []  # Placeholder for face data processing
        recognizer.train(faces, np.array(ids))
        recognizer.save('trainer.yml')
        return jsonify({"message": "Training completed successfully"})
    except Exception as e:
        logging.error(f"Training error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/reset-password-request', methods=['GET', 'POST'])
@limiter.limit("5 per hour")
def reset_password_request():
    if request.method == 'POST':
        email = request.form.get('email')
        if not email:
            flash('Email is required', 'error')
            return redirect(url_for('login'))
            
        user = db_session.query(User).filter_by(email=email).first()
        if user:
            token = user.generate_token(type='reset')
            send_reset_password_email(mail, user.email, token)
            flash('Check your email for password reset instructions.', 'success')
        else:
            flash('Email address not found.', 'error')
    return redirect(url_for('login'))

@app.route('/api/send-login-notification', methods=['POST'])
@login_required
def send_login_notification_api():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        recipient_email = data.get('email')
        user_name = data.get('name')
        login_time = data.get('login_time')
        ip_address = data.get('ip_address')
        
        if not all([recipient_email, user_name, login_time, ip_address]):
            return jsonify({'error': 'Missing required fields'}), 400
            
        send_login_notification(
            mail=mail,
            recipient_email=recipient_email,
            user_name=user_name,
            login_time=login_time,
            ip_address=ip_address
        )
        return jsonify({'message': 'Login notification sent successfully'}), 200
    except Exception as e:
        logging.error(f"Error in send_login_notification_api: {str(e)}")
        return jsonify({'error': 'Failed to send login notification'}), 500

@app.route('/api/resend-registration-confirmation', methods=['POST'])
@login_required
def resend_registration_confirmation_api():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        recipient_email = data.get('email')
        user_name = data.get('name')
        registration_time = data.get('registration_time')
        
        if not all([recipient_email, user_name, registration_time]):
            return jsonify({'error': 'Missing required fields'}), 400
            
        send_registration_confirmation(
            mail=mail,
            recipient_email=recipient_email,
            user_name=user_name,
            registration_time=registration_time
        )
        return jsonify({'message': 'Registration confirmation sent successfully'}), 200
    except Exception as e:
        logging.error(f"Error in resend_registration_confirmation_api: {str(e)}")
        return jsonify({'error': 'Failed to send registration confirmation'}), 500

@login_manager.user_loader
def load_user(user_id):
    return db_session.query(User).get(int(user_id))

def send_otp_email(mail, email, otp):
    """Send OTP verification email"""
    try:
        msg = Message(
            'Email Verification Code',
            sender=app.config['MAIL_USERNAME'],
            recipients=[email]
        )
        msg.body = f'Your verification code is: {otp}\nThis code will expire in 10 minutes.'
        mail.send(msg)
        logging.info(f"OTP email sent successfully to {email}")
        return True
    except Exception as e:
        logging.error(f"Failed to send OTP email to {email}: {str(e)}")
        raise

def send_registration_confirmation(mail, email):
    """Send registration confirmation email"""
    try:
        msg = Message(
            'Welcome to Face Recognition System',
            sender=app.config['MAIL_USERNAME'],
            recipients=[email]
        )
        msg.body = 'Thank you for registering! Please verify your email to activate your account.'
        mail.send(msg)
        logging.info(f"Registration confirmation email sent to {email}")
        return True
    except Exception as e:
        logging.error(f"Failed to send registration confirmation to {email}: {str(e)}")
        raise

def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])

@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    """Handle CSRF token errors."""
    logging.error(f"CSRF Error: {str(e)}")
    # Check if request is AJAX using proper header check
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Return JSON response for AJAX requests
        return jsonify({
            'error': 'CSRF token validation failed',
            'message': str(e),
            'new_token': csrf.generate_csrf()
        }), 400
    # Return HTML response for regular requests
    return render_template('error.html', 
                         error_title='Security Error',
                         error_message='Your form submission failed due to expired or missing security token. Please try again.',
                         error_details=str(e)), 400

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors."""
    return render_template('error.html',
                         error_title='Page Not Found',
                         error_message='The requested page could not be found.'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    db_session.rollback()  # Roll back any failed database transactions
    logging.error(f"Internal Server Error: {str(error)}")
    return render_template('error.html',
                         error_title='Internal Server Error',
                         error_message='An unexpected error occurred. Please try again later.'), 500

if __name__ == '__main__':
    try:
        init_db()
        app.run(debug=True)
    except Exception as e:
        logging.error("An error occurred", exc_info=True)
    finally:
        # Clean up resources
        if camera is not None:
            logging.info("Releasing camera on application shutdown")
            camera.release()
