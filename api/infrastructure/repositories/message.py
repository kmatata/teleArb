from typing import Optional, List
from datetime import datetime
import aiosqlite
import sqlite3
from domain.interfaces.repositories import MessageRepository
from domain.models.message import MessageCursor
from core.config import settings
from core.exceptions import DatabaseOperationError


class SQLiteMessageRepository(MessageRepository):
    """Repository implementation for message cursor management"""

    def __init__(self):
        self.db_path = settings.monitor_db_path.parent / "message_cursors.db"
        self._init_db()

    def _init_db(self) -> None:
        """Initialize message cursors database"""
        try:
            # Create cursors db if it doesn't exist
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS message_cursors (
                        message_id INTEGER,
                        chat_id INTEGER,
                        match_id INTEGER,
                        market_type TEXT,
                        data_source TEXT,
                        created_at TIMESTAMP,
                        updated_at TIMESTAMP,
                        last_event_type TEXT,
                        is_active BOOLEAN,
                        update_count INTEGER,
                        last_arbitrage_id INTEGER,
                        PRIMARY KEY (message_id, chat_id)
                    )
                """
                )
                conn.commit()
        except Exception as e:
            raise DatabaseOperationError(
                f"Failed to initialize message cursors db: {str(e)}"
            )

    async def get_cursor(
        self, message_id: int, chat_id: int
    ) -> Optional[MessageCursor]:
        """Get message cursor by IDs"""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                conn.row_factory = aiosqlite.Row
                cursor = await conn.execute(
                    """
                    SELECT * FROM message_cursors 
                    WHERE message_id = ? AND chat_id = ?
                """,
                    (message_id, chat_id),
                )

                if row := await cursor.fetchone():
                    return MessageCursor(
                        message_id=row["message_id"],
                        chat_id=row["chat_id"],
                        match_id=row["match_id"],
                        market_type=row["market_type"],
                        data_source=row["data_source"],
                        created_at=datetime.fromisoformat(row["created_at"]),
                        updated_at=(
                            datetime.fromisoformat(row["updated_at"])
                            if row["updated_at"]
                            else None
                        ),
                        last_event_type=row["last_event_type"],
                        is_active=bool(row["is_active"]),
                        update_count=row["update_count"],
                        last_arbitrage_id=row["last_arbitrage_id"],
                    )
                return None
        except Exception as e:
            raise DatabaseOperationError(f"Failed to get message cursor: {str(e)}")

    async def save_cursor(self, cursor: MessageCursor) -> None:
        """Save or update message cursor"""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                await conn.execute(
                    """
                    INSERT OR REPLACE INTO message_cursors (
                        message_id, chat_id, match_id, market_type, data_source,
                        created_at, updated_at, last_event_type, is_active,
                        update_count, last_arbitrage_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        cursor.message_id,
                        cursor.chat_id,
                        cursor.match_id,
                        cursor.market_type,
                        cursor.data_source,
                        cursor.created_at.isoformat(),
                        cursor.updated_at.isoformat() if cursor.updated_at else None,
                        cursor.last_event_type,
                        cursor.is_active,
                        cursor.update_count,
                        cursor.last_arbitrage_id,
                    ),
                )
                await conn.commit()
        except Exception as e:
            raise DatabaseOperationError(f"Failed to save message cursor: {str(e)}")

    async def get_active_cursors_by_match(self, match_id: int) -> List[MessageCursor]:
        """Get all active cursors for a match"""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                conn.row_factory = aiosqlite.Row
                cursor = await conn.execute(
                    """
                    SELECT * FROM message_cursors 
                    WHERE match_id = ? AND is_active = 1
                    ORDER BY updated_at DESC NULLS LAST
                """,
                    (match_id,),
                )

                rows = await cursor.fetchall()
                return [
                    MessageCursor(
                        message_id=row["message_id"],
                        chat_id=row["chat_id"],
                        match_id=row["match_id"],
                        market_type=row["market_type"],
                        data_source=row["data_source"],
                        created_at=datetime.fromisoformat(row["created_at"]),
                        updated_at=(
                            datetime.fromisoformat(row["updated_at"])
                            if row["updated_at"]
                            else None
                        ),
                        last_event_type=row["last_event_type"],
                        is_active=bool(row["is_active"]),
                        update_count=row["update_count"],
                        last_arbitrage_id=row["last_arbitrage_id"],
                    )
                    for row in rows
                ]
        except Exception as e:
            raise DatabaseOperationError(f"Failed to get active cursors: {str(e)}")

    async def cleanup_inactive_cursors(self, max_age_hours: int = 24) -> int:
        """Clean up old inactive cursors"""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                cursor = await conn.execute(
                    """
                    DELETE FROM message_cursors 
                    WHERE is_active = 0 
                    AND datetime(updated_at) < datetime('now', ?)
                """,
                    (f"-{max_age_hours} hours",),
                )
                await conn.commit()
                return cursor.rowcount
        except Exception as e:
            raise DatabaseOperationError(f"Failed to cleanup cursors: {str(e)}")
