import asyncio
import subprocess
from typing import Any, Dict, List, cast

import aiofiles
import httpx

import djoek.settings as settings
from djoek.providers import MetadataSchema, Provider, SearchResultSchema


class SoundcloudProvider(Provider):
    key = "soundcloud"

    async def get_track_info(self, content_id: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                "https://api-v2.soundcloud.com/tracks",
                params={"ids": content_id, "client_id": settings.SOUNDCLOUD_CLIENT_ID},
            )
        return cast(Dict[str, Any], r.json()[0])

    async def get_metadata(self, content_id: str) -> MetadataSchema:
        metadata = await self.get_track_info(content_id)
        return MetadataSchema(
            title=metadata["title"],
            tags=metadata["tag_list"].split(),
            extension=".mp3",
            preview_url=metadata["permalink_url"],
        )

    async def download(self, content_id: str, path: str) -> None:
        metadata = await self.get_track_info(content_id)
        p = await asyncio.create_subprocess_exec(
            "youtube-dl",
            "-f",
            "mp3",
            "-o",
            "-",
            metadata["permalink_url"],
            stdout=subprocess.PIPE,
        )
        data, _ = await p.communicate()

        async with aiofiles.open(path, "wb") as f:
            await f.write(data)

    async def search(self, query: str) -> List[SearchResultSchema]:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                "https://api-v2.soundcloud.com/search",
                params={
                    "q": query,
                    "limit": 10,
                    "client_id": settings.SOUNDCLOUD_CLIENT_ID,
                },
            )
            result = r.json()

        return [
            SearchResultSchema(
                title=item["title"],
                external_id=f"{self.key}:{item['id']}",
                preview_url=item["permalink_url"],
            )
            for item in result["collection"]
        ]
