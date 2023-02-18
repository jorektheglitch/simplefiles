from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime as dt, timedelta as td
from pathlib import Path

from typing import AsyncIterator, ClassVar, Literal, NamedTuple
from typing import TypeVar

from ._types import MIMEType, MIMESubtype
from ._types import AudiosMIME, VideosMIME, ImagesMIME


E = TypeVar("E", bound=Exception)
T = TypeVar("T")


@dataclass
class Media(ABC):
    name: str  # displayed file name
    info: FileInfo
    type: ClassVar[MIMEType]  # MIME type
    subtype: MIMESubtype  # MIME subtype
    loaded_at: dt


M = TypeVar("M", bound=Media)


class Resolution(NamedTuple):
    width: int
    height: int


@dataclass
class Image(Media):
    type: ClassVar[Literal[MIMEType.IMAGE]] = MIMEType.IMAGE
    subtype: ImagesMIME
    resolution: Resolution | None = None

    @property
    @abstractmethod
    async def preview(self) -> Preview | None: ...


@dataclass
class Video(Media):
    type: ClassVar[Literal[MIMEType.VIDEO]] = MIMEType.VIDEO
    subtype: VideosMIME
    resolution: Resolution | None = None
    length: td | None = None

    @property
    @abstractmethod
    async def preview(self) -> Preview | None: ...


@dataclass
class Audio(Media):
    type: ClassVar[Literal[MIMEType.AUDIO]] = MIMEType.AUDIO
    subtype: AudiosMIME
    length: td | None = None
    artist: str | None = None
    album: str | None = None
    track: str | None = None


class File(Media):
    type: ClassVar[Literal[MIMEType.APPLICATION]] = MIMEType.APPLICATION
    subtype: str


@dataclass
class Preview(Media):
    type: ClassVar[Literal[MIMEType.IMAGE]]
    subtype: Literal[ImagesMIME.WEBP]


@dataclass
class FileInfo:
    path: Path
    hash: str
    size: int


class TempFile(ABC):

    @property
    @abstractmethod
    def hash(self) -> bytes:
        pass

    @property
    @abstractmethod
    def size(self) -> int:
        pass

    @asynccontextmanager
    @classmethod
    @abstractmethod
    async def open(cls: type[_TF]) -> AsyncIterator[_TF]:
        tempfile = cls()
        yield tempfile
        await tempfile.close()

    @abstractmethod
    async def write(self, data: bytes) -> None:
        pass

    @abstractmethod
    async def close(self) -> None:
        pass

    @abstractmethod
    async def materialize(self, path: str | Path, exists_ok: bool = False) -> None:
        pass


_TF = TypeVar("_TF", bound=TempFile)
