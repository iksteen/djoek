import os

import peewee
from mpd import MPDClient
from psycopg2.errors import UndefinedColumn
from psycopg2.extensions import parse_dsn

import djoek.settings as settings
from djoek.models import Song, database


def migrate_extension() -> None:
    database.execute_sql(
        """
        ALTER TABLE song ADD COLUMN extension TEXT;
        UPDATE song SET extension = '.m4a';
        ALTER TABLE song ALTER COLUMN extension SET NOT NULL;
        """
    )

    for song in Song.select():
        old_path = os.path.join(settings.MUSIC_DIR, f"{song.id}{song.extension}")
        new_path = os.path.join(settings.MUSIC_DIR, song.filename)
        if os.path.exists(old_path):
            if not os.path.exists(new_path):
                os.rename(old_path, new_path)
            else:
                os.unlink(old_path)

    client = MPDClient()
    client.connect(settings.MPD_HOST, 6600)
    client.update()
    client.idle("update")


def migrate_preview_url() -> None:
    database.execute_sql(
        """
        ALTER TABLE song ADD COLUMN preview_url TEXT;
        UPDATE song
            SET preview_url = 'http://youtu.be/' || SPLIT_PART(external_id, ':', 2)
            WHERE SPLIT_PART(external_id, ':', 1) = 'youtube';
        """
    )


def column_exists(column_name: str) -> bool:
    try:
        database.execute_sql(f'SELECT "{column_name}" FROM song;')
    except peewee.ProgrammingError as e:
        if isinstance(e.orig, UndefinedColumn):
            database.rollback()
            return False
        else:
            raise
    return True


if __name__ == "__main__":
    db_config = parse_dsn(settings.DB_URI)
    database.init(db_config.pop("dbname"), **db_config)
    database.create_tables([Song])

    if not column_exists("extension"):
        migrate_extension()

    if not column_exists("preview_url"):
        migrate_preview_url()
