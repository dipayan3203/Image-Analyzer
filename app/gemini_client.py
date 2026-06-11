import os
from typing import Any, Dict, Optional
import json
from io import BytesIO
from PIL import Image

try:
    import google.generativeai as genai
    from google.api_core import exceptions as google_exceptions
except ImportError:
    genai = None
    google_exceptions = None

# Google Gemini Vision API client wrapper with mock mode


class GeminiClient:
    def __init__(self, api_key: Optional[str] = None, mock: bool = False):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        # Enable mock if explicitly requested or no API key is available (developer convenience)
        env_mock = os.getenv("GEMINI_MOCK", "false").lower() == "true"
        self.mock = mock or env_mock or not self.api_key
        
        # Load model from env
        env_model = os.getenv("GEMINI_MODEL")
        self.model = env_model or "gemini-2.5-flash"
        
        # Configure the API key if available and not in mock mode
        if not self.mock and self.api_key and genai:
            genai.configure(api_key=self.api_key)

    def analyze(self, image_bytes: bytes, analysis_type: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if self.mock:
            # deterministic mock response for testing and early development
            return {
                "status": "success",
                "analysis": {
                    "description": "Mock description: detected a sample object.",
                    "labels": [{"name": "object", "confidence": 0.98}],
                    "confidence": 0.98,
                },
            }

        if not self.api_key:
            raise RuntimeError("Missing GEMINI_API_KEY")

        if not genai:
            raise RuntimeError("google-generativeai library not installed")

        try:
            # Build prompt based on analysis type
            prompts = {
                "general": "Analyze this image. Provide a short, pointed, numbered list of key observations and insights. Keep descriptions concise.",
                "classification": "Classify the main objects and subjects in this image. Provide a numbered list of categories and labels.",
                "extraction": "Extract all text, labels, numbers, and important information visible in this image. Format as a numbered list.",
                "jewelry": """You are a jewelry domain expert with deep knowledge of fine jewelry, gemstones, and retail catalog standards.

Analyze the provided jewelry image and extract structured product data suitable for ERP and eCommerce systems.

Return ONLY valid JSON in the exact structure below. Do not include any explanation or extra text.

{
  "item_name": "",
  "jewelry_type": "",
  "category": "",
  "style": "",
  "design_style": "",
  "metal_type": "",
  "metal_color": "",
  "stone_type": "",
  "stone_color": "",
  "stone_shape": "",
  "setting_type": "",
  "finish": "",
  "occasion": "",
  "target_gender": "",
  "price_tier": "",
  "collection": "",
  "tags": [],
  "seo_title": "",
  "seo_description": "",
  "marketing_text": "",
  "short_description": "",
  "description": "",
  "confidence": 0.0
}

Instructions:
1. Item Naming: Generate a clean commercial item name (e.g., "White Gold Emerald Halo Necklace")
2. Jewelry Classification: ring, necklace, pendant, earring, bracelet, bangle; category: fine_jewelry, fashion_jewelry, bridal, luxury
3. Metal: gold, silver, platinum, mixed; color: yellow, white, rose
4. Stones: diamond, emerald, sapphire, ruby, moissanite, cz, gemstone; simple colors; shapes: round, oval, pear, princess, cushion, emerald
5. Style & Design: halo, solitaire, vintage, modern, minimalist, cluster; design: classic, contemporary, luxury, traditional
6. Setting: prong, bezel, pave, channel, halo
7. Finish: polished, matte, textured
8. Occasion: engagement, wedding, daily_wear, party, gift
9. Target: women, men, unisex
10. Price Tier: budget, mid, premium, luxury
11. Tags: Array of lowercase keywords (type, stone, color, style, metal)
12. SEO: concise title, 1-2 line description
13. Descriptions: short (1 sentence), description (natural ecommerce), marketing (persuasive)
14. General Rules:
- Use short, consistent values
- Do not hallucinate technical data
- If unsure, leave field empty but keep key
- tags must always be an array
- confidence must be between 0 and 1
- Return ONLY JSON""",
            }
            prompt = prompts.get(analysis_type, prompts["general"])

            # Get the model
            model = genai.GenerativeModel(self.model)
            
            # Convert bytes to PIL Image for Gemini API
            image = Image.open(BytesIO(image_bytes))
            
            # Send request to Gemini API
            response = model.generate_content([prompt, image])
            
            # Extract text from response
            try:
                text = response.text

                if analysis_type == 'jewelry':
                    try:
                        data = json.loads(text)
                        
                        def remove_empty_values(d):
                            """Recursively remove keys with empty values from a dict."""
                            if isinstance(d, dict):
                                return {k: v for k, v in ((k, remove_empty_values(v)) for k, v in d.items()) if v not in (None, "", [])}
                            return d

                        cleaned_data = remove_empty_values(data)

                        return {
                            "status": "success",
                            "analysis": {
                                "description": cleaned_data.get("short_description") or cleaned_data.get("description", "Structured data extracted."),
                                "labels": [{"name": tag, "confidence": 0.9} for tag in cleaned_data.get("tags", [])],
                                "confidence": cleaned_data.get("confidence", 0.95),
                                "data": cleaned_data
                            }
                        }
                    except json.JSONDecodeError:
                        pass # If not valid JSON, pass through as text to be handled below

            except ValueError:
                text = "No analysis available (Response might be blocked by safety settings)"
            
            return {
                "status": "success",
                "analysis": {
                    "description": text,
                    "labels": [],
                    "confidence": 0.95,
                },
            }

        except Exception as e:
            # Handle specific model availability errors
            if google_exceptions and isinstance(e, (google_exceptions.NotFound, google_exceptions.InvalidArgument)):
                msg = str(e)
                if "API key" in msg or "API_KEY" in msg:
                    return {
                        "status": "error",
                        "analysis": None,
                        "errors": [f"Google Gemini API Key Error. Details: {msg}"],
                    }
                return {
                    "status": "error",
                    "analysis": None,
                    "errors": [f"The model '{self.model}' is unavailable. Details: {msg}"],
                }

            error_msg = str(e)
            return {
                "status": "error",
                "analysis": None,
                "errors": [f"Gemini API Error: {error_msg}"],
            }
