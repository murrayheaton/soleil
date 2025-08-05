"""
Event Bus for Inter-Module Communication

This module provides a simple publish/subscribe event bus for communication
between SOLEil modules without creating direct dependencies.
"""
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timezone
import asyncio
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class EventPriority(Enum):
    """Priority levels for event handling"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Event:
    """Base event class for all module events"""
    name: str
    module: str
    data: Dict[str, Any]
    timestamp: datetime = None
    priority: EventPriority = EventPriority.NORMAL
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)


class EventBus:
    """
    Simple event bus implementation for module communication.
    
    Features:
    - Async event handling
    - Priority-based processing
    - Event history
    - Error isolation
    """
    
    def __init__(self, history_size: int = 100):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._event_history: List[Event] = []
        self._history_size = history_size
        self._lock = asyncio.Lock()
        
    async def publish(self, event_type: str, data: dict, source_module: str) -> None:
        """
        Publish an event to all subscribers.
        
        Args:
            event_type: Type of the event
            data: Event data
            source_module: Module that published the event
        """
        event = Event(
            name=event_type,
            module=source_module,
            data=data,
            priority=data.get('priority', EventPriority.NORMAL)
        )
        
        async with self._lock:
            # Add to history
            self._event_history.append(event)
            if len(self._event_history) > self._history_size:
                self._event_history.pop(0)
                
            # Get subscribers for this event
            subscribers = self._subscribers.get(event.name, [])
            
            # Sort by priority if needed
            if event.priority != EventPriority.NORMAL:
                # For high priority events, process immediately
                await self._process_event(event, subscribers)
            else:
                # For normal priority, schedule processing
                asyncio.create_task(self._process_event(event, subscribers))
    
    async def _process_event(self, event: Event, subscribers: List[dict]) -> None:
        """Process an event for all subscribers"""
        for subscriber_info in subscribers:
            handler = subscriber_info['handler'] if isinstance(subscriber_info, dict) else subscriber_info
            module = subscriber_info.get('module', 'unknown') if isinstance(subscriber_info, dict) else 'unknown'
            
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(
                    f"Error processing event {event.name} in module '{module}': {e}",
                    exc_info=True
                )
    
    def subscribe(self, event_type: str, handler: Callable, target_module: str) -> None:
        """
        Subscribe to an event.
        
        Args:
            event_type: Type of the event to subscribe to
            handler: Callback function to handle the event
            target_module: Module that is subscribing
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        
        # Store handler with metadata
        handler_info = {
            'handler': handler,
            'module': target_module
        }
        self._subscribers[event_type].append(handler_info)
        logger.debug(f"Module '{target_module}' subscribed to event: {event_type}")
    
    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """
        Unsubscribe from an event.
        
        Args:
            event_type: Type of the event to unsubscribe from
            handler: The handler to remove
        """
        if event_type in self._subscribers:
            # Find and remove the handler
            self._subscribers[event_type] = [
                sub for sub in self._subscribers[event_type]
                if (sub['handler'] if isinstance(sub, dict) else sub) != handler
            ]
            if not self._subscribers[event_type]:
                del self._subscribers[event_type]
    
    def get_history(self, event_name: Optional[str] = None) -> List[Event]:
        """
        Get event history.
        
        Args:
            event_name: Optional filter by event name
            
        Returns:
            List of historical events
        """
        if event_name:
            return [e for e in self._event_history if e.name == event_name]
        return self._event_history.copy()
    
    def clear_history(self) -> None:
        """Clear event history"""
        self._event_history.clear()
    
    def get_subscribers_count(self) -> Dict[str, int]:
        """Get count of subscribers per event"""
        return {event: len(handlers) for event, handlers in self._subscribers.items()}


# Global event bus instance
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get the global event bus instance"""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


def reset_event_bus() -> None:
    """Reset the global event bus (mainly for testing)"""
    global _event_bus
    _event_bus = None