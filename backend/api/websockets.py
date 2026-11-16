"""
WebSocket Connection Manager:
Maintains active real-time connections to the frontend dashboard and broadcasts state events.
"""

import json
import logging
from typing import List
from fastapi import WebSocket, WebSocketDisconnect
from ..models.state import WebSocketEvent

logger = logging.getLogger("medflow.websockets")


class ConnectionManager:
    """
    Thread-safe connection pool for streaming real-time hospital events.
    """
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Dashboard client connected. Active clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"Dashboard client disconnected. Active clients: {len(self.active_connections)}")

    async def broadcast(self, event: WebSocketEvent):
        """
        Sends event to all connected dashboard instances.
        """
        message_json = event.model_dump_json()
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.warning(f"Failed to send to client ({e}). Marking for disconnection.")
                disconnected.append(connection)
                
        for dead_conn in disconnected:
            self.disconnect(dead_conn)


ws_manager = ConnectionManager()
