from datetime import datetime
from database import Base, Session, engine
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
import json

class ActivityLog(Base):
    __tablename__ = 'activity_logs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    action = Column(String(100))
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(String(500))

def log_activity(user_id, action, details, request, status='success'):
    session = Session()
    try:
        log = ActivityLog(
            user_id=user_id,
            action=action,
            details=details,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string,
            status=status
        )
        session.add(log)
        session.commit()
    except Exception as e:
        print(f"Error logging activity: {e}")
    finally:
        session.close()

def get_activity_chart_data():
    session = Session()
    try:
        # Your chart data logic here
        activities = session.query(ActivityLog).all()
        # Process activities and return chart data
        return process_activities(activities)
    except Exception as e:
        print(f"Error getting activity chart data: {e}")
        return None
    finally:
        session.close()

def process_activities(activities):
    # Process activities logic
    pass 