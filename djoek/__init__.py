import http.cookies
import logging
import os
import re
from typing import no_type_check

from starlette.staticfiles import StaticFiles

import djoek.settings as settings
from djoek.api import app
from djoek.models import setup_manager, shutdown_manager
from djoek.player import setup_player, shutdown_player

logger = logging.getLogger(__name__)


@no_type_check
def fix_cookies() -> None:
    for c in "@{}":
        if c not in http.cookies._LegalChars:
            http.cookies._LegalChars += c
            http.cookies._is_legal_key = re.compile(
                "[%s]+" % re.escape(http.cookies._LegalChars)
            ).fullmatch


@app.on_event("startup")
async def on_startup() -> None:
    fix_cookies()
    await setup_manager(app)
    await setup_player(app)


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await shutdown_player(app)
    await shutdown_manager(app)


if settings.SERVE_PLAYER:
    player_path = os.path.join(os.path.split(__file__)[0], "..", "player")
    app.mount("/player", StaticFiles(directory=player_path), name="player")
