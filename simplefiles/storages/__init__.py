from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from simplefiles.core.entities import TempFile


class UoW:
    files: FilesStorage


class DB(ABC):
    pass


class FilesStorage(ABC):

    @abstractmethod
    async def create_tempfile(self) -> TempFile:
        pass

    @abstractmethod
    async def materialize_tempfile(self, tempfile: TempFile, path: str | Path, exists_ok: bool = False) -> None:
        pass

    @abstractmethod
    async def terminate_tempfile(self, tempfile: TempFile) -> None:
        pass
