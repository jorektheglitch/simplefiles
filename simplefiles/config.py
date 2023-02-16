from __future__ import annotations

from dataclasses import dataclass

from typing import Any, Mapping

import dataclass_factory


FACTORY = dataclass_factory.Factory()


@dataclass
class Config:
    app: ApplicationOptions
    db: DBOptions
    serve_static: bool = False


@dataclass
class ApplicationOptions:
    host: str = "localhost"
    port: int = 8080


@dataclass
class DBOptions:
    pass


def create_from_mapping(mapping: Mapping[str, Any]) -> Config:
    return FACTORY.load(mapping, Config)
