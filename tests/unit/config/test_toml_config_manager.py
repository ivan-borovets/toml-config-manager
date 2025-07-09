import logging
import textwrap
from collections.abc import Iterator
from copy import deepcopy
from pathlib import Path

import pytest

from config.toml_config_manager import (
    ENV_VAR_NAME,
    DirContents,
    LoggingLevel,
    ValidEnvs,
    configure_logging,
    get_current_env,
    load_full_config,
    merge_dicts,
    read_config,
    validate_env,
    validate_logging_level,
)


@pytest.fixture
def clean_logging() -> Iterator[None]:
    try:
        yield
    finally:
        logging.getLogger().handlers.clear()


@pytest.mark.parametrize("level", ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
def test_validate_logging_level_valid(level):
    assert validate_logging_level(level=level) == level


@pytest.mark.parametrize("level", ["", "debug", "INVALID_LEVEL", "INFOO"])
def test_validate_logging_level_invalid(level):
    with pytest.raises(ValueError):
        validate_logging_level(level=level)


@pytest.mark.parametrize(
    ("lvl_given", "lvl_expected"),
    [
        (LoggingLevel.DEBUG, logging.DEBUG),
        (LoggingLevel.INFO, logging.INFO),
        (LoggingLevel.WARNING, logging.WARNING),
        (LoggingLevel.ERROR, logging.ERROR),
        (LoggingLevel.CRITICAL, logging.CRITICAL),
    ],
)
@pytest.mark.usefixtures("clean_logging")
def test_logger_uses_given_level(
    lvl_given: LoggingLevel,
    lvl_expected: int,
) -> None:
    logger = logging.getLogger()

    configure_logging(level=lvl_given)

    assert logger.level == lvl_expected


@pytest.mark.parametrize("env", list(ValidEnvs))
def test_returns_enum_for_correct_env_string(env: ValidEnvs) -> None:
    assert validate_env(env=env) == env


@pytest.mark.parametrize(
    "env",
    ["Incorrect", None],
)
def test_raises_for_incorrect_env_string_or_none(env: str | None) -> None:
    with pytest.raises(ValueError):
        validate_env(env=env)


@pytest.mark.parametrize("env_str", list(ValidEnvs))
def test_reads_and_validates_env_var(
    env_str: ValidEnvs,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(ENV_VAR_NAME, str(env_str))

    assert get_current_env() == env_str


def test_reader_returns_dict_for_valid_toml(tmp_path: Path) -> None:
    cfg_file = tmp_path / "config.toml"
    fake_cfg_text = textwrap.dedent("""\
        [database]
        USER = "test_postgres"
        PORT = 1234
    """)
    cfg_file.write_text(fake_cfg_text, encoding="utf-8")

    result = read_config(
        env=ValidEnvs.DEV,
        config=DirContents.CONFIG_NAME,
        dir_paths={ValidEnvs.DEV: tmp_path},
    )

    assert result == {"database": {"USER": "test_postgres", "PORT": 1234}}


def test_reader_raises_for_missing_dir() -> None:
    with pytest.raises(FileNotFoundError):
        read_config(
            env=ValidEnvs.DEV,
            config=DirContents.CONFIG_NAME,
            dir_paths={ValidEnvs.DEV: Path("wrong_path")},
        )


def test_reader_raises_for_missing_env_path() -> None:
    with pytest.raises(FileNotFoundError):
        read_config(
            env=ValidEnvs.PROD,
            config=DirContents.CONFIG_NAME,
            dir_paths={},
        )


def test_merges_flat_dicts() -> None:
    assert merge_dicts(dict1={"a": 1}, dict2={"b": 2}) == {"a": 1, "b": 2}


def test_merges_nested_dicts() -> None:
    d1 = {"db": {"host": "localhost"}}
    d2 = {"db": {"port": 5432}}

    assert merge_dicts(dict1=d1, dict2=d2) == {
        "db": {"host": "localhost", "port": 5432}
    }


def test_merger_overwrites_values_to_latest() -> None:
    d1 = {"a": 1}
    d2 = {"a": {"nested": True}}

    assert merge_dicts(dict1=d1, dict2=d2) == {"a": {"nested": True}}


def test_merger_does_not_mutate_inputs() -> None:
    dict1 = {"a": {"x": 1}, "b": {"z": 3}}
    dict2 = {"a": {"y": 2}, "c": {"w": 4}}
    dict1_copy = deepcopy(dict1)
    dict2_copy = deepcopy(dict2)

    merge_dicts(dict1=dict1, dict2=dict2)

    assert dict1 == dict1_copy
    assert dict2 == dict2_copy


def test_full_loader_merges_config_and_secrets(tmp_path: Path) -> None:
    # Arrange
    config_file = tmp_path / "config.toml"
    config_text = textwrap.dedent("""\
        [db]
        USER = "admin"
        PORT = 5432
    """)
    config_file.write_text(config_text, encoding="utf-8")

    secrets_file = tmp_path / ".secrets.toml"
    secrets_text = textwrap.dedent("""\
        [db]
        PASSWORD = "secret"
    """)
    secrets_file.write_text(secrets_text, encoding="utf-8")

    # Act
    result = load_full_config(
        env=ValidEnvs.DEV,
        dir_paths={ValidEnvs.DEV: tmp_path},
    )

    # Assert
    assert result == {
        "db": {
            "USER": "admin",
            "PORT": 5432,
            "PASSWORD": "secret",
        }
    }


def test_full_loader_skips_missing_secrets(tmp_path: Path) -> None:
    config_file = tmp_path / "config.toml"
    config_text = textwrap.dedent("""\
        [db]
        USER = "admin"
        PORT = 5432
    """)
    config_file.write_text(config_text, encoding="utf-8")

    result = load_full_config(
        env=ValidEnvs.DEV,
        dir_paths={ValidEnvs.DEV: tmp_path},
    )

    assert result == {
        "db": {
            "USER": "admin",
            "PORT": 5432,
        }
    }
