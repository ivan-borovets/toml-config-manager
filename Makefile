# Environment
PYTHON := python
CONFIGS_DIG := config
TOML_CONFIG_MANAGER := $(CONFIGS_DIG)/toml_config_manager.py

.PHONY: env dotenv
env:
	@echo APP_ENV=$(APP_ENV)

dotenv:
	@$(PYTHON) $(TOML_CONFIG_MANAGER) ${APP_ENV}

# Docker compose
DOCKER_COMPOSE := docker compose

.PHONY: guard-APP_ENV up.db up.db-echo down down.total
guard-APP_ENV:
ifndef APP_ENV
	$(error "APP_ENV is not set. Set APP_ENV before running this command.")
endif

up.db: guard-APP_ENV
	@echo "APP_ENV=$(APP_ENV)"
	@cd $(CONFIGS_DIG)/$(APP_ENV) && $(DOCKER_COMPOSE) --env-file .env.$(APP_ENV) up -d app_db_pg --build

up.db-echo: guard-APP_ENV
	@echo "APP_ENV=$(APP_ENV)"
	@cd $(CONFIGS_DIG)/$(APP_ENV) && $(DOCKER_COMPOSE) --env-file .env.$(APP_ENV) up app_db_pg --build

down: guard-APP_ENV
	@cd $(CONFIGS_DIG)/$(APP_ENV) && $(DOCKER_COMPOSE) --env-file .env.$(APP_ENV) down

down.total: guard-APP_ENV
	@cd $(CONFIGS_DIG)/$(APP_ENV) && $(DOCKER_COMPOSE) --env-file .env.$(APP_ENV) down -v

# Code quality
.PHONY: code.format code.lint code.test code.cov code.cov.html code.check

# Source code formatting
.PHONY: code.format code.lint code.test code.cov code.cov.html code.check
code.format:
	ruff format

code.lint: code.format
	ruff check --exit-non-zero-on-fix
	mypy

code.test:
	pytest -v

code.cov:
	coverage run -m pytest
	coverage combine
	coverage report

code.cov.html:
	coverage run -m pytest
	coverage combine
	coverage html

code.check: code.lint code.test
