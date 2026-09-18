from collections import OrderedDict, deque
from time import monotonic

from app.core.errors import AppError


class RateLimiter:
    """Bounded per-process limiter. Run one worker or enforce shared limits at your proxy."""

    def __init__(self) -> None:
        self.buckets: OrderedDict[str, deque[float]] = OrderedDict()

    def check(self, key: str, limit: int, seconds: int = 60) -> None:
        now = monotonic()
        bucket = self.buckets.setdefault(key, deque())
        self.buckets.move_to_end(key)
        while bucket and bucket[0] <= now - seconds:
            bucket.popleft()
        if len(bucket) >= limit:
            raise AppError("Too many attempts. Please wait a minute and try again.", 429)
        bucket.append(now)
        if len(self.buckets) > 5000:
            self.buckets.popitem(last=False)


limiter = RateLimiter()
