#!/usr/bin/env python3
"""
Completely standalone OAuth server - no imports from app directory.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="Standalone OAuth")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return "OK"

@app.get("/api/auth/google/login")
def google_login():
    auth_url = (
        "https://accounts.google.com/o/oauth2/auth?"
        "client_id=360999037847-dg2hqrp1ftfvuc1klpl4cuagsc499172.apps.googleusercontent.com&"
        "response_type=code&"
        "scope=email%20https://www.googleapis.com/auth/drive.readonly&"
        "redirect_uri=https://solepower.live/api/auth/google/callback&"
        "access_type=offline&"
        "prompt=consent"
    )
    
    return {
        "auth_url": auth_url,
        "message": "Visit the auth_url to authenticate with Google Drive"
    }

@app.get("/api/auth/google/callback")
def google_callback(code: str):
    return {
        "status": "success", 
        "message": f"OAuth successful! Authorization code received: {code[:20]}...", 
        "redirect_url": "https://solepower.live/"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)