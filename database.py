from sqlalchemy import create_engine, Column, Integer, String, LargeBinary, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from datetime import datetime, timedelta
import os
import logging
import json
from werkzeug.security import generate_password_hash, check_password_hash

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('database.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Create database engine with updated configuration
engine = create_engine('sqlite:///face_recognition.db')
db_session = scoped_session(sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
))

Base = declarative_base()
Base.query = db_session.query_property()

# Add metadata configuration
metadata = Base.metadata
metadata.bind = engine

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(128))
    is_active = Column(Boolean, default=False)
    is_email_verified = Column(Boolean, default=False)  # Added email verification field
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime)
    otp_secret = Column(String(32))
    otp_valid_until = Column(DateTime)
    
    def __init__(self, name=None, email=None, is_active=False, is_email_verified=False):
        self.name = name
        self.email = email
        self.is_active = is_active
        self.is_email_verified = is_email_verified
        
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    def set_otp(self, otp):
        """Set OTP and its expiry time (10 minutes)"""
        self.otp_secret = otp
        self.otp_valid_until = datetime.utcnow() + timedelta(minutes=10)
        
    def verify_otp(self, otp):
        """Verify OTP and check if it's still valid"""
        if not self.otp_secret or not self.otp_valid_until:
            return False
        
        if datetime.utcnow() > self.otp_valid_until:
            return False
            
        is_valid = self.otp_secret == otp
        if is_valid:
            # Clear OTP after successful verification
            self.otp_secret = None
            self.otp_valid_until = None
        return is_valid
        
    def activate_account(self):
        """Activate user account after email verification"""
        self.is_active = True
        self.otp_secret = None
        self.otp_valid_until = None
        logger.info(f"Account activated for user {self.email}")
        
    def is_authenticated(self):
        return True
        
    def is_anonymous(self):
        return False
        
    def get_id(self):
        return str(self.id)
        
    def record_login_attempt(self, success):
        """Record login attempt and handle account locking"""
        if success:
            self.failed_login_attempts = 0
            self.locked_until = None
            self.last_login = datetime.utcnow()
        else:
            self.failed_login_attempts += 1
            if self.failed_login_attempts >= 5:  # Lock after 5 failed attempts
                self.locked_until = datetime.utcnow() + timedelta(minutes=30)
                logger.warning(f"Account locked for {self.email} due to multiple failed attempts")

class FaceEncoding(Base):
    __tablename__ = 'face_encodings'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    encoding_data = Column(LargeBinary, nullable=False)  # Stores the face encoding
    encoding_meta = Column(Text)  # JSON string for additional metadata
    data_hash = Column(String(64), nullable=False)  # SHA-256 hash for integrity check
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime)
    is_active = Column(Boolean, default=True)
    confidence_score = Column(Integer)  # Store recognition confidence
    failed_verification_count = Column(Integer, default=0)
    
    def __init__(self, user_id, encoding_data, encoding_meta=None, data_hash=None):
        self.user_id = user_id
        self.encoding_data = encoding_data
        self.encoding_meta = encoding_meta
        self.data_hash = data_hash
        
    def update_last_used(self):
        self.last_used = datetime.utcnow()
        
    def increment_failed_verification(self):
        self.failed_verification_count += 1
        if self.failed_verification_count >= 3:
            self.is_active = False
            logger.warning(f"Face encoding {self.id} deactivated due to multiple failed verifications")

class SecurityAudit(Base):
    __tablename__ = 'security_audits'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    event_type = Column(String(50), nullable=False)  # login, face_verification, etc.
    event_data = Column(Text)  # JSON string for event details
    timestamp = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String(45))  # IPv6 compatible
    success = Column(Boolean, default=False)
    
    def __init__(self, user_id, event_type, event_data=None, ip_address=None):
        self.user_id = user_id
        self.event_type = event_type
        self.event_data = event_data
        self.ip_address = ip_address

def init_db():
    try:
        # Drop existing tables
        metadata.drop_all(bind=engine)
        # Create all tables
        metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise

def cleanup_old_data():
    """Clean up old face encodings and audit logs"""
    try:
        # Archive old audit logs (older than 90 days)
        ninety_days_ago = datetime.utcnow() - timedelta(days=90)
        old_audits = SecurityAudit.query.filter(SecurityAudit.timestamp < ninety_days_ago).all()
        
        # Archive the data before deletion
        if old_audits:
            archive_security_audits(old_audits)
            
        # Delete inactive face encodings
        inactive_encodings = FaceEncoding.query.filter_by(is_active=False).all()
        for encoding in inactive_encodings:
            db_session.delete(encoding)
            
        db_session.commit()
        logger.info("Database cleanup completed successfully")
    except Exception as e:
        logger.error(f"Error during database cleanup: {str(e)}")
        db_session.rollback()

def archive_security_audits(audits):
    """Archive old security audit logs"""
    try:
        archive_dir = os.path.join('archives', 'security_audits')
        os.makedirs(archive_dir, exist_ok=True)
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        archive_file = os.path.join(archive_dir, f'audit_archive_{timestamp}.json')
        
        audit_data = [{
            'id': audit.id,
            'user_id': audit.user_id,
            'event_type': audit.event_type,
            'event_data': audit.event_data,
            'timestamp': audit.timestamp.isoformat(),
            'ip_address': audit.ip_address,
            'success': audit.success
        } for audit in audits]
        
        with open(archive_file, 'w') as f:
            json.dump(audit_data, f, indent=2)
            
        # Set secure permissions on archive file
        os.chmod(archive_file, 0o600)
        
        logger.info(f"Security audits archived to {archive_file}")
    except Exception as e:
        logger.error(f"Error archiving security audits: {str(e)}")
        raise