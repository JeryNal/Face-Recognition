from database import engine, Session
from activity_log import ActivityLog

def test_database():
    try:
        # Test connection
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            print("Database connection successful")
            
        # Test session
        session = Session()
        try:
            # Try a simple query
            logs = session.query(ActivityLog).first()
            print("Session query successful")
        finally:
            session.close()
            
    except Exception as e:
        print(f"Database test failed: {e}")

if __name__ == "__main__":
    test_database() 