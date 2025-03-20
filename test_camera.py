import cv2
import numpy as np

def test_opencv():
    print("Testing OpenCV installation...")
    
    # Create a simple test image
    test_image = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.putText(test_image, "OK", (30, 60), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    try:
        # Try to save the image
        cv2.imwrite('test_opencv.jpg', test_image)
        print("OpenCV is working correctly! ✓")
        return True
    except Exception as e:
        print(f"Error testing OpenCV: {e}")
        return False

if __name__ == "__main__":
    test_opencv() 