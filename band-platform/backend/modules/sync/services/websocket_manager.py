class WebSocketManager:
    """Minimal WebSocket manager used for tests."""

    def __init__(self) -> None:
        self.connections = {}

    async def broadcast_to_band(self, band_id: int, message: str) -> None:
        """Broadcast a message to all connections for a band."""
        # In tests this method will be mocked, so keep it simple.
        return None
