from typing import Optional, Dict, Any, AsyncGenerator, List
import asyncio
from datetime import datetime
from dataclasses import dataclass, field
import heapq
from zoneinfo import ZoneInfo

from core.events import BaseEvent, BookmakerStatusChangedEvent
from core.constants import EventType, MessagePriority, QUEUE_PRIORITIES
from core.exceptions import QueueOperationError


@dataclass(order=True)
class PrioritizedEvent:
    """Event wrapper with priority information"""

    priority: MessagePriority
    timestamp: datetime = field(compare=False)
    event: BaseEvent = field(compare=False)
    attempts: int = field(default=0, compare=False)
    last_attempt: Optional[datetime] = field(default=None, compare=False)


class AsyncPriorityQueue:
    """Thread-safe async priority queue implementation"""

    def __init__(self):
        self._queue = []
        self._lock = asyncio.Lock()

    async def put(self, item: PrioritizedEvent) -> None:
        """Add item to queue"""
        async with self._lock:
            heapq.heappush(self._queue, item)

    async def get(self) -> Optional[PrioritizedEvent]:
        """Get item from queue"""
        async with self._lock:
            if not self._queue:
                return None
            return heapq.heappop(self._queue)

    async def peek(self) -> Optional[PrioritizedEvent]:
        """View next item without removing"""
        async with self._lock:
            if not self._queue:
                return None
            return self._queue[0]

    def empty(self) -> bool:
        """Check if queue is empty"""
        return len(self._queue) == 0

    def size(self) -> int:
        """Get current queue size"""
        return len(self._queue)

    async def find_event(self, event: BaseEvent) -> Optional[PrioritizedEvent]:
        """Find specific event in queue"""
        async with self._lock:
            for item in self._queue:
                # Compare relevant identifiers based on event type
                if (hasattr(item.event, 'match_id') and 
                    hasattr(event, 'match_id') and
                    item.event.match_id == event.match_id and
                    item.event.event_type == event.event_type):
                    return item
            return None


class MessageQueue:
    """Priority-based message queue with rate limiting"""

    def __init__(
        self,
        batch_size: int = 10,
        rate_limit: int = 30,  # messages per minute
        retry_limit: int = 3,
        status_batch_size: int = 5  # Separate batch size for status events
    ):
        self._queue = AsyncPriorityQueue()
        self._batch_size = batch_size
        self._status_batch_size = status_batch_size
        self._rate_limit = rate_limit
        self._retry_limit = retry_limit
        self._processing = False
        self._last_processed: Dict[EventType, datetime] = {}
        self._status_events_buffer: List[BookmakerStatusChangedEvent] = []

    async def enqueue(self, event: BaseEvent) -> None:
        """Add event to queue with appropriate priority"""
        try:
            priority = QUEUE_PRIORITIES.get(event.event_type, MessagePriority.LOW)

            prioritized = PrioritizedEvent(
                priority=priority, timestamp=datetime.now(ZoneInfo("UTC")), event=event
            )

            await self._queue.put(prioritized)

        except Exception as e:
            raise QueueOperationError(f"Failed to enqueue event: {str(e)}")

    async def dequeue(self) -> Optional[BaseEvent]:
        """Get next event from queue respecting rate limits"""
        try:
            if self._queue.empty():
                return None

            prioritized = await self._queue.get()
            if not prioritized:
                return None

            event_type = prioritized.event.event_type

            # Check rate limiting
            if event_type in self._last_processed:
                time_since_last = (
                    datetime.now(ZoneInfo("UTC")) - self._last_processed[event_type]
                ).total_seconds()

                if time_since_last < (60 / self._rate_limit):
                    # Re-queue if rate limited
                    await self.enqueue(prioritized.event)
                    return None

            self._last_processed[event_type] = datetime.now(ZoneInfo("UTC"))
            return prioritized.event

        except Exception as e:
            raise QueueOperationError(f"Failed to dequeue event: {str(e)}")

    async def process_batch(self) -> AsyncGenerator[BaseEvent, None]:
        """Process batch of events respecting priorities and rate limits"""
        try:
            if self._processing:
                return

            self._processing = True
            processed = 0

            while processed < self._batch_size and not self._queue.empty():
                if event := await self.dequeue():
                    # Handle status events differently
                    if isinstance(event, BookmakerStatusChangedEvent):
                        self._status_events_buffer.append(event)
                        status_count += 1
                        
                        # Yield buffered status events when batch size reached
                        if status_count >= self._status_batch_size:
                            async for event in self._process_status_buffer():
                                yield event
                            status_count = 0
                    else:
                        yield event
                        processed += 1
                await asyncio.sleep(0.1)  # Prevent busy loop
            
            # Process any remaining status events
            if self._status_events_buffer:
                async for event in self._process_status_buffer():
                    yield event

            self._processing = False

        except Exception as e:
            self._processing = False
            raise QueueOperationError(f"Batch processing failed: {str(e)}")
        
    async def _process_status_buffer(self) -> AsyncGenerator[BaseEvent, None]:
        """Process buffered status events"""
        try:
            # Group status events by match_id
            grouped_events = {}
            for event in self._status_events_buffer:
                key = (event.match_id, event.market_type)
                if key not in grouped_events:
                    grouped_events[key] = []
                grouped_events[key].append(event)

            # Yield grouped events
            for events in grouped_events.values():
                yield events[0]  # Yield most recent for each match_id
            
            self._status_events_buffer.clear()

        except Exception as e:
            raise QueueOperationError(f"Status buffer processing failed: {str(e)}")

    async def retry_event(self, event: BaseEvent) -> None:
        """Re-queue event for retry with backoff"""
        try:
            # Find event in queue
            if prioritized := await self._queue.find_event(event):
                if prioritized.attempts < self._retry_limit:
                    # Create new prioritized event with incremented attempts
                    new_prioritized = PrioritizedEvent(
                        priority=MessagePriority.LOW,  # Lower priority for retries
                        timestamp=datetime.now(ZoneInfo("UTC")),
                        event=event,
                        attempts=prioritized.attempts + 1,
                        last_attempt=datetime.now(ZoneInfo("UTC")),
                    )
                    await self.enqueue(new_prioritized.event)

        except Exception as e:
            raise QueueOperationError(f"Failed to retry event: {str(e)}")

    def get_queue_stats(self) -> Dict[str, Any]:
        """Get current queue statistics"""
        return {
            "total_queued": self._queue.size(),
            "processing": self._processing,
            "last_processed": {
                k.value: v.isoformat() for k, v in self._last_processed.items()
            },
        }
