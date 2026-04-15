import requests

# Paste your details here
TOKEN = "8642770074:AAF_XZ2JXhOUAX7GGB6sBiEVtohB3ZZ_kDA"
CHAT_ID = "8128199273"

def send_telegram_photo(image_path, confidence):
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    
    message = f"🚨 SMOKING DETECTED!\nConfidence: {confidence}%"
    
    # We open the image file in 'rb' (read binary) mode
    with open(image_path, 'rb') as photo_file:
        payload = {
            'chat_id': CHAT_ID,
            'caption': message
        }
        files = {
            'photo': photo_file
        }
        response = requests.post(url, data=payload, files=files)
        
    if response.status_code == 200:
        print("Photo sent successfully!")
    else:
        print(f"Failed to send photo. Error: {response.text}")


# TEsting the function with a sample image and confidence value.

if __name__ == "__main__":
    test_confidence = 96.5
    print("Testing Telegram alert...")
    send_telegram_photo("test_2.jpg", test_confidence)