from typing import Dict, List, Set
import asyncio
from logging import Logger

from core.events import BaseEvent
from core.constants import EventType
from core.exceptions import EventProcessingError
from domain.events.base import DomainEventHandler
from .queue import MessageQueue

class EventDispatcher:
    """Handles distribution of events to registered handlers"""
    
    def __init__(
        self, 
        message_queue: MessageQueue,
        logger: Logger
    ):
        self._queue = message_queue
        self._logger = logger
        self._handlers: Dict[EventType, List[DomainEventHandler]] = {}
        self._running = False
        self._processing_tasks: Set[asyncio.Task] = set()

    async def register_handler(
        self, 
        event_type: EventType, 
        handler: DomainEventHandler
    ) -> None:
        """Register a handler for specific event type"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        self._logger.info(f"Registered handler {handler.__class__.__name__} for {event_type}")

    async def dispatch_event(self, event: BaseEvent) -> None:
        """Dispatch single event to registered handlers"""
        try:
            if event.event_type not in self._handlers:
                self._logger.warning(f"No handlers registered for {event.event_type}")
                return

            handlers = self._handlers[event.event_type]
            for handler in handlers:
                if await handler.can_handle(event):
                    try:
                        await handler.handle(event)
                    except Exception as e:
                        self._logger.error(
                            f"Handler {handler.__class__.__name__} failed: {str(e)}"
                        )
                        # Retry logic for failed events
                        await self._queue.retry_event(event)

        except Exception as e:
            raise EventProcessingError(f"Event dispatch failed: {str(e)}")

    async def start_processing(self) -> None:
        """Start processing events from queue"""
        if self._running:
            return

        self._running = True
        self._logger.info("Starting event dispatcher")

        try:
            while self._running:
                async for event in self._queue.process_batch():
                    # Create task for each event
                    task = asyncio.create_task(self.dispatch_event(event))
                    self._processing_tasks.add(task)
                    task.add_done_callback(self._processing_tasks.discard)

                await asyncio.sleep(0.1)  # Prevent busy loop

        except Exception as e:
            self._logger.error(f"Event processing loop failed: {str(e)}")
            self._running = False
            raise

    async def stop_processing(self) -> None:
        """Stop processing events"""
        self._logger.info("Stopping event dispatcher")
        self._running = False
        
        # Wait for pending tasks
        if self._processing_tasks:
            await asyncio.gather(*self._processing_tasks, return_exceptions=True)
        
        self._processing_tasks.clear()
        self._logger.info("Event dispatcher stopped")

    def get_stats(self) -> Dict[str, any]:
        """Get dispatcher statistics"""
        return {
            "running": self._running,
            "handlers": {
                event_type.value: [h.__class__.__name__ for h in handlers]
                for event_type, handlers in self._handlers.items()
            },
            "active_tasks": len(self._processing_tasks),
            "queue_stats": self._queue.get_queue_stats()
        }