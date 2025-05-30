import logging
import os
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from types import MappingProxyType
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from config.toml_config_manager import (
    ValidEnvs,
    configure_logging,
    extract_exported,
    get_current_env,
    get_env_value_by_export_field,
    load_export_fields,
    load_full_config,
    merge_dicts,
    read_config,
    validate_env,
    validate_logging_level,
    write_dotenv_file,
)


@pytest.mark.parametrize("level", ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
def test_validate_logging_level_valid(level):
    assert validate_logging_level(level=level) == level


@pytest.mark.parametrize("level", ["", "debug", "INVALID_LEVEL", "INFOO"])
def test_validate_logging_level_invalid(level):
    with pytest.raises(ValueError):
        validate_logging_level(level=level)


@pytest.mark.parametrize(
    ("level_str", "expected_level"),
    [
        ("DEBUG", logging.DEBUG),
        ("INFO", logging.INFO),
        ("WARNING", logging.WARNING),
        ("ERROR", logging.ERROR),
        ("CRITICAL", logging.CRITICAL),
    ],
)
def test_configure_logging_levels(level_str, expected_level):
    with patch("config.toml_config_manager.logging.basicConfig") as mock:
        configure_logging(level=level_str)

        assert mock.call_args[1]["level"] == expected_level


@pytest.mark.parametrize(
    ("env", "expected_exception"),
    [
        pytest.param(ValidEnvs.LOCAL, None, id="env_correct"),
        pytest.param(None, ValueError, id="env_none"),
        pytest.param("INCORRECT", ValueError, id="env_incorrect"),
    ],
)
def test_validate_env(env, expected_exception):
    if not expected_exception:
        assert validate_env(env=env) == env

    else:
        with pytest.raises(ValueError):
            validate_env(env=env)


def test_get_current_env():
    test_app_env_key = "TEST_APP_ENV_KEY"
    test_app_env_value = "TEST_APP_ENV_VALUE"

    class TestValidEnvs(StrEnum):
        test_app_env_key = test_app_env_value

    with (
        patch("config.toml_config_manager.ENV_VAR_NAME", test_app_env_key),
        patch.dict(os.environ, {test_app_env_key: test_app_env_value}),
        patch("config.toml_config_manager.ValidEnvs", TestValidEnvs),
    ):
        assert get_current_env() == test_app_env_value


def test_read_config(tmp_path):
    config_file = tmp_path / "config.toml"
    config_file.write_text('[database]\nUSER = "test_postgres"\nPORT = 1234\n')

    with patch(
        "config.toml_config_manager.ENV_TO_DIR_PATHS", {ValidEnvs.DEV: tmp_path}
    ):
        result = read_config(env=ValidEnvs.DEV)

        assert result == {"database": {"USER": "test_postgres", "PORT": 1234}}

    with patch(
        "config.toml_config_manager.ENV_TO_DIR_PATHS",
        {ValidEnvs.DEV: Path("wrong_path"), ValidEnvs.PROD: None},
    ):
        with pytest.raises(FileNotFoundError):
            read_config(env=ValidEnvs.DEV)

        with pytest.raises(FileNotFoundError):
            read_config(env=ValidEnvs.PROD)


@pytest.mark.parametrize(
    ("dict1", "dict2", "result"),
    [
        pytest.param(
            {"a": 1, "b": 2},
            {"b": 3, "c": 4},
            {"a": 1, "b": 3, "c": 4},
            id="flat",
        ),
        pytest.param(
            {"a": 1, "b": {"x": 1, "y": 2}},
            {"b": {"y": 3, "z": 4}, "c": 5},
            {"a": 1, "b": {"x": 1, "y": 3, "z": 4}, "c": 5},
            id="nested",
        ),
    ],
)
def test_merge_dicts(dict1, dict2, result):
    assert merge_dicts(dict1=dict1, dict2=dict2) == result


def test_merge_dicts_keep_original():
    original_dict1 = {"a": 1}
    original_dict2 = {"b": 2}

    merge_dicts(dict1=original_dict1, dict2=original_dict2)

    assert original_dict1 == {"a": 1}
    assert original_dict2 == {"b": 2}


def test_load_full_config(tmp_path):
    config_file = tmp_path / "config.toml"
    config_file.write_text('[database]\nUSER = "test_postgres"\nPORT = 1234\n')
    secrets_file = tmp_path / ".secrets.toml"
    secrets_file.write_text(
        '[database]\nPASSWORD = "secret"\n[api]\nKEY = "apikey123"\n',
    )

    with patch(
        "config.toml_config_manager.ENV_TO_DIR_PATHS", {ValidEnvs.DEV: tmp_path}
    ):
        result = load_full_config(env=ValidEnvs.DEV)

        assert result == {
            "database": {"USER": "test_postgres", "PORT": 1234, "PASSWORD": "secret"},
            "api": {"KEY": "apikey123"},
        }

        secrets_file.unlink()

        result_no_secrets = load_full_config(env=ValidEnvs.DEV)

        assert result_no_secrets == {
            "database": {"USER": "test_postgres", "PORT": 1234}
        }


def test_get_env_value_by_export_field():
    config: dict[str, Any] = {
        "database": {"USER": "postgres", "PORT": 5432, "SETTINGS": {"TIMEOUT": 30}},
        "api": {"KEY": "apikey123"},
    }

    assert (
        get_env_value_by_export_field(config=config, field="database.USER")
        == "postgres"
    )
    assert get_env_value_by_export_field(config=config, field="database.PORT") == "5432"
    assert (
        get_env_value_by_export_field(config=config, field="database.SETTINGS.TIMEOUT")
        == "30"
    )
    assert get_env_value_by_export_field(config=config, field="api.KEY") == "apikey123"

    with pytest.raises(KeyError):
        get_env_value_by_export_field(config=config, field="database.PASSWORD")

    config["database"]["COMPLEX"] = {"nested": "value"}

    with pytest.raises(ValueError):
        get_env_value_by_export_field(config=config, field="database.COMPLEX")

    class UnstringableObject:
        def __str__(self):
            raise TypeError

    config["database"]["UNSTRINGABLE"] = UnstringableObject()

    with pytest.raises(ValueError):
        get_env_value_by_export_field(config=config, field="database.UNSTRINGABLE")


def test_extract_exported():
    config = {
        "database": {"USER": "postgres", "PORT": 5432},
        "api": {"KEY": "apikey123", "TIMEOUT": 30},
    }
    export_fields = ["database.USER", "database.PORT", "api.KEY"]

    result = extract_exported(config=config, export_fields=export_fields)

    assert result == {
        "DATABASE_USER": "postgres",
        "DATABASE_PORT": "5432",
        "API_KEY": "apikey123",
    }
    assert not extract_exported(config=config, export_fields=[])
    with pytest.raises(KeyError):
        extract_exported(config=config, export_fields=["database.PASSWORD"])


def test_load_export_fields(tmp_path, monkeypatch):
    config_file = tmp_path / "config.toml"
    config_file.write_text('[database]\nUSER = "postgres"\nPORT = 5432\n')
    export_file = tmp_path / "export.toml"
    export_file.write_text('[export]\nfields = ["database.USER", "database.PORT"]\n')
    fake_dir_paths = MappingProxyType({ValidEnvs.DEV: tmp_path})
    monkeypatch.setattr("config.toml_config_manager.ENV_TO_DIR_PATHS", fake_dir_paths)

    config, export_fields = load_export_fields(env=ValidEnvs.DEV)

    assert config == {"database": {"USER": "postgres", "PORT": 5432}}
    assert export_fields == ["database.USER", "database.PORT"]

    export_file.write_text('[wrong_section]\nfields = ["database.USER"]\n')

    with pytest.raises(ValueError):
        load_export_fields(env=ValidEnvs.DEV)

    export_file.write_text('[export]\nwrong_key = ["database.USER"]\n')

    with pytest.raises(ValueError):
        load_export_fields(env=ValidEnvs.DEV)


def test_write_dotenv_file(tmp_path, monkeypatch):
    export_fields = {
        "DATABASE_USER": "postgres",
        "DATABASE_PORT": "5432",
        "API_KEY": "secret123",
    }
    fake_dir_paths = MappingProxyType({ValidEnvs.DEV: tmp_path})
    monkeypatch.setattr("config.toml_config_manager.ENV_TO_DIR_PATHS", fake_dir_paths)
    monkeypatch.setattr(
        "config.toml_config_manager.BASE_DIR_PATH",
        Path("/fake/base/path"),
    )
    mock_now = datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC)
    monkeypatch.setattr(
        "config.toml_config_manager.datetime",
        MagicMock(now=lambda _: mock_now),
    )

    write_dotenv_file(env=ValidEnvs.DEV, exported_fields=export_fields)

    env_path = tmp_path / f".env.{ValidEnvs.DEV.value}"

    assert env_path.exists()

    content = env_path.read_text()

    assert "# This .env file was automatically generated" in content
    assert f"# Environment: {ValidEnvs.DEV}" in content
    assert "# Generated: 2023-01-01T12:00:00+00:00" in content
    assert "DATABASE_USER=postgres" in content
    assert "DATABASE_PORT=5432" in content
    assert "API_KEY=secret123" in content
