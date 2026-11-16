"""
Dependency injection and global coordinator singleton.
"""

import asyncio
from typing import Optional
from ..agents.coordinator import HospitalCoordinator
from ..models.state import WebSocketEvent
from .websockets import ws_manager


def _async_event_emitter(event: WebSocketEvent):
    """Bridges synchronous coordinator events into the asynchronous WebSocket manager."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(ws_manager.broadcast(event))
        else:
            asyncio.run(ws_manager.broadcast(event))
    except Exception:
        pass


# Global Singleton Coordinator
global_coordinator = HospitalCoordinator(event_callback=_async_event_emitter)


def get_coordinator() -> HospitalCoordinator:
    return global_coordinator
