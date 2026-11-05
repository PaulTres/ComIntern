"""`comintern`: run the API with uvicorn on RUN__HOST:RUN__PORT."""

import uvicorn

from comintern.api.app import create_app
from comintern.configuration.config import get_settings

GRACEFUL_SHUTDOWN_SECONDS = 30


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        create_app(cors_settings=settings.cors),
        host=settings.run.host,
        port=settings.run.port,
        log_level=settings.logging.level.lower(),
        timeout_graceful_shutdown=GRACEFUL_SHUTDOWN_SECONDS,
    )


if __name__ == "__main__":
    main()
