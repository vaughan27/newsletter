import threading
import time
from collections import defaultdict

from fastapi import HTTPException, status


class LoginThrottle:
    """Small in-memory brute-force guard: N failures per key within a window.

    Per-process only. If you run several workers, put the same idea in Redis or
    behind your reverse proxy.
    """

    def __init__(self, max_failures: int = 5, window_seconds: int = 15 * 60) -> None:
        self.max_failures = max_failures
        self.window = window_seconds
        self._failures: dict[str, list[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def _recent(self, key: str) -> list[float]:
        cutoff = time.monotonic() - self.window
        recent = [t for t in self._failures[key] if t > cutoff]
        if recent:
            self._failures[key] = recent
        else:
            self._failures.pop(key, None)
        return recent

    def check(self, key: str) -> None:
        with self._lock:
            if len(self._recent(key)) >= self.max_failures:
                raise HTTPException(
                    status.HTTP_429_TOO_MANY_REQUESTS,
                    "Too many failed attempts. Try again in a few minutes.",
                )

    def fail(self, key: str) -> None:
        with self._lock:
            self._recent(key)
            self._failures[key].append(time.monotonic())

    def reset(self, key: str) -> None:
        with self._lock:
            self._failures.pop(key, None)


login_throttle = LoginThrottle()
