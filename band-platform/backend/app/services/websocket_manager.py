"""Simple WebSocket manager stub for tests."""

from typing import Any

class WebSocketManager:
    """Manage WebSocket connections for broadcasting."""

    async def broadcast_to_band(self, band_id: int, message: Any) -> None:
        """Broadcast a message to all connections for a band."""
        # In tests we just record the call via mocks
        pass
