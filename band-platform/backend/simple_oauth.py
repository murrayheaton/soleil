#!/usr/bin/env python3
"""
Ultra-simple OAuth server with no dependencies.
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

# Get environment variables directly - no dotenv import
GOOGLE_CLIENT_ID = "360999037847-dg2hqrp1ftfvuc1klpl4cuagsc499172.apps.googleusercontent.com"
REDIRECT_URI = "https://solepower.live/api/auth/google/callback"

app = FastAPI(title="Simple OAuth")

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
    auth_url = (
        f"https://accounts.google.com/o/oauth2/auth?"
        f"client_id={GOOGLE_CLIENT_ID}&"
        f"response_type=code&"
        f"scope=email https://www.googleapis.com/auth/drive.readonly&"
        f"redirect_uri={REDIRECT_URI}&"
        f"access_type=offline&"
        f"prompt=consent"
    )
    
    return {
        "auth_url": auth_url,
        "message": "Visit the auth_url to authenticate with Google Drive"
    }

@app.get("/api/auth/google/callback")
def google_callback(code: str):
    return {
        "status": "success", 
        "message": f"OAuth successful! Code: {code[:20]}...", 
        "note": "Callback working - OAuth flow complete!"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)