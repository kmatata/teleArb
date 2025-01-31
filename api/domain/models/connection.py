from datetime import datetime
from typing import Optional, Dict, Any, Set
from pydantic import BaseModel, Field
from zoneinfo import ZoneInfo

from core.exceptions import WebSocketConnectionError


class WebSocketConnection(BaseModel):
    """Manages individual WebSocket connection state and metadata"""

    # Connection identifiers
    client_id: str
    connection_id: str

    # Connection state
    connected_at: datetime = Field(
        default_factory=lambda: datetime.now(ZoneInfo("UTC"))
    )
    last_heartbeat: datetime = Field(
        default_factory=lambda: datetime.now(ZoneInfo("UTC"))
    )
    disconnected_at: Optional[datetime] = None
    is_active: bool = True

    # Client metadata
    client_metadata: Dict[str, Any] = Field(default_factory=dict)

    # Subscription tracking
    subscribed_matches: Set[int] = Field(default_factory=set)

    def update_heartbeat(self) -> None:
        """Update last heartbeat timestamp"""
        self.last_heartbeat = datetime.now(ZoneInfo("UTC"))

    def has_expired(self, timeout_seconds: int) -> bool:
        """Check if connection has expired based on heartbeat"""
        if not self.is_active:
            return True

        time_since_heartbeat = (
            datetime.now(ZoneInfo("UTC")) - self.last_heartbeat
        ).seconds
        return time_since_heartbeat > timeout_seconds

    def disconnect(self) -> None:
        """Mark connection as disconnected"""
        self.is_active = False
        self.disconnected_at = datetime.now(ZoneInfo("UTC"))
        self.subscribed_matches.clear()

    def subscribe_to_match(self, match_id: int) -> None:
        """Add match to subscription list"""
        if not self.is_active:
            raise WebSocketConnectionError("Cannot subscribe: Connection inactive")
        self.subscribed_matches.add(match_id)

    def unsubscribe_from_match(self, match_id: int) -> None:
        """Remove match from subscription list"""
        self.subscribed_matches.discard(match_id)

    def is_subscribed_to_match(self, match_id: int) -> bool:
        """Check if subscribed to specific match"""
        return match_id in self.subscribed_matches

    @classmethod
    def from_client_data(
        cls, client_id: str, metadata: Dict[str, Any]
    ) -> "WebSocketConnection":
        """Create connection from client data"""
        try:
            return cls(
                client_id=client_id,
                connection_id=f"{client_id}_{datetime.now(ZoneInfo('UTC')).timestamp()}",
                client_metadata=metadata,
            )
        except Exception as e:
            raise WebSocketConnectionError(f"Failed to create connection: {str(e)}")
