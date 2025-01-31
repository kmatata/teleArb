from datetime import datetime
from typing import Optional, Dict, Any, TypedDict
from pydantic import BaseModel, Field
from constants import EventType, MarketType, DataSource
from exceptions import InvalidEventTypeError
from zoneinfo import ZoneInfo


class BaseEvent(BaseModel):
    """Base event model"""

    event_type: EventType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(ZoneInfo("UTC")))
    metadata: Optional[Dict[str, Any]] = None

    def validate_event_type(self) -> None:
        if self.event_type not in EventType:
            raise InvalidEventTypeError(f"Invalid event type: {self.event_type}")


class BookmakerData(TypedDict):
    odd: float
    active: bool
    status: bool
    destination_url: str
    stake: Optional[float]


class ArbitrageEvent(BaseEvent):
    """Event for new arbitrage opportunities"""

    match_id: int
    home_team_name: str
    away_team_name: str
    arbitrage_id: int
    bet_description: str
    market_type: MarketType
    data_source: DataSource
    min_profit: float
    max_profit: float
    bookmakers: Dict[
        str, BookmakerData
    ]  # Keys like 'yes'/'no' for BTTS or 'home'/'away'/'draw' for THREE_WAY
    status: bool = (
        True  # Active status --> essentially not expired (do we need this...wont it just remove it from messages when expired??)
    )

    class Config:
        schema_extra = {
            "exampleBtts": {
                "yes": {
                    "odd": 25.0,
                    "active": True,
                    "status": True,
                    "destination_url": "https://wx.com",
                    "stake": 8.32,
                },
                "no": {
                    "odd": 1.08,
                    "active": True,
                    "status": False,
                    "destination_url": "https://yz.com",
                    "stake": 191.68,
                },
            },
            "exampleThree_way": {
                "home": {
                    "odd": 25.0,
                    "active": True,
                    "status": True,
                    "destination_url": "https://uv.com",
                    "stake": 8.32,
                },
                "draw": {
                    "odd": 1.08,
                    "active": True,
                    "status": False,
                    "destination_url": "https://wx.com",
                    "stake": 191.68,
                },
                "away": {
                    "odd": 1.08,
                    "active": True,
                    "status": False,
                    "destination_url": "https://yz.com",
                    "stake": 191.68,
                },
            },
        }


class MarketStatusEvent(BaseEvent):
    """Event for market status changes"""

    match_id: int
    arbitrage_id: int
    market_type: MarketType
    bookmaker_key: str  # Which bookmaker changed status
    previous_active: bool  # Was betting active
    new_active: bool  # Is betting now active
    previous_status: bool  # Previous market status
    new_status: bool  # New market status
    status_change_reason: Optional[str] = None


class BookmakerStatusChangedEvent(BaseEvent):
    """Event for individual bookmaker status changes"""

    bookmaker_key: str  # 'yes'/'no' for BTTS, 'home'/'draw'/'away' for THREE_WAY
    bookmaker_name: str  # 'betika', 'shabiki', etc.
    active_changed: bool  # Did active state change
    status_changed: bool  # Did status state change
    previous_active: bool  # Previous active state
    new_active: bool  # New active state
    previous_status: bool  # Previous status state
    new_status: bool  # New status state
    change_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(ZoneInfo("UTC"))
    )


class ProfitEvent(BaseEvent):
    """Event for profit threshold crossings"""

    match_id: int
    arbitrage_id: int
    previous_min_profit: float
    previous_max_profit: float
    new_min_profit: float
    new_max_profit: float
    threshold_crossed: float


class OddsChangedEvent(BaseEvent):
    """Event for odds changes in markets"""

    match_id: int
    arbitrage_id: int
    market_type: MarketType
    bookmaker_key: str
    previous_odds: float
    new_odds: float
    delta_percentage: float
    stake_impact: Optional[float] = None


class MarketExpiredEvent(BaseEvent):
    """Event for expired markets based on cleanup rules"""

    match_id: int
    arbitrage_id: int
    market_type: MarketType
    data_source: DataSource
    expiry_reason: str
    last_update_time: datetime


class EventFactory:
    """Factory for creating typed events"""

    @staticmethod
    def create_event(event_type: EventType, **data) -> BaseEvent:
        event_map = {
            EventType.ARBITRAGE_DETECTED: ArbitrageEvent,
            # EventType.MARKET_STATUS_CHANGED: MarketStatusEvent,
            EventType.BOOKMAKER_STATUS_CHANGED: BookmakerStatusChangedEvent,
            EventType.PROFIT_THRESHOLD_CROSSED: ProfitEvent,
            EventType.PROFIT_THRESHOLD_CROSSED: ProfitEvent,
            EventType.ODDS_CHANGED: OddsChangedEvent,
            EventType.MARKET_EXPIRED: MarketExpiredEvent,
        }

        event_class = event_map.get(event_type)
        if not event_class:
            raise InvalidEventTypeError(f"No event class for type: {event_type}")

        data["event_type"] = event_type
        return event_class(**data)
