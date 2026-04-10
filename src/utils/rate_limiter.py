import time
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """Simple rate limiter to control request frequency."""
    def __init__(self, requests_per_second=1):
        self.min_delay = 1.0 / max(0.001, requests_per_second)
        self.last_request_time = 0.0

    def wait(self):
        now = time.time()
        delta = now - self.last_request_time
        if delta < self.min_delay:
            time.sleep(self.min_delay - delta)
        self.last_request_time = time.time()
