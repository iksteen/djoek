import asyncio
import logging
import re
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, cast

import aiofiles
import aiofiles.os
import mutagen
from fastapi import Depends, FastAPI, HTTPException
from peewee import IntegrityError, fn
from peewee_async import Manager
from pydantic import BaseModel

from djoek import settings
from djoek.auth import require_auth, require_user_id
from djoek.models import Song, get_manager
from djoek.mpdclient import MPDClient
from djoek.player import Player, get_player
from djoek.providers import Provider, SearchResultSchema
from djoek.providers.registry import PROVIDERS

app = FastAPI()

logger = logging.getLogger(__name__)
WORD_RE = re.compile(r"\w+", re.UNICODE)


class StatusSchema(BaseModel):
    current_song: Optional[str]
    next_song: Optional[str]


class PlaylistItemSchema(BaseModel):
    title: str
    duration: Optional[Decimal]


class LibraryAddSchema(BaseModel):
    external_id: str
    enqueue: bool = True


class SearchRequestSchema(BaseModel):
    provider: str
    q: str


class SearchResponseSchema(BaseModel):
    provider: str
    results: List[SearchResultSchema]


@app.get("/", response_model=StatusSchema)
async def status(player: Player = Depends(get_player),) -> StatusSchema:
    return StatusSchema(
        current_song=player.current_song.title if player.current_song else None,
        next_song=player.next_song.title if player.next_song else None,
    )


@app.get(
    "/playlist/",
    response_model=List[PlaylistItemSchema],
    dependencies=[Depends(require_auth)],
)
async def playlist_list(
    player: Player = Depends(get_player),
) -> List[PlaylistItemSchema]:
    return [
        PlaylistItemSchema(title=song.title, duration=song.duration)
        for song in player.queue
    ]


def edge_ngrams(key: str) -> List[str]:
    return [key[0:i] for i in range(1, len(key) + 1)]


async def wait_for_song(song: Song) -> None:
    async with MPDClient(settings.MPD_HOST) as mpd_client:
        await mpd_client.execute(f"update {song.filename}")
        while not await mpd_client.execute(f"find file {song.filename}"):
            await mpd_client.execute("idle update")


async def download(
    manager: Manager,
    provider: Provider,
    content_id: str,
    song: Song,
    do_update: bool = True,
) -> None:
    try:
        await aiofiles.os.stat(song.path)
    except FileNotFoundError:
        pass
    else:
        return

    await provider.download(content_id, song)
    process = await asyncio.create_subprocess_exec(
        "loudgain", "-s", "i", str(song.path)
    )
    await process.communicate()

    def process_metadata(song_path: Path, title: str) -> float:
        m = mutagen.File(song_path, easy=True)
        m["title"] = title
        m.save()
        return float(m.info.length)

    loop = asyncio.get_event_loop()
    try:
        song.duration = await loop.run_in_executor(
            None, process_metadata, song.path, song.title
        )
        if do_update:
            await manager.update(song, only=["duration"])
    except Exception:
        logger.exception("Failed to determine song length")


@app.post("/library/", response_model=str)
async def playlist_add(
    task: LibraryAddSchema,
    manager: Manager = Depends(get_manager),
    player: Player = Depends(get_player),
    user_id: Dict[str, Any] = Depends(require_user_id),
) -> str:
    provider_key, content_id = task.external_id.split(":", 1)
    provider = PROVIDERS[provider_key]

    metadata = await provider.get_metadata(content_id)

    keywords = [content_id]

    for keyword in metadata.title.split():
        keywords.append(keyword)
        keyword = "".join(WORD_RE.findall(keyword))
        keywords.extend([ngram for ngram in edge_ngrams(keyword) if ngram != keyword])

    for tag in metadata.tags:
        keywords.extend(edge_ngrams(tag))

    search_value = fn.to_tsvector(" ".join(keywords))

    song: Song

    async with manager.atomic():
        try:
            async with manager.atomic():
                song = await manager.create(
                    Song,
                    title=metadata.title,
                    tags=metadata.tags,
                    search_field=search_value,
                    external_id=task.external_id,
                    extension=metadata.extension,
                    preview_url=metadata.preview_url,
                    user_id=user_id,
                )
                await download(manager, provider, content_id, song)
        except IntegrityError:
            song = await manager.get(Song, external_id=task.external_id)
            song.title = metadata.title
            song.search_field = search_value
            await download(manager, provider, content_id, song, False)
            await manager.update(song, only=["title", "search_field", "duration"])

        try:
            await asyncio.wait_for(wait_for_song(song), timeout=5.0)
        except asyncio.TimeoutError:
            logger.warning("Timed out waiting for %s", song.filename)
            raise HTTPException(status_code=500, detail="Song did not appear")

    if task.enqueue:
        await player.enqueue(song)

    return cast(str, song.title)


@app.post(
    "/search/",
    response_model=List[SearchResultSchema],
    dependencies=[Depends(require_auth)],
)
async def search(
    query: SearchRequestSchema, manager: Manager = Depends(get_manager)
) -> List[SearchResultSchema]:
    if query.provider == "local":
        songs = await manager.execute(
            Song.select().where(Song.search_field.match(query.q, plain=True))
        )
        return [
            SearchResultSchema(
                title=song.title,
                external_id=song.external_id,
                preview_url=song.preview_url,
                duration=song.duration,
            )
            for song in songs
        ]

    provider = PROVIDERS[query.provider]
    return await provider.search(query.q)
