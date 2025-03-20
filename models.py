from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from database import Base

class ActivityLog(Base):
    __tablename__ = 'activity_logs'
    __table_args__ = {'extend_existing': True}  # Allow redefinition if needed

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    action = Column(String(100))
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(String(500))
    status = Column(String(50))
    ip_address = Column(String(50))

    def __init__(self, user_id, action, details=None, status="success", ip_address=None):
        self.user_id = user_id
        self.action = action
        self.details = details
        self.status = status
        self.ip_address = ip_address

    def __repr__(self):
        return f'<ActivityLog {self.action}>'

# Rename to UserModel to avoid conflict with database.py User class
class UserModel(Base):
    __tablename__ = 'users'
    __table_args__ = {'extend_existing': True}  # Allow redefinition if needed

    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(128))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime) 