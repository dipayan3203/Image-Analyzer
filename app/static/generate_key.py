import secrets

def generate_app_key():
    """
    Generates a secure, URL-safe API key for protecting this application.
    """
    key = secrets.token_urlsafe(32)
    print(f"Generated App API Key: {key}")
    print("\nTo use this key:")
    print("1. Add it to your server environment variables (e.g., APP_API_KEY).")
    print("2. Configure your backend to verify the 'X-API-Key' header matches this value.")
    print("3. Enter this key in the frontend 'Settings' panel.")

if __name__ == "__main__":
    generate_app_key()