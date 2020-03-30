import asyncio
import os

import mutagen
import peewee
from psycopg2.errors import UndefinedColumn, UndefinedTable
from psycopg2.extensions import parse_dsn

import djoek.settings as settings
from djoek.models import Song, User, database
from djoek.mpdclient import MPDClient


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

    async def update() -> None:
        async with MPDClient(settings.MPD_HOST) as client:
            await client.execute("update")

    asyncio.run(update())


def migrate_preview_url() -> None:
    database.execute_sql(
        """
        ALTER TABLE song ADD COLUMN preview_url TEXT;
        UPDATE song
            SET preview_url = 'http://youtu.be/' || SPLIT_PART(external_id, ':', 2)
            WHERE SPLIT_PART(external_id, ':', 1) = 'youtube';
        """
    )


def migrate_duration() -> None:
    database.execute_sql(
        """
        ALTER TABLE song ADD COLUMN duration NUMERIC(10, 5)
        """
    )
    for song in Song.select():
        path = os.path.join(settings.MUSIC_DIR, song.filename)
        try:
            m = mutagen.File(path)
            song.duration = m.info.length
            song.save(only={"duration"})
        except Exception as e:
            print(f"Skipping {song.title} ({e})")


def table_exists(table_name: str) -> bool:
    try:
        database.execute_sql(f'SELECT 1 FROM "{table_name}"')
    except peewee.ProgrammingError as e:
        if isinstance(e.orig, UndefinedTable):
            database.rollback()
            return False
        else:
            raise
    return True


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


def migrate_submitter() -> None:
    database.execute_sql(
        """
        ALTER TABLE song ADD COLUMN user_id INTEGER REFERENCES "user"(id) ON DELETE SET NULL;
        """
    )


if __name__ == "__main__":
    db_config = parse_dsn(settings.DB_URI)
    database.init(db_config.pop("dbname"), **db_config)

    if not table_exists("user"):
        database.create_tables([User])

    if not table_exists("song"):
        database.create_tables([Song])

    if not column_exists("extension"):
        migrate_extension()

    if not column_exists("preview_url"):
        migrate_preview_url()

    if not column_exists("duration"):
        migrate_duration()

    if not column_exists("user_id"):
        migrate_submitter()
