<p align="center">
  <a href="https://codecov.io/gh/ivan-borovets/toml-to-dotenv">
    <img src="https://codecov.io/gh/ivan-borovets/toml-to-dotenv/graph/badge.svg" alt="Codecov Coverage"/>
  </a>
</p>

Configuration management system for Python projects that uses structured TOML files as the single source of truth, with
support for multiple environments (local, development, production, custom).

Provides both a conversion utility that transforms TOML to environment-specific .env files and a methodology for
applications to read settings directly from the appropriate config directory based on APP_ENV value.

TOML configuration files serve as single source of truth for both application settings and infrastructure configuration.
Based on APP_ENV value, application reads settings directly from appropriate config directory, while .env files are
generated for infrastructure tools like Docker Compose.

Designed as drop-in solution — just copy config directory to project root and use provided Makefile commands.

<p align="center">
  <img src="docs/1.tldr.svg" alt="tldr" />
  <br><em>Figure 1: TL;DR</em>
</p>

# Prerequisites for usage

* Python 3.12
* `rtoml` (`pip install rtoml`)

## Configuration Files

- **config.toml**: Main application settings organized in sections
- **export.toml**: Lists fields to export to .env (`export.fields = ["postgres.USER", "postgres.PASSWORD", ...]`)
- **.secrets.toml**: Optional sensitive data (same format as config.toml, merged with main config)

See `examples/read_config.py` for usage examples.

**Warning**: Despite the approach shown in `examples/read_config.py`, importing code from
`config/toml_config_manager.py` is potentially dangerous.
If you need functionality from this file, copy the relevant code directly into your application instead of importing it.

# Usage

1. Add to `.gitignore`

```gitignore
config/dev/*
config/prod/*
.secrets.*
.env.*
```

2. Copy to the root of your project

* `config/`
* `Makefile` snippets: `make env`, `make dotenv` (and dependencies) or entire `Makefile`

3. [Configure](#configuration-files) local environment

* Create `.secrets.toml` in `config/local` following `.secrets.toml.example`
* Edit TOML files in `config/local` according to your project requirements
* When using Docker Compose, remember to pass `APP_ENV` to your service:

```yaml
services:
  app:
    # ...
    environment:
      APP_ENV: ${APP_ENV}
```

* `.env.local` will be generated later — **don't** create it manually


4. [Configure](#configuration-files) dev/prod environment

* Create similar structure in `config/dev` or `config/prod` with files:
    * `config.toml`
    * `.secrets.toml`
    * `export.toml`
    * `docker-compose.yaml` if needed
* `.env.dev` or `.env.prod` will be generated later — **don't** create them manually


5. Set environment variable

```shell
export APP_ENV=local
# export APP_ENV=dev
# export APP_ENV=prod
```

6. Check it and generate `.env`

```shell
make env  # should print APP_ENV=local
make dotenv  # should tell you where .env.local was generated
```

# Adding new environments

1. Add new value to `ValidEnvs` enum in `config/toml_config_manager.py`
2. Update `ENV_TO_DIR_PATHS` mapping in the same file
3. Create corresponding directory in `config/` folder
4. Add required [configuration files](#configuration-files)

Environment directories can also contain other env-specific files like `docker-compose.yaml`, which will be used by
Makefile commands.

# Examples and tests

1. Setup virtual environment

```shell
# sudo apt update
# sudo apt install pipx
# pipx ensurepath
# pipx install uv
uv venv
source .venv/bin/activate
# .venv\Scripts\activate  # Windows
# https://docs.astral.sh/uv/getting-started/installation/#shell-autocompletion
# uv python install 3.12
uv pip install -e '.[test,dev]'
```

2. See the example how settings are read by the app from `.toml`

```shell
# locally
export APP_ENV=local
python examples/read_config.py
```

```shell
# or via Docker
docker rm myapp_test
docker build -t myapp:test -f examples/Dockerfile .
docker run -d --name myapp_test myapp:test
docker logs myapp_test
```

3. See the example how settings are read by the Docker Compose from `.env`

```shell
export APP_ENV=local
make up.db-echo  # Ctrl + C to stop
make down
```

4. Run tests

```shell
make code.cov.html
```

# Integration Example

You can see an example of this project in use
at [fastapi-clean-example](https://github.com/ivan-borovets/fastapi-clean-example).
