from abc import ABC, abstractmethod
from typing import List

from djoek.models import Song
from djoek.schemas import ItemSchema, MetadataSchema


class Provider(ABC):
    key: str

    @abstractmethod
    async def get_metadata(self, content_id: str) -> MetadataSchema:
        ...

    @abstractmethod
    async def download(self, content_id: str, song: Song) -> None:
        ...

    @abstractmethod
    async def search(self, query: str) -> List[ItemSchema]:
        ...
