from enum import Enum, auto
from typing import Final


class MarketType(str, Enum):
    """Market types from monitor.sql schema"""

    BTTS = "btts"
    THREE_WAY = "three_way"


class DataSource(str, Enum):
    """Data sources from db_manager cleanup rules"""

    LIVE = "live"
    UPCOMING = "upcoming"


class EventType(str, Enum):
    """Event types for websocket and message queue"""

    ARBITRAGE_DETECTED = "arbitrage_detected"
    BOOKMAKER_STATUS_CHANGED = "bookmaker_status_changed"  # Individual bookmaker
    OPPORTUNITY_STATUS_CHANGED = "opportunity_status_changed"  # Combined status
    PROFIT_THRESHOLD_CROSSED = "profit_threshold_crossed"
    ODDS_CHANGED = "odds_changed"
    MARKET_EXPIRED = "market_expired"
    MESSAGE_STATE_CHANGED = "message_state_changed"


class MessagePriority(int, Enum):
    """Priority levels for message queue"""

    HIGH = auto()  # New high-profit opportunities
    MEDIUM = auto()  # Status changes, significant updates
    LOW = auto()  # Regular updates, minor changes


# Queue Constants
QUEUE_PRIORITIES: Final = {
    EventType.ARBITRAGE_DETECTED: MessagePriority.HIGH,
    EventType.PROFIT_THRESHOLD_CROSSED: MessagePriority.HIGH,
    EventType.MESSAGE_STATE_CHANGED: MessagePriority.HIGH,
    EventType.OPPORTUNITY_STATUS_CHANGED: MessagePriority.MEDIUM,  # Combined status changes
    EventType.BOOKMAKER_STATUS_CHANGED: MessagePriority.LOW,  # Individual updates
    EventType.ODDS_CHANGED: MessagePriority.LOW,
    EventType.MARKET_EXPIRED: MessagePriority.LOW,
}

# WebSocket Event Constants
WS_EVENT_TYPES: Final = set(EventType)

# Profit Threshold Constants
MIN_PROFIT_THRESHOLD: Final[float] = 5.0  # Minimum profit % for high priority
SIGNIFICANT_PROFIT_CHANGE: Final[float] = 2.0  # % change considered significant
