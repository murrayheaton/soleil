"""
Core Module - Shared Infrastructure

This module provides shared infrastructure for all SOLEil modules:
- Event bus for inter-module communication
- API gateway for module registration
- Shared middleware and utilities
- Configuration management
"""

from .event_bus import EventBus, Event, EventPriority, get_event_bus
from .api_gateway import APIGateway, get_api_gateway
from . import events

__all__ = [
    'EventBus',
    'Event', 
    'EventPriority',
    'get_event_bus',
    'APIGateway',
    'get_api_gateway',
    'events'
]