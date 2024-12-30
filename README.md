# Face Recognition Project

This project demonstrates a basic implementation of face recognition using Python. It uses OpenCV for detecting faces and identifying individuals. The project contains scripts to gather data, train a model, and perform face recognition.

## Project Structure

- `recognition.py`: This script performs face recognition using a pre-trained model and Haar Cascade classifier.
- `gathering.py`: This script helps in gathering images (data) to train the face recognition model.
- `haarcascade_frontalface_default.xml`: A Haar Cascade classifier for face detection, required for the project.
- `Data/`: A subfolder where the dataset images will be stored during the data collection phase.

Setup

 1. Clone the Repository
To set up the project, clone the repository to your local machine.

''bash
git clone <repository_url>
cd Face-Recognition

 2.Install Required Libraries

pip install opencv-python opencv-python-headless numpy

 3.Download the Haar Cascade Classifier

    curl -o haarcascade_frontalface_default.xml https://github.com/opencv/opencv/blob/master/data/haarcascades/haarcascade_frontalface_default.xml
    
    mkdir Data
    Move this file into the Data/ subfolder.
    mv haarcascade_frontalface_default.xml Data/


  4. Data Collection (gathering.py)
     Run gathering.py to collect training data by capturing images of faces. This script will save the images to the Data/ folder.
     ''bash
     python gathering.py

  5.   Train the Model (recognition.py)
       Once you have gathered enough data, you can use recognition.py to train the model.
       ''bash
       python recognition.py
       This script will train the face recognition model using the images collected and allow it to identify faces.



