from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional

class APISettings(BaseSettings):
    # Database paths (pointing to aggregator module paths)
    MONITOR_DB_PATH: str = "../../aggregator/monitorDB/monitor.db"
    MONITOR_SCHEMA_PATH: str = "../../aggregator/sql/monitor.sql"
    
    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # WebSocket Settings
    WS_HEARTBEAT_INTERVAL: int = 30  # seconds
    WS_CONNECTION_TIMEOUT: int = 60   # seconds
    
    # Message Queue Settings
    QUEUE_BATCH_SIZE: int = 10
    QUEUE_PROCESSING_INTERVAL: int = 1  # seconds
    
    # Telegram Bot Settings
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_CHAT_ID: Optional[str] = None
    
    # Market Cleanup Intervals (from existing db_manager.py)
    LIVE_MARKET_CLEANUP_SECONDS: int = 30
    UPCOMING_MARKET_CLEANUP_SECONDS: int = 80

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def monitor_db_path(self) -> Path:
        """Returns absolute path to the monitor.db in aggregator module"""
        return Path(__file__).parent.parent.parent / "aggregator" / "monitorDB" / "monitor.db"

    @property
    def schema_path(self) -> Path:
        """Returns absolute path to the monitor.sql in aggregator module"""
        return Path(__file__).parent.parent.parent / "aggregator" / "sql" / "monitor.sql"

# Create settings instance
settings = APISettings()