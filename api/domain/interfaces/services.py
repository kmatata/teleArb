from abc import abstractmethod
from typing import Protocol, AsyncIterator

from models.arbitrage import Arbitrage
from models.connection import WebSocketConnection
from core.events import BaseEvent


class ArbitrageService(Protocol):
    """Service interface for arbitrage business logic"""
    
    @abstractmethod
    async def process_new_arbitrage(self, arbitrage: Arbitrage) -> BaseEvent:
        """Process new arbitrage opportunity"""
        pass
    
    @abstractmethod
    async def update_market_status(
        self, 
        match_id: int, 
        arbitrage_id: int, 
        is_active: bool
    ) -> BaseEvent:
        """Update market status and generate appropriate event"""
        pass
    
    @abstractmethod
    async def calculate_profit_changes(
        self, 
        current: Arbitrage, 
        previous: Arbitrage
    ) -> BaseEvent:
        """Calculate profit changes and generate event if threshold crossed"""
        pass

class MessageQueueService(Protocol):
    """Service interface for message queue operations"""
    
    @abstractmethod
    async def queue_event(self, event: BaseEvent) -> None:
        """Queue new event for processing"""
        pass
    
    @abstractmethod
    async def process_queue(self) -> AsyncIterator[BaseEvent]:
        """Process queued events"""
        pass
    
    @abstractmethod
    async def get_pending_count(self) -> int:
        """Get count of pending events"""
        pass

class WebSocketService(Protocol):
    """Service interface for WebSocket operations"""
    
    @abstractmethod
    async def register_connection(
        self, 
        client_id: str, 
        metadata: dict
    ) -> WebSocketConnection:
        """Register new WebSocket connection"""
        pass
    
    @abstractmethod
    async def broadcast_event(self, event: BaseEvent) -> None:
        """Broadcast event to relevant connections"""
        pass
    
    @abstractmethod
    async def handle_subscription(
        self, 
        client_id: str, 
        match_id: int, 
        subscribe: bool
    ) -> None:
        """Handle match subscription/unsubscription"""
        pass