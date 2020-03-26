import json
import logging
import os
import random
from base64 import urlsafe_b64decode
from typing import List, Optional, cast

import aiofiles
from peewee_async import Manager

from djoek import settings
from djoek.models import Song
from djoek.mpdclient import MPDClient, MPDCommandError

logger = logging.getLogger(__name__)


class Player:
    mpd_client: MPDClient
    queue: List[Song]
    current_song: Optional[Song]
    next_song: Optional[Song]
    recent: List[int]

    def __init__(self, manager: Manager):
        self.manager = manager
        self.queue = []
        self.mpd_client = MPDClient(settings.MPD_HOST)
        self.current_song = None
        self.next_song = None
        self.recent = []

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
                Song.select().where(Song.id.in_(queue_ids))
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

            await self.check_playlist()

            while True:
                await self.mpd_client.execute("idle playlist update")
                await self.check_playlist()

    async def enqueue(self, song: Song) -> None:
        self.queue.append(song)
        await self.save_state()
        await self.check_playlist()

    def add_recent(self, song_id: int) -> None:
        if song_id in self.recent:
            self.recent.remove(song_id)
        self.recent.append(song_id)
        self.recent = self.recent[-settings.REMEMBER_RECENT :]

    async def check_playlist(self) -> None:
        status = await self.mpd_client.execute("status")

        if int(status["playlistlength"]) < 2:
            while True:
                song = await self.get_next_song()
                if not song:
                    break

                try:
                    await self.mpd_client.execute(f"addid {song.filename}")
                except MPDCommandError:
                    logger.exception("Failed to add song")
                    continue
                return

        if status["state"] != "play":
            await self.mpd_client.execute("play")

        if "songid" in status:
            self.current_song = await self.get_song_by_playlist_id(status["songid"])
            if self.current_song:
                self.add_recent(self.current_song.id)

        if "nextsongid" in status:
            self.next_song = await self.get_song_by_playlist_id(status["nextsongid"])
            if self.next_song:
                self.add_recent(self.next_song.id)

        await self.save_state()

    async def get_song_by_playlist_id(self, playlist_song_id: str) -> Optional[Song]:
        song_data = await self.mpd_client.execute(f"playlistid {playlist_song_id}")
        if not song_data:
            return None

        basename, extension = os.path.splitext(song_data["file"])
        song_external_id = urlsafe_b64decode(f"{basename}==")
        try:
            return cast(
                Song,
                await self.manager.get(
                    Song, external_id=song_external_id, extension=extension
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

            if len(song_ids) > 1:
                song_ids -= set(
                    self.recent[-min(len(self.recent), len(song_ids) - 1) :]
                )

            song_id = random.choice(tuple(song_ids))
            try:
                song: Song = await self.manager.get(Song, id=song_id)
                self.add_recent(song_id)
                return song
            except Song.DoesNotExist:
                pass
