import asyncio
import logging
import re
from enum import Enum
from pathlib import Path
from typing import List, cast

import aiofiles
import aiofiles.os
import mutagen
from fastapi import Depends, FastAPI, HTTPException
from peewee import JOIN, DatabaseError, IntegrityError, fn
from peewee_async import Manager
from starlette.responses import Response
from starlette.status import HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST
from starlette.websockets import WebSocket

from djoek import settings
from djoek.auth import is_authenticated, require_auth, require_user, require_user_id
from djoek.models import Song, User, get_manager
from djoek.mpdclient import MPDClient
from djoek.player import Player, get_player
from djoek.providers import Provider
from djoek.providers.registry import PROVIDERS
from djoek.schemas import (
    ItemSchema,
    LibraryAddSchema,
    SearchRequestSchema,
    StatusSchema,
)
from djoek.util import send_updates

app = FastAPI()
app.state.ws_clients = []
app.state.vote_song_id = None
app.state.voting = set()
app.state.votes = {}

logger = logging.getLogger(__name__)
WORD_RE = re.compile(r"\w+", re.UNICODE)


class VoteDirection(Enum):
    up = "up"
    down = "down"


@app.get("/", response_model=StatusSchema)
async def status(
    player: Player = Depends(get_player),
    is_authenticated: bool = Depends(is_authenticated),
) -> StatusSchema:
    return StatusSchema(
        current_song=ItemSchema.from_song(
            player.current_song, is_authenticated=is_authenticated
        ),
        next_song=ItemSchema.from_song(
            player.next_song, is_authenticated=is_authenticated
        ),
    )


@app.get(
    "/playlist/", response_model=List[ItemSchema], dependencies=[Depends(require_auth)]
)
async def playlist_list(player: Player = Depends(get_player)) -> List[ItemSchema]:
    return [ItemSchema.from_song(song, is_authenticated=True) for song in player.queue]


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
    user: User = Depends(require_user),
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
                    user=user,
                )
                await download(manager, provider, content_id, song)
        except IntegrityError:
            song = await manager.get(
                Song.select(Song, User)
                .join(User, JOIN.LEFT_OUTER)
                .where(Song.external_id == task.external_id)
            )
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
    "/search/", response_model=List[ItemSchema], dependencies=[Depends(require_auth)],
)
async def search(
    query: SearchRequestSchema, manager: Manager = Depends(get_manager)
) -> List[ItemSchema]:
    if query.provider == "local":
        songs = await manager.execute(
            Song.select(Song, User)
            .join(User, JOIN.LEFT_OUTER)
            .where(Song.search_field.match(query.q, plain=True))
        )
        return [ItemSchema.from_song(song, is_authenticated=True) for song in songs]

    provider = PROVIDERS[query.provider]
    return await provider.search(query.q)


@app.post("/vote/{direction}", status_code=HTTP_204_NO_CONTENT, response_class=Response)
async def vote_up(
    direction: VoteDirection,
    user_id: int = Depends(require_user_id),
    player: Player = Depends(get_player),
    manager: Manager = Depends(get_manager),
) -> None:
    if player.current_song_id is None or player.current_song is None:
        return

    if direction is VoteDirection.up:
        field, counter_field = Song.upvotes, Song.downvotes
    else:
        field, counter_field = Song.downvotes, Song.upvotes

    if player.current_song_id != app.state.vote_song_id:
        app.state.vote_song_id = player.current_song_id
        app.state.voting = set()
        app.state.votes = {}

    current_song = player.current_song
    voting = app.state.voting
    votes = app.state.votes

    # From this point on, don't trust app state to prevent race conditions
    # due to asynchronicity.

    current_vote = votes.get(user_id)
    ignore_increase = False

    if direction is VoteDirection.up:
        if current_song.user_id is None:
            if current_vote is VoteDirection.down:
                ignore_increase = True
            else:
                raise HTTPException(
                    status_code=HTTP_400_BAD_REQUEST,
                    detail="Can't upvote unclaimed song.",
                )

        if current_song.user_id == user_id:
            if current_vote is VoteDirection.down:
                ignore_increase = True
            else:
                raise HTTPException(
                    status_code=HTTP_400_BAD_REQUEST,
                    detail="Can't upvote your own songs.",
                )

    if current_vote is direction:
        return

    if user_id in voting:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST, detail="Have some patience."
        )
    voting.add(user_id)

    votes[user_id] = direction

    try:
        async with manager.atomic():
            if current_vote is not None:
                await manager.execute(
                    Song.update({counter_field: counter_field - 1}).where(
                        Song.id == current_song.id
                    )
                )
            if not ignore_increase:
                await manager.execute(
                    Song.update({field: field + 1}).where(Song.id == current_song.id)
                )
    except DatabaseError:
        votes[user_id] = current_vote
        raise
    finally:
        voting.remove(user_id)

    if current_vote is not None:
        setattr(
            current_song,
            counter_field.name,
            getattr(current_song, counter_field.name) - 1,
        )
    if not ignore_increase:
        setattr(current_song, field.name, getattr(current_song, field.name) + 1)

    await send_updates(app.state.ws_clients)


@app.websocket("/events")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    app.state.ws_clients.append(websocket)
    try:
        while True:
            message = await websocket.receive()
            if message["type"] == "websocket.disconnect":
                break
            await websocket.close(code=1000)
    finally:
        app.state.ws_clients.remove(websocket)
