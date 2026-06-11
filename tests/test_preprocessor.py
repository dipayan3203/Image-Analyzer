import base64
import io

from PIL import Image

from app.preprocessor import load_image_from_base64, validate_and_normalize


def make_test_png_bytes():
    im = Image.new("RGB", (100, 100), color=(255, 0, 0))
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return buf.getvalue()


def test_base64_loading_and_validation():
    b = make_test_png_bytes()
    b64 = base64.b64encode(b).decode()
    raw = load_image_from_base64(b64)
    img_bytes, fmt = validate_and_normalize(raw)
    assert fmt in ("PNG", "JPEG", "BMP", "GIF")
    assert len(img_bytes) > 0
