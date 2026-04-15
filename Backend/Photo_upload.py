import requests
import base64
import cv2

# 1. API Configuration
API_KEY = "YOUR_API_KEY_HERE"
PROJECT_ID = "smoking-tasfx/3"
UPLOAD_URL = f"https://detect.roboflow.com/{PROJECT_ID}?api_key={API_KEY}"

def send_single_photo():
    # 2. Capture one frame from the camera
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release() # Release immediately to save power

    if not ret:
        print("Failed to grab frame from camera")
        return

    # 3. Encode image to Base64 (Roboflow requirement)
    # We encode to .jpg first so the data size is small
    _, buffer = cv2.imencode('.jpg', frame)
    img_base64 = base64.b64encode(buffer).decode("utf-8")

    # 4. Send the POST request
    print("Sending photo to Roboflow...")
    response = requests.post(
        UPLOAD_URL, 
        data=img_base64, 
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    # 5. Process the Result
    if response.status_code == 200:
        predictions = response.json().get("predictions", [])
        if predictions:
            print(f"Detected: {predictions[0]['class']} with {predictions[0]['confidence']:.1%}")
            return predictions
        else:
            print("No smoking detected in this photo.")
    else:
        print(f"API Error: {response.status_code}")

# Trigger the action
send_single_photo()