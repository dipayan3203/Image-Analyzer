from fastapi import Header, HTTPException, status
from typing import Optional
import time

try:
    from app.api_keys import verify_api_key
except ImportError:
    from api_keys import verify_api_key

# Simple in-memory rate limiter (Fixed Window)
# Stores {api_key: (window_start_time, request_count)}
RATE_LIMIT_STORE = {}
RATE_LIMIT_WINDOW = 60  # Window size in seconds (e.g., 1 minute)
RATE_LIMIT_MAX_REQUESTS = 60  # Max requests per window

def check_rate_limit(api_key: str) -> bool:
    """Check if the API key has exceeded the rate limit."""
    now = time.time()
    
    # Get current window data or initialize
    window_start, count = RATE_LIMIT_STORE.get(api_key, (0, 0))
    
    # If window has passed, reset counter
    if now - window_start > RATE_LIMIT_WINDOW:
        RATE_LIMIT_STORE[api_key] = (now, 1)
        return True
        
    # Check limit within current window
    if count >= RATE_LIMIT_MAX_REQUESTS:
        return False
        
    # Increment counter
    RATE_LIMIT_STORE[api_key] = (window_start, count + 1)
    return True

async def get_api_key(x_api_key: Optional[str] = Header(None, alias="X-API-Key")):
    """FastAPI dependency to validate X-API-Key header against the database."""
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-API-Key header is missing",
        )
    
    if not verify_api_key(x_api_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or inactive API Key",
        )

    if not check_rate_limit(x_api_key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
        )
        
    return x_api_key