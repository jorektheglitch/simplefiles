from dataclasses import dataclass
from datetime import timedelta as td
from pathlib import Path

from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy import CheckConstraint, ForeignKeyConstraint
from sqlalchemy import DateTime, Enum, Integer, String
from sqlalchemy import orm
from sqlalchemy import join
from sqlalchemy.types import TypeDecorator
from sqlalchemy.engine import Dialect

from simplefiles.core._types import AudiosMIME, ImagesMIME, MIMEType
from simplefiles.core import entities


class FilePath(TypeDecorator[Path]):

    impl = String

    cache_ok = True

    def process_bind_param(self, value: Path | None, dialect: Dialect) -> str | None:
        if value is None:
            return None
        return str(value)

    def process_result_value(self, value: str | None, dialect: Dialect) -> Path | None:
        if value is None:
            return None
        return Path(value)


class MediaLength(TypeDecorator[td]):
    impl = String
    cache_ok = True

    def process_bind_param(self, value: td | None, dialect: Dialect) -> str | None:
        if value is None:
            return None
        days = value.days
        minutes, seconds = divmod(value.seconds, 60)
        hours, minutes = divmod(minutes, 60)
        microseconds = value.microseconds
        return f"{days}:{hours}:{minutes}:{seconds}.{microseconds:.3f}"

    def process_result_value(self, value: str | None, dialect: Dialect) -> td | None:
        if value is None:
            return None
        days, hours, minutes, seconds = value.split(":")
        total_seconds = int(hours)*3600 + int(minutes)*60 + float(seconds)
        return td(days=int(days), seconds=total_seconds)


registry = orm.registry()


file_infos = Table(
    "files_info",
    registry.metadata,
    Column("hash", String, primary_key=True),
    Column("path", FilePath),
    Column("size", Integer)
)

medias = Table(
    "medias",
    registry.metadata,
    Column("media_id", Integer, primary_key=True, autoincrement=True),
    Column("media_type", Enum(MIMEType)),
    Column("name", String),
    Column("file_hash", String, ForeignKey(file_infos.c.hash)),
    Column("loaded_at", DateTime),
)

audios = Table(
    "audios",
    registry.metadata,
    Column("audio_id", Integer, primary_key=True),
    Column("audio_type", Enum(MIMEType), default=MIMEType.AUDIO),
    Column("subtype", Enum(AudiosMIME)),
    Column("length", MediaLength),
    ForeignKeyConstraint(
        ("audio_id", "audio_type"),
        (medias.c.media_id, medias.c.media_type)
    ),
    CheckConstraint(
        "subtype IN ('MPEG', 'OGG')"
    )
)

images = Table(
    "images",
    registry.metadata,
    Column("image_id", Integer, primary_key=True),
    Column("image_type", Enum(MIMEType), default=MIMEType.IMAGE),
    Column("subtype", Enum(ImagesMIME)),
    Column("preview_id", Integer),
    ForeignKeyConstraint(
        ("image_id", "image_type"),
        (medias.c.media_id, medias.c.media_type)
    ),
    CheckConstraint(
        "subtype IN ('JPEG', 'PNG')"
    )
)


@registry.mapped
@dataclass
class Media(entities.Media):
    __table__ = medias


@registry.mapped
@dataclass
class FileInfo(entities.FileInfo):
    __table__ = file_infos


@registry.mapped
@dataclass
class Image(entities.Image):
    __table__ = join(medias, images)

    file_hash: str

    @property
    async def file_info(self) -> entities.FileInfo:
        return None  # type: ignore

    @property
    async def preview(self) -> entities.Preview | None:
        return None

    def __post_init__(self) -> None:
        self.media_type = self.type


@registry.mapped
@dataclass
class Audio(entities.Audio):
    __table__ = join(medias, audios)

    file_hash: str

    @property
    async def file_info(self) -> entities.FileInfo:
        return None  # type: ignore

    def __post_init__(self) -> None:
        self.media_type = self.type
