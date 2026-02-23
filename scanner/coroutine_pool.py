"""Coroutine Pool - Dynamic async task pool."""

import asyncio
import logging
from collections.abc import Callable, Coroutine
from typing import Any

logger = logging.getLogger(__name__)


class CoroutinePool:
    """Async coroutine pool with dynamic sizing."""

    def __init__(self, max_size: int = 100) -> None:
        self._max_size = max_size
        self._semaphore = asyncio.Semaphore(max_size)
        self._tasks: set[asyncio.Task] = set()
        self._active_count = 0
        self._stopped = False

    @property
    def max_size(self) -> int:
        """Get max pool size."""
        return self._max_size

    @property
    def active_count(self) -> int:
        """Get number of active coroutines."""
        return self._active_count

    @property
    def available_slots(self) -> int:
        """Get number of available slots."""
        return self._max_size - self._active_count

    def resize(self, new_size: int) -> None:
        """Resize the pool (affects new tasks only)."""
        self._max_size = new_size
        self._semaphore = asyncio.Semaphore(new_size)
        logger.info(f"Pool resized to {new_size}")

    async def submit(
        self,
        func: Callable[..., Coroutine[Any, Any, Any]],
        *args: Any,
        **kwargs: Any,
    ) -> asyncio.Task:
        """Submit a coroutine to the pool."""
        if self._stopped:
            raise RuntimeError("Pool is stopped")

        await self._semaphore.acquire()
        self._active_count += 1

        async def wrapped() -> Any:
            try:
                return await func(*args, **kwargs)
            finally:
                self._active_count -= 1
                self._semaphore.release()

        task = asyncio.create_task(wrapped())
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

        return task

    async def submit_many(
        self,
        funcs: list[Callable[..., Coroutine[Any, Any, Any]]],
        *args: Any,
        **kwargs: Any,
    ) -> list[asyncio.Task]:
        """Submit multiple coroutines to the pool."""
        tasks = []
        for func in funcs:
            task = await self.submit(func, *args, **kwargs)
            tasks.append(task)
        return tasks

    async def wait_all(self) -> list[Any]:
        """Wait for all tasks to complete and return results."""
        results = await asyncio.gather(*self._tasks, return_exceptions=True)
        return results

    async def stop(self, timeout: float = 30.0) -> None:
        """Stop the pool and cancel all pending tasks."""
        self._stopped = True

        if self._tasks:
            # Wait for tasks with timeout
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self._tasks, return_exceptions=True),
                    timeout=timeout,
                )
            except TimeoutError:
                # Cancel remaining tasks
                for task in self._tasks:
                    task.cancel()
                await asyncio.gather(*self._tasks, return_exceptions=True)

        logger.info("Pool stopped")

    async def __aenter__(self) -> "CoroutinePool":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.stop()
