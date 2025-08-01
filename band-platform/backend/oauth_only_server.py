#!/usr/bin/env python3
"""
Minimal OAuth-only server for testing Google authentication.
"""

import uvicorn
from fastapi import FastAPI
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

# Load only specific environment variables we need
load_dotenv()
# Override any DATABASE_URL to prevent connection attempts
os.environ.pop('DATABASE_URL', None)

app = FastAPI(title="OAuth Test Server")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/api/auth/google/login")
async def google_login():
    """Start Google OAuth flow"""
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "https://solepower.live/api/auth/google/callback")
    
    if not client_id:
        return {"error": "Google Client ID not configured"}
    
    auth_url = (
        f"https://accounts.google.com/o/oauth2/auth?"
        f"client_id={client_id}&"
        f"response_type=code&"
        f"scope=email https://www.googleapis.com/auth/drive.readonly&"
        f"redirect_uri={redirect_uri}&"
        f"access_type=offline&"
        f"prompt=consent"
    )
    
    return {
        "auth_url": auth_url,
        "message": "Visit the auth_url to authenticate with Google Drive"
    }

@app.get("/api/auth/google/callback")
async def google_callback(code: str):
    """Handle Google OAuth callback"""
    return {
        "status": "success",
        "message": f"Received authorization code: {code[:20]}...",
        "note": "OAuth flow working! Now redirect to your main app."
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)