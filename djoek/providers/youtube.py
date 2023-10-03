import asyncio
import html
import re
from typing import Optional

import httpx
import isodate

import djoek.settings as settings
from djoek.models import Song
from djoek.providers import Provider
from djoek.schemas import ItemSchema, MetadataSchema

YOUTUBE_URL_RE = re.compile(
    r"^(?:https?://(?:[^/]+.)?youtube.com/watch\?(?:v=|.*&v=)|https?://youtu.be/|youtube:)([a-zA-Z0-9_-]{11})"
)


class YouTubeProvider(Provider):
    key = "youtube"

    async def get_metadata(self, content_id: str) -> MetadataSchema:
        tags: list[str]
        async with httpx.AsyncClient() as client:
            r = await client.get(
                "https://www.googleapis.com/youtube/v3/videos",
                params={
                    "part": "snippet,contentDetails",
                    "id": content_id,
                    "key": settings.GOOGLE_API_KEY,
                },
            )
            duration: Optional[float]
            if r.status_code == 403:
                # Fall back to oEmbed. Lacks tags, still better than failing.
                r = await client.get(
                    "https://noembed.com/embed",
                    params={"url": f"https://youtu.be/{content_id}"},
                )
                r.raise_for_status()
                title = r.json()["title"]
                tags = []
                duration = None
            else:
                r.raise_for_status()
                metadata = r.json()
                snippet = metadata["items"][0]["snippet"]
                title = snippet["title"]
                tags = snippet.get("tags", [])
                duration = isodate.parse_duration(
                    metadata["items"][0]["contentDetails"]["duration"]
                ).total_seconds()

        return MetadataSchema(
            title=title,
            tags=tags,
            extension=".mp3",
            preview_url=f"https://youtu.be/{content_id}",
            duration=duration,
        )

    async def download(self, content_id: str, song: Song) -> None:
        basename = song.path.parent / song.path.stem
        process = await asyncio.create_subprocess_exec(
            "yt-dlp",
            "-x",
            "--audio-format",
            "mp3",
            "--audio-quality",
            "1",
            "-o",
            f"{basename}.%(ext)s",
            "--no-cache-dir",
            f"https://www.youtube.com/watch?v={content_id}",
        )
        await process.communicate()

    async def search(self, query: str) -> list[ItemSchema]:
        m = YOUTUBE_URL_RE.match(query)
        if m is not None:
            content_id = m.group(1)
            metadata = await self.get_metadata(content_id)
            return [
                ItemSchema(
                    title=metadata.title,
                    external_id=f"{self.key}:{content_id}",
                    preview_url=f"https://youtu.be/{content_id}",
                    duration=metadata.duration,
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

            r = await client.get(
                "https://www.googleapis.com/youtube/v3/videos",
                params={
                    "part": "contentDetails",
                    "id": ",".join(item["id"]["videoId"] for item in result["items"]),
                    "key": settings.GOOGLE_API_KEY,
                },
            )
            durations = {
                item["id"]: isodate.parse_duration(
                    item["contentDetails"]["duration"]
                ).total_seconds()
                for item in r.json()["items"]
            }

        return [
            ItemSchema(
                title=html.unescape(item["snippet"]["title"]),
                external_id=f"{self.key}:{item['id']['videoId']}",
                preview_url=f"https://youtu.be/{item['id']['videoId']}",
                duration=durations.get(item["id"]["videoId"]),
            )
            for item in result["items"]
            if item["id"]["kind"] == "youtube#video"
        ]
