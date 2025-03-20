from models import ActivityLog
from database import Session
from datetime import datetime

def log_activity(user_id, action, details=None, status="success", ip_address=None):
    session = Session()
    try:
        activity = ActivityLog(
            user_id=user_id,
            action=action,
            details=details,
            status=status,
            ip_address=ip_address
        )
        session.add(activity)
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error logging activity: {e}")
    finally:
        session.close() 