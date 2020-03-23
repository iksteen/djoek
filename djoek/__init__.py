import asyncio
import logging
import os

from peewee_async import Manager
from psycopg2.extensions import parse_dsn
from starlette.staticfiles import StaticFiles

import djoek.settings as settings
from djoek.api import app
from djoek.models import database
from djoek.player import Player

logger = logging.getLogger(__name__)


@app.on_event("startup")
async def on_startup() -> None:
    loop = asyncio.get_event_loop()

    db_config = parse_dsn(settings.DB_URI)
    db_name = db_config.pop("dbname")
    database.init(db_name, **db_config)
    database.set_allow_sync(False)

    app.state.manager = manager = Manager(database)

    app.state.player = player = Player(manager)
    loop.create_task(player.run())


@app.on_event("shutdown")
async def on_shutdown() -> None:
    app.state.manager.database.close()
    app.state.mpd_client.disconnect()


if settings.SERVE_PLAYER:
    player_path = os.path.join(os.path.split(__file__)[0], "..", "player")
    app.mount("/player", StaticFiles(directory=player_path), name="player")
