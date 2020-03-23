import asyncio
import subprocess
from typing import List

import aiofiles
import httpx

import djoek.settings as settings
from djoek.providers import MetadataSchema, Provider, SearchResultSchema


class YouTubeProvider(Provider):
    key = "youtube"

    async def get_metadata(self, content_id: str) -> MetadataSchema:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                "https://www.googleapis.com/youtube/v3/videos",
                params={
                    "part": "snippet,contentDetails",
                    "id": content_id,
                    "key": settings.GOOGLE_API_KEY,
                },
            )
        metadata = r.json()
        snippet = metadata["items"][0]["snippet"]
        return MetadataSchema(
            title=snippet["title"],
            tags=snippet.get("tags", []),
            extension=".m4a",
            preview_url=f"https://youtu.be/{content_id}",
        )

    async def download(self, content_id: str, path: str) -> None:
        p = await asyncio.create_subprocess_exec(
            "youtube-dl",
            "-f",
            "m4a",
            "-o",
            "-",
            f"https://www.youtube.com/watch?v={content_id}",
            stdout=subprocess.PIPE,
        )
        data, _ = await p.communicate()

        async with aiofiles.open(path, "wb") as f:
            await f.write(data)

    async def search(self, query: str) -> List[SearchResultSchema]:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                "https://www.googleapis.com/youtube/v3/search",
                params={
                    "part": "snippet",
                    "maxResults": "10",
                    "q": query,
                    "type": "video",
                    "key": settings.GOOGLE_API_KEY,
                },
            )
            result = r.json()

        return [
            SearchResultSchema(
                title=item["snippet"]["title"],
                external_id=f"{self.key}:{item['id']['videoId']}",
                preview_url=f"https://youtu.be/{item['id']['videoId']}",
            )
            for item in result["items"]
            if item["id"]["kind"] == "youtube#video"
        ]
