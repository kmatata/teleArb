from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional, List, AsyncGenerator
import aiosqlite

from core.exceptions import DatabaseOperationError
from infrastructure.database.connection import db

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """Base repository for reading from monitor.db"""

    def __init__(self):
        self._db = db

    @abstractmethod
    async def _map_to_entity(self, row: aiosqlite.Row) -> T:
        """Map database row to domain entity"""
        pass

    async def get_by_query(self, query: str, params: tuple = ()) -> Optional[T]:
        """Execute custom query and return single entity"""
        try:
            async with self._db.get_connection() as conn:
                cursor = await conn.execute(query, params)
                if row := await cursor.fetchone():
                    return await self._map_to_entity(row)
                return None
        except Exception as e:
            raise DatabaseOperationError(f"Query failed: {str(e)}")

    async def get_many(self, query: str, params: tuple = ()) -> List[T]:
        """Execute custom query and return multiple entities"""
        try:
            async with self._db.get_connection() as conn:
                cursor = await conn.execute(query, params)
                rows = await cursor.fetchall()
                return [await self._map_to_entity(row) for row in rows]
        except Exception as e:
            raise DatabaseOperationError(f"Query failed: {str(e)}")

    async def watch_table(
        self, query: str, params: tuple = ()
    ) -> AsyncGenerator[T, None]:
        """Watch for changes using custom query"""
        try:
            last_update = None
            while True:
                async with self._db.get_connection() as conn:
                    # Add timestamp check if query has one
                    modified_query = query
                    if last_update:
                        modified_query = f"{query} AND arbitrage_updated > ?"
                        params = (*params, last_update)

                    cursor = await conn.execute(modified_query, params)
                    while row := await cursor.fetchone():
                        entity = await self._map_to_entity(row)
                        if hasattr(row, "arbitrage_updated"):
                            last_update = row["arbitrage_updated"]
                        yield entity
        except Exception as e:
            raise DatabaseOperationError(f"Watch query failed: {str(e)}")
