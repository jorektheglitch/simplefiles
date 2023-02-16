from pathlib import Path

from aiohttp import web

from .app import create_app
from .config import create_from_mapping, Config


def run(config: Config) -> None:
    app = create_app(config)
    web.run_app(app, host=config.app.host, port=config.app.port)


if __name__ == "__main__":
    from argparse import ArgumentParser

    import tomlkit

    parser = ArgumentParser(description='MicroChat server')
    parser.add_argument(
        '--config', dest='config',
        type=Path, required=False,
        help='Path to config file'
    )

    args = parser.parse_args()
    config_path: Path | None = args.config
    if not config_path:
        parser.print_help()
    with config_path.open() as config_file:
        config_toml = tomlkit.load(config_file)
    config = create_from_mapping(config_toml)
    run(config)
