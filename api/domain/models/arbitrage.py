from datetime import datetime
from decimal import Decimal
from typing import Dict, Optional, Any
from pydantic import BaseModel, Field, model_validator
from zoneinfo import ZoneInfo

from core.constants import MarketType, DataSource
from core.events import (
    ArbitrageEvent,
    EventFactory,
    EventType,
)  # why are we importing EventType from events yet its in constants
from core.exceptions import MarketValidationError


class BookmakerOdds(BaseModel):
    """Represents odds data for a single bookmaker"""

    odd: Decimal
    active: bool
    status: bool
    destination_url: str
    stake: Optional[Decimal] = None


class MarketData(BaseModel):
    """Base class for market-specific data"""

    total_stake: Decimal
    odds_data: Dict[str, BookmakerOdds]


class ThreeWayMarketData(MarketData):
    """Represents three-way market data"""

    home_stake: Decimal
    away_stake: Decimal
    draw_stake: Decimal


class BTTSMarketData(MarketData):
    """Represents BTTS market data"""

    yes_stake: Decimal
    no_stake: Decimal


class Arbitrage(BaseModel):
    """Core domain model for arbitrage opportunities"""

    # Primary identifiers
    match_id: int
    arbitrage_id: int

    # Team and competition details
    home_team_name: str
    away_team_name: str

    # Market details
    market_type: MarketType
    data_source: DataSource
    bet_description: str

    # Timing information
    arbitrage_created: datetime = Field(
        default_factory=lambda: datetime.now(ZoneInfo("UTC"))
    )
    arbitrage_updated: Optional[datetime]

    # Financial calculations
    total_stake: Decimal
    min_guaranteed_profit: Decimal
    max_guaranteed_profit: Decimal

    # Market data
    three_way_market_data: Optional[Dict[str, Any]]
    btts_market_data: Optional[Dict[str, Any]]
    three_way_odds_data: Optional[Dict[str, Any]]
    btts_odds_data: Optional[Dict[str, Any]]

    @model_validator(mode="after")
    def validate_market_data(cls, v, values):
        """Ensure market data matches market type"""
        if v == MarketType.THREE_WAY and not values.get("three_way_market_data"):
            raise MarketValidationError(
                "Three-way market type requires three_way_market_data"
            )
        if v == MarketType.BTTS and not values.get("btts_market_data"):
            raise MarketValidationError("BTTS market type requires btts_market_data")
        return v

    def to_event(
        self, event_type: EventType = EventType.ARBITRAGE_DETECTED
    ) -> ArbitrageEvent:
        """Convert arbitrage to event object"""
        bookmakers = {}

        if self.market_type == MarketType.BTTS:
            bookmakers = {
                "yes": BookmakerOdds(**self.btts_odds_data["yes"]),
                "no": BookmakerOdds(**self.btts_odds_data["no"]),
            }
        elif self.market_type == MarketType.THREE_WAY:
            bookmakers = {
                "home": BookmakerOdds(**self.three_way_odds_data["home"]),
                "away": BookmakerOdds(**self.three_way_odds_data["away"]),
                "draw": BookmakerOdds(**self.three_way_odds_data["draw"]),
            }

        return EventFactory.create_event(
            event_type=event_type,
            match_id=self.match_id,
            arbitrage_id=self.arbitrage_id,
            home_team_name=self.home_team_name,
            away_team_name=self.away_team_name,
            bet_description=self.bet_description,
            market_type=self.market_type,
            data_source=self.data_source,
            min_profit=float(self.min_guaranteed_profit),
            max_profit=float(self.max_guaranteed_profit),
            bookmakers={k: v.model_dump() for k, v in bookmakers.items()},
        )

    @classmethod
    def from_db_dict(cls, data: Dict[str, Any]) -> "Arbitrage":
        """Create Arbitrage instance from database dictionary"""
        return cls(**{k: v for k, v in data.items() if k in Arbitrage.model_fields})

    # def is_active(self) -> bool:
    #     """Check if arbitrage opportunity is still active"""
    #     if self.market_type == MarketType.BTTS:
    #         return all(odd["active"] for odd in self.btts_odds_data.values())
    #     return all(odd["active"] for odd in self.three_way_odds_data.values())

    def get_bookmaker_states(self) -> Dict[str, Dict[str, Dict[str, bool]]]:
        """Get current states of all bookmakers in this opportunity"""
        if self.market_type == MarketType.BTTS:
            return {
                "btts": {
                    k: {"active": v["active"], "status": v["status"]}
                    for k, v in self.btts_odds_data.items()
                }
            }
        else:  # THREE_WAY
            return {
                "three_way": {
                    k: {"active": v["active"], "status": v["status"]}
                    for k, v in self.three_way_odds_data.items()
                }
            }

    def calculate_profit_change(self, previous: "Arbitrage") -> tuple[float, float]:
        """Calculate profit changes from previous state"""
        min_delta = float(self.min_guaranteed_profit - previous.min_guaranteed_profit)
        max_delta = float(self.max_guaranteed_profit - previous.max_guaranteed_profit)
        return min_delta, max_delta
