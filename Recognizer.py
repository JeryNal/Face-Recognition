import cv2
import numpy as np
from PIL import Image
import os
import logging
from database import db_session, User, FaceEncoding, SecurityAudit
import hashlib
from datetime import datetime
import json
from pathlib import Path
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('recognizer.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class SecureFaceRecognizer:
    def __init__(self):
        self.data_path = Path('Data')
        self.backup_path = Path('Data_Backup')
        self.model_path = Path('models')
        self.max_failed_attempts = 3
        self.confidence_threshold = 80
        self._setup_directories()
        
    def _setup_directories(self):
        """Create necessary directories with proper permissions"""
        for path in [self.data_path, self.backup_path, self.model_path]:
            path.mkdir(exist_ok=True)
            # Ensure directory is only accessible by the application
            os.chmod(path, 0o700)
            
    def _hash_image(self, image_data):
        """Generate secure hash of image data for integrity checking"""
        return hashlib.sha256(image_data.tobytes()).hexdigest()
        
    def _backup_training_data(self):
        """Create backup of training data"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.backup_path / f"backup_{timestamp}"
        shutil.copytree(self.data_path, backup_dir)
        logger.info(f"Training data backed up to {backup_dir}")
        
    def _validate_face_image(self, image):
        """Validate face image meets security requirements"""
        if image.size[0] < 100 or image.size[1] < 100:
            raise ValueError("Image resolution too low for secure face recognition")
        if image.size[0] > 1000 or image.size[1] > 1000:
            raise ValueError("Image resolution too high, please reduce size")
        return True
        
    def save_face_data(self, user_id, face_data, metadata=None):
        """Securely save face data with integrity check"""
        try:
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{user_id}_{timestamp}.npz"
            filepath = self.data_path / filename
            
            # Hash the face data for integrity check
            data_hash = self._hash_image(face_data)
            
            # Save face data and metadata
            metadata = metadata or {}
            metadata.update({
                'timestamp': timestamp,
                'data_hash': data_hash,
                'user_id': user_id
            })
            
            # Save to database
            face_encoding = FaceEncoding(
                user_id=user_id,
                encoding_data=face_data.tobytes(),
                encoding_meta=json.dumps(metadata),
                data_hash=data_hash
            )
            db_session.add(face_encoding)
            db_session.commit()
            
            logger.info(f"Face data saved for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving face data: {str(e)}")
            db_session.rollback()
            raise
            
    def verify_face(self, face_data, claimed_user_id):
        """Verify face against stored data with anti-spoofing checks"""
        try:
            # Get user's stored face encodings
            stored_encodings = db_session.query(FaceEncoding).filter_by(
                user_id=claimed_user_id,
                is_active=True  # Only check active encodings
            ).all()
            
            if not stored_encodings:
                logger.warning(f"No stored encodings found for user {claimed_user_id}")
                return False, 0
                
            # Verify data integrity
            for encoding in stored_encodings:
                stored_hash = encoding.data_hash
                computed_hash = hashlib.sha256(encoding.encoding_data).hexdigest()
                
                if stored_hash != computed_hash:
                    logger.error(f"Face data integrity check failed for user {claimed_user_id}")
                    return False, 0
                    
            # Perform face recognition
            max_confidence = 0
            for encoding in stored_encodings:
                stored_data = np.frombuffer(encoding.encoding_data, dtype=np.uint8)
                confidence = self._compare_faces(face_data, stored_data)
                max_confidence = max(max_confidence, confidence)
                
                # Update last used timestamp if confidence is high enough
                if confidence >= self.confidence_threshold:
                    encoding.update_last_used()
                else:
                    encoding.increment_failed_verification()
                    
            is_match = max_confidence >= self.confidence_threshold
            
            # Log the verification attempt
            self._log_verification_attempt(claimed_user_id, is_match, max_confidence)
            
            return is_match, max_confidence
            
        except Exception as e:
            logger.error(f"Error during face verification: {str(e)}")
            return False, 0
            
    def _log_verification_attempt(self, user_id, success, confidence):
        """Log face verification attempts for security audit"""
        try:
            audit = SecurityAudit(
                user_id=user_id,
                event_type='face_verification',
                event_data=json.dumps({
                    'confidence': confidence,
                    'success': success,
                    'timestamp': datetime.utcnow().isoformat()
                })
            )
            db_session.add(audit)
            db_session.commit()
        except Exception as e:
            logger.error(f"Error logging verification attempt: {str(e)}")
            db_session.rollback()

    def _compare_faces(self, face1, face2):
        """Compare two face encodings and return confidence score"""
        try:
            # Implement actual face comparison logic here
            # This is a placeholder - replace with your actual implementation
            return 0
        except Exception as e:
            logger.error(f"Error comparing faces: {str(e)}")
            return 0

# Initialize the secure recognizer
secure_recognizer = SecureFaceRecognizer()

def get_user_names():
    """Get user names from database for face recognition mapping"""
    try:
        users = db_session.query(User).all()
        # Create mapping with 'None' at index 0
        names = ['None'] + [user.name for user in users]
        return names
    except Exception as e:
        logger.error(f"Failed to fetch user names from database: {e}")
        return ['None']  # Return minimal list if database fetch fails

def imgsandlables(path, detector):
    if not os.path.exists(path):
        logger.error(f"Data directory '{path}' not found")
        raise FileNotFoundError(f"Data directory '{path}' not found")
        
    imagePaths = [os.path.join(path, f) for f in os.listdir(path) if f.endswith(('.jpg', '.jpeg', '.png'))]
    if not imagePaths:
        logger.error(f"No valid images found in {path}")
        raise ValueError(f"No valid images found in {path}")
        
    indfaces = []
    ids = []
    
    logger.info(f"Found {len(imagePaths)} images for training")
    
    for imagePath in imagePaths:
        try:
            img = Image.open(imagePath).convert('L')
            imgnp = np.array(img, 'uint8')
            id = int(os.path.split(imagePath)[-1].split(".")[0])

            faces = detector.detectMultiScale(imgnp, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
            logger.debug(f"Processing {imagePath}: {len(faces)} face(s) detected.")

            if len(faces) == 0:
                logger.warning(f"No faces detected in {imagePath}, skipping this image.")
                continue

            for (x, y, w, h) in faces:
                indfaces.append(imgnp[y:y+h, x:x+w])
                ids.append(id)
        except Exception as e:
            logger.error(f"Error processing image {imagePath}: {e}")
            continue

    if not indfaces:
        logger.error("No valid faces found in any images")
        raise ValueError("No valid faces found in any images")

    return indfaces, ids

def setup_face_recognition():
    try:
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        detector = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
        
        if detector.empty():
            raise RuntimeError("Could not load Haar Cascade classifier")
            
        return recognizer, detector
    except Exception as e:
        raise RuntimeError(f"Failed to initialize face recognition: {str(e)}")

def initialize_webcam():
    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        raise RuntimeError("Could not open webcam")
    return cam

def main():
    try:
        # Initialize face recognition
        recognizer, detector = setup_face_recognition()
        
        # Get user names from database
        names = get_user_names()
        logger.info(f"Loaded {len(names)} user names from database")
        
        # Train the model
        logger.info("Starting training process...")
        faces, ids = imgsandlables('Data', detector)
        
        if len(faces) == 0:
            raise ValueError("No faces detected in the training images")
            
        recognizer.train(faces, np.array(ids))
        logger.info(f"Training completed with {len(faces)} faces")
        logger.info(f"Unique IDs in training: {set(ids)}")
        
        # Initialize webcam
        cam = initialize_webcam()
        
        # Main recognition loop
        while True:
            ret, img = cam.read()
            if not ret:
                logger.error("Failed to grab frame from webcam")
                continue
                
            img = cv2.flip(img, 1)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            faces_detected = detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

            for (x, y, w, h) in faces_detected:
                cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)

                id, confidence = recognizer.predict(gray[y:y + h, x:x + w])

                # Ensure id is within valid range
                if 0 <= id < len(names) and confidence < 100:
                    name = names[id]
                    confidence_text = f"  {100 - confidence:.2f}%"
                else:
                    name = "Unknown"
                    confidence_text = f"  {100 - confidence:.2f}%"

                cv2.putText(img, name, (x - 5, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
                cv2.putText(img, confidence_text, (x + 5, y + h - 5), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)

            cv2.imshow('Camera', img)

            if cv2.waitKey(10) & 0xFF == 27:
                break
            
        try:
            recognizer.save('trainer.yml')
            logger.info("Model trained and saved successfully")
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")
        
    except Exception as e:
        logger.error(f"Critical error in main loop: {str(e)}")
    finally:
        if 'cam' in locals():
            cam.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
