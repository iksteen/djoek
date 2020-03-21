import asyncio
import os
import subprocess
from typing import Any, Dict, cast

import aiofiles
import httpx
from peewee import IntegrityError, fn
from peewee_async import Manager

import djoek.settings as settings
from djoek.models import Song


async def download_video(vid: str) -> bytes:
    p = await asyncio.create_subprocess_exec(
        "youtube-dl",
        "-f",
        "m4a",
        "-o",
        "-",
        f"https://www.youtube.com/watch?v={vid}",
        stdout=subprocess.PIPE,
    )
    data, _ = await p.communicate()
    return data


async def get_metadata(vid: str) -> Dict[str, Any]:
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"https://www.googleapis.com/youtube/v3/videos?part=snippet,contentDetails&id={vid}&key={settings.GOOGLE_API_KEY}"
        )
    return cast(Dict[str, Any], r.json())


async def add_from_youtube(manager: Manager, vid: str) -> Song:
    metadata = await get_metadata(vid)
    snippet = metadata["items"][0]["snippet"]
    title = snippet["title"]
    tags = snippet["tags"]
    external_id = f"youtube:{vid}"

    try:
        async with manager.atomic():
            song = await manager.create(
                Song,
                title=title,
                tags=tags,
                search_field=fn.to_tsvector(f"{title} {vid} {' '.join(tags)}"),
                external_id=external_id,
            )

            data = await download_video(vid)

            async with aiofiles.open(
                os.path.join(settings.MUSIC_DIR, f"{song.id}.m4a"), "wb"
            ) as f:
                await f.write(data)
        return cast(Song, song)
    except IntegrityError:
        return cast(Song, await manager.get(Song, external_id=external_id))
