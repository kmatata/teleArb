from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import Field
from zoneinfo import ZoneInfo

from core.events import BaseEvent
from core.exceptions import EventProcessingError

class DomainEvent(BaseEvent):
    """Base class for all domain events"""
    
    # Event metadata
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(ZoneInfo("UTC")))
    processed_at: Optional[datetime] = None
    
    # Additional context
    context: Dict[str, Any] = Field(default_factory=dict)
    
    def mark_processed(self) -> None:
        """Mark event as processed with timestamp"""
        self.processed_at = datetime.now(ZoneInfo("UTC"))
    
    def add_context(self, key: str, value: Any) -> None:
        """Add additional context to event"""
        self.context[key] = value

    @abstractmethod
    def get_routing_key(self) -> str:
        """Get routing key for event processing"""
        pass

class DomainEventHandler(ABC):
    """Base interface for domain event handlers"""
    
    @abstractmethod
    async def handle(self, event: DomainEvent) -> None:
        """Handle domain event"""
        pass
    
    @abstractmethod
    async def can_handle(self, event: DomainEvent) -> bool:
        """Check if handler can process event"""
        pass

class DomainEventPublisher:
    """Base publisher for domain events"""
    
    def __init__(self):
        self._handlers: Dict[str, list[DomainEventHandler]] = {}
        
    async def publish(self, event: DomainEvent) -> None:
        """Publish event to registered handlers"""
        routing_key = event.get_routing_key()
        
        if routing_key not in self._handlers:
            return
            
        for handler in self._handlers[routing_key]:
            if await handler.can_handle(event):
                try:
                    await handler.handle(event)
                except Exception as e:
                    raise EventProcessingError(
                        f"Failed to process event {event.event_type}: {str(e)}"
                    )
                    
        event.mark_processed()
    
    def register_handler(self, routing_key: str, handler: DomainEventHandler) -> None:
        """Register event handler for routing key"""
        if routing_key not in self._handlers:
            self._handlers[routing_key] = []
        self._handlers[routing_key].append(handler)