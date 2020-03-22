from base64 import urlsafe_b64encode

from peewee import AutoField, Model, TextField
from peewee_asyncext import PooledPostgresqlExtDatabase
from playhouse.postgres_ext import ArrayField, TSVectorField

database = PooledPostgresqlExtDatabase(None)


class Song(Model):
    class Meta:
        database = database

    id = AutoField()
    title = TextField()
    tags = ArrayField(field_class=TextField)
    search_field = TSVectorField()
    external_id = TextField(unique=True)
    extension = TextField()

    @property
    def filename(self) -> str:
        basename = (
            urlsafe_b64encode(self.external_id.encode("utf-8"))
            .rstrip(b"=")
            .decode("utf-8")
        )
        return f"{basename}{self.extension}"
