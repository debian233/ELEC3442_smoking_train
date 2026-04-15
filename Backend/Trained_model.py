from roboflow import Roboflow
import cv2

# 1. Initialize with your API Key
rf = Roboflow(api_key="XsefeoI0fr82nJqNchBE")

# 2. Access your specific project
project = rf.workspace("kennys-workspace-84mke").project("smoking-tasfx-1lbyy")
model = project.version(1).model 

# 3. Run prediction on a local image
# Make sure "smoking_test.jpg" is in your folder!
image_path = "test_9.jpg"
prediction = model.predict(image_path, confidence=40)

# 4. Extract the JSON data
results = prediction.json()

# 5. Loop through every detection found
if "predictions" in results and len(results["predictions"]) > 0:
    print("\n--- DETECTION FOUND! ---")
    for det in results["predictions"]:
        label = det['class']
        # 'confidence' comes as a decimal (e.g., 0.852), we multiply by 100
        conf_percent = det['confidence'] * 100
        
        print(f"Object: {label}")
        print(f"Confidence Score: {conf_percent:.1f}%") # This shows one decimal point
        print(f"Location: x={det['x']}, y={det['y']}")
        print("-----------------------")
else:
    print("\n[!] The AI didn't see any smoking in this photo.")

# 6. Save the image so you can see the boxes
prediction.save("result_output.jpg")
print("\nSuccess: Check 'result_output.jpg' to see the visual boxes.")