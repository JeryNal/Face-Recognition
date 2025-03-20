from database import DatabaseManager
from debug_config import log_info, log_error

def test_database():
    try:
        db = DatabaseManager('sqlite:///your_database.db')
        if db.test_connection():
            log_info("Database connection successful")
            return True
        else:
            log_error("Database connection failed")
            return False
    except Exception as e:
        log_error(f"Database test failed: {str(e)}")
        return False

if __name__ == "__main__":
    test_database() 