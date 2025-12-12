import threading
from collections import deque
from typing import Optional
from .models import Task


class InMemoryQueue:
    def __init__(self):
        self._q = deque()
        self._lock = threading.Lock()

    def put(self, t: Task):
        with self._lock:
            self._q.append(t)

    def get(self) -> Optional[Task]:
        with self._lock:
            if self._q:
                return self._q.popleft()
            return None

    def size(self) -> int:
        with self._lock:
            return len(self._q)

