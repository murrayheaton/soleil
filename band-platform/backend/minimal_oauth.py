#!/usr/bin/env python3
"""
Completely isolated OAuth server for Google authentication testing.
"""

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os

# Get environment variables directly
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "https://solepower.live/api/auth/google/callback")

app = FastAPI(title="Minimal OAuth Server")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/api/auth/google/login")
def google_login():
    """Start Google OAuth flow"""
    if not GOOGLE_CLIENT_ID:
        return {"error": "Google Client ID not configured"}
    
    auth_url = (
        f"https://accounts.google.com/o/oauth2/auth?"
        f"client_id={GOOGLE_CLIENT_ID}&"
        f"response_type=code&"
        f"scope=email https://www.googleapis.com/auth/drive.readonly&"
        f"redirect_uri={GOOGLE_REDIRECT_URI}&"
        f"access_type=offline&"
        f"prompt=consent"
    )
    
    return {
        "auth_url": auth_url,
        "message": "Visit the auth_url to authenticate with Google Drive"
    }

@app.get("/api/auth/google/callback")
def google_callback(code: str):
    """Handle Google OAuth callback"""
    return {
        "status": "success", 
        "message": f"OAuth successful! Code: {code[:20]}...",
        "redirect": "/"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)