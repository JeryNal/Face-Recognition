from models import ActivityLog, User
from database import Session
from datetime import datetime

def test_models():
    session = Session()
    try:
        # Create a test user
        test_user = User(
            username="test_user",
            email="test@example.com"
        )
        session.add(test_user)
        session.commit()

        # Create a test activity log
        test_log = ActivityLog(
            user_id=test_user.id,
            action="test_action",
            details="Testing activity log"
        )
        session.add(test_log)
        session.commit()

        print("Test successful!")
        return True
    except Exception as e:
        print(f"Test failed: {e}")
        session.rollback()
        return False
    finally:
        session.close()

if __name__ == "__main__":
    test_models() 