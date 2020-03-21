import asyncio
import os
import re
import subprocess
from typing import Any, Dict, List, cast

import aiofiles
import httpx
from peewee import IntegrityError, fn
from peewee_async import Manager

import djoek.settings as settings
from djoek.models import Song

WORD_RE = re.compile(r"\w+", re.UNICODE)


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


def edge_ngrams(key: str) -> List[str]:
    return [key[0:i] for i in range(1, len(key) + 1)]


async def add_from_youtube(manager: Manager, vid: str) -> Song:
    metadata = await get_metadata(vid)
    snippet = metadata["items"][0]["snippet"]
    title = snippet["title"]
    tags = snippet["tags"]
    external_id = f"youtube:{vid}"

    keywords = [vid]
    for keyword in title.split():
        keywords.append(keyword)
        keyword = "".join(WORD_RE.findall(keyword))
        keywords.extend([ngram for ngram in edge_ngrams(keyword) if ngram != keyword])
    for tag in tags:
        keywords.extend(edge_ngrams(tag))
    search_value = fn.to_tsvector(" ".join(keywords))

    song: Song

    try:
        async with manager.atomic():
            song = await manager.create(
                Song,
                title=title,
                tags=tags,
                search_field=search_value,
                external_id=external_id,
            )

            data = await download_video(vid)

            async with aiofiles.open(
                os.path.join(settings.MUSIC_DIR, f"{song.id}.m4a"), "wb"
            ) as f:
                await f.write(data)
        return song
    except IntegrityError:
        song = await manager.get(Song, external_id=external_id)
        song.search_field = search_value
        await manager.update(song, only=["search_field"])
        return song
