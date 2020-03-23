import asyncio
import html
import subprocess
from typing import List

import aiofiles
import httpx

import djoek.settings as settings
from djoek.providers import MetadataSchema, Provider, SearchResultSchema


class YouTubeProvider(Provider):
    key = "youtube"

    async def get_metadata(self, content_id: str) -> MetadataSchema:
        tags: List[str]
        async with httpx.AsyncClient() as client:
            r = await client.get(
                "https://www.googleapis.com/youtube/v3/videos",
                params={
                    "part": "snippet",
                    "id": content_id,
                    "key": settings.GOOGLE_API_KEY,
                },
            )
            if r.status_code == 403:
                # Fall back to oEmbed. Lacks tags, still better than failing.
                r = await client.get(
                    "https://noembed.com/embed",
                    params={"url": f"https://youtu.be/{content_id}"},
                )
                r.raise_for_status()
                title = r.json()["title"]
                tags = []
            else:
                r.raise_for_status()
                metadata = r.json()
                snippet = metadata["items"][0]["snippet"]
                title = snippet["title"]
                tags = snippet.get("tags", [])

        return MetadataSchema(
            title=title,
            tags=tags,
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
                title=html.unescape(item["snippet"]["title"]),
                external_id=f"{self.key}:{item['id']['videoId']}",
                preview_url=f"https://youtu.be/{item['id']['videoId']}",
            )
            for item in result["items"]
            if item["id"]["kind"] == "youtube#video"
        ]
