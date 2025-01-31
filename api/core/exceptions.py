from typing import Optional, Any

class APIBaseException(Exception):
    """Base exception for API module"""
    def __init__(self, message: str, details: Optional[Any] = None):
        self.message = message
        self.details = details
        super().__init__(self.message)

# Database Exceptions
class DatabaseConnectionError(APIBaseException):
    """Raised when unable to connect to monitor.db"""
    pass

class DatabaseOperationError(APIBaseException):
    """Raised when database operation fails"""
    pass

# WebSocket Exceptions
class WebSocketConnectionError(APIBaseException):
    """Raised for WebSocket connection issues"""
    pass

class WebSocketMessageError(APIBaseException):
    """Raised when processing WebSocket messages fails"""
    pass

# Event Processing Exceptions
class EventProcessingError(APIBaseException):
    """Raised when event processing fails"""
    pass

class InvalidEventTypeError(APIBaseException):
    """Raised when event type is invalid"""
    pass

# Message Queue Exceptions
class QueueOperationError(APIBaseException):
    """Raised when queue operation fails"""
    pass

class MessageProcessingError(APIBaseException):
    """Raised when processing queued message fails"""
    pass

# Market Data Exceptions
class MarketValidationError(APIBaseException):
    """Raised when market data validation fails"""
    pass

class MarketStateError(APIBaseException):
    """Raised when market state transition is invalid"""
    pass