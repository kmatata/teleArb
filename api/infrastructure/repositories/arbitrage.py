from typing import Optional, List, AsyncIterator, Dict, Any
import json
from decimal import Decimal

from domain.interfaces.repositories import ArbitrageRepository
from domain.models.arbitrage import Arbitrage
from core.constants import MarketType, DataSource
from base import BaseRepository


class SQLiteArbitrageRepository(BaseRepository[Arbitrage], ArbitrageRepository):
    """Repository implementation for match_arbitrage_aggregate table"""

    async def _map_to_entity(self, row: Dict[str, Any]) -> Arbitrage:
        """Map database row to Arbitrage entity"""
        # Parse JSON fields
        three_way_market = (
            json.loads(row["three_way_market_data"])
            if row["three_way_market_data"]
            else None
        )
        btts_market = (
            json.loads(row["btts_market_data"]) if row["btts_market_data"] else None
        )
        three_way_odds = (
            json.loads(row["three_way_odds_data"])
            if row["three_way_odds_data"]
            else None
        )
        btts_odds = json.loads(row["btts_odds_data"]) if row["btts_odds_data"] else None

        return Arbitrage(
            match_id=row["match_id"],
            arbitrage_id=row["arbitrage_id"],
            home_team_name=row["home_team_name"],
            away_team_name=row["away_team_name"],
            market_type=MarketType(row["market_type"]),
            data_source=DataSource(row["data_source"]),
            bet_description=row["bet_description"],
            arbitrage_created=row["arbitrage_created"],
            arbitrage_updated=row["arbitrage_updated"],
            total_stake=Decimal(str(row["total_stake"])),
            min_guaranteed_profit=Decimal(str(row["min_guaranteed_profit"])),
            max_guaranteed_profit=Decimal(str(row["max_guaranteed_profit"])),
            three_way_market_data=three_way_market,
            btts_market_data=btts_market,
            three_way_odds_data=three_way_odds,
            btts_odds_data=btts_odds,
        )

    async def get_by_id(self, match_id: int, arbitrage_id: int) -> Optional[Arbitrage]:
        """Get specific arbitrage opportunity"""
        query = """
            SELECT * FROM match_arbitrage_aggregate 
            WHERE match_id = ? AND arbitrage_id = ?
        """
        return await self.get_by_query(query, (match_id, arbitrage_id))

    async def get_active_by_match(self, match_id: int) -> List[Arbitrage]:
        """Get all active arbitrage opportunities for a match"""
        query = """
            SELECT * FROM match_arbitrage_aggregate 
            WHERE match_id = ?
            AND arbitrage_updated = (
                SELECT MAX(arbitrage_updated)
                FROM match_arbitrage_aggregate
                WHERE match_id = ?
            )
        """
        return await self.get_many(query, (match_id, match_id))

    async def get_by_market_type(
        self, market_type: MarketType, data_source: DataSource
    ) -> List[Arbitrage]:
        """Get arbitrage opportunities by market type and source"""
        query = """
            SELECT * FROM match_arbitrage_aggregate 
            WHERE market_type = ? 
            AND data_source = ?
            ORDER BY arbitrage_updated DESC
        """
        return await self.get_many(query, (market_type.value, data_source.value))

    async def watch_updates(self) -> AsyncIterator[Arbitrage]:
        """Watch for new arbitrage updates"""
        base_query = """
            SELECT * FROM match_arbitrage_aggregate 
            WHERE 1=1
        """
        async for arbitrage in self.watch_table(base_query):
            yield arbitrage

    async def get_latest_opportunities(self, limit: int = 10) -> List[Arbitrage]:
        """Get most recent arbitrage opportunities"""
        query = """
            SELECT * FROM match_arbitrage_aggregate 
            ORDER BY arbitrage_updated DESC 
            LIMIT ?
        """
        return await self.get_many(query, (limit,))

    async def get_high_profit_opportunities(
        self, min_profit: float = 5.0
    ) -> List[Arbitrage]:
        """Get opportunities with high profit potential"""
        query = """
            SELECT * FROM match_arbitrage_aggregate 
            WHERE min_guaranteed_profit >= ?
            ORDER BY min_guaranteed_profit DESC
        """
        return await self.get_many(query, (min_profit,))
