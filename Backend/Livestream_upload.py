import requests
import base64
import cv2
import threading
import time

# 1. Configuration
API_KEY = "YOUR_API_KEY_HERE"
PROJECT_ID = "smoking-tasfx/3"
UPLOAD_URL = f"https://detect.roboflow.com/{PROJECT_ID}?api_key={API_KEY}"

class RoboflowThread(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.cap = cv2.VideoCapture(0)
        self.running = True
        self.last_results = []
        self.new_data_available = False # Flag to tell main script there's a fresh update

    def run(self):
        print("[INFO] Roboflow Background Thread Started.")
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                print("[Thread Error] Camera disconnected.")
                break

            _, buffer = cv2.imencode('.jpg', frame)
            img_data = base64.b64encode(buffer).decode("utf-8")

            try:
                response = requests.post(UPLOAD_URL, data=img_data, headers={
                    "Content-Type": "application/x-www-form-urlencoded"
                }, timeout=5)

                if response.status_code == 200:
                    self.last_results = response.json().get("predictions", [])
                    self.new_data_available = True # Signal to main loop
                    
                    if self.last_results:
                        print(f"\n[AI] Detected {len(self.last_results)} objects.")
                
            except Exception as e:
                print(f"\n[Thread Error] {e}")

            time.sleep(2) # Protects your credits

    def stop(self):
        self.running = False
        if self.cap.isOpened():
            self.cap.release()

if __name__ == "__main__":
    bg_ai = RoboflowThread()
    bg_ai.start()

    try:
        while True:
            # Check if there is NEW information from the AI
            if bg_ai.new_data_available:
                if bg_ai.last_results:
                    # --- TRIGGER ALARM / SQLITE HERE ---
                    print(">>> SMOKING ALERT ACTIVE <<<")
                else:
                    print("Status: Area Clear")
                
                # Reset the flag so we don't process the same result twice
                bg_ai.new_data_available = False
            
            time.sleep(0.1) # Fast loop for responsiveness
            
    except KeyboardInterrupt:
        print("\nStopping...")
        bg_ai.stop()