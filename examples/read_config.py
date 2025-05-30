import logging
import os
from typing import Literal, NewType, Self, cast

from pydantic import (
    BaseModel,
    Field,
    PostgresDsn as PydanticPostgresDsn,
    field_validator,
)

from config.toml_config_manager import (
    ValidEnvs,
    configure_logging,
    get_current_env,
    load_full_config,
)

log = logging.getLogger(__name__)

PostgresDsn = NewType("PostgresDsn", str)


class PostgresSettings(BaseModel):
    user: str = Field(alias="USER")
    password: str = Field(alias="PASSWORD")
    db: str = Field(alias="DB")
    host: str = Field(alias="HOST")
    port: int = Field(alias="PORT")
    driver: str = Field(alias="DRIVER")

    @field_validator("host")
    @classmethod
    def override_host_from_env(cls, v: str) -> str:
        postgres_host_env = os.environ.get("POSTGRES_HOST")
        if postgres_host_env:
            return postgres_host_env
        return v

    @field_validator("port")
    @classmethod
    def validate_port_range(cls, v: int) -> int:
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v

    @property
    def dsn(self) -> PostgresDsn:
        return cast(
            PostgresDsn,
            str(
                PydanticPostgresDsn.build(
                    scheme=f"postgresql+{self.driver}",
                    username=self.user,
                    password=self.password,
                    host=self.host,
                    port=self.port,
                    path=self.db,
                ),
            ),
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
    configure_logging()

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
