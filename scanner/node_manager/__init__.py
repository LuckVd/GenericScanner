"""Node Manager - Manages scanner node lifecycle and coroutine pool."""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Callable

import aio_pika
import psutil

from common.utils.config import get_settings
from common.utils.database import get_db_context
from scanner.coroutine_pool import CoroutinePool

logger = logging.getLogger(__name__)
settings = get_settings()


class NodeManager:
    """Manages scanner node lifecycle."""

    def __init__(self, node_id: str | None = None) -> None:
        self.node_id = node_id or f"node-{uuid.uuid4().hex[:8]}"
        self._running = False
        self._pool: CoroutinePool | None = None
        self._heartbeat_task: asyncio.Task | None = None
        self._connection: aio_pika.Connection | None = None
        self._channel: aio_pika.Channel | None = None
        self._task_queue: aio_pika.Queue | None = None
        self._task_handlers: dict[str, Callable] = {}

    @property
    def is_running(self) -> bool:
        """Check if node is running."""
        return self._running

    @property
    def cpu_load(self) -> float:
        """Get CPU load (0-1)."""
        return psutil.cpu_percent() / 100

    @property
    def memory_load(self) -> float:
        """Get memory load (0-1)."""
        return psutil.virtual_memory().percent / 100

    @property
    def active_tasks(self) -> int:
        """Get number of active tasks."""
        return self._pool.active_count if self._pool else 0

    def register_handler(self, task_type: str, handler: Callable) -> None:
        """Register a task handler."""
        self._task_handlers[task_type] = handler
        logger.info(f"Registered handler for task type: {task_type}")

    async def start(self, max_concurrency: int | None = None) -> None:
        """Start the scanner node."""
        if self._running:
            logger.warning("Node is already running")
            return

        concurrency = max_concurrency or settings.scanner_max_concurrency

        # Initialize coroutine pool
        self._pool = CoroutinePool(max_size=concurrency)

        # Connect to RabbitMQ
        try:
            await self._connect_mq()
            logger.info("Connected to RabbitMQ")
        except Exception as e:
            logger.warning(f"Failed to connect to RabbitMQ: {e}")

        # Register node in database
        await self._register_node()

        # Start heartbeat
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

        self._running = True
        logger.info(f"Scanner node {self.node_id} started with max_concurrency={concurrency}")

    async def stop(self) -> None:
        """Stop the scanner node."""
        if not self._running:
            return

        self._running = False

        # Stop heartbeat
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass

        # Stop coroutine pool
        if self._pool:
            await self._pool.stop()

        # Disconnect from RabbitMQ
        if self._connection:
            await self._connection.close()

        # Update node status
        await self._update_node_status("offline")

        logger.info(f"Scanner node {self.node_id} stopped")

    async def run(self) -> None:
        """Run the scanner node (blocks until stopped)."""
        await self.start()

        try:
            # Start consuming tasks
            if self._task_queue:
                async with self._task_queue.iterator() as queue_iter:
                    async for message in queue_iter:
                        if not self._running:
                            break
                        async with message.process():
                            await self._handle_task(message.body)
            else:
                # No MQ, just wait
                while self._running:
                    await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        finally:
            await self.stop()

    async def _connect_mq(self) -> None:
        """Connect to RabbitMQ."""
        self._connection = await aio_pika.connect_robust(settings.rabbitmq_url)
        self._channel = await self._connection.channel()

        # Declare and bind to task queue
        self._task_queue = await self._channel.declare_queue(
            settings.rabbitmq_task_queue,
            durable=True,
        )

    async def _handle_task(self, body: bytes) -> None:
        """Handle incoming task message."""
        import json

        try:
            task_data = json.loads(body)
            task_type = task_data.get("type", "scan")

            handler = self._task_handlers.get(task_type)
            if handler:
                if self._pool:
                    await self._pool.submit(handler, task_data)
                else:
                    await handler(task_data)
            else:
                logger.warning(f"No handler for task type: {task_type}")

        except Exception as e:
            logger.error(f"Failed to handle task: {e}")

    async def _register_node(self) -> None:
        """Register node in database."""
        from common.models.node import ScanNode

        async with get_db_context() as db:
            result = await db.execute(
                ScanNode.__table__.select().where(ScanNode.id == self.node_id)
            )
            existing = result.first()

            if existing:
                # Update existing
                await db.execute(
                    ScanNode.__table__.update()
                    .where(ScanNode.id == self.node_id)
                    .values(status="online", last_heartbeat=datetime.utcnow())
                )
            else:
                # Create new
                node = ScanNode(
                    id=self.node_id,
                    status="online",
                    cpu_load=self.cpu_load,
                    memory_load=self.memory_load,
                    tasks_running=0,
                    max_tasks=settings.scanner_max_concurrency,
                    last_heartbeat=datetime.utcnow(),
                )
                db.add(node)

            await db.flush()
            logger.info(f"Node {self.node_id} registered")

    async def _update_node_status(self, status: str) -> None:
        """Update node status in database."""
        from common.models.node import ScanNode

        async with get_db_context() as db:
            await db.execute(
                ScanNode.__table__.update()
                .where(ScanNode.id == self.node_id)
                .values(
                    status=status,
                    cpu_load=self.cpu_load,
                    memory_load=self.memory_load,
                    tasks_running=self.active_tasks,
                    last_heartbeat=datetime.utcnow(),
                )
            )
            await db.flush()

    async def _heartbeat_loop(self) -> None:
        """Send periodic heartbeats."""
        while self._running:
            try:
                await self._update_node_status("online" if self._running else "offline")
                logger.debug(f"Heartbeat sent: cpu={self.cpu_load:.2f}, mem={self.memory_load:.2f}")
            except Exception as e:
                logger.error(f"Heartbeat failed: {e}")

            await asyncio.sleep(settings.scanner_heartbeat_interval)


# Global node manager instance
node_manager = NodeManager()
