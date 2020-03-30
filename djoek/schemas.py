from decimal import Decimal
from typing import List, Optional, TypeVar, overload

from pydantic.main import BaseModel

from djoek.models import Song

T_ItemSchema = TypeVar("T_ItemSchema", bound="ItemSchema")


class ItemSchema(BaseModel):
    title: str
    duration: Optional[Decimal]
    external_id: str
    preview_url: str
    username: Optional[str]
    upvotes: Optional[int]
    downvotes: Optional[int]

    @classmethod
    @overload
    def from_song(cls, song: None, *, is_authenticated: bool) -> None:
        ...

    @classmethod  # noqa: F811
    @overload
    def from_song(cls, song: Song, *, is_authenticated: bool) -> T_ItemSchema:
        ...

    @classmethod  # noqa: F811
    def from_song(
        cls, song: Optional[Song], *, is_authenticated: bool
    ) -> Optional[T_ItemSchema]:
        if song is not None:
            return cls(
                title=song.title,
                duration=song.duration,
                external_id=song.external_id,
                preview_url=song.preview_url,
                username=song.username if is_authenticated else None,
                upvotes=song.upvotes,
                downvotes=song.downvotes,
            )
        else:
            return None


class StatusSchema(BaseModel):
    current_song: Optional[ItemSchema]
    next_song: Optional[ItemSchema]


class LibraryAddSchema(BaseModel):
    external_id: str
    enqueue: bool = True


class SearchRequestSchema(BaseModel):
    provider: str
    q: str


class MetadataSchema(BaseModel):
    title: str
    tags: List[str]
    extension: str
    preview_url: Optional[str]
    duration: Optional[Decimal]
