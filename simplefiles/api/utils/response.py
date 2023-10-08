from __future__ import annotations
from abc import ABC

from dataclasses import dataclass
import enum
import json
import functools

from typing import Any, AsyncIterable, Generic, Mapping, Sequence, TypeVar

from .types import Renderable, JSON


RenderableBody = Renderable[JSON] | Sequence[Renderable[JSON]] | Mapping[str, Renderable[JSON]]
# Sequence and Mapping used instead of list and dict because they are invariant (and then it is
# list[EntityChildClass] is not matched by theese union)

T = TypeVar("T")  # , bound=RenderableBody | JSON | AsyncIterable[bytes] | Queue[Renderable[str]], covariant=True)


class Status(enum.Enum):
    OK = 200
    CREATED = 201
    NO_CONTENT = 204


class HEADER(enum.Enum):
    ContentDisposition = "Content-Disposition"
    ContentType = "Content-Type"


@dataclass
class Response(ABC, Generic[T]):
    payload: T
    status: Status = Status.OK
    reason: str | None = None
    headers: dict[str, str] | None = None

    def __init__(
        self,
        payload: T | None = None,
        status: Status = Status.OK,
        reason: str | None = None,
        headers: dict[HEADER, str] | None = None,
    ) -> None:
        if payload is not None:
            self.payload = payload
        self.status = status
        self.reason = reason
        self.headers = {
            key.value: value for key, value in headers.items()
        } if headers else None

    @property
    def status_code(self) -> int:
        return self.status.value


@dataclass
class JSONResponse(Response[JSON]):
    pass


@dataclass
class StreamResponse(Response[AsyncIterable[bytes]]):
    pass


class APIResponseEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:  # type: ignore  # Any not allowed
        # TODO: make serialization for all entity types
        return super().default(o)


DEFAULT_JSON_DUMPER = functools.partial(json.dumps, cls=APIResponseEncoder)
