from __future__ import annotations

import dataclasses
import hashlib
import uuid
from contextlib import asynccontextmanager
from datetime import datetime as dt, timezone as tz
from functools import wraps
from pathlib import Path
from typing import AsyncIterator, Awaitable, Callable, TypeVar

import aiofiles
from aiohttp import web
from sqlalchemy.sql import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import joinedload

from simplefiles.config import Config
from simplefiles.core import entities
from simplefiles.core.entities import TempFile, MIMEType, MIMESubtype, AudiosMIME, ImagesMIME, VideosMIME
from .db import Audio, Image, Video, File, FileInfo, Media
from .db import registry


REQUEST_ATTRS = (
    "charset", "content_type", "content_length",
    "cookies", "forwarded", "headers", "http_range", "remote"
)


class MaterialTempFile(TempFile):
    _path: Path
    _file: aiofiles.threadpool.binary.AsyncBufferedIOBase

    def __init__(self, directory: Path | None) -> None:
        tmpdir = directory or (Path.cwd() / "tmp")
        self._path = tmpdir / str(uuid.uuid4())
        self._hasher = hashlib.new("sha256")
        self._size = 0

    @property
    def hash(self) -> bytes:
        return self._hasher.digest()

    @property
    def size(self) -> int:
        return self._size

    @classmethod
    @asynccontextmanager
    async def open(cls: type[_MTF], directory: Path | None = None) -> AsyncIterator[_MTF]:
        tempfile = cls(directory)
        await tempfile._open()
        yield tempfile
        await tempfile.close()
        tempfile._path.unlink(missing_ok=True)

    async def _open(self) -> None:
        self._file = await aiofiles.open(self._path, "wb")

    async def write(self, data: bytes) -> None:
        await self._file.write(data)
        self._hasher.update(data)
        self._size += len(data)

    async def close(self) -> None:
        await self._file.close()

    async def materialize(self, path: str | Path, exists_ok: bool = False) -> None:
        target_path = Path(path)
        if target_path.exists() and not exists_ok:
            raise RuntimeError
        self._path.rename(path)


_MTF = TypeVar("_MTF", bound=MaterialTempFile)


def utcnow() -> dt:
    return dt.now(tz.utc)


def log_request(request: web.Request) -> None:
    print("\n\t".join((
        "Got request from %(remote)s (%(forwarded)s):",
        "headers: %(headers)s",
        "content_length: %(content_length)s",
        "content_type: %(content_type)s",
        "charset: %(charset)s",
        "cookies: %(cookies)s",
        "http_range: %(http_range)s",
        "remote: %(remote)s",
        "forwarded: %(forwarded)s",
    )) % {name: getattr(request, name) for name in REQUEST_ATTRS})


def redirect(target: str) -> Callable[[web.Request], Awaitable[web.StreamResponse]]:
    async def redirector(request: web.Request) -> web.Response:
        return web.Response(status=301, headers={"location": target})
    return redirector


def make_wrapper(
    sessionmaker: async_sessionmaker[AsyncSession],
) -> Callable[
    [Callable[[web.Request, AsyncSession], Awaitable[web.StreamResponse]]],
    Callable[[web.Request], Awaitable[web.StreamResponse]]
]:
    def wrap(
        fn: Callable[[web.Request, AsyncSession], Awaitable[web.StreamResponse]]
    ) -> Callable[[web.Request], Awaitable[web.StreamResponse]]:
        @wraps(fn)
        async def handler(request: web.Request) -> web.StreamResponse:
            async with sessionmaker() as session:
                response = await fn(request, session)
                return response
        return handler
    return wrap


def parse_content_type(string: str) -> tuple[MIMEType, MIMESubtype]:
    try:
        type_str, subtype_str = string.split("/", maxsplit=1)
    except TypeError as e:
        raise ValueError(f"{string!r} is not valid MIME type.") from e
    mime_type = MIMEType(type_str)
    SubType: type[MIMESubtype] = str
    match mime_type:
        case MIMEType.AUDIO: SubType = AudiosMIME
        case MIMEType.IMAGE: SubType = ImagesMIME
        case MIMEType.VIDEO: SubType = VideosMIME
    try:
        mime_subtype = SubType(subtype_str)
    except ValueError:
        mime_subtype = subtype_str
    return mime_type, mime_subtype


async def store(request: web.Request, session: AsyncSession) -> web.StreamResponse:
    log_request(request)
    parts = await request.multipart()
    async for part in parts:
        print()
        print(
            "Got part!",
            f"Name: {part.name}",
            f"Filename: {part.filename}",
            f"Headers: {part.headers}",
            sep="\n\t"
        )
        content_type = part.headers.get("Content-Type", "application/octet-stream")
        mime_type, mime_subtype = parse_content_type(content_type)
        file_name = part.filename
        if file_name is None:
            raise web.HTTPBadRequest(text="'name' field of 'Content-Disposition' header is not set")
        if part.name == 'file':
            async with MaterialTempFile.open() as tmp:
                while chunk := await part.read_chunk(1024*1):
                    await tmp.write(chunk)
                file_hash = tmp.hash.hex()
                file_path = Path.cwd() / "tmp" / file_hash
                await tmp.materialize(file_path, exists_ok=True)
            file = FileInfo(file_path, file_hash, tmp.size)
            try:
                session.add(file)
                await session.commit()
            except IntegrityError:
                await session.rollback()
                file = await session.get(FileInfo, file_hash)  # type: ignore
            media: entities.Media
            match mime_type:
                case MIMEType.APPLICATION: media = File(file_name, file, mime_subtype, utcnow())
                case MIMEType.AUDIO: media = Audio(file_name, file, mime_subtype, utcnow())
                case MIMEType.CHEMICAL: media = File(file_name, file, mime_subtype, utcnow())
                case MIMEType.FONT: media = File(file_name, file, mime_subtype, utcnow())
                case MIMEType.IMAGE: media = Image(file_name, file, mime_subtype, utcnow())
                case MIMEType.VIDEO: media = Video(file_name, file, mime_subtype, utcnow())
                case _: media = File(file_name, file, mime_subtype, utcnow())
            try:
                session.add(media)
            finally:
                await session.commit()
            print(f"\tHash: {tmp.hash.hex()}\n\tSize: {tmp.size}")
        if part.filename == "7oYT8NfEETQ.jpg":
            raise RuntimeError
    print()
    return web.json_response({})


async def show(request: web.Request, session: AsyncSession) -> web.StreamResponse:
    data = await request.json()
    if not isinstance(data, dict):
        raise web.HTTPBadRequest()
    id = data.get("id")
    if not isinstance(id, int):
        raise web.HTTPBadRequest()
    media_info = await session.get(Media, id)
    if media_info is None:
        raise web.HTTPNotFound()
    media: Media | None
    match media_info.type:
        case MIMEType.AUDIO: media = await session.get(Audio, id)
        case MIMEType.IMAGE: media = await session.get(Image, id)
        case MIMEType.VIDEO: media = await session.get(Video, id)
        case _: media = await session.get(File, id)
    if media is None:
        raise web.HTTPNotFound()
    info = dataclasses.asdict(media)
    return web.json_response(info)


async def download(request: web.Request, session: AsyncSession) -> web.StreamResponse:
    data = request.query
    id_raw = data.get("id")
    if id_raw is None:
        raise web.HTTPBadRequest()
    try:
        id = int(id_raw)
    except ValueError:
        raise web.HTTPBadRequest()
    media_info = await session.get(Media, id)
    if media_info is None:
        raise web.HTTPNotFound()
    media: Media | None
    match media_info.type:
        case MIMEType.AUDIO: media = await session.get(Audio, id)
        case MIMEType.IMAGE: media = await session.get(Image, id)
        case MIMEType.VIDEO: media = await session.get(Video, id)
        case _: media = await session.get(File, id)
    if media is None:
        raise web.HTTPNotFound()
    file_path = Path.cwd() / "tmp" / media.info.hash
    response = web.StreamResponse(
        status=200,
        headers={
            "Content-Disposition": f"attachment; filename={media.name}",
            "Content-Type": f"{media.type}/{media.subtype}",
            "Content-Length": str(media.info.size),
        },
    )
    await response.prepare(request)
    CHUNK_SIZE = 64*1024
    async with aiofiles.open(file_path, "rb") as file:
        chunk = await file.read(CHUNK_SIZE)
        while chunk:
            await response.write(chunk)
            chunk = await file.read(CHUNK_SIZE)
    return response


async def create_app(config: Config) -> web.Application:
    app = web.Application()
    engine = create_async_engine("sqlite+aiosqlite:///tmp/test.db")
    async with engine.begin() as conn:
        await conn.execute(text("PRAGMA foreign_keys = 1"))
        await conn.run_sync(registry.metadata.create_all)
    sessions_factory = async_sessionmaker(engine, class_=AsyncSession)
    wrap = make_wrapper(sessions_factory)
    static_dir = Path.cwd() / "webui"
    app.router.add_get("/", redirect("/index.html"))
    app.router.add_static("/", static_dir)
    app.router.add_post("/api/store", wrap(store))
    app.router.add_get("/api/show", wrap(show))
    app.router.add_get("/api/download", wrap(download))
    return app
