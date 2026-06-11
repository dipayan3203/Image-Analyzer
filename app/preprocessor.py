import base64
import io
import os
from typing import Tuple

from PIL import Image, UnidentifiedImageError

# Config
MAX_SIZE_BYTES = 5 * 1024 * 1024  # 5MB
ALLOWED_FORMATS = {"JPEG", "PNG", "GIF", "BMP"}
MAX_DIMENSION = 2048


def load_image_from_base64(data_uri: str) -> bytes:
    if data_uri.startswith("data:"):
        header, b64 = data_uri.split(",", 1)
    else:
        b64 = data_uri
    return base64.b64decode(b64)


def load_image_from_path(path: str) -> bytes:
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    with open(path, "rb") as f:
        return f.read()


def validate_and_normalize(image_bytes: bytes) -> Tuple[bytes, str]:
    if len(image_bytes) > MAX_SIZE_BYTES:
        raise ValueError(f"Image too large: {len(image_bytes)} bytes")

    with io.BytesIO(image_bytes) as bio:
        try:
            im = Image.open(bio)
            fmt = im.format.upper()
            if fmt not in ALLOWED_FORMATS:
                raise ValueError(f"Unsupported image format: {fmt}")
        except UnidentifiedImageError:
            raise ValueError("Invalid image data or unsupported format")

        # Resize if too large
        w, h = im.size
        if max(w, h) > MAX_DIMENSION:
            ratio = MAX_DIMENSION / max(w, h)
            new_size = (int(w * ratio), int(h * ratio))
            im = im.resize(new_size, Image.LANCZOS)

        out = io.BytesIO()
        im.save(out, format=fmt)
        return out.getvalue(), fmt
