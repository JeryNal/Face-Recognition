import cv2
import numpy as np
from Recognizer import SecureFaceRecognizer
from database import User, FaceEncoding, SecurityAudit, db_session
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_face_security():
    """Test the secure face recognition features"""
    recognizer = SecureFaceRecognizer()
    
    # 1. Test user creation with secure password
    test_user = User(name="test_user", email="test@example.com")
    test_user.set_password("secure_password123")
    db_session.add(test_user)
    db_session.commit()
    logger.info("Created test user")
    
    try:
        # 2. Test face data validation
        # Load a test image (you should replace this with an actual face image)
        image_path = "test_opencv.jpg"
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not load test image: {image_path}")
        
        # Convert to grayscale for face detection
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 3. Test face encoding storage
        logger.info("Testing face encoding storage...")
        recognizer.save_face_data(
            user_id=test_user.id,
            face_data=gray,
            metadata={"source": "test_image", "quality": "high"}
        )
        
        # 4. Test face verification
        logger.info("Testing face verification...")
        is_match, confidence = recognizer.verify_face(gray, test_user.id)
        logger.info(f"Face verification result: Match={is_match}, Confidence={confidence}")
        
        # 5. Test security audit logging
        audits = db_session.query(SecurityAudit).filter_by(
            user_id=test_user.id,
            event_type='face_verification'
        ).all()
        logger.info(f"Found {len(audits)} security audit entries")
        
        # 6. Test failed verification handling
        logger.info("Testing failed verification handling...")
        # Modify the image to force a failure
        modified_img = gray + np.random.normal(0, 50, gray.shape).astype(np.uint8)
        for _ in range(3):  # Try 3 failed attempts
            is_match, confidence = recognizer.verify_face(modified_img, test_user.id)
            logger.info(f"Failed attempt result: Match={is_match}, Confidence={confidence}")
        
        # 7. Check if encoding was deactivated
        encoding = db_session.query(FaceEncoding).filter_by(
            user_id=test_user.id
        ).first()
        logger.info(f"Face encoding active status: {encoding.is_active}")
        
        # 8. Test data integrity
        logger.info("Testing data integrity...")
        stored_hash = encoding.data_hash
        computed_hash = recognizer._hash_image(
            np.frombuffer(encoding.encoding_data, dtype=np.uint8)
        )
        logger.info(f"Hash verification: {stored_hash == computed_hash}")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise
    finally:
        # Cleanup test data
        db_session.query(SecurityAudit).filter_by(user_id=test_user.id).delete()
        db_session.query(FaceEncoding).filter_by(user_id=test_user.id).delete()
        db_session.query(User).filter_by(id=test_user.id).delete()
        db_session.commit()
        logger.info("Test cleanup completed")

if __name__ == "__main__":
    test_face_security()
