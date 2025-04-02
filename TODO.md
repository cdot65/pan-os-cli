# To-Do List: Building `panos-cli`

## 1. Project Setup

- [ ] Create a new project directory: `panos-cli`.
- [ ] Initialize a Git repository with `git init`.
- [ ] Set up Poetry with `poetry init` and configure `pyproject.toml` with provided dependencies.
- [ ] Create the project structure:
  - `src/panos_cli/`
  - `tests/`
  - `docs/`
- [ ] Install dependencies with `poetry install`.
- [ ] Configure pre-commit hooks with `poetry run pre-commit install`.
- [ ] Add initial files: `README.md`, `LICENSE`, `SUPPORT.md`, `.pre-commit-config.yaml`.

## 2. Configuration Management

- [ ] Create `src/panos_cli/config.py`.
- [ ] Define `PanosConfig` Pydantic model with fields: `username`, `password`, `hostname`, `api_key`, `mock_mode`, `thread_pool_size`.
- [ ] Implement configuration loading using `dynaconf` to support environment variables and `~/.panos-cli/config.yaml`.
- [ ] Add logic to auto-generate API key if not provided using `pan-os-python`.
- [ ] Write unit tests for config loading in `tests/test_config.py`.

## 3. PAN-OS Client with Multi-Threading

- [ ] Create `src/panos_cli/client.py`.
- [ ] Implement `PanosClient` class with `Panorama` initialization from `pan-os-python`.
- [ ] Integrate `ThreadPoolExecutor` for multi-threaded API calls, configurable via `thread_pool_size`.
- [ ] Add methods: `add_objects`, `commit`, with mock mode support.
- [ ] Implement error handling for API failures with retries (3 attempts, exponential backoff).
- [ ] Write unit tests for client methods in `tests/test_client.py`, mocking API calls.

## 4. Data Models

- [ ] Create `src/panos_cli/models/` directory.
- [ ] Define Pydantic models in separate files:
  - `models/objects.py`: `Address`, `AddressGroup`.
  - `models/network.py`: `SecurityZone`.
  - `models/security.py`: `SecurityRule`.
- [ ] Add validation logic for each model (e.g., IP format for `Address.ip_netmask`).
- [ ] Write unit tests for model validation in `tests/test_objects.py`, `tests/test_network.py`, `tests/test_security.py`.

## 5. Utility Functions

- [ ] Create `src/panos_cli/utils.py`.
- [ ] Implement `load_yaml(file_path)` to parse YAML files.
- [ ] Add `validate_object(obj, model)` to validate data against Pydantic models.
- [ ] Implement `log_action(action, details)` for mock mode and debugging output.
- [ ] Write unit tests for utilities in `tests/test_utils.py`.

## 6. CLI Entry Point

- [ ] Create `src/panos_cli/main.py` with Typer app setup.
- [ ] Define main `app` and sub-apps: `set_app`, `delete_app`, `load_app`.
- [ ] Add callback docstring with CLI pattern and examples.
- [ ] Register sub-apps for `objects`, `network`, `security`.

## 7. Command Implementation

### 7.1 Objects Commands (`src/panos_cli/commands/objects.py`)

- [ ] Create Typer apps: `set_app`, `delete_app`, `load_app`.
- [ ] Implement `set address` command with options: `name`, `ip_netmask`, `description`, `tags`, `devicegroup`, `mock`.
- [ ] Implement `set address-group` command with options: `name`, `type`, `members`, `filter`, `devicegroup`, `mock`.
- [ ] Implement `delete address` and `delete address-group` commands.
- [ ] Implement `load address` command for bulk YAML loading with multi-threading.
- [ ] Write integration tests in `tests/test_objects.py`.

### 7.2 Network Commands (`src/panos_cli/commands/network.py`)

- [ ] Create Typer apps: `set_app`, `delete_app`, `load_app`.
- [ ] Implement `set security-zone` command with options: `name`, `mode`, `enable_user_id`, `devicegroup`, `mock`.
- [ ] Implement `delete security-zone` command.
- [ ] Implement `load security-zone` command for bulk YAML loading with multi-threading.
- [ ] Write integration tests in `tests/test_network.py`.

### 7.3 Security Commands (`src/panos_cli/commands/security.py`)

- [ ] Create Typer apps: `set_app`, `delete_app`, `load_app`.
- [ ] Implement `set rule` command with options: `name`, `source_zones`, `destination_zones`, `source_addresses`, `destination_addresses`, `applications`, `services`, `action`, `log_end`, `devicegroup`, `mock`.
- [ ] Implement `delete rule` command.
- [ ] Implement `load rule` command for bulk YAML loading with multi-threading.
- [ ] Write integration tests in `tests/test_security.py`.

## 8. Error Handling

- [ ] Add try-except blocks in `client.py` for `PanosAPIError` with user-friendly messages.
- [ ] Implement Typer `exit()` for invalid input scenarios in command functions.
- [ ] Test error handling in all test files.

## 9. Testing

- [ ] Configure `pytest` in `pyproject.toml` with markers (`unit`, `integration`).
- [ ] Write unit tests for all utility functions and models.
- [ ] Write integration tests for commands, mocking `pan-os-python` API calls.
- [ ] Run `poetry run pytest --cov` to ensure >80% coverage.

## 10. Documentation

- [ ] Add docstrings to all classes, functions, and commands.
- [ ] Set up MkDocs in `docs/` with `index.md` and logo.
- [ ] Configure MkDocs plugins in `pyproject.toml`.
- [ ] Generate initial docs with `poetry run mkdocs build`.
- [ ] Add detailed command examples to `README.md` and MkDocs.

## 11. Code Quality

- [ ] Run `poetry run ruff check .` to lint code.
- [ ] Format code with `poetry run ruff format .`.
- [ ] Test pre-commit hooks with `poetry run pre-commit run --all-files`.

## 12. Packaging & Release Prep

- [ ] Update `pyproject.toml` with version `0.2.1` and metadata.
- [ ] Build package with `poetry build`.
- [ ] Test local install with `pip install dist/panos-cli-0.2.1.tar.gz`.
- [ ] Prepare GitHub repository with updated `README.md` and docs link.

## 13. Final Validation

- [ ] Verify multi-threading works for bulk operations (e.g., load 100 addresses).
- [ ] Test all commands with mock mode enabled.
- [ ] Confirm no critical linting or test failures.
