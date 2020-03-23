import os

import dotenv

dotenv.load_dotenv()

SERVE_PLAYER = os.environ.get("DJOEK_SERVE_PLAYER", "false").lower() in (
    "true",
    "t",
    "yes",
    "y",
    "1",
)

MPD_HOST = os.environ.get("DJOEK_MPD_HOST", "localhost")
DB_URI = os.environ.get("DJOEK_DB_URI", "postgres:///djoek")
MUSIC_DIR = os.environ.get("DJOEK_MUSIC_DIR", "./music")

AUTH0_DOMAIN = os.environ.get("DJOEK_AUTH0_DOMAIN", "")
AUTH0_AUDIENCE = os.environ.get("DJOEK_AUTH0_AUDIENCE", "")
AUTH0_PARTIES = set(os.environ.get("DJOEK_AUTH0_PARTIES", "").split(","))

REMEMBER_RECENT = int(os.environ.get("DJOEK_REMEMBER_RECENT", "25"))

GOOGLE_API_KEY = os.environ.get("DJOEK_GOOGLE_API_KEY", "")
SOUNDCLOUD_CLIENT_ID = os.environ.get("DJOEK_SOUNDCLOUD_CLIENT_ID", "")
