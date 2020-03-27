from abc import ABC, abstractmethod
from decimal import Decimal
from typing import List, Optional

from pydantic.main import BaseModel


class MetadataSchema(BaseModel):
    title: str
    tags: List[str]
    extension: str
    preview_url: Optional[str]
    duration: Optional[Decimal]


class SearchResultSchema(BaseModel):
    title: str
    external_id: str
    preview_url: Optional[str]
    duration: Optional[Decimal]


class Provider(ABC):
    key: str

    @abstractmethod
    async def get_metadata(self, content_id: str) -> MetadataSchema:
        ...

    @abstractmethod
    async def download(
        self, content_id: str, metadata: MetadataSchema, path: str
    ) -> None:
        ...

    @abstractmethod
    async def search(self, query: str) -> List[SearchResultSchema]:
        ...
