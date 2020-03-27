from base64 import urlsafe_b64encode
from typing import cast

from fastapi import FastAPI
from peewee import AutoField, DecimalField, ForeignKeyField, Model, TextField
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

    @property
    def filename(self) -> str:
        basename = (
            urlsafe_b64encode(self.external_id.encode("utf-8"))
            .rstrip(b"=")
            .decode("utf-8")
        )
        return f"{basename}{self.extension}"

    @property
    def provider(self) -> str:
        return cast(str, self.external_id.split(":", 1)[0])

    @property
    def content_id(self) -> str:
        return cast(str, self.external_id.split(":", 1)[1])
