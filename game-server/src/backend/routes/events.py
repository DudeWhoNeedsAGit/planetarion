from __future__ import annotations

import json
import time
from datetime import datetime
from queue import Empty

from flask import Blueprint, Response, request
from flask_jwt_extended import decode_token

from backend.services.event_bus import EventMessage, event_bus


events_bp = Blueprint("events", __name__, url_prefix="/api/events")


def _sse(event: str, data: dict, *, event_id: int | None = None) -> str:
    payload = []
    if event_id is not None:
        payload.append(f"id: {int(event_id)}")
    payload.append(f"event: {event}")
    payload.append(f"data: {json.dumps(data, separators=(',', ':'))}")
    payload.append("")  # blank line terminates the SSE message
    return "\n".join(payload) + "\n"


def _get_user_id_from_query_token() -> int | None:
    raw = (request.args.get("token") or request.args.get("access_token") or "").strip()
    if not raw:
        return None
    try:
        decoded = decode_token(raw)
        sub = decoded.get("sub")
        return int(sub) if sub is not None else None
    except Exception:
        return None


@events_bp.route("/stream", methods=["GET"])
def stream_events():
    """
    Server-Sent Events stream.

    Note: EventSource cannot send Authorization headers. For this MVP we accept the JWT
    as a query param: /api/events/stream?token=...
    """
    user_id = _get_user_id_from_query_token()
    if not user_id:
        return Response("Unauthorized", status=401)

    q = event_bus.subscribe(user_id)

    def gen():
        # Initial hello (lets the client know the stream is alive).
        yield _sse("hello", {"ts": datetime.utcnow().isoformat() + "Z"})
        heartbeat_seconds = 15
        last_ping = time.time()

        try:
            while True:
                timeout = max(1, heartbeat_seconds - int(time.time() - last_ping))
                try:
                    msg: EventMessage = q.get(timeout=timeout)
                    yield _sse(msg.event, msg.data, event_id=msg.id)
                except Empty:
                    # heartbeat comment to keep connection open
                    last_ping = time.time()
                    yield ": ping\n\n"
        finally:
            event_bus.unsubscribe(user_id, q)

    headers = {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        # If behind nginx, prevent response buffering.
        "X-Accel-Buffering": "no",
    }
    return Response(gen(), headers=headers)

