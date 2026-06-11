from app.gemini_client import GeminiClient


def test_mock_client():
    c = GeminiClient(mock=True)
    resp = c.analyze(b"\x89PNG\r\n", analysis_type="general")
    assert resp["status"] == "success"
    assert "analysis" in resp
