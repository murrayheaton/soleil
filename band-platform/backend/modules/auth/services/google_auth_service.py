"""
Google OAuth 2.0 authentication service.

Handles Google OAuth flow, token management, and user profile retrieval.
"""
import logging
import secrets
from typing import Dict, Any, Optional, Tuple

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import backoff

from app.config import settings
from ..exceptions import AuthenticationError, TokenError

logger = logging.getLogger(__name__)


class GoogleAuthService:
    """
    Google OAuth 2.0 authentication service.
    
    Handles Google OAuth flow, token management, and user profile retrieval.
    """
    
    def __init__(self):
        """Initialize the Google auth service."""
        self.client_id = settings.google_client_id
        self.client_secret = settings.google_client_secret
        self.redirect_uri = settings.google_redirect_uri
        
        # OAuth 2.0 scopes required for the band platform
        self.scopes = [
            'openid',
            'email', 
            'profile',
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/calendar'
        ]
        
        # Statistics
        self.stats = {
            "auth_attempts": 0,
            "auth_successes": 0,
            "auth_failures": 0,
            "token_refreshes": 0,
            "token_refresh_failures": 0,
        }
    
    def get_authorization_url(self, state: Optional[str] = None) -> Tuple[str, str]:
        """
        Get Google OAuth authorization URL.
        
        Args:
            state: Optional state parameter for CSRF protection.
            
        Returns:
            Tuple of (authorization_url, state) where state is generated if not provided.
        """
        try:
            # Create OAuth flow
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [self.redirect_uri]
                    }
                },
                scopes=self.scopes
            )
            flow.redirect_uri = self.redirect_uri
            
            # Generate state if not provided
            if not state:
                state = secrets.token_urlsafe(32)
            
            # Get authorization URL
            auth_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                state=state,
                prompt='consent'  # Force consent to get refresh token
            )
            
            logger.debug(f"Generated OAuth authorization URL with state: {state}")
            return auth_url, state
            
        except Exception as e:
            logger.error(f"Error generating authorization URL: {e}")
            raise AuthenticationError(f"Failed to generate authorization URL: {e}")
    
    async def exchange_code_for_tokens(
        self, 
        authorization_code: str, 
        state: str
    ) -> Credentials:
        """
        Exchange authorization code for access and refresh tokens.
        
        Args:
            authorization_code: The authorization code from Google.
            state: The state parameter for CSRF validation.
            
        Returns:
            Google OAuth credentials with tokens.
        """
        try:
            self.stats["auth_attempts"] += 1
            
            # Create OAuth flow
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [self.redirect_uri]
                    }
                },
                scopes=self.scopes,
                state=state
            )
            flow.redirect_uri = self.redirect_uri
            
            # Exchange code for tokens
            flow.fetch_token(code=authorization_code)
            credentials = flow.credentials
            
            self.stats["auth_successes"] += 1
            logger.info("Successfully exchanged authorization code for tokens")
            
            return credentials
            
        except Exception as e:
            self.stats["auth_failures"] += 1
            logger.error(f"Error exchanging authorization code: {e}")
            raise AuthenticationError(f"Failed to exchange code for tokens: {e}")
    
    @backoff.on_exception(
        backoff.expo,
        Exception,
        max_tries=3,
        max_time=60
    )
    async def get_user_profile(self, credentials: Credentials) -> Dict[str, Any]:
        """
        Get user profile information from Google.
        
        Args:
            credentials: Google OAuth credentials.
            
        Returns:
            User profile information.
        """
        try:
            # Refresh credentials if needed
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
                self.stats["token_refreshes"] += 1
            
            # Build People API service
            service = build('people', 'v1', credentials=credentials)
            
            # Get user profile
            profile = service.people().get(
                resourceName='people/me',
                personFields='names,emailAddresses,photos'
            ).execute()
            
            # Extract relevant information
            email = None
            if 'emailAddresses' in profile:
                email = profile['emailAddresses'][0].get('value')
            
            name = None
            if 'names' in profile:
                name = profile['names'][0].get('displayName')
            
            photo_url = None
            if 'photos' in profile:
                photo_url = profile['photos'][0].get('url')
            
            return {
                'email': email,
                'name': name,
                'photo_url': photo_url,
                'google_id': profile.get('resourceName', '').replace('people/', '')
            }
            
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            raise AuthenticationError(f"Failed to get user profile: {e}")
    
    async def refresh_credentials(self, credentials: Credentials) -> Credentials:
        """
        Refresh Google OAuth credentials.
        
        Args:
            credentials: Expired credentials to refresh.
            
        Returns:
            Refreshed credentials.
        """
        try:
            if not credentials.refresh_token:
                raise TokenError("No refresh token available")
            
            credentials.refresh(Request())
            self.stats["token_refreshes"] += 1
            
            logger.debug("Successfully refreshed Google credentials")
            return credentials
            
        except Exception as e:
            self.stats["token_refresh_failures"] += 1
            logger.error(f"Error refreshing credentials: {e}")
            raise TokenError(f"Failed to refresh credentials: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get authentication service statistics."""
        return self.stats.copy()