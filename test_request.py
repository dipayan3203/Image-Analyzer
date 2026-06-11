import requests
import os

# --- CONFIGURATION ---
# Paste the key you generated with 'python -m app.api_keys client'
# It should look like: "someprefix.somerandomsecretstring"
API_KEY = "d7c2441f.2ahoiiIgavGOroCMp2wQ9rTiKwc9FoeaQb8-_NRCB4c"

URL = "http://127.0.0.1:8000/analyze"
IMAGE_FILE = "test_image.png"
# ---------------------

def create_dummy_image():
    """Creates a small red square if no image exists."""
    from PIL import Image
    img = Image.new('RGB', (100, 100), color='red')
    img.save(IMAGE_FILE)
    print(f"Created dummy image: {IMAGE_FILE}")

if API_KEY == "PASTE_YOUR_KEY_HERE":
    print("Error: Please update 'API_KEY' in test_request.py with a valid key.")
    print("You can generate one by running: python -m app.api_keys client")
    exit(1)

if not os.path.exists(IMAGE_FILE):
    create_dummy_image()

try:
    with open(IMAGE_FILE, "rb") as f:
        files = {"file": f}
        data = {"analysis_type": "general"}
        headers = {"X-API-Key": API_KEY} # Key goes in Header

        print(f"Sending request to {URL}...")
        response = requests.post(URL, headers=headers, files=files, data=data)

        print(f"Status Code: {response.status_code}")
        if response.status_code == 403:
            print("(!) 403 Forbidden: The API Key in this script does not match the server's database.")
            print("    Run 'python -m app.api_keys client' to generate a valid key, then update API_KEY above.")
        # Use .json() for JSON response, but handle cases where it's not JSON
        try:
            print(f"Response: {response.json()}")
        except requests.exceptions.JSONDecodeError:
            print(f"Response (non-JSON): {response.text}")
except Exception as e:
    print(f"Error: {e}")