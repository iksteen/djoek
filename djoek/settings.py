import os

import dotenv

dotenv.load_dotenv()

MPD_HOST = os.environ.get("DJOEK_MPD_HOST", "localhost")
DB_URI = os.environ.get("DJOEK_DB_URI", "postgres:///djoek")
GOOGLE_API_KEY = os.environ.get("DJOEK_GOOGLE_API_KEY", "")
MUSIC_DIR = os.environ.get("DJOEK_MUSIC_DIR", "./music")

AUTH0_DOMAIN = os.environ.get("DJOEK_AUTH0_DOMAIN", "")
AUTH0_AUDIENCE = os.environ.get("DJOEK_AUTH0_AUDIENCE", "")
AUTH0_PARTIES = set(os.environ.get("DJOEK_AUTH0_PARTIES", "").split(","))

REMEMBER_RECENT = int(os.environ.get("DJOEK_REMEMBER_RECENT", "25"))
