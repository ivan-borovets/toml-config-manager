import logging
import os
from typing import Literal, Self

from pydantic import BaseModel, Field, field_validator

from config.toml_config_manager import (
    ENV_VAR_NAME,
    ValidEnvs,
    configure_logging,
    load_full_config,
    validate_env,
)

log = logging.getLogger(__name__)


class PostgresSettings(BaseModel):
    user: str = Field(alias="USER")
    password: str = Field(alias="PASSWORD")
    db: str = Field(alias="DB")
    host: str = Field(alias="HOST")
    port: int = Field(alias="PORT")
    driver: str = Field(alias="DRIVER")

    @field_validator("port")
    @classmethod
    def validate_port_range(cls, v: int) -> int:
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v

    @property
    def dsn(self) -> str:
        return (
            f"{self.driver}://"
            f"{self.user}:"
            f"{self.password}@"
            f"{self.host}:"
            f"{self.port}/"
            f"{self.db}"
        )


class SqlaSettings(BaseModel):
    echo: bool = Field(alias="ECHO")
    echo_pool: bool = Field(alias="ECHO_POOL")
    pool_size: int = Field(alias="POOL_SIZE")
    max_overflow: int = Field(alias="MAX_OVERFLOW")


class LoggingSettings(BaseModel):
    level: Literal[
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL",
    ] = Field(alias="LEVEL")


class Secrets(BaseModel):
    secret_one: str = Field(alias="SECRET_ONE")
    secret_two: str = Field(alias="SECRET_TWO")


def get_current_env() -> ValidEnvs:
    env_value = os.environ.get(ENV_VAR_NAME)
    return validate_env(env=env_value)


class AppSettings(BaseModel):
    postgres: PostgresSettings
    sqla: SqlaSettings
    logs: LoggingSettings
    secrets: Secrets | None = None

    @classmethod
    def from_toml(cls, env: ValidEnvs | None = None) -> Self:
        if env is None:
            env = get_current_env()
        raw_config = load_full_config(env=env)
        log.info("Reading config for environment: '%s'", env)
        return cls.model_validate(raw_config)


def load_settings(env: ValidEnvs | None = None) -> AppSettings:
    return AppSettings.from_toml(env=env)


if __name__ == "__main__":
    configure_logging(level="INFO")

    try:
        current_env = get_current_env()
        log.info("Current environment: '%s'", current_env)

        app_settings = load_settings(env=current_env)
        log.info("PostgreSQL settings: '%s'", app_settings.postgres)
        log.info("Database URL: '%s'", app_settings.postgres.dsn)
        log.info("SQLAlchemy settings: '%s'", app_settings.sqla)
        log.info("Log level: '%s'", app_settings.logs.level)
        if app_settings.secrets:
            log.info("Secret values: '%s'", app_settings.secrets)
        else:
            log.info("No secrets was found in config")

    except Exception as e:
        log.error("Failed to load settings: '%s'", e)
