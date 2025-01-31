from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import Field
from zoneinfo import ZoneInfo

from models.message import MessageCursor
from models.enums import MessageState, UpdatePriority
from base import DomainEvent, DomainEventHandler
from core.constants import EventType

class MessageDomainEvent(DomainEvent):
    """Base class for message-related domain events"""
    message_id: int
    chat_id: int
    state: MessageState
    priority: UpdatePriority
    
    def get_routing_key(self) -> str:
        """Get routing key for message processing"""
        return f"message.{self.state}.{self.priority}"

class MessageStateEvent(MessageDomainEvent):
    """Event for message state transitions"""
    previous_state: MessageState
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error_details: Optional[str] = None
    
    @classmethod
    def from_cursor(cls, cursor: MessageCursor, new_state: MessageState, 
                   error: Optional[str] = None) -> "MessageStateEvent":
        """Create event from MessageCursor"""
        return cls(
            event_type=EventType.MESSAGE_STATE_CHANGED,
            message_id=cursor.message_id,
            chat_id=cursor.chat_id,
            state=new_state,
            previous_state=cursor.last_event_type,
            priority=UpdatePriority.HIGH,
            error_details=error,
            metadata={
                "match_id": cursor.match_id,
                "market_type": cursor.market_type,
                "update_count": cursor.update_count
            }
        )

class MessageUpdateEvent(MessageDomainEvent):
    """Event for content updates to existing messages"""
    content_hash: str  # Hash of new content for deduplication
    update_type: str   # Type of update (edit/delete/etc)
    content_delta: Optional[Dict[str, Any]] = None  # Changes in content
    
    def get_routing_key(self) -> str:
        return f"{super().get_routing_key()}.update"

class MessageDeliveryEvent(MessageDomainEvent):
    """Event for message delivery status"""
    delivery_attempt: int
    delivered_at: Optional[datetime] = None
    delivery_error: Optional[str] = None
    retry_after: Optional[int] = None
    
    def get_routing_key(self) -> str:
        return f"{super().get_routing_key()}.delivery"

class MessageExpiryEvent(MessageDomainEvent):
    """Event for message expiration"""
    expiry_time: datetime = Field(default_factory=lambda: datetime.now(ZoneInfo("UTC")))
    expiry_reason: str
    cleanup_required: bool = True
    
    def get_routing_key(self) -> str:
        return f"{super().get_routing_key()}.expired"

# Event Handlers
class MessageEventHandler(DomainEventHandler):
    """Base handler for message events"""
    
    async def can_handle(self, event: DomainEvent) -> bool:
        return isinstance(event, MessageDomainEvent)
    
    async def handle(self, event: MessageDomainEvent) -> None:
        """Route event to specific handler method"""
        handlers = {
            MessageStateEvent: self._handle_state_change,
            MessageUpdateEvent: self._handle_update,
            MessageDeliveryEvent: self._handle_delivery,
            MessageExpiryEvent: self._handle_expiry
        }
        
        handler = handlers.get(type(event))
        if handler:
            await handler(event)
    
    async def _handle_state_change(self, event: MessageStateEvent) -> None:
        """Handle message state transitions"""
        pass  # Implement in concrete handlers
    
    async def _handle_update(self, event: MessageUpdateEvent) -> None:
        """Handle message content updates"""
        pass  # Implement in concrete handlers
    
    async def _handle_delivery(self, event: MessageDeliveryEvent) -> None:
        """Handle message delivery status"""
        pass  # Implement in concrete handlers
    
    async def _handle_expiry(self, event: MessageExpiryEvent) -> None:
        """Handle message expiration"""
        pass  # Implement in concrete handlers