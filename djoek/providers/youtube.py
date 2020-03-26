import html
import re
from typing import List

import aiofiles
import asyncpipe
import httpx

import djoek.settings as settings
from djoek.providers import MetadataSchema, Provider, SearchResultSchema

YOUTUBE_URL_RE = re.compile(
    r"^(?:https?://(?:[^/]+.)?youtube.com/watch\?(?:v=|.*&v=)|https?://youtu.be/|youtube:)([a-zA-Z0-9_-]{11})"
)


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
            extension=".mp3",
            preview_url=f"https://youtu.be/{content_id}",
        )

    async def download(
        self, content_id: str, metadata: MetadataSchema, path: str
    ) -> None:
        pipe = asyncpipe.PipeBuilder(
            "youtube-dl",
            "-f",
            "bestaudio",
            "-o",
            "-",
            f"https://www.youtube.com/watch?v={content_id}",
        )
        pipe.chain(
            "ffmpeg",
            "-i",
            "pipe:",
            "-codec:a",
            "libmp3lame",
            "-qscale:a",
            "1",
            "-f",
            "mp3",
            "-",
        )
        result = await pipe.call_async()

        async with aiofiles.open(path, "wb") as f:
            await f.write(result[-1].stdout)

    async def search(self, query: str) -> List[SearchResultSchema]:
        m = YOUTUBE_URL_RE.match(query)
        if m is not None:
            content_id = m.group(1)
            metadata = await self.get_metadata(content_id)
            return [
                SearchResultSchema(
                    title=metadata.title,
                    external_id=f"{self.key}:{content_id}",
                    preview_url=f"https://youtu.be/{content_id}",
                )
            ]

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
