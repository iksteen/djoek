import asyncio

from starlette.websockets import WebSocket


async def send_updates(ws_clients: list[WebSocket]) -> None:
    fs = [
        ws_client.send_json({"action": "EVENT", "event": "update"})
        for ws_client in ws_clients
    ]
    if fs:
        await asyncio.gather(*fs)
