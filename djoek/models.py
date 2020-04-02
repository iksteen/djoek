from base64 import urlsafe_b64encode
from pathlib import Path
from typing import Optional, cast

from fastapi import FastAPI
from peewee import (
    SQL,
    AutoField,
    DecimalField,
    ForeignKeyField,
    IntegerField,
    Model,
    TextField,
)
from peewee_async import Manager
from peewee_asyncext import PooledPostgresqlExtDatabase
from playhouse.postgres_ext import ArrayField, JSONField, TSVectorField
from psycopg2._psycopg import parse_dsn
from starlette.requests import Request

from djoek import settings

database = PooledPostgresqlExtDatabase(None)


async def setup_manager(app: FastAPI) -> None:
    db_config = parse_dsn(settings.DB_URI)
    db_name = db_config.pop("dbname")
    database.init(db_name, **db_config)
    database.set_allow_sync(False)
    app.state.manager = Manager(database)


async def shutdown_manager(app: FastAPI) -> None:
    app.state.manager.database.close()


async def get_manager(request: Request) -> Manager:
    return request.app.state.manager


class User(Model):
    class Meta:
        database = database

    sub = TextField(unique=True)
    profile = JSONField()


class Song(Model):
    class Meta:
        database = database

    id = AutoField()
    title = TextField()
    tags = ArrayField(field_class=TextField)
    search_field = TSVectorField()
    external_id = TextField(unique=True)
    extension = TextField()
    preview_url = TextField(null=True)
    duration = DecimalField(null=True)
    user = ForeignKeyField(User, null=True)
    upvotes = IntegerField(default=0, constraints=[SQL("DEFAULT 0")])
    downvotes = IntegerField(default=0, constraints=[SQL("DEFAULT 0")])

    @property
    def filename(self) -> str:
        basename = (
            urlsafe_b64encode(self.external_id.encode("utf-8"))
            .rstrip(b"=")
            .decode("utf-8")
        )
        return f"{basename}{self.extension}"

    @property
    def path(self) -> Path:
        return settings.MUSIC_DIR / self.filename

    @property
    def provider(self) -> str:
        return cast(str, self.external_id.split(":", 1)[0])

    @property
    def content_id(self) -> str:
        return cast(str, self.external_id.split(":", 1)[1])

    @property
    def username(self) -> Optional[str]:
        if self.user is not None:
            return settings.USER_FORMAT.format(user=self.user)
        else:
            return None

    @property
    def rating(self) -> int:
        rating: int = self.upvotes - self.downvotes
        return rating
