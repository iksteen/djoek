import logging
import os

from starlette.staticfiles import StaticFiles

import djoek.settings as settings
from djoek.api import app
from djoek.models import setup_manager, shutdown_manager
from djoek.player import setup_player, shutdown_player

logger = logging.getLogger(__name__)


@app.on_event("startup")
async def on_startup() -> None:
    await setup_manager(app)
    await setup_player(app)


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await shutdown_player(app)
    await shutdown_manager(app)


if settings.SERVE_PLAYER:
    player_path = os.path.join(os.path.split(__file__)[0], "..", "player")
    app.mount("/player", StaticFiles(directory=player_path), name="player")
