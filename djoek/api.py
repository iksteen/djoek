from typing import Any, Dict, List, Optional, cast

import httpx
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mpd.asyncio import MPDClient
from peewee_async import Manager
from pydantic import BaseModel
from starlette.requests import Request

from djoek import settings
from djoek.download import add_from_youtube
from djoek.models import Song
from djoek.player import Player, get_mpd_client

app = FastAPI()
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["GET"]
)


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
    video_id: str
    enqueue: bool = True


class SearchRequestSchema(BaseModel):
    q: str
    youtube: bool = False


class SearchResultSchema(BaseModel):
    title: str
    video_id: str


@app.get("/", response_model=StatusSchema)
async def status(player: Player = Depends(get_player),) -> StatusSchema:
    return StatusSchema(
        current_song=player.current_song.title if player.current_song else None,
        next_song=player.next_song.title if player.next_song else None,
    )


@app.get("/playlist/", response_model=List[PlaylistItemSchema])
async def playlist_list(
    player: Player = Depends(get_player),
) -> List[PlaylistItemSchema]:
    return [PlaylistItemSchema(title=song.title) for song in player.queue]


@app.post("/playlist/")
async def playlist_add(
    task: LibraryAddSchema,
    manager: Manager = Depends(get_manager),
    mpd_client: MPDClient = Depends(get_mpd_client),
    player: Player = Depends(get_player),
) -> str:
    song = await add_from_youtube(manager, task.video_id)

    await mpd_client.update()
    async for _ in mpd_client.idle(["update"]):
        f = await mpd_client.find("file", f"{song.id}.m4a")
        if f:
            break

    if task.enqueue:
        await player.enqueue(song)

    return cast(str, song.title)


@app.post("/search/", response_model=List[SearchResultSchema])
async def search(
    query: SearchRequestSchema, manager: Manager = Depends(get_manager)
) -> List[Dict[str, Any]]:
    if not query.youtube:
        songs = await manager.execute(
            Song.select().where(Song.search_field.match(query.q, plain=True))
        )
        if songs:
            return [
                {"title": song.title, "video_id": song.external_id.split(":")[1]}
                for song in songs
            ]

    async with httpx.AsyncClient() as client:
        r = await client.get(
            "https://www.googleapis.com/youtube/v3/search",
            params={
                "part": "snippet",
                "maxResults": "10",
                "q": query.q,
                "type": "video",
                "key": settings.GOOGLE_API_KEY,
            },
        )
        result = r.json()

    return [
        {"title": item["snippet"]["title"], "video_id": item["id"]["videoId"]}
        for item in result["items"]
        if item["id"]["kind"] == "youtube#video"
    ]
