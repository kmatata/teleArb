from typing import AsyncGenerator
import aiosqlite
import sqlite3

from core.config import settings
from core.exceptions import DatabaseConnectionError, DatabaseOperationError


class DatabaseManager:
    """Async database manager for Monitor DB operations"""

    def __init__(self):
        self.db_path = settings.monitor_db_path
        self.schema_path = settings.schema_path
        self._verify_db()

    def _verify_db(self) -> None:
        """Verify database exists and is accessible"""
        try:
            if not self.db_path.exists():
                raise DatabaseConnectionError(
                    f"Monitor DB not found at {self.db_path}. "
                    "Ensure aggregator is properly initialized."
                )

            # Test connection
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")

        except Exception as e:
            raise DatabaseConnectionError(f"Database verification failed: {str(e)}")

    async def get_connection(self) -> AsyncGenerator[aiosqlite.Connection, None]:
        """Get async database connection"""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                conn.row_factory = aiosqlite.Row
                yield conn
        except Exception as e:
            raise DatabaseConnectionError(
                f"Failed to get database connection: {str(e)}"
            )

    async def execute_query(self, query: str, params: tuple = ()) -> aiosqlite.Cursor:
        """Execute single query"""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                conn.row_factory = aiosqlite.Row
                return await conn.execute(query, params)
        except Exception as e:
            raise DatabaseOperationError(f"Query execution failed: {str(e)}")

    async def execute_many(self, query: str, params_list: list[tuple]) -> None:
        """Execute multiple queries"""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                await conn.executemany(query, params_list)
                await conn.commit()
        except Exception as e:
            raise DatabaseOperationError(f"Batch execution failed: {str(e)}")


# Global instance
db = DatabaseManager()
