from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from zoneinfo import ZoneInfo

from core.constants import MarketType, DataSource, EventType
from core.exceptions import MessageProcessingError

class MessageCursor(BaseModel):
    """Tracks state of Telegram messages for arbitrage updates"""
    
    # Message identifiers
    message_id: int  
    chat_id: int
    match_id: int
    
    # Market details
    market_type: MarketType
    data_source: DataSource
    
    # Timing and state
    created_at: datetime = Field(default_factory=lambda: datetime.now(ZoneInfo("UTC")))
    updated_at: Optional[datetime] = None
    last_event_type: EventType
    is_active: bool = True
    
    # Track message updates
    update_count: int = 0
    last_arbitrage_id: Optional[int] = None
    
    def update_state(self, event_type: EventType, arbitrage_id: int) -> None:
        """Update cursor state with new event"""
        self.updated_at = datetime.now(ZoneInfo("UTC"))
        self.last_event_type = event_type
        self.last_arbitrage_id = arbitrage_id
        self.update_count += 1

    def should_edit_message(self, event_type: EventType) -> bool:
        """Determine if message should be edited based on event type"""
        # High priority events always trigger edit
        if event_type in [EventType.ARBITRAGE_DETECTED, EventType.PROFIT_THRESHOLD_CROSSED]:
            return True
            
        # For other events, limit rapid updates
        if self.updated_at:
            time_since_update = (datetime.now(ZoneInfo("UTC")) - self.updated_at).seconds
            return time_since_update >= 5  # Minimum 5 seconds between updates
            
        return True

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MessageCursor":
        """Create MessageCursor from dictionary data"""
        try:
            return cls(**{
                k: v for k, v in data.items()
                if k in MessageCursor.model_fields
            })
        except Exception as e:
            raise MessageProcessingError(f"Failed to create MessageCursor: {str(e)}")