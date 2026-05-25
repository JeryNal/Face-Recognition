"""
Simplified Face Recognition Demo App
Demonstrates the core features of the face recognition system
"""
import os
import sys
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from datetime import datetime, timedelta
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'demo-secret-key-12345')
app.config['SESSION_TYPE'] = 'filesystem'

# In-memory database for demo
users_db = {
    'demo@example.com': {
        'id': 1,
        'name': 'Demo User',
        'email': 'demo@example.com',
        'password': 'demo123',
        'is_verified': True,
        'is_active': True,
        'created_at': datetime.utcnow(),
        'face_encodings': 3
    },
    'admin@example.com': {
        'id': 2,
        'name': 'Admin User',
        'email': 'admin@example.com',
        'password': 'admin123',
        'is_verified': True,
        'is_active': True,
        'created_at': datetime.utcnow(),
        'face_encodings': 5
    }
}

# In-memory audit logs
audit_logs = [
    {
        'id': 1,
        'user_email': 'demo@example.com',
        'action': 'Login',
        'status': 'success',
        'timestamp': datetime.utcnow() - timedelta(hours=2),
        'ip_address': '192.168.1.100',
        'details': 'Face recognition successful'
    },
    {
        'id': 2,
        'user_email': 'admin@example.com',
        'action': 'Login',
        'status': 'success',
        'timestamp': datetime.utcnow() - timedelta(hours=1),
        'ip_address': '192.168.1.101',
        'details': 'Face recognition successful'
    },
    {
        'id': 3,
        'user_email': 'unknown@example.com',
        'action': 'Login',
        'status': 'failed',
        'timestamp': datetime.utcnow() - timedelta(minutes=30),
        'ip_address': '192.168.1.102',
        'details': 'Face not recognized'
    }
]

def log_audit_event(user_email, action, status, ip_address, details):
    """Log an audit event"""
    event = {
        'id': len(audit_logs) + 1,
        'user_email': user_email,
        'action': action,
        'status': status,
        'timestamp': datetime.utcnow(),
        'ip_address': ip_address,
        'details': details
    }
    audit_logs.append(event)
    logger.info(f"Audit Event: {action} - {status} - {user_email}")
    return event

def is_logged_in():
    """Check if user is logged in"""
    return 'user_email' in session and session['user_email'] in users_db

def get_current_user():
    """Get current logged in user"""
    if is_logged_in():
        return users_db.get(session['user_email'])
    return None

# Routes
@app.route('/')
def index():
    """Home page"""
    if is_logged_in():
        return redirect(url_for('dashboard'))
    return render_template('index_demo.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        email = data.get('email', '').strip()
        name = data.get('name', '').strip()
        password = data.get('password', '').strip()

        # Validation
        if not all([email, name, password]):
            return jsonify({
                'success': False,
                'message': 'All fields are required'
            }), 400

        if email in users_db:
            return jsonify({
                'success': False,
                'message': 'Email already registered'
            }), 400

        if len(password) < 6:
            return jsonify({
                'success': False,
                'message': 'Password must be at least 6 characters'
            }), 400

        # Create new user
        new_user = {
            'id': len(users_db) + 1,
            'name': name,
            'email': email,
            'password': password,
            'is_verified': False,
            'is_active': False,
            'created_at': datetime.utcnow(),
            'face_encodings': 0
        }
        users_db[email] = new_user
        
        # Log audit event
        log_audit_event(email, 'Registration', 'success', 
                       request.remote_addr, 'User registered successfully')

        return jsonify({
            'success': True,
            'message': 'Registration successful! Please verify your email.',
            'redirect': url_for('verify_email')
        })

    return render_template('register.html')

@app.route('/verify-email', methods=['GET', 'POST'])
def verify_email():
    """Email verification"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        email = data.get('email', '').strip()
        otp = data.get('otp', '').strip()

        if email not in users_db:
            return jsonify({
                'success': False,
                'message': 'Email not found'
            }), 404

        # Demo: accept any 6-digit OTP
        if len(otp) != 6 or not otp.isdigit():
            return jsonify({
                'success': False,
                'message': 'Invalid OTP format'
            }), 400

        # Mark email as verified
        users_db[email]['is_verified'] = True
        
        log_audit_event(email, 'Email Verification', 'success', 
                       request.remote_addr, 'Email verified successfully')

        return jsonify({
            'success': True,
            'message': 'Email verified! Please proceed to face registration.',
            'redirect': url_for('register_face')
        })

    return render_template('verify_email.html')

@app.route('/register-face', methods=['GET', 'POST'])
def register_face():
    """Face registration"""
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email', '').strip()

        if email not in users_db:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404

        user = users_db[email]
        if not user['is_verified']:
            return jsonify({
                'success': False,
                'message': 'Please verify your email first'
            }), 400

        # Simulate face encoding capture
        user['face_encodings'] = data.get('encoding_count', 3)
        user['is_active'] = True

        log_audit_event(email, 'Face Registration', 'success', 
                       request.remote_addr, f'Registered {user["face_encodings"]} face encodings')

        return jsonify({
            'success': True,
            'message': f'Face registration successful! {user["face_encodings"]} encodings saved.',
            'redirect': url_for('login')
        })

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login with face recognition"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()

        if email not in users_db:
            log_audit_event(email, 'Login', 'failed', 
                           request.remote_addr, 'User not found')
            return jsonify({
                'success': False,
                'message': 'Invalid email or password'
            }), 401

        user = users_db[email]

        if not user['is_active']:
            log_audit_event(email, 'Login', 'failed', 
                           request.remote_addr, 'User account inactive')
            return jsonify({
                'success': False,
                'message': 'Account not active. Please complete registration.'
            }), 401

        if user['password'] != password:
            log_audit_event(email, 'Login', 'failed', 
                           request.remote_addr, 'Invalid password')
            return jsonify({
                'success': False,
                'message': 'Invalid email or password'
            }), 401

        # Successful login
        session['user_email'] = email
        session.permanent = True
        session.modified = True
        
        log_audit_event(email, 'Login', 'success', 
                       request.remote_addr, 'Logged in successfully')

        return jsonify({
            'success': True,
            'message': f'Welcome back, {user["name"]}!',
            'redirect': url_for('dashboard')
        })

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    """Admin/User dashboard"""
    if not is_logged_in():
        return redirect(url_for('login'))

    user = get_current_user()
    recent_logs = sorted(audit_logs, key=lambda x: x['timestamp'], reverse=True)[:10]

    return render_template('dashboard_demo.html', user=user, logs=recent_logs)

@app.route('/api/audit-logs')
def api_audit_logs():
    """API endpoint for audit logs"""
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401

    logs = sorted(audit_logs, key=lambda x: x['timestamp'], reverse=True)
    
    # Convert datetime to string for JSON serialization
    logs_data = []
    for log in logs:
        log_copy = log.copy()
        log_copy['timestamp'] = log_copy['timestamp'].isoformat()
        logs_data.append(log_copy)

    return jsonify({
        'success': True,
        'total': len(logs_data),
        'logs': logs_data
    })

@app.route('/api/users')
def api_users():
    """API endpoint for users list"""
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401

    users_list = []
    for email, user in users_db.items():
        user_copy = user.copy()
        user_copy['created_at'] = user_copy['created_at'].isoformat()
        users_list.append(user_copy)

    return jsonify({
        'success': True,
        'total': len(users_list),
        'users': users_list
    })

@app.route('/logout')
def logout():
    """Logout user"""
    email = session.get('user_email')
    if email:
        log_audit_event(email, 'Logout', 'success', 
                       request.remote_addr, 'User logged out')
    
    session.clear()
    return redirect(url_for('index'))

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Face Recognition System',
        'timestamp': datetime.utcnow().isoformat(),
        'users': len(users_db),
        'audit_logs': len(audit_logs)
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template('error.html', error='Page not found', code=404), 404

@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors"""
    logger.error(f"Server error: {error}")
    return render_template('error.html', error='Internal server error', code=500), 500

if __name__ == '__main__':
    print("=" * 60)
    print("Face Recognition System - Demo Application")
    print("=" * 60)
    print("\n✓ Starting application...")
    print("✓ Default users available:")
    print("  - Email: demo@example.com")
    print("  - Password: demo123")
    print("\n  - Email: admin@example.com")
    print("  - Password: admin123")
    print("\n✓ Access the application at: http://localhost:5000")
    print("\n" + "=" * 60)
    
    app.run(debug=True, host='127.0.0.1', port=5000)
