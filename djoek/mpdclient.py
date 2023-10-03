import asyncio
import logging
import re
from functools import partial
from types import TracebackType
from typing import Literal, Match, Optional, Self, Type

from multidict import MultiDict

logger = logging.getLogger(__name__)

MPD_COMMAND_TIMEOUT = 10

SERVER_RESPONSE = re.compile(r"(OK|ACK \[(\d+)@(\d+)\] {(.*?)} (.+))")


class MPDCommandError(Exception):
    def __init__(
        self, error: int, command: int, current_command: str, description: str
    ) -> None:
        self.error = error
        self.command = command
        self.current_command = current_command
        self.description = description

    def __str__(self) -> str:
        return self.description


class MPDClient:
    task: Optional[asyncio.Task[None]]

    def __init__(self, host: str = "localhost", port: int = 6600) -> None:
        self.host = host
        self.port = port
        self.task = None
        self.command_queue: asyncio.Queue[
            tuple[str, asyncio.Future[MultiDict[str | bytes]]]
        ] = asyncio.Queue()
        self.command_event = asyncio.Event()

    def start(self) -> None:
        if self.task is not None:
            raise RuntimeError(f"{self} has already started")

        loop = asyncio.get_event_loop()
        self.task = loop.create_task(self._run())
        self.task.add_done_callback(partial(run_done_callback, self))

    async def _run(self) -> None:
        reader: Optional[asyncio.StreamReader] = None
        writer: Optional[asyncio.StreamWriter] = None

        async def reset_connection(
            message: str = "Lost connection to mpd, reconnecting.",
        ) -> None:
            nonlocal reader
            nonlocal writer
            if writer is not None:
                writer.close()
                await writer.wait_closed()
            reader, writer = None, None
            logger.warning(message)

        try:
            while True:
                command, f = await self.command_queue.get()
                command_raw = f"{command}\n".encode("utf-8")
                self.command_event.clear()

                while True:
                    if reader is None or writer is None:
                        reader, writer = await self._connect()

                    logger.debug("> %s", command)
                    writer.write(command_raw)
                    await writer.drain()

                    is_idle_command = command.startswith("idle ")
                    response: MultiDict[str | bytes] = MultiDict()
                    match: Optional[Match[str]] = None

                    while True:
                        if is_idle_command:
                            t_event = asyncio.create_task(self.command_event.wait())
                            t_readline = asyncio.create_task(reader.readline())
                            tasks: set[
                                asyncio.Task[Literal[True]] | asyncio.Task[bytes]
                            ] = {
                                t_event,
                                t_readline,
                            }
                            done, pending = await asyncio.wait(
                                tasks,
                                return_when=asyncio.FIRST_COMPLETED,
                            )

                            if t_event in pending:
                                t_event.cancel()

                            if t_readline not in done:
                                logger.debug("> noidle")
                                writer.write(b"noidle\n")
                                await writer.drain()

                            line_raw = await t_readline
                        else:
                            try:
                                line_raw = await asyncio.wait_for(
                                    reader.readline(), MPD_COMMAND_TIMEOUT
                                )
                            except asyncio.TimeoutError:
                                await reset_connection(
                                    "mpd did not respond in time, reconnecting."
                                )
                                break

                        if not line_raw:
                            await reset_connection()
                            break

                        line = line_raw.decode("utf-8").rstrip("\n")
                        logger.debug("< %s", line)

                        match = SERVER_RESPONSE.fullmatch(line)
                        if match:
                            break

                        key, value = line.split(": ", 1)
                        if key == "binary":
                            data_length = int(value)
                            if data_length > 0:
                                data = await reader.read(data_length)
                                if not data:
                                    await reset_connection()
                                    break
                            else:
                                data = b""
                            response.add(key, data)
                        else:
                            response.add(key, value)

                    if match is None:
                        continue

                    if match.group(1) == "OK":
                        f.set_result(response)
                    else:
                        f.set_exception(
                            MPDCommandError(
                                int(match.group(2)),
                                int(match.group(3)),
                                match.group(4),
                                match.group(5),
                            )
                        )
                    break
        finally:
            if writer is not None:
                writer.close()
                await writer.wait_closed()

    async def _connect(self) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        """
        Do not call this yourself. Use `.start()` instead.
        """
        timeout = 0
        while True:
            if timeout:
                await asyncio.sleep(timeout)
            timeout = max(1, min(timeout * 2, 60))

            logger.debug("Connecting to %s:%s", self.host, self.port)
            try:
                reader, writer = await asyncio.open_connection(self.host, self.port)
            except Exception:
                logger.exception(
                    "Connection to %s:%s failed. Retrying in %ss.",
                    self.host,
                    self.port,
                    timeout,
                )
                continue

            server_hello = await asyncio.wait_for(
                reader.readline(), MPD_COMMAND_TIMEOUT
            )
            if not server_hello.startswith(b"OK "):
                logger.warning(
                    "Received invalid server hello from %s:%s. Retrying in %ss.",
                    self.host,
                    self.port,
                    timeout,
                )
                continue

            return reader, writer

    async def execute(self, command: str) -> MultiDict[str | bytes]:
        loop = asyncio.get_event_loop()
        f: asyncio.Future[MultiDict[str | bytes]] = loop.create_future()
        await self.command_queue.put((command, f))
        self.command_event.set()
        return await f

    async def __aenter__(self) -> Self:
        self.start()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        if self.task is not None and not self.task.done():
            self.task.cancel()


def run_done_callback(client: MPDClient, f: asyncio.Future[None]) -> None:
    client.task = None
    try:
        f.result()
    except asyncio.CancelledError:
        pass
    except Exception:
        logger.exception("MPDClient encountered an exception")
