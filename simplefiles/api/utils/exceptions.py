from __future__ import annotations

from abc import ABC

from typing import ClassVar

from .response import Response, JSON


class APIError(Exception, Response[JSON], ABC):
    status_code: ClassVar[int]

    def __init__(
        self,
        msg: str | None = None,
        *,
        payload: JSON = None,
        reason: str | None = None
    ) -> None:
        super().__init__(msg)
        if payload is None and msg is not None:
            self.payload = msg
        else:
            self.payload = payload
        self.reason = reason


class BadRequest(APIError):
    status_code = 400


class Unauthorized(APIError):
    status_code = 401


class Forbidden(APIError):
    status_code = 403


class NotFound(APIError):
    status_code = 404
