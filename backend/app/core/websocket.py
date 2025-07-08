import json
import logging
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
from uuid import UUID


class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.session_subscribers: Dict[str, Set[str]] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logging.info(f"WebSocket client {client_id} connected")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        
        # Remove from all session subscriptions
        for session_id in list(self.session_subscribers.keys()):
            if client_id in self.session_subscribers[session_id]:
                self.session_subscribers[session_id].remove(client_id)
                if not self.session_subscribers[session_id]:
                    del self.session_subscribers[session_id]
        
        logging.info(f"WebSocket client {client_id} disconnected")

    async def subscribe_to_session(self, client_id: str, session_id: str):
        if session_id not in self.session_subscribers:
            self.session_subscribers[session_id] = set()
        self.session_subscribers[session_id].add(client_id)
        logging.info(f"Client {client_id} subscribed to session {session_id}")

    async def send_personal_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(json.dumps(message))
            except Exception as e:
                logging.error(f"Error sending message to {client_id}: {e}")
                self.disconnect(client_id)

    async def broadcast_to_session(self, session_id: str, message: dict):
        if session_id in self.session_subscribers:
            disconnected_clients = []
            
            for client_id in self.session_subscribers[session_id]:
                if client_id in self.active_connections:
                    try:
                        await self.active_connections[client_id].send_text(json.dumps(message))
                    except Exception as e:
                        logging.error(f"Error broadcasting to {client_id}: {e}")
                        disconnected_clients.append(client_id)
            
            # Clean up disconnected clients
            for client_id in disconnected_clients:
                self.disconnect(client_id)

    async def broadcast_analysis_status(
        self, 
        session_id: UUID, 
        status: str, 
        message: str, 
        data: dict = None
    ):
        from datetime import datetime, timezone
        
        message_data = {
            "type": "analysis_status",
            "session_id": str(session_id),
            "status": status,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data or {}
        }
        
        await self.broadcast_to_session(str(session_id), message_data)


websocket_manager = WebSocketManager()