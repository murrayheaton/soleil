"""Tests for cookie security and persistence."""

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from starlette.testclient import TestClient

from app.api.auth import router


app = FastAPI()
app.include_router(router, prefix="/api/auth")


@app.get("/subpath/check")
def read_subpath(request: Request):
    """Return the auth cookie value for testing."""
    return {"auth": request.cookies.get("soleil_auth")}


@app.get("/redirect")
def redirect_to_subpath():
    """Redirect to a subpath to test cookie persistence."""
    return RedirectResponse("/subpath/check")


client = TestClient(app, base_url="https://testserver")


def test_login_cookie_has_security_flags():
    response = client.post("/api/auth/login")
    assert response.status_code == 200
    cookie = response.headers.get("set-cookie", "").lower()
    assert "soleil_auth=true" in cookie
    assert "httponly" in cookie
    assert "secure" in cookie
    assert "samesite=lax" in cookie


def test_profile_complete_cookie_has_security_flags():
    response = client.post("/api/auth/profile/complete")
    assert response.status_code == 200
    cookie = response.headers.get("set-cookie", "").lower()
    assert "soleil_profile_complete=true" in cookie
    assert "httponly" in cookie
    assert "secure" in cookie
    assert "samesite=lax" in cookie


def test_cookie_persists_across_redirect_and_subpath():
    client.post("/api/auth/login")
    final = client.get("/redirect")
    assert final.json()["auth"] == "true"

