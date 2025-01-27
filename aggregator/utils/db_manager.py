import sqlite3
from pathlib import Path
from typing import Dict, Any
from .logger import Logger


class MonitorDatabaseManager:
    """Manages the aggregation database operations and cleanup rules"""

    def __init__(self, db_path: str, schema_path: str):
        self.db_path = Path(db_path)
        self.schema_path = Path(schema_path)
        self.logger = Logger(__name__)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database with schema if it doesn't exist"""
        try:
            # directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

            # schema file
            with open(self.schema_path, "r") as f:
                schema_sql = f.read()

            with sqlite3.connect(self.db_path) as conn:
                conn.executescript(schema_sql)
                self.logger.info("Database initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize database: {str(e)}")
            raise

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def clean_old_records(self) -> None:
        """Clean records based on market type and timestamp rules"""
        try:
            with self._get_connection() as conn:
                # Delete LIVE market records older than 30 seconds
                conn.execute(
                    """
                    DELETE FROM match_arbitrage_aggregate
                    WHERE data_source = 'live'
                    AND (
                        (arbitrage_updated IS NULL 
                        AND strftime('%s', 'now') - strftime('%s', arbitrage_created) > 30)
                        OR 
                        (arbitrage_updated IS NOT NULL 
                        AND strftime('%s', 'now') - strftime('%s', arbitrage_updated) > 30)
                    )
                """
                )

                # Delete UPCOMING market records older than 80 seconds
                conn.execute(
                    """
                    DELETE FROM match_arbitrage_aggregate
                    WHERE data_source = 'upcoming'
                    AND (
                        (arbitrage_updated IS NULL 
                        AND strftime('%s', 'now') - strftime('%s', arbitrage_created) > 80)
                        OR 
                        (arbitrage_updated IS NOT NULL 
                        AND strftime('%s', 'now') - strftime('%s', arbitrage_updated) > 80)
                    )
                """
                )

                deleted_count = conn.total_changes
                self.logger.info(f"Cleaned {deleted_count} old records")

        except Exception as e:
            self.logger.error(f"Failed to clean old records: {str(e)}")
            raise

    def upsert_record(self, record: Dict[str, Any]) -> None:
        """Insert or update a record based on composite uniqueness"""
        try:
            with self._get_connection() as conn:
                # Check if record exists using all uniqueness fields
                cursor = conn.execute(
                    """
                    SELECT match_id 
                    FROM match_arbitrage_aggregate 
                    WHERE match_id = ? 
                    AND arbitrage_id = ?
                    AND market_type = ?
                    AND data_source = ?
                    AND bet_description = ?
                    """,
                    (
                        record["match_id"],
                        record["arbitrage_id"],
                        record["market_type"],
                        record["data_source"],
                        record["bet_description"],
                    ),
                )

                exists = cursor.fetchone() is not None

                if exists:
                    # Update existing record
                    set_clauses = []
                    values = []

                    for key, value in record.items():
                        if key not in [
                            "match_id",
                            "arbitrage_id",
                            "market_type",
                            "data_source",
                            "bet_description",
                        ]:
                            set_clauses.append(f"{key} = ?")
                            values.append(value)

                    # WHERE clause values
                    values.extend(
                        [
                            record["match_id"],
                            record["arbitrage_id"],
                            record["market_type"],
                            record["data_source"],
                            record["bet_description"],
                        ]
                    )

                    update_sql = f"""
                        UPDATE match_arbitrage_aggregate 
                        SET {', '.join(set_clauses)}
                        WHERE match_id = ?
                        AND arbitrage_id = ?
                        AND market_type = ?
                        AND data_source = ?
                        AND bet_description = ?
                    """

                    conn.execute(update_sql, values)
                    self.logger.debug(
                        f"Updated record: match_id={record['match_id']}, "
                        f"arbitrage_id={record['arbitrage_id']}, "
                        f"market_type={record['market_type']}"
                    )

                else:
                    # Insert new record
                    placeholders = ", ".join(["?" for _ in record])
                    columns = ", ".join(record.keys())

                    insert_sql = f"""
                        INSERT INTO match_arbitrage_aggregate ({columns})
                        VALUES ({placeholders})
                    """

                    conn.execute(insert_sql, list(record.values()))
                    self.logger.debug(
                        f"Inserted new record: match_id={record['match_id']}, "
                        f"arbitrage_id={record['arbitrage_id']}, "
                        f"market_type={record['market_type']}"
                    )

                conn.commit()

        except Exception as e:
            self.logger.error(f"Failed to upsert record: {str(e)}")
            raise

    def process_export_db(self, export_path: Path) -> bool:
        """Process records from an export database"""
        try:
            with sqlite3.connect(export_path) as export_conn:
                export_conn.row_factory = sqlite3.Row

                # all records from export database
                cursor = export_conn.execute("SELECT * FROM match_arbitrage_export")
                records = cursor.fetchall()

                processed_count = 0
                for record in records:
                    self.upsert_record(dict(record))
                    processed_count += 1

                self.logger.info(
                    f"Processed {processed_count} records from {export_path}"
                )
                return True

        except Exception as e:
            self.logger.error(
                f"Failed to process export database {export_path}: {str(e)}"
            )
            return False
