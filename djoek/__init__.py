import asyncio
import logging

from peewee_async import Manager
from psycopg2.extensions import parse_dsn

import djoek.settings as settings
from djoek.api import app
from djoek.models import Song, database
from djoek.player import Player

logger = logging.getLogger(__name__)


@app.on_event("startup")
async def on_startup() -> None:
    loop = asyncio.get_event_loop()

    db_config = parse_dsn(settings.DB_URI)
    db_name = db_config.pop("dbname")
    database.init(db_name, **db_config)
    database.create_tables([Song])
    database.set_allow_sync(False)

    app.state.manager = manager = Manager(database)

    app.state.player = player = Player(manager)
    loop.create_task(player.run())


@app.on_event("shutdown")
async def on_shutdown() -> None:
    app.state.manager.database.close()
    app.state.mpd_client.disconnect()
