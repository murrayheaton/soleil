"""Tests for EventBus functionality"""
import asyncio
import pytest

from ..event_bus import EventBus, Event, EventPriority, get_event_bus, reset_event_bus


class TestEventBus:
    """Test EventBus functionality"""
    
    def setup_method(self):
        """Reset event bus before each test"""
        reset_event_bus()
        self.event_bus = EventBus()
        self.received_events = []
        
    def sync_handler(self, event: Event):
        """Synchronous event handler for testing"""
        self.received_events.append(event)
        
    async def async_handler(self, event: Event):
        """Asynchronous event handler for testing"""
        await asyncio.sleep(0.01)  # Simulate async work
        self.received_events.append(event)
        
    @pytest.mark.asyncio
    async def test_publish_subscribe_sync(self):
        """Test basic publish/subscribe with sync handler"""
        # Subscribe to event
        self.event_bus.subscribe("test.event", self.sync_handler)
        
        # Publish event
        event = Event(
            name="test.event",
            module="test",
            data={"message": "Hello"}
        )
        await self.event_bus.publish(event)
        
        # Allow event processing
        await asyncio.sleep(0.1)
        
        # Verify event received
        assert len(self.received_events) == 1
        assert self.received_events[0].name == "test.event"
        assert self.received_events[0].data["message"] == "Hello"
        
    @pytest.mark.asyncio
    async def test_publish_subscribe_async(self):
        """Test publish/subscribe with async handler"""
        # Subscribe to event
        self.event_bus.subscribe("test.async", self.async_handler)
        
        # Publish event
        event = Event(
            name="test.async",
            module="test",
            data={"value": 42}
        )
        await self.event_bus.publish(event)
        
        # Allow async processing
        await asyncio.sleep(0.1)
        
        # Verify event received
        assert len(self.received_events) == 1
        assert self.received_events[0].data["value"] == 42
        
    @pytest.mark.asyncio
    async def test_multiple_subscribers(self):
        """Test multiple subscribers to same event"""
        counter = {"value": 0}
        
        def handler1(event):
            counter["value"] += 1
            
        def handler2(event):
            counter["value"] += 10
            
        # Subscribe multiple handlers
        self.event_bus.subscribe("multi.event", handler1)
        self.event_bus.subscribe("multi.event", handler2)
        
        # Publish event
        event = Event(name="multi.event", module="test", data={})
        await self.event_bus.publish(event)
        
        await asyncio.sleep(0.1)
        
        # Both handlers should have run
        assert counter["value"] == 11
        
    @pytest.mark.asyncio
    async def test_unsubscribe(self):
        """Test unsubscribe functionality"""
        # Subscribe and then unsubscribe
        self.event_bus.subscribe("unsub.event", self.sync_handler)
        self.event_bus.unsubscribe("unsub.event", self.sync_handler)
        
        # Publish event
        event = Event(name="unsub.event", module="test", data={})
        await self.event_bus.publish(event)
        
        await asyncio.sleep(0.1)
        
        # No events should be received
        assert len(self.received_events) == 0
        
    @pytest.mark.asyncio
    async def test_event_history(self):
        """Test event history functionality"""
        # Publish several events
        for i in range(5):
            event = Event(
                name=f"history.event.{i}",
                module="test",
                data={"index": i}
            )
            await self.event_bus.publish(event)
            
        # Check history
        history = self.event_bus.get_history()
        assert len(history) == 5
        
        # Check filtered history
        event = Event(name="history.event.2", module="test", data={})
        await self.event_bus.publish(event)
        
        filtered = self.event_bus.get_history("history.event.2")
        assert len(filtered) == 2
        
    @pytest.mark.asyncio
    async def test_event_priority(self):
        """Test event priority handling"""
        # High priority event should be processed immediately
        event = Event(
            name="priority.event",
            module="test",
            data={},
            priority=EventPriority.HIGH
        )
        
        self.event_bus.subscribe("priority.event", self.sync_handler)
        await self.event_bus.publish(event)
        
        # Should be processed immediately
        await asyncio.sleep(0.01)
        assert len(self.received_events) == 1
        
    def test_global_event_bus(self):
        """Test global event bus singleton"""
        bus1 = get_event_bus()
        bus2 = get_event_bus()
        assert bus1 is bus2
        
        reset_event_bus()
        bus3 = get_event_bus()
        assert bus3 is not bus1
        
    def test_subscriber_count(self):
        """Test getting subscriber counts"""
        self.event_bus.subscribe("count.event", self.sync_handler)
        self.event_bus.subscribe("count.event", self.async_handler)
        self.event_bus.subscribe("other.event", self.sync_handler)
        
        counts = self.event_bus.get_subscribers_count()
        assert counts["count.event"] == 2
        assert counts["other.event"] == 1