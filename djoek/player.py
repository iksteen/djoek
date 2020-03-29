import asyncio
import json
import logging
import os
import random
from base64 import urlsafe_b64decode
from typing import List, Optional, cast

import aiofiles
from fastapi import FastAPI
from peewee import JOIN
from peewee_async import Manager
from starlette.requests import Request
from starlette.websockets import WebSocket

from djoek import settings
from djoek.models import Song, User
from djoek.mpdclient import MPDClient, MPDCommandError

logger = logging.getLogger(__name__)


async def setup_player(app: FastAPI) -> None:
    loop = asyncio.get_event_loop()
    app.state.player = player = Player(app.state.manager, app.state.ws_clients)
    app.state.player_task = loop.create_task(player.run())


async def shutdown_player(app: FastAPI) -> None:
    app.state.player_task.cancel()


async def get_player(request: Request) -> "Player":
    return cast(Player, request.app.state.player)


class Player:
    mpd_client: MPDClient
    queue: List[Song]
    current_song_id: Optional[int]
    current_song: Optional[Song]
    next_song_id: Optional[int]
    next_song: Optional[Song]
    recent: List[int]

    def __init__(self, manager: Manager, ws_clients: List[WebSocket]):
        self.manager = manager
        self.queue = []
        self.mpd_client = MPDClient(settings.MPD_HOST)
        self.current_song_id = None
        self.current_song = None
        self.next_song_id = None
        self.next_song = None
        self.recent = []
        self.ws_clients = ws_clients

    async def load_state(self) -> None:
        if not settings.STATE_PATH:
            return
        try:
            async with aiofiles.open(settings.STATE_PATH, "r") as f:
                state = json.loads(await f.read())
        except Exception:
            logger.exception("Failed to load state")
        else:
            queue_ids = state.get("queue", [])
            songs = await self.manager.execute(
                Song.select(Song, User)
                .join(User, JOIN.LEFT_OUTER)
                .where(Song.id.in_(queue_ids))
            )
            self.queue = sorted(songs, key=lambda song: queue_ids.index(song.id))
            self.recent = state.get("recent", [])

    async def save_state(self) -> None:
        if not settings.STATE_PATH:
            return

        state = json.dumps(
            {"queue": [song.id for song in self.queue], "recent": self.recent}, indent=4
        )
        async with aiofiles.open(settings.STATE_PATH, "w") as f:
            await f.write(state)

    async def run(self) -> None:
        await self.load_state()

        async with self.mpd_client:
            self.mpd_client = self.mpd_client
            await self.mpd_client.execute("random 0")
            await self.mpd_client.execute("repeat 0")
            await self.mpd_client.execute("single 0")
            await self.mpd_client.execute("consume 1")

            while await self.check_playlist():
                await self.mpd_client.execute("idle playlist")

            while True:
                await self.mpd_client.execute("idle playlist update player")
                await self.check_playlist()

    async def enqueue(self, song: Song) -> bool:
        if (
            (self.current_song is not None and song.id == self.current_song.id)
            or (self.next_song is not None and song.id == self.next_song.id)
            or song.id in [s.id for s in self.queue]
        ):
            return False

        self.queue.append(song)
        await self.save_state()
        await self.check_playlist()
        await self.send_updates()
        return True

    async def add_recent(self, song: Song) -> None:
        self.recent.append(song.id)
        self.recent = self.recent[-settings.REMEMBER_RECENT :]
        await self.save_state()

    async def check_playlist(self) -> bool:
        status = await self.mpd_client.execute("status")

        playlistlength = int(status["playlistlength"])
        if playlistlength < 2:
            while True:
                song = await self.get_next_song()
                if not song:
                    break

                try:
                    await self.mpd_client.execute(f"addid {song.filename}")
                except MPDCommandError:
                    logger.exception("Failed to add song, deleting from database")
                    await self.manager.delete(song)
                    continue
                if playlistlength == 0:
                    await self.add_recent(song)
                return True

        if status["state"] != "play":
            await self.mpd_client.execute("play")
            return False

        playlist_updated = False

        current_song_id = int(status["songid"]) if "songid" in status else None
        if current_song_id != self.current_song_id:
            self.current_song_id = current_song_id
            playlist_updated = True
            self.current_song = await self.get_song_by_playlist_id(current_song_id)
            if self.current_song is not None:
                await self.add_recent(self.current_song)

        next_song_id = int(status["nextsongid"]) if "nextsongid" in status else None
        if next_song_id != self.next_song_id:
            self.next_song_id = next_song_id
            playlist_updated = True
            self.next_song = await self.get_song_by_playlist_id(next_song_id)

        if playlist_updated:
            await self.send_updates()

        return False

    async def get_song_by_playlist_id(
        self, playlist_song_id: Optional[int]
    ) -> Optional[Song]:
        if playlist_song_id is None:
            return None

        song_data = await self.mpd_client.execute(f"playlistid {playlist_song_id}")
        if not song_data:
            return None

        basename, extension = os.path.splitext(song_data["file"])
        song_external_id = urlsafe_b64decode(f"{basename}==")
        try:
            return cast(
                Song,
                await self.manager.get(
                    Song.select(Song, User)
                    .join(User, JOIN.LEFT_OUTER)
                    .where(
                        Song.external_id == song_external_id,
                        Song.extension == extension,
                    ),
                ),
            )
        except Song.DoesNotExist:
            return None

    async def get_next_song(self) -> Optional[Song]:
        if self.queue:
            return self.queue.pop(0)

        while True:
            song_ids = {
                song.id for song in await self.manager.execute(Song.select(Song.id))
            }
            if not song_ids:
                return None

            recent = [recent_id for recent_id in self.recent if recent_id in song_ids]
            if self.next_song is not None and self.next_song.id in song_ids:
                recent.append(self.next_song.id)

            if len(song_ids) > 1:
                song_ids -= set(recent[-min(len(recent), len(song_ids) - 1) :])

            song_id = random.choice(tuple(song_ids))
            try:
                song: Song = await self.manager.get(Song, id=song_id)
                return song
            except Song.DoesNotExist:
                pass

    async def send_updates(self) -> None:
        fs = [
            ws_client.send_json({"action": "EVENT", "event": "update"})
            for ws_client in self.ws_clients
        ]
        if fs:
            await asyncio.gather(*fs)
