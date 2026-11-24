import time
from collections import defaultdict, deque
from threading import Lock


class BoundedRateLimiter:
    def __init__(self, limit: int, window_seconds: int) -> None:
        self._limit = limit
        self._window_seconds = window_seconds
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, key: str, now: float | None = None) -> bool:
        timestamp = time.monotonic() if now is None else now
        cutoff = timestamp - self._window_seconds
        with self._lock:
            queue = self._requests[key]
            while queue and queue[0] <= cutoff:
                queue.popleft()
            if len(queue) >= self._limit:
                return False
            queue.append(timestamp)
            return True

