from typing import Optional

from fastapi import FastAPI, File, HTTPException, UploadFile, Form, Request, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os
from typing import Any, Dict
import sys

# Add project root to sys.path to allow running script directly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from .env file
load_dotenv()

try:
    from app.schemas import AnalyzeRequest, AnalyzeResponse
except ImportError:
    from schemas import AnalyzeRequest, AnalyzeResponse

from app.preprocessor import (
    load_image_from_base64,
    load_image_from_path,
    validate_and_normalize,
)
from app.gemini_client import GeminiClient
from app.normalizer import normalize_response
from app.middleware import get_api_key
from app.database import init_db


# --- App Initialization ---
app = FastAPI(title="Gemini Image Analyzer")

# Add CORS middleware to allow cross-origin requests (e.g., from a separate frontend dev server)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the database on startup
init_db()

client = GeminiClient()
print(f"Server started. Using Gemini model: {client.model}")
if client.api_key:
    masked_key = f"...{client.api_key[-4:]}" if len(client.api_key) > 4 else "***"
    print(f"API Key loaded: {masked_key}")
else:
    print("Warning: No API Key loaded. GeminiClient running in mock mode.")

# Get the directory where this file is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler to ensure JSON response for unexpected errors"""
    return JSONResponse(
        status_code=500,
        content={"status": "error", "analysis": None, "errors": [str(exc)]},
    )


@app.get("/")
async def root():
    """Serve the main HTML page"""
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


async def _process_image_and_analyze(
    image_bytes: bytes,
    analysis_type: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> JSONResponse:
    """Helper to process image bytes, analyze, and return a JSON response."""
    try:
        if not image_bytes:
            raise ValueError("Empty image data received.")

        validated_bytes, _ = validate_and_normalize(image_bytes)

        gemini_result = client.analyze(
            image_bytes=validated_bytes,
            analysis_type=analysis_type,
            metadata=metadata or {},
        )

        normalized_response = normalize_response(gemini_result)
        return JSONResponse(content=normalized_response)

    except ValueError as e:
        # Catches validation errors from preprocessor or empty data check
        return JSONResponse(
            status_code=400,
            content={"status": "error", "analysis": None, "errors": [str(e)]},
        )


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_endpoint(
    file: Optional[UploadFile] = File(None, description="Image file to analyze"),
    analysis_type: str = Form("general", description="Type of analysis: general, classification, or extraction"),
    _ = Depends(get_api_key),
):
    """
    Analyze an image using Google Gemini Vision API.
    
    Upload an image file and specify the type of analysis needed.
    """
    if file is None:
        raise HTTPException(status_code=400, detail="No image file provided")

    raw = await file.read()
    return await _process_image_and_analyze(raw, analysis_type)


@app.post("/analyze-base64", response_model=AnalyzeResponse)
async def analyze_base64_endpoint(
    request: AnalyzeRequest,
    _ = Depends(get_api_key),
):
    """
    Analyze an image from base64 data or file path.
    
    Provide either:
    - Base64 encoded image data
    - Local file path (starting with / or drive letter like C:/)
    - Data URI (data:image/png;base64,...)
    """
    if not request.image:
        raise HTTPException(status_code=400, detail="No image data or path provided")

    img_str = request.image

    # Check if it's a file path.
    # Heuristic: Paths are generally short (<1024 chars) and must exist on disk.
    # This prevents Base64 strings starting with "/" (like JPEGs) from being treated as paths.
    if len(img_str) < 1024 and (os.path.exists(img_str)):
        raw = load_image_from_path(img_str)
    else:
        raw = load_image_from_base64(img_str)

    return await _process_image_and_analyze(raw, request.analysis_type, request.metadata)


@app.post("/admin/generate-key")
async def generate_key_endpoint(owner: str = "admin", setup_secret: str = ""):
    """One-time endpoint to generate an API key. Protect with a setup secret."""
    SETUP_SECRET = os.getenv("SETUP_SECRET", "")
    if not SETUP_SECRET or setup_secret != SETUP_SECRET:
        raise HTTPException(status_code=403, detail="Invalid setup secret")

    from app.api_keys import generate_api_key
    api_key, prefix = generate_api_key(owner)
    return {"api_key": api_key, "prefix": prefix}


if __name__ == "__main__":
    # Allow running the app module directly for local development.
    # Prefer using: `python -m uvicorn app.main:app --reload` or the Dockerfile in production.
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "127.0.0.1")
    print(f"Server running locally at: http://localhost:{port}")
    uvicorn.run("app.main:app", host=host, port=port, reload=True)
