from dataclasses import dataclass, field
from datetime import timedelta as td
from pathlib import Path
from typing import Any, ClassVar

from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy import CheckConstraint, ForeignKeyConstraint
from sqlalchemy import DateTime, Enum, Integer, String
from sqlalchemy import MetaData
from sqlalchemy import orm
from sqlalchemy.sql import Selectable
from sqlalchemy.types import TypeDecorator
from sqlalchemy.engine import Dialect

from simplefiles.core._types import AudiosMIME, ImagesMIME, VideosMIME, MIMEType
from simplefiles.core import entities


NAMING = {
    'ix': 'index_%(table_name)s_%(column_0_N_name)s',
    'uq': 'unique_%(table_name)s_%(column_0_N_name)s',
    'ck': 'check_%(table_name)s_%(column_0_N_name)s',
    'fk': 'foreign_%(table_name)s_%(column_0_N_name)s_%(referred_table_name)s_%(referred_column_0_N_name)s',
    'pk': 'primary_%(table_name)s',
}


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


class MediaResolution(TypeDecorator[entities.Resolution]):
    impl = String
    cache_ok = True

    def process_bind_param(self, value: entities.Resolution | None, dialect: Dialect) -> str | None:
        if value is None:
            return None
        return f"{value.width}x{value.height}"

    def process_result_value(self, value: str | None, dialect: Dialect) -> entities.Resolution | None:
        if value is None:
            return None
        width, height = map(int, value.split("x"))
        return entities.Resolution(width, height)


registry = orm.registry(metadata=MetaData(naming_convention=NAMING))


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
    Column("media_type", Enum(MIMEType), default=MIMEType.AUDIO),
    Column("subtype", Enum(AudiosMIME)),
    Column("length", MediaLength),
    ForeignKeyConstraint(
        ("audio_id", "media_type"),
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
    Column("media_type", Enum(MIMEType), default=MIMEType.IMAGE),
    Column("subtype", Enum(ImagesMIME)),
    Column("resolution", MediaResolution),
    Column("preview_id", Integer),
    ForeignKeyConstraint(
        ("image_id", "media_type"),
        (medias.c.media_id, medias.c.media_type)
    ),
    CheckConstraint(
        "subtype IN ('JPEG', 'PNG')"
    )
)

videos = Table(
    "videos",
    registry.metadata,
    Column("video_id", Integer, primary_key=True),
    Column("media_type", Enum(MIMEType), default=MIMEType.VIDEO),
    Column("subtype", Enum(VideosMIME)),
    Column("resolution", MediaResolution),
    Column("length", MediaLength),
    ForeignKeyConstraint(
        ("video_id", "media_type"),
        (medias.c.media_id, medias.c.media_type)
    ),
    CheckConstraint(
        "subtype IN ('MP4', 'MPEG', 'OGG')"
    )
)

files = Table(
    "files",
    registry.metadata,
    Column("file_id", Integer, primary_key=True),
    Column("media_type", Enum(MIMEType), default=MIMEType.APPLICATION),
    Column("subtype", String),
    ForeignKeyConstraint(
        ("file_id", "media_type"),
        (medias.c.media_id, medias.c.media_type)
    ),
)


@registry.mapped
@dataclass
class FileInfo(entities.FileInfo):
    __table__ = file_infos


@registry.mapped
@dataclass
class Media(entities.Media):
    media_id: int = field(init=False)

    __table__: ClassVar[Selectable] = medias

    __mapper_args__: ClassVar[dict[str, Any]] = {  # type: ignore
        # "polymorphic_identity": "medias",
        "polymorphic_on": "media_type",
        "properties": {
            "info": orm.relationship(FileInfo)
        },
    }


@registry.mapped
@dataclass
class Image(Media, entities.Image):
    __table__ = images
    __mapper_args__ = {
        "polymorphic_identity": MIMEType.IMAGE,
        "properties": {
            "info": orm.relationship(FileInfo)
        },
    }

    @property
    async def preview(self) -> entities.Preview | None:
        return None

    def __post_init__(self) -> None:
        self.media_type = self.type


@registry.mapped
@dataclass
class Audio(Media, entities.Audio):
    __table__ = audios
    __mapper_args__ = {
        "polymorphic_identity": MIMEType.AUDIO,
        "properties": {
            "info": orm.relationship(FileInfo)
        },
    }

    def __post_init__(self) -> None:
        self.media_type = self.type


@registry.mapped
@dataclass
class Video(Media, entities.Video):
    __table__ = videos
    __mapper_args__ = {
        "polymorphic_identity": MIMEType.VIDEO,
        "properties": {
            "info": orm.relationship(FileInfo)
        },
    }

    @property
    async def preview(self) -> entities.Preview:
        return None  # type: ignore

    def __post_init__(self) -> None:
        self.media_type = self.type


@registry.mapped
@dataclass
class File(Media, entities.File):
    __table__ = files
    __mapper_args__ = {
        "polymorphic_identity": MIMEType.APPLICATION,
        "properties": {
            "info": orm.relationship(FileInfo)
        },
    }

    def __post_init__(self) -> None:
        self.media_type = self.type
