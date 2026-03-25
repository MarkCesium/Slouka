import logging
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, PostgresDsn
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).parent.parent.parent


class LoggingConfig(BaseModel):
    level: Literal[
        "debug",
        "info",
        "warning",
        "error",
        "critical",
    ] = "info"
    format: str = (
        "[%(asctime)s.%(msecs)03d] %(module)10s:%(lineno)-3d %(levelname)-7s - %(message)s"
    )
    date_format: str = "%Y-%m-%d %H:%M:%S"

    @property
    def level_value(self) -> int:
        return logging.getLevelNamesMapping()[self.level.upper()]


class PostgresConfig(BaseModel):
    url: PostgresDsn = Field(...)
    echo: bool = Field(default=False)
    echo_pool: bool = Field(default=False)
    pool_size: int = Field(default=50)
    max_overflow: int = Field(default=10)
    pool_pre_ping: bool = Field(default=True)
    pool_timeout: int = Field(default=30)


class TelegramConfig(BaseModel):
    token: str = Field(...)


class VerbumConfig(BaseModel):
    url: str = Field(...)


class RedisConfig(BaseModel):
    url: str = Field(...)


class Settings(BaseSettings):
    logging: LoggingConfig = Field(...)
    telegram: TelegramConfig = Field(...)
    verbum: VerbumConfig = Field(...)
    database: PostgresConfig = Field(...)
    redis: RedisConfig = Field(...)

    class Config:
        env_file = BASE_DIR / ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"
