from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    """Application configuration, read from the environment.

    Keeping configuration in the environment (instead of in code) is one of the
    twelve-factor principles: the same image runs in dev, CI and production and
    only the environment differs.
    """

    database_url: str | None
    version: str
    log_level: str

    @classmethod
    def from_env(cls) -> Config:
        return cls(
            # Empty string is treated like "unset" so that an empty compose
            # variable does not silently produce a broken DSN.
            database_url=os.environ.get("DATABASE_URL") or None,
            version=os.environ.get("APP_VERSION", "0.0.0-dev"),
            log_level=os.environ.get("LOG_LEVEL", "INFO").upper(),
        )
