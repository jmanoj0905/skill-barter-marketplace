from collections import defaultdict
from fastapi import WebSocket
from typing import Dict, List


class WarningConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = defaultdict(list)

    async def connect(self, barter_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[barter_id].append(websocket)

    def disconnect(self, barter_id: int, websocket: WebSocket):
        if barter_id in self.active_connections:
            if websocket in self.active_connections[barter_id]:
                self.active_connections[barter_id].remove(websocket)

            if not self.active_connections[barter_id]:
                del self.active_connections[barter_id]

    async def broadcast(self, barter_id: int, message: dict):
        if barter_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[barter_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.append(connection)

            for connection in disconnected:
                self.disconnect(barter_id, connection)


manager = WarningConnectionManager()