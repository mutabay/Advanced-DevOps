import asyncio
import logging
from typing import Callable, Any, Awaitable


log = logging.getLogger(__name__)


class AsyncWorker:
    """Simple in-process async worker using an asyncio.Queue.

    submit(func, *args, **kwargs) enqueues an async callable.
    start() launches worker coroutines; stop() stops them gracefully.
    """

    def __init__(self, num_workers: int = 4):
        self.queue: asyncio.Queue = asyncio.Queue()
        self.num_workers = num_workers
        self._workers: list[asyncio.Task] = []
        self._running = False

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        log.info("Starting %d worker(s)", self.num_workers)
        for i in range(self.num_workers):
            t = asyncio.create_task(self._worker_loop(i))
            self._workers.append(t)

    async def stop(self) -> None:
        if not self._running:
            return
        self._running = False
        log.info("Stopping workers")
        # Send sentinel None to unblock workers
        for _ in range(self.num_workers):
            await self.queue.put(None)
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
        log.info("Workers stopped")

    def submit(self, func: Callable[..., Awaitable[Any]], *args, **kwargs) -> None:
        """Enqueue an async callable for execution by workers."""
        # Use put_nowait because the queue is in-process and bounded only by memory
        self.queue.put_nowait((func, args, kwargs))
        log.debug("Job submitted; queue size now %d", self.queue.qsize())

    async def _worker_loop(self, worker_index: int) -> None:
        log.info("Worker %d started loop", worker_index)
        while True:
            item = await self.queue.get()
            if item is None:
                log.info("Worker %d received shutdown sentinel", worker_index)
                break
            func, args, kwargs = item
            try:
                log.debug("Worker %d executing job %s", worker_index, getattr(func, '__name__', str(func)))
                await func(*args, **kwargs)
                log.debug("Worker %d finished job %s", worker_index, getattr(func, '__name__', str(func)))
            except Exception:
                # Keep worker alive on errors; in a real app log the exception
                log.exception("Worker %d encountered exception while running job", worker_index)

    def queue_size(self) -> int:
        return self.queue.qsize()

    def num_workers_active(self) -> int:
        # Best-effort: return configured worker count
        return self.num_workers

