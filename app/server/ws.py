"""WebSocket bridge for connecting agent loop to WebSocket clients."""

import asyncio
import json
import uuid
from typing import Dict, Any, Optional, Callable
from fastapi import WebSocket, WebSocketDisconnect


class WebSocketBridge:
    def __init__(self, websocket: WebSocket):
        self._ws = websocket
        self._pending_permissions: Dict[str, asyncio.Event] = {}
        self._permission_results: Dict[str, bool] = {}

    async def send_event(self, event_type: str, data: Any) -> None:
        try:
            print(f"Sending event: {event_type} with data: {data}")
            await self._ws.send_json({"type": event_type, "data": data})
            print(f"Sent event successfully: {event_type}")
        except Exception as e:
            print(f"Error sending event {event_type}: {type(e).__name__}: {e}")
            raise

    async def on_event(self, event_type: str, data: Any) -> None:
        await self.send_event(event_type, data)

    async def ask_permission(
        self,
        tool_name: str,
        reason: str,
        tool_input: Optional[Dict] = None,
    ) -> bool:
        request_id = uuid.uuid4().hex[:8]
        event = asyncio.Event()
        self._pending_permissions[request_id] = event

        await self.send_event(
            "permission_required",
            {
                "request_id": request_id,
                "tool_name": tool_name,
                "reason": reason,
                "tool_input": tool_input or {},
            },
        )

        try:
            await asyncio.wait_for(event.wait(), timeout=120.0)
        except asyncio.TimeoutError:
            return False

        return self._permission_results.pop(request_id, False)

    def resolve_permission(self, request_id: str, approved: bool) -> None:
        self._permission_results[request_id] = approved
        if request_id in self._pending_permissions:
            self._pending_permissions[request_id].set()

    async def receive_messages(self, handler: Callable[[str, Any], Any]) -> None:
        try:
            while True:
                try:
                    data = await self._ws.receive_json()
                    print(f"Received raw data: {data}")
                except json.JSONDecodeError as e:
                    print(f"Failed to decode JSON: {e}")
                    continue
                except Exception as e:
                    print(f"Error receiving message: {type(e).__name__}: {e}")
                    break

                msg_type = data.get("type")
                msg_data = data.get("data", {})
                if msg_type:
                    try:
                        result = handler(msg_type, msg_data)
                        if asyncio.iscoroutine(result):
                            await result
                    except Exception as e:
                        print(f"Error handling message {msg_type}: {type(e).__name__}: {e}")
                else:
                    print(f"Message without type: {data}")
        except WebSocketDisconnect:
            print("WebSocket disconnected normally")
        except Exception as e:
            print(f"Unexpected error in receive_messages: {type(e).__name__}: {e}")
