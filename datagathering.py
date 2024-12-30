import cv2
import numpy as np
from PIL import Image
import os

# Path to the data folder (where training images are stored)
path = 'Data'  # Make sure the 'Data' folder is in the correct path relative to your script

# Initialize the face recognizer (LBPH) and the face detector (Haar Cascade)
recognizer = cv2.face.LBPHFaceRecognizer_create()
detector = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

# Check if the Haar cascade file is loaded correctly
if detector.empty():
    print("Error: Could not load Haar Cascade classifier.")
    exit()

# Function to load images and labels from the specified path
def imgsandlables(path):
    imagePaths = [os.path.join(path, f) for f in os.listdir(path) if f.endswith(('.jpg', '.jpeg', '.png'))]
    indfaces = []
    ids = []

    for imagePath in imagePaths:
        try:
            img = Image.open(imagePath).convert('L')  # Convert image to grayscale
            imgnp = np.array(img, 'uint8')  # Convert to numpy array
            id = int(os.path.split(imagePath)[-1].split(".")[0])  # Extract ID from image file name

            # Detect faces in the image
            faces = detector.detectMultiScale(imgnp, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
            print(f"Processing {imagePath}: {len(faces)} face(s) detected.")  # Debug line

            if len(faces) == 0:
                print(f"No faces detected in {imagePath}, skipping this image.")

            for (x, y, w, h) in faces:
                indfaces.append(imgnp[y:y+h, x:x+w])  # Crop face region
                ids.append(id)  # Append the corresponding ID
        except Exception as e:
            print(f"Error processing image {imagePath}: {e}")

    return indfaces, ids

# Collect faces and labels from the images in the 'Data' folder
faces, ids = imgsandlables(path)

# If no faces were detected, exit the program
if len(faces) == 0:
    print("No faces detected in the images. Please check your dataset.")
    exit()

# Train the recognizer with the collected faces and IDs
recognizer.train(faces, np.array(ids))

# Define names for recognized IDs (add more names if needed)
names = ['None', 'jerry', 'inno']  # IDs: 1 -> 'jerry', 2 -> 'inno', etc.

# Initialize the webcam capture
cam = cv2.VideoCapture(0)

# Check if the webcam was opened successfully
if not cam.isOpened():
    print("Error: Could not open webcam.")
    exit()

while True:
    _, img = cam.read()  # Read a frame from the webcam
    img = cv2.flip(img, 1)  # Flip the image horizontally for a mirror effect
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)  # Convert the image to grayscale for face detection

    # Detect faces in the current frame
    faces_detected = detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    # For each face detected in the webcam frame
    for (x, y, w, h) in faces_detected:
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)  # Draw a rectangle around the face

        # Predict the ID of the detected face
        id, confidence = recognizer.predict(gray[y:y + h, x:x + w])

        # Check if confidence is below 100, meaning a good match
        if confidence < 100:
            id = names[id]  # Map the ID to a name
            confidence_text = f"  {100 - confidence:.2f}%"  # Display confidence level
        else:
            id = "Unknown"
            confidence_text = f"  {100 - confidence:.2f}%"  # Display confidence level for unknown faces

        # Display the recognized name and confidence level on the frame
        cv2.putText(img, str(id), (x - 5, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
        cv2.putText(img, confidence_text, (x + 5, y + h - 5), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)

    # Show the webcam image with the face detection
    cv2.imshow('Camera', img)

    # Exit the loop when the 'Esc' key (key code 27) is pressed
    if cv2.waitKey(10) & 0xFF == 27:
        break

# Release the webcam and close all OpenCV windows
cam.release()
cv2.destroyAllWindows()
