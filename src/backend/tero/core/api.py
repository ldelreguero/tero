
import asyncio
from typing import AsyncIterator

from sse_starlette.event import ServerSentEvent


BASE_PATH = "/api"
MCP_PATH = "/mcp"


import contextlib
from typing import AsyncIterator, Any

async def with_heartbeat(stream: AsyncIterator[bytes]) -> AsyncIterator[bytes]:
    """
    Wraps an async generator to inject periodic heartbeat messages.
    
    This ensures the SSE connection stays alive even during long pauses
    between events, preventing nginx/proxy timeouts and detecting client
    disconnections early.
    """
    async with BackgroundIterator(stream) as iterator:
        loop = asyncio.get_event_loop()
        last_heartbeat = loop.time()
        heartbeat_interval = 15
        
        while True:
            delta = loop.time() - last_heartbeat
            timeout = max(0, heartbeat_interval - delta)
            
            try:
                yield await iterator.next(timeout=timeout)
            except asyncio.TimeoutError:
                yield ServerSentEvent(event="heartbeat").encode()
                last_heartbeat = loop.time()
            except StopAsyncIteration:
                break


class BackgroundIterator:
    """
    Iterates over an async stream in a background task and buffers items in a queue.
    This ensures that the stream iteration happens consistently in the same task context,
    regardless of how the consumer operates (e.g. valid for anyio task affinity).

    This solution was required to keep working with tools like playwright due to creating 
    a task for each iteration generated "RuntimeError: Attempted to exit cancel scope in a 
    different task than it was entered in" 
    """
    def __init__(self, stream: AsyncIterator):
        self._stream = stream
        self._queue = asyncio.Queue()
        self._task = None
        self._STOP = object()

    async def __aenter__(self):
        self._task = asyncio.create_task(self._producer())
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._task and not self._task.done():
            self._task.cancel()
            # Awaiting the cancelled task re-raises the CancelledError,
            # so we must suppress it to prevent it from propagating.
            with contextlib.suppress(asyncio.CancelledError):
                await self._task

    async def next(self, timeout: float) -> Any:
        item = await asyncio.wait_for(self._queue.get(), timeout=timeout)
        if item is self._STOP:
            raise StopAsyncIteration
        elif isinstance(item, Exception):
            raise item
        else:
            return item

    async def _producer(self):
        try:
            async for item in self._stream:
                await self._queue.put(item)
            await self._queue.put(self._STOP)
        except Exception as e:
            await self._queue.put(e)

