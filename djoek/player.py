import logging
import os
import random
from base64 import urlsafe_b64decode
from typing import List, Optional, cast

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

    async def run(self) -> None:
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
