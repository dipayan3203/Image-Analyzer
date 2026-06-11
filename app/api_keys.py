import secrets
import hashlib
from typing import Tuple

try:
    from app.database import get_db, init_db
except ImportError:
    from database import get_db, init_db

def generate_api_key(owner: str = "user") -> Tuple[str, str]:
    """
    Generates a new API key, stores its hash, and returns the raw key.
    Format: prefix.secret
    Returns: (api_key, key_prefix)
    """
    init_db()
    
    # Generate a secure random prefix (8 chars) and secret (43 chars)
    # Prefix allows fast lookup, Secret provides security
    prefix = secrets.token_hex(4)
    secret = secrets.token_urlsafe(32)
    api_key = f"{prefix}.{secret}"
    
    # Hash only the secret part for storage
    key_hash = hashlib.sha256(secret.encode()).hexdigest()
    
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO api_keys (key_prefix, key_hash, owner) VALUES (?, ?, ?)",
            (prefix, key_hash, owner)
        )
        conn.commit()
    finally:
        conn.close()
        
    return api_key, prefix

def verify_api_key(api_key: str) -> bool:
    """Verifies if the provided raw API key is valid and active."""
    if not api_key or "." not in api_key:
        return False
        
    prefix, secret = api_key.split(".", 1)
    
    # Hash the provided secret to compare with stored hash
    input_hash = hashlib.sha256(secret.encode()).hexdigest()
    
    conn = get_db()
    try:
        cursor = conn.execute(
            "SELECT key_hash, is_active FROM api_keys WHERE key_prefix = ?", 
            (prefix,)
        )
        row = cursor.fetchone()
        
        if not row or not row["is_active"]:
            return False
            
        # Use constant-time comparison to prevent timing attacks
        return secrets.compare_digest(row["key_hash"], input_hash)
    finally:
        conn.close()

if __name__ == "__main__":
    import sys
    user = sys.argv[1] if len(sys.argv) > 1 else "admin"
    key, prefix = generate_api_key(user)
    print(f"Generated API Key for '{user}':\n{key}")