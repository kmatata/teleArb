from datetime import datetime
from typing import Dict, Optional
from pydantic import Field
from zoneinfo import ZoneInfo

from models.arbitrage import Arbitrage, BookmakerOdds
from models.enums import ArbitrageStatus, BookmakerStatus
from base import DomainEvent, DomainEventHandler
from core.constants import MarketType, DataSource
from core.events import EventType


class ArbitrageDomainEvent(DomainEvent):
    """Base class for arbitrage domain events"""

    match_id: int
    arbitrage_id: int
    market_type: MarketType
    data_source: DataSource

    def get_routing_key(self) -> str:
        """Get routing key for event processing"""
        return f"arbitrage.{self.market_type}.{self.data_source}"


class BookmakerStatusChangedEvent(ArbitrageDomainEvent):
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

    def get_routing_key(self) -> str:
        return f"{super().get_routing_key()}.bookmaker_status"


class OpportunityStatusChangedEvent(ArbitrageDomainEvent):
    """Event for overall opportunity status changes"""

    previous_valid: bool  # Was opportunity valid
    new_valid: bool  # Is opportunity still valid
    affected_bookmakers: Dict[str, Dict[str, bool]]  # Status map of all bookmakers
    invalidation_reason: Optional[str] = None


class ArbitrageDetectedEvent(ArbitrageDomainEvent):
    """Event for new arbitrage opportunities"""

    bookmakers: Dict[str, BookmakerOdds]
    min_profit: float
    max_profit: float
    status: ArbitrageStatus = ArbitrageStatus.ACTIVE

    @classmethod
    def from_arbitrage(cls, arbitrage: Arbitrage) -> "ArbitrageDetectedEvent":
        """Create event from Arbitrage model"""
        # Get appropriate odds data based on market type
        if arbitrage.market_type == MarketType.BTTS:
            bookmakers = {
                "yes": BookmakerOdds(**arbitrage.btts_odds_data["yes"]),
                "no": BookmakerOdds(**arbitrage.btts_odds_data["no"]),
            }
        else:  # THREE_WAY
            bookmakers = {
                "home": BookmakerOdds(**arbitrage.three_way_odds_data["home"]),
                "away": BookmakerOdds(**arbitrage.three_way_odds_data["away"]),
                "draw": BookmakerOdds(**arbitrage.three_way_odds_data["draw"]),
            }

        return cls(
            event_type=EventType.ARBITRAGE_DETECTED,
            match_id=arbitrage.match_id,
            arbitrage_id=arbitrage.arbitrage_id,
            market_type=arbitrage.market_type,
            data_source=arbitrage.data_source,
            bookmakers=bookmakers,
            min_profit=float(arbitrage.min_guaranteed_profit),
            max_profit=float(arbitrage.max_guaranteed_profit),
        )


class MarketStatusChangedEvent(ArbitrageDomainEvent):
    """Event for market status transitions"""

    previous_status: ArbitrageStatus
    new_status: ArbitrageStatus
    bookmaker_statuses: Dict[str, BookmakerStatus]
    change_reason: Optional[str] = None

    def get_routing_key(self) -> str:
        return f"{super().get_routing_key()}.status_changed"


class ProfitUpdateEvent(ArbitrageDomainEvent):
    """Event for profit threshold changes"""

    previous_min: float
    previous_max: float
    new_min: float
    new_max: float
    percentage_change: float
    threshold_crossed: Optional[float] = None

    def get_routing_key(self) -> str:
        return f"{super().get_routing_key()}.profit_update"


class ArbitrageExpiredEvent(ArbitrageDomainEvent):
    """Event for expired arbitrage opportunities"""

    expiry_time: datetime = Field(default_factory=lambda: datetime.now(ZoneInfo("UTC")))
    last_update_time: datetime
    expiry_reason: str

    def get_routing_key(self) -> str:
        return f"{super().get_routing_key()}.expired"


# Event Handlers
class ArbitrageEventHandler(DomainEventHandler):
    """Base handler for arbitrage events"""

    async def can_handle(self, event: DomainEvent) -> bool:
        return isinstance(event, ArbitrageDomainEvent)

    async def handle(self, event: ArbitrageDomainEvent) -> None:
        """Route event to specific handler method"""
        handlers = {
            ArbitrageDetectedEvent: self._handle_detected,
            BookmakerStatusChangedEvent: self._handle_bookmaker_status,
            MarketStatusChangedEvent: self._handle_status_change,
            ProfitUpdateEvent: self._handle_profit_update,
            ArbitrageExpiredEvent: self._handle_expired,
        }

        handler = handlers.get(type(event))
        if handler:
            await handler(event)

    async def _handle_detected(self, event: ArbitrageDetectedEvent) -> None:
        """Handle new arbitrage detection"""
        pass  # Implement in concrete handlers

    async def _handle_bookmaker_status(
        self, event: BookmakerStatusChangedEvent
    ) -> None:
        """Handle bookmaker status changes"""
        pass  # Implement in concrete handlers

    async def _handle_status_change(self, event: MarketStatusChangedEvent) -> None:
        """Handle status changes"""
        pass  # Implement in concrete handlers

    async def _handle_profit_update(self, event: ProfitUpdateEvent) -> None:
        """Handle profit updates"""
        pass  # Implement in concrete handlers

    async def _handle_expired(self, event: ArbitrageExpiredEvent) -> None:
        """Handle expired opportunities"""
        pass  # Implement in concrete handlers
