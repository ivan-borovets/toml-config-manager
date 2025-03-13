# Makefile variables, pt. 1
PYTHON := python
CONFIGS_DIG := config
TOML_CONFIG_MANAGER := $(CONFIGS_DIG)/toml_config_manager.py

# Setting environment
.PHONY: env dotenv

env:
	@echo APP_ENV=$(APP_ENV)

dotenv:
	@$(PYTHON) $(TOML_CONFIG_MANAGER) ${APP_ENV}

# Makefile variables, pt. 2
DOCKER_COMPOSE := docker compose

# Docker Compose controls
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

# Makefile variables, pt. 3
TESTS_DIR := tests
EXAMPLES_DIR := examples

# Source code formatting
.PHONY: code.format code.lint code.test code.cov code.cov.html code.check

code.format:
	isort $(CONFIGS_DIG) $(TESTS_DIR) $(EXAMPLES_DIR)
	black $(CONFIGS_DIG) $(TESTS_DIR) $(EXAMPLES_DIR)

code.lint: code.format
	bandit -r $(CONFIGS_DIG) -c pyproject.toml
	ruff check $(CONFIGS_DIG) $(TESTS_DIR) $(EXAMPLES_DIR)
	pylint $(CONFIGS_DIG) $(TESTS_DIR) $(EXAMPLES_DIR)
	mypy $(CONFIGS_DIG) $(EXAMPLES_DIR)

code.test:
	pytest -v

code.cov:
	coverage run -m pytest
	coverage report

code.cov.html:
	coverage run -m pytest
	coverage html

code.check: code.lint code.test
