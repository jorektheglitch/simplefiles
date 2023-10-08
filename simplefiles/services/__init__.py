from contextlib import asynccontextmanager
from pathlib import Path

from typing import AsyncIterator

from simplefiles.core.entities import Media, TempFile
from simplefiles.storages import UoW


class FilesService:

    def __init__(self, uow: UoW) -> None:
        self.uow = uow

    @asynccontextmanager
    async def tempfile(self) -> AsyncIterator[TempFile]:
        tempfile = await self.uow.files.create_tempfile()
        yield tempfile
        await self.uow.files.terminate_tempfile(tempfile)

    async def materialize(self, tempfile: TempFile, path: str | Path, exists_ok: bool = True) -> Media:
        await self.uow.files.materialize_tempfile(tempfile, path, exists_ok)
