"""Dispatcher - Task scheduling and distribution via RabbitMQ."""

import asyncio
import json
import logging
from typing import Optional

import aio_pika
from aio_pika import ExchangeType, Message

from common.models.task import TaskStatus
from common.utils.config import get_settings
from scheduler.task_manager import task_manager

logger = logging.getLogger(__name__)
settings = get_settings()


class Dispatcher:
    """Task dispatcher using RabbitMQ."""

    def __init__(self) -> None:
        self._connection: aio_pika.Connection | None = None
        self._channel: aio_pika.Channel | None = None
        self._exchange: aio_pika.Exchange | None = None
        self._task_queue: aio_pika.Queue | None = None
        self._result_queue: aio_pika.Queue | None = None
        self._running = False

    async def connect(self) -> None:
        """Connect to RabbitMQ."""
        try:
            self._connection = await aio_pika.connect_robust(settings.rabbitmq_url)
            self._channel = await self._connection.channel()

            # Declare exchange
            self._exchange = await self._channel.declare_exchange(
                settings.rabbitmq_exchange,
                ExchangeType.DIRECT,
                durable=True,
            )

            # Declare task queue
            self._task_queue = await self._channel.declare_queue(
                settings.rabbitmq_task_queue,
                durable=True,
            )
            await self._task_queue.bind(self._exchange, routing_key="task")

            # Declare result queue
            self._result_queue = await self._channel.declare_queue(
                settings.rabbitmq_result_queue,
                durable=True,
            )
            await self._result_queue.bind(self._exchange, routing_key="result")

            logger.info("Connected to RabbitMQ")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from RabbitMQ."""
        self._running = False
        if self._connection:
            await self._connection.close()
            logger.info("Disconnected from RabbitMQ")

    async def dispatch_task(self, task_id: str, targets: list[str]) -> None:
        """Dispatch task to scan nodes."""
        if not self._exchange:
            await self.connect()

        # Split targets into chunks
        chunks = task_manager.split_targets(targets)

        for i, chunk in enumerate(chunks):
            message = {
                "task_id": task_id,
                "chunk_id": i,
                "targets": chunk,
                "total_chunks": len(chunks),
            }

            await self._exchange.publish(
                Message(
                    body=json.dumps(message).encode(),
                    content_type="application/json",
                    correlation_id=task_id,
                ),
                routing_key="task",
            )

        # Mark task as running
        await task_manager.mark_running(task_id)
        logger.info(f"Dispatched task {task_id} with {len(chunks)} chunks")

    async def start_result_consumer(self) -> None:
        """Start consuming results from scan nodes."""
        if not self._result_queue:
            await self.connect()

        self._running = True

        async with self._result_queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    await self._handle_result(message.body)

    async def _handle_result(self, body: bytes) -> None:
        """Handle result message from scan node."""
        try:
            result = json.loads(body)
            task_id = result.get("task_id")
            status = result.get("status")
            completed = result.get("completed", 0)

            if status == "progress":
                await task_manager.update_progress(task_id, completed)
            elif status == "completed":
                await task_manager.mark_completed(task_id)
            elif status == "failed":
                error = result.get("error", "Unknown error")
                await task_manager.mark_failed(task_id, error)

            logger.debug(f"Handled result for task {task_id}: {status}")
        except Exception as e:
            logger.error(f"Failed to handle result: {e}")

    async def schedule_pending_tasks(self) -> None:
        """Schedule all pending tasks."""
        tasks, _ = await task_manager.list_tasks(status=TaskStatus.PENDING.value)

        for task in tasks:
            try:
                await self.dispatch_task(task.id, task.targets)
            except Exception as e:
                logger.error(f"Failed to dispatch task {task.id}: {e}")
                await task_manager.mark_failed(task.id, str(e))


# Global dispatcher instance
dispatcher = Dispatcher()
