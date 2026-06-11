from app.normalizer import normalize_response


def test_normalize_basic():
    raw = {
        "status": "success",
        "analysis": {"description": "ok", "labels": [{"name": "cat", "confidence": 0.9}]},
    }
    norm = normalize_response(raw)
    assert norm["status"] == "success"
    assert norm["analysis"]["description"] == "ok"
    assert isinstance(norm["analysis"]["labels"], list)
