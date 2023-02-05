from __future__ import annotations

from dataclasses import dataclass

from typing import Any, Mapping


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


def create_from_mapping(mapping: Mapping[str, Mapping[str, Any]]) -> Config:
    app_config = mapping.get("app")
    db_config = mapping.get("db")
    if app_config is None:
        raise ValueError("Missing 'app' key in config")
    if db_config is None:
        raise ValueError("Missing 'db' key in config")
    app = ApplicationOptions(**app_config)
    db = DBOptions(**db_config)
    return Config(app, db)
