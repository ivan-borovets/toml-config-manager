from types import MappingProxyType

from config.toml_config_manager import ValidEnvs, generate_dotenv, main


def test_generate_dotenv(tmp_path, monkeypatch):
    dev_dir = tmp_path / "dev"
    dev_dir.mkdir()
    config_file = dev_dir / "config.toml"
    config_file.write_text('[database]\nUSER = "postgres"\n')
    export_file = dev_dir / "export.toml"
    export_file.write_text('[export]\nfields = ["database.USER"]\n')
    monkeypatch.setattr(
        "config.toml_config_manager.ENV_TO_DIR_PATHS",
        MappingProxyType({ValidEnvs.DEV: dev_dir}),
    )
    monkeypatch.setattr("config.toml_config_manager.BASE_DIR_PATH", tmp_path)

    generate_dotenv(env=ValidEnvs.DEV)

    env_file = dev_dir / ".env.dev"
    assert env_file.exists()
    content = env_file.read_text()
    assert "DATABASE_USER=postgres" in content


def test_main(tmp_path, monkeypatch):
    config_dir = tmp_path / "config"
    dev_dir = config_dir / "dev"
    dev_dir.mkdir(parents=True)
    config_file = dev_dir / "config.toml"
    config_file.write_text('[database]\nUSER = "postgres"\n')
    export_file = dev_dir / "export.toml"
    export_file.write_text('[export]\nfields = ["database.USER"]\n')
    monkeypatch.setenv("APP_ENV", "dev")
    monkeypatch.setattr("config.toml_config_manager.BASE_DIR_PATH", tmp_path)
    monkeypatch.setattr("config.toml_config_manager.CONFIG_PATH", config_dir)
    monkeypatch.setattr(
        "config.toml_config_manager.ENV_TO_DIR_PATHS",
        MappingProxyType({ValidEnvs.DEV: dev_dir}),
    )

    main()

    env_file = dev_dir / ".env.dev"
    assert env_file.exists()
    content = env_file.read_text()
    assert "DATABASE_USER=postgres" in content
