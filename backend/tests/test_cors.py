from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

PREFLIGHT = {"Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "content-type"}


def test_frontend_origin_is_allowed():
    r = client.options("/ask", headers={"Origin": "http://localhost:5173", **PREFLIGHT})
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_other_websites_are_not_allowed():
    r = client.options("/ask", headers={"Origin": "https://evil.example", **PREFLIGHT})
    assert "access-control-allow-origin" not in r.headers


def test_normal_requests_carry_the_header_too():
    r = client.get("/health", headers={"Origin": "http://localhost:5173"})
    assert r.headers["access-control-allow-origin"] == "http://localhost:5173"