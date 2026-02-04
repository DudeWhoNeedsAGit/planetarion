"""
In-memory Event Bus (MVP)

Used for event-driven UI updates (Server-Sent Events).

Design goals:
- Simple, low-dependency, good enough for local dev / small deployments.
- Per-user subscriptions (streams) that receive JSON-serializable payloads.
- Thread-safe for: Flask request threads + APScheduler tick thread.

Non-goals:
- Durable queues / guaranteed delivery across server restarts.
- Fan-out across multiple app instances (needs Redis/pubsub later).
"""

from __future__ import annotations

from dataclasses import dataclass
from queue import Queue
from threading import Lock
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class EventMessage:
    event: str
    data: Dict[str, Any]
    id: Optional[int] = None


class UserEventBus:
    def __init__(self) -> None:
        self._lock = Lock()
        self._subscribers: Dict[int, set[Queue[EventMessage]]] = {}

    def subscribe(self, user_id: int) -> Queue[EventMessage]:
        q: Queue[EventMessage] = Queue()
        with self._lock:
            self._subscribers.setdefault(int(user_id), set()).add(q)
        return q

    def unsubscribe(self, user_id: int, q: Queue[EventMessage]) -> None:
        with self._lock:
            subs = self._subscribers.get(int(user_id))
            if not subs:
                return
            subs.discard(q)
            if not subs:
                self._subscribers.pop(int(user_id), None)

    def publish(self, user_id: int, message: EventMessage) -> None:
        with self._lock:
            subs = list(self._subscribers.get(int(user_id), set()))
        for q in subs:
            try:
                q.put_nowait(message)
            except Exception:
                # Drop if subscriber is wedged.
                pass


event_bus = UserEventBus()

