import asyncio
from collections import deque


class Throttler:
    """Siple throttler for asyncio"""

    def __init__(self, req_per_sec, loop=None):
        self.rate_limit = req_per_sec
        self.loop = loop or asyncio.get_event_loop()

        self._task_logs = deque()

    async def __aenter__(self):
        while True:
            now = self.loop.time()

            # Pop items(which are start times) that are no longer in the
            # time window
            while self._task_logs:
                if now - self._task_logs[0] > 1.0:
                    self._task_logs.popleft()
                else:
                    break

            # Exit the infinite loop when new task can be processed
            if len(self._task_logs) < self.rate_limit:
                break

            print("Sleeping for rate limit")
            await asyncio.sleep(1 / self.rate_limit)

        # Push new task's start time
        self._task_logs.append(self.loop.time())

        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass
