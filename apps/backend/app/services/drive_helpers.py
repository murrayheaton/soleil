import asyncio
import logging
from typing import Any, Dict, Tuple

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

from ..config import settings

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple token bucket rate limiter."""

    def __init__(self, requests_per_second: float):
        self.requests_per_second = requests_per_second
        self.tokens = requests_per_second
        self.last_update = asyncio.get_event_loop().time()
        self.lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self.lock:
            now = asyncio.get_event_loop().time()
            time_passed = now - self.last_update

            self.tokens = min(
                self.requests_per_second,
                self.tokens + time_passed * self.requests_per_second,
            )
            self.last_update = now

            if self.tokens >= 1:
                self.tokens -= 1
                return

            wait_time = (1 - self.tokens) / self.requests_per_second
            await asyncio.sleep(wait_time)
            self.tokens = 0


class GoogleDriveAuth:
    """Utility helpers for Google Drive OAuth."""

    @staticmethod
    def create_oauth_flow(redirect_uri: str) -> Flow:
        return Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=[settings.google_drive_scope],
            redirect_uri=redirect_uri,
        )

    @staticmethod
    def get_authorization_url(flow: Flow) -> Tuple[str, str]:
        authorization_url, state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )
        return authorization_url, state

    @staticmethod
    def exchange_code_for_credentials(flow: Flow, authorization_response: str) -> Credentials:
        flow.fetch_token(authorization_response=authorization_response)
        return flow.credentials


class StatsMixin:
    """Mixin providing stats tracking helpers."""

    def init_stats(self) -> None:
        self.stats = {
            "requests_made": 0,
            "rate_limit_hits": 0,
            "errors": 0,
            "files_processed": 0,
            "last_sync": None,
        }

    def get_stats(self) -> Dict[str, Any]:
        return self.stats.copy()

    def reset_stats(self) -> None:
        self.init_stats()


def create_drive_service(credentials: Credentials):
    from .google_drive import GoogleDriveService

    return GoogleDriveService(credentials)


async def test_drive_connection(service) -> bool:
    try:
        async with service._get_service() as drive:
            def make_request():
                return drive.about().get(fields="user").execute()

            await service._make_request(make_request)
            return True
    except Exception as e:  # pragma: no cover - connection issues
        logger.error(f"Drive connection test failed: {e}")
        return False
