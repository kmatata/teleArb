from enum import Enum, auto
from typing import Final

class ArbitrageStatus(str, Enum):
    """Status of an arbitrage opportunity"""
    ACTIVE = "active"
    EXPIRED = "expired"
    INVALID = "invalid"
    SUSPENDED = "suspended"

class BookmakerStatus(str, Enum):
    """Status of bookmaker odds/markets"""
    AVAILABLE = "available"
    SUSPENDED = "suspended"
    CLOSED = "closed"
    ERROR = "error"

class MessageState(str, Enum):
    """State of a Telegram message"""
    PENDING = "pending"
    SENT = "sent"
    EDITED = "edited"
    DELETED = "deleted"
    FAILED = "failed"

class UpdatePriority(int, Enum):
    """Priority levels for message updates"""
    IMMEDIATE = auto()  # New opportunities, significant profit changes
    HIGH = auto()      # Status changes, market transitions
    NORMAL = auto()    # Regular odds updates
    LOW = auto()       # Minor changes, cleanup notifications

class SubscriptionType(str, Enum):
    """Types of WebSocket subscriptions"""
    ALL_MATCHES = "all_matches"
    SPECIFIC_MATCH = "specific_match"
    MARKET_TYPE = "market_type"
    HIGH_PROFIT = "high_profit"

# Validation Constants
ODDS_THRESHOLDS: Final = {
    "min_valid": 1.01,
    "max_valid": 1000.0
}

PROFIT_THRESHOLDS: Final = {
    "min_notable": 3.0,     # Minimum profit % to consider notable
    "min_priority": 5.0,    # Minimum profit % for high priority
    "significant_change": 2.0  # % change considered significant
}