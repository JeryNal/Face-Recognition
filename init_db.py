import os
from database import init_db, db_session, User, FaceEncoding, Base
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    # Delete the database file if it exists
    if os.path.exists('face_recognition.db'):
        try:
            os.remove('face_recognition.db')
            logger.info("Removed existing database file")
        except Exception as e:
            logger.error(f"Failed to remove database file: {e}")
            return
    
    # Create all tables
    try:
        logger.info("Creating database tables...")
        init_db()
        logger.info("Database tables created successfully")
        
        # Create a test user if needed
        create_test_user()
        
    except Exception as e:
        logger.error(f"Error creating database: {e}")
    finally:
        db_session.remove()

def create_test_user():
    """Create a test user for development purposes"""
    try:
        # Check if any users exist
        if db_session.query(User).count() == 0:
            # Create a test user
            test_user = User(
                name="Test User",
                email="test@example.com",
                face_id=1,
                created_by=1,  # Admin ID
                is_active=True  # Test user is always active
            )
            # Set a test password
            test_user.set_password("password123")
            
            db_session.add(test_user)
            db_session.commit()
            logger.info(f"Created test user: {test_user.name} (ID: {test_user.id})")
    except Exception as e:
        logger.error(f"Error creating test user: {e}")
        db_session.rollback()

if __name__ == "__main__":
    main() 