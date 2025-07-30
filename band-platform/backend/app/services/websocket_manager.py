"""WebSocket manager for broadcasting real-time updates."""

from typing import Any


class WebSocketManager:
    """Minimal WebSocket manager used in tests."""

    async def broadcast_to_band(self, band_id: int, message: Any) -> None:
        """Broadcast a message to all band members.

        In the real application this would forward the message to connected
        WebSocket clients. The test suite mocks this method.
        """

        # Placeholder implementation for tests
        return None
