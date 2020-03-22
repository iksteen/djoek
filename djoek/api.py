import os
import re
from typing import List, Optional, cast

import aiofiles
import aiofiles.os
from fastapi import Depends, FastAPI
from mpd.asyncio import MPDClient
from peewee import IntegrityError, fn
from peewee_async import Manager
from pydantic import BaseModel
from starlette.requests import Request

from djoek import settings
from djoek.auth import require_auth
from djoek.models import Song
from djoek.player import Player, get_mpd_client
from djoek.providers import SearchResultSchema
from djoek.providers.registry import PROVIDERS

app = FastAPI()

WORD_RE = re.compile(r"\w+", re.UNICODE)


async def get_manager(request: Request) -> Manager:
    return request.app.state.manager


async def get_player(request: Request) -> Player:
    return cast(Player, request.app.state.player)


class StatusSchema(BaseModel):
    current_song: Optional[str]
    next_song: Optional[str]


class PlaylistItemSchema(BaseModel):
    title: str


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
    return [PlaylistItemSchema(title=song.title) for song in player.queue]


def edge_ngrams(key: str) -> List[str]:
    return [key[0:i] for i in range(1, len(key) + 1)]


@app.post("/library/", response_model=str, dependencies=[Depends(require_auth)])
async def playlist_add(
    task: LibraryAddSchema,
    manager: Manager = Depends(get_manager),
    mpd_client: MPDClient = Depends(get_mpd_client),
    player: Player = Depends(get_player),
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
            )

            song_path = os.path.join(settings.MUSIC_DIR, song.filename)
            try:
                await aiofiles.os.stat(song_path)
            except FileNotFoundError:
                await provider.download(content_id, song_path)
    except IntegrityError:
        song = await manager.get(Song, external_id=task.external_id)
        song.search_field = search_value
        await manager.update(song, only=["search_field"])

    await mpd_client.update()
    async for _ in mpd_client.idle(["update"]):
        f = await mpd_client.find("file", song.filename)
        if f:
            break

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
            )
            for song in songs
        ]

    provider = PROVIDERS[query.provider]
    return await provider.search(query.q)
