import random
from typing import List, Optional, cast

from mpd.asyncio import MPDClient
from peewee_async import Manager

from djoek import settings
from djoek.models import Song


async def get_mpd_client() -> MPDClient:
    mpd_client = MPDClient()
    await mpd_client.connect(settings.MPD_HOST)
    return mpd_client


class Player:
    mpd_client: Optional[MPDClient]
    queue: List[Song]
    current_song: Optional[Song]
    next_song: Optional[Song]
    recent: List[int]

    def __init__(self, manager: Manager):
        self.manager = manager
        self.queue = []
        self.mpd_client = None
        self.current_song = None
        self.next_song = None
        self.recent = []

    async def run(self) -> None:
        self.mpd_client = await get_mpd_client()
        await self.mpd_client.random(0)
        await self.mpd_client.repeat(0)
        await self.mpd_client.single(0)
        await self.mpd_client.consume(1)

        await self.check_playlist()

        async for _ in self.mpd_client.idle(["playlist", "player"]):
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
        if self.mpd_client is None:
            return

        status = await self.mpd_client.status()

        if int(status["playlistlength"]) < 2:
            song = await self.get_next_song()
            if song:
                await self.mpd_client.addid(f"{song.id}.m4a")
            return

        if status["state"] == "stop":
            await self.mpd_client.play()

        if "songid" in status:
            self.current_song = await self.get_song_by_playlist_id(status["songid"])
            if self.current_song:
                self.add_recent(self.current_song.id)

        if "nextsongid" in status:
            self.next_song = await self.get_song_by_playlist_id(status["nextsongid"])
            if self.next_song:
                self.add_recent(self.next_song.id)

    async def get_song_by_playlist_id(self, playlist_song_id: str) -> Optional[Song]:
        if not self.mpd_client:
            return None

        song_data = await self.mpd_client.playlistid(playlist_song_id)
        if not song_data:
            return None

        song_id = int(song_data[0]["file"].split(".")[0])
        try:
            return cast(Song, await self.manager.get(Song, id=song_id))
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
