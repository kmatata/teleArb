from abc import abstractmethod
from typing import List, Optional, Protocol, AsyncIterator

from models.arbitrage import Arbitrage
from models.message import MessageCursor
from models.connection import WebSocketConnection
from core.constants import MarketType, DataSource

class ArbitrageRepository(Protocol):
    """Repository interface for arbitrage operations"""
    
    @abstractmethod
    async def get_by_id(self, match_id: int, arbitrage_id: int) -> Optional[Arbitrage]:
        """Retrieve specific arbitrage by IDs"""
        pass
    
    @abstractmethod
    async def get_active_by_match(self, match_id: int) -> List[Arbitrage]:
        """Get all active arbitrage opportunities for a match"""
        pass
    
    @abstractmethod
    async def get_by_market_type(
        self, 
        market_type: MarketType, 
        data_source: DataSource
    ) -> List[Arbitrage]:
        """Get arbitrage opportunities by market type and source"""
        pass
        
    @abstractmethod
    async def watch_updates(self) -> AsyncIterator[Arbitrage]:
        """Stream of arbitrage updates"""
        pass

class MessageRepository(Protocol):
    """Repository interface for message cursor operations"""
    
    @abstractmethod
    async def get_cursor(self, message_id: int, chat_id: int) -> Optional[MessageCursor]:
        """Get message cursor by IDs"""
        pass
    
    @abstractmethod
    async def save_cursor(self, cursor: MessageCursor) -> None:
        """Save or update message cursor"""
        pass
        
    @abstractmethod
    async def get_active_cursors_by_match(self, match_id: int) -> List[MessageCursor]:
        """Get all active cursors for a match"""
        pass

class ConnectionRepository(Protocol):
    """Repository interface for WebSocket connection management"""
    
    @abstractmethod
    async def save_connection(self, connection: WebSocketConnection) -> None:
        """Save or update connection state"""
        pass
    
    @abstractmethod
    async def get_connection(self, client_id: str) -> Optional[WebSocketConnection]:
        """Get connection by client ID"""
        pass
        
    @abstractmethod
    async def get_active_connections(self) -> List[WebSocketConnection]:
        """Get all active connections"""
        pass
        
    @abstractmethod
    async def remove_connection(self, client_id: str) -> None:
        """Remove connection"""
        pass