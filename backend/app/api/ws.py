import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self):
        # execution_id -> list of websocket connections
        self.execution_connections: dict[str, list[WebSocket]] = {}
        # dashboard-level connections
        self.dashboard_connections: list[WebSocket] = []

    async def connect_execution(self, websocket: WebSocket, execution_id: str):
        await websocket.accept()
        if execution_id not in self.execution_connections:
            self.execution_connections[execution_id] = []
        self.execution_connections[execution_id].append(websocket)

    async def disconnect_execution(self, websocket: WebSocket, execution_id: str):
        if execution_id in self.execution_connections:
            if websocket in self.execution_connections[execution_id]:
                self.execution_connections[execution_id].remove(websocket)
            if not self.execution_connections[execution_id]:
                del self.execution_connections[execution_id]

    async def connect_dashboard(self, websocket: WebSocket):
        await websocket.accept()
        self.dashboard_connections.append(websocket)

    async def disconnect_dashboard(self, websocket: WebSocket):
        if websocket in self.dashboard_connections:
            self.dashboard_connections.remove(websocket)

    async def broadcast_to_execution(self, execution_id: str, message: dict):
        """Send a message to all clients watching a specific execution."""
        connections = self.execution_connections.get(execution_id, [])
        disconnected = []
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)

        for conn in disconnected:
            await self.disconnect_execution(conn, execution_id)

    async def broadcast_to_dashboard(self, message: dict):
        """Send a message to all dashboard clients."""
        disconnected = []
        for connection in self.dashboard_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)

        for conn in disconnected:
            await self.disconnect_dashboard(conn)

    async def broadcast(self, message: dict):
        """Broadcast to all dashboard connections and all execution connections."""
        await self.broadcast_to_dashboard(message)
        for execution_id in list(self.execution_connections.keys()):
            await self.broadcast_to_execution(execution_id, message)


def _get_manager(websocket: WebSocket) -> ConnectionManager:
    """Retrieve the ConnectionManager from app.state, with fallback."""
    return websocket.app.state.ws_manager


@router.websocket("/ws/executions/{execution_id}")
async def execution_websocket(websocket: WebSocket, execution_id: str):
    manager = _get_manager(websocket)
    await manager.connect_execution(websocket, execution_id)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                # Echo back with type confirmation for client-side handling
                await websocket.send_json({
                    "type": "ack",
                    "data": message,
                })
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON",
                })
    except WebSocketDisconnect:
        await manager.disconnect_execution(websocket, execution_id)


@router.websocket("/ws/dashboard")
async def dashboard_websocket(websocket: WebSocket):
    manager = _get_manager(websocket)
    await manager.connect_dashboard(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                await websocket.send_json({
                    "type": "ack",
                    "data": message,
                })
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON",
                })
    except WebSocketDisconnect:
        await manager.disconnect_dashboard(websocket)
