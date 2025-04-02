# To-Do List: Building `pan-os-cli`

## 1. Project Setup

- [ ] Create a new project directory: `pan-os-cli`.
- [ ] Initialize a Git repository with `git init`.
- [ ] Set up Poetry with `poetry init` and configure `pyproject.toml` with provided dependencies.
- [ ] Create the project structure:
  - `src/pan_os_cli/`
  - `tests/`
  - `docs/`
- [ ] Install dependencies with `poetry install`.
- [ ] Configure pre-commit hooks with `poetry run pre-commit install`.
- [ ] Add initial files: `README.md`, `LICENSE`, `SUPPORT.md`, `.pre-commit-config.yaml`.

## 2. Configuration Management

- [ ] Create `src/pan_os_cli/config.py`.
- [ ] Define `PanosConfig` Pydantic model with fields: `username`, `password`, `hostname`, `api_key`, `mock_mode`, `thread_pool_size`.
- [ ] Implement configuration loading using `dynaconf` to support environment variables and `~/.pan-os-cli/config.yaml`.
- [ ] Add logic to auto-generate API key if not provided using `pan-os-python`.
- [ ] Write unit tests for config loading in `tests/test_config.py`.

## 3. PAN-OS Client with Multi-Threading

- [ ] Create `src/pan_os_cli/client.py`.
- [ ] Implement `PanosClient` class with `Panorama` initialization from `pan-os-python`.
- [ ] Integrate `ThreadPoolExecutor` for multi-threaded API calls, configurable via `thread_pool_size`.
- [ ] Add methods: `add_objects`, `commit`, with mock mode support.
- [ ] Implement error handling for API failures with retries (3 attempts, exponential backoff).
- [ ] Write unit tests for client methods in `tests/test_client.py`, mocking API calls.

## 4. Data Models - Phase 1

- [ ] Create `src/pan_os_cli/models/` directory.
- [ ] Define Pydantic models for core objects:
  - `models/objects.py`: `Address`, `AddressGroup`.
- [ ] Add validation logic for each model (e.g., IP format for `Address.ip_netmask`).
- [ ] Write unit tests for model validation in `tests/test_objects.py`.

## 5. Utility Functions

- [ ] Create `src/pan_os_cli/utils.py`.
- [ ] Implement `load_yaml(file_path)` to parse YAML files.
- [ ] Add `validate_object(obj, model)` to validate data against Pydantic models.
- [ ] Implement `log_action(action, details)` for mock mode and debugging output.
- [ ] Write unit tests for utilities in `tests/test_utils.py`.

## 6. CLI Entry Point

- [ ] Create `src/pan_os_cli/main.py` with Typer app setup.
- [ ] Define main `app` and sub-apps: `set_app`, `delete_app`, `load_app`.
- [ ] Add callback docstring with CLI pattern and examples.
- [ ] Register sub-apps for `objects`, `network`, `security`.

## 7. Phase 1 Command Implementation

### 7.1 Objects Commands - Core Functionality

- [ ] Create Typer apps: `set_app`, `delete_app`, `load_app`.
- [ ] Implement `set address` command with options: `name`, `ip_netmask`, `description`, `tags`, `devicegroup`, `mock`.
- [ ] Implement `set address-group` command with options: `name`, `type`, `members`, `filter`, `devicegroup`, `mock`.
- [ ] Implement `delete address` and `delete address-group` commands.
- [ ] Implement `load address` command for bulk YAML loading with multi-threading.
- [ ] Write integration tests in `tests/test_objects.py`.

### 7.2 Operations Commands

- [ ] Create Typer app for `commit` operations.
- [ ] Implement `commit objects changes` command with options: `description`, `async`, `timeout`.
- [ ] Add Panorama-specific options: `device-group`, `device`, `push`.
- [ ] Write integration tests for commit operations.

## 8. Documentation Setup

- [ ] Set up MkDocs with Material theme.
- [ ] Configure plugins: mkdocstrings, linkcheck, minify, git-revision-date-localized.
- [ ] Create basic documentation structure in `docs/`.
- [ ] Add GitHub Actions workflow for automating deployment to GitHub Pages.
- [ ] Add detailed documentation for existing commands.
- [ ] Create YAML structure guide and bulk operations guide.

## 9. Phase 2: Extended Object Types

### 9.1 Tag Support

- [ ] Add Tag model in `models/objects.py`.
- [ ] Implement `set tag` command with options: `name`, `color`, `comments`.
- [ ] Implement `delete tag` command.
- [ ] Implement `load tag` command for bulk YAML loading.
- [ ] Update documentation with tag command examples.

### 9.2 Services Implementation

- [ ] Create `models/services.py` with `Service` and `ServiceGroup` models.
- [ ] Implement `set services service` command with options: `name`, `protocol`, `port`, `description`.
- [ ] Implement `set services service-group` command.
- [ ] Implement `delete` commands for services.
- [ ] Implement `load` commands for bulk service operations.
- [ ] Add service examples to documentation.

### 9.3 Bulk Operation Enhancements

- [ ] Implement dependency detection between objects in bulk operations.
- [ ] Add ordered creation based on dependencies.
- [ ] Enhance validation for bulk operations.
- [ ] Improve error reporting for bulk operations.
- [ ] Update YAML structure documentation with all supported objects.

## 10. Phase 3: Network & Security Configuration

### 10.1 Network Commands

- [ ] Create Typer apps: `set_app`, `delete_app`, `load_app` for network objects.
- [ ] Define `models/network.py` with `SecurityZone` and `Interface` models.
- [ ] Implement `set security-zone` command with options: `name`, `mode`, `enable_user_id`, `devicegroup`.
- [ ] Implement `set interface` command with required options for different interface types.
- [ ] Implement `delete` commands for network objects.
- [ ] Implement `load` commands with multi-threading for bulk network configuration.
- [ ] Write integration tests in `tests/test_network.py`.

### 10.2 Security Commands

- [ ] Create Typer apps for security policy management.
- [ ] Define `models/security.py` with `SecurityRule` and `NatRule` models.
- [ ] Implement `set security rule` command with options: `name`, `source_zones`, `destination_zones`, `source_addresses`, `destination_addresses`, `applications`, `services`, `action`, `log_end`.
- [ ] Implement `set nat rule` command with appropriate options.
- [ ] Implement `delete` commands for security policies.
- [ ] Implement `load` commands for bulk security policy configuration.
- [ ] Write integration tests in `tests/test_security.py`.

## 11. Phase 4: Advanced Features

### 11.1 Dashboard & Status Commands

- [ ] Implement `status` command to show current connection status.
- [ ] Add `dashboard` command to display firewall performance metrics.
- [ ] Create `show` commands for viewing configuration objects.
- [ ] Add visualization options for complex policies.

### 11.2 Configuration Management

- [ ] Add configuration validation before commit.
- [ ] Implement `export` command to save current configuration to YAML.
- [ ] Implement `import` command for full configuration import.
- [ ] Add `diff` command to show configuration differences.

### 11.3 Panorama Template Support

- [ ] Add models for Panorama templates and template stacks.
- [ ] Implement template management commands.
- [ ] Support device group operations with template context.
- [ ] Add documentation for template operations.

## 12. Phase 5: Polish & Release

### 12.1 Testing & Quality Assurance

- [ ] Ensure test coverage is >80% for all core modules.
- [ ] Implement comprehensive integration tests for all commands.
- [ ] Perform load testing with large configurations.
- [ ] Fix any identified bugs and issues.

### 12.2 Documentation Completion

- [ ] Complete all command reference documentation.
- [ ] Add tutorials for common workflows.
- [ ] Create troubleshooting guide.
- [ ] Add examples for complex scenarios.

### 12.3 Release Preparation

- [ ] Update version to `1.0.0` in `pyproject.toml`.
- [ ] Generate change log.
- [ ] Build package with `poetry build`.
- [ ] Prepare for PyPI publication.
- [ ] Create release notes.

## 13. Post-Release Roadmap

### 13.1 Additional Configuration Types

- [ ] Support for application objects and groups.
- [ ] Support for URL filtering categories.
- [ ] Support for external dynamic lists.
- [ ] Support for decryption policies.

### 13.2 Advanced Automation

- [ ] Add scheduling capabilities for recurring operations.
- [ ] Implement configuration drift detection.
- [ ] Support for policy optimization suggestions.
- [ ] Integration with infrastructure as code tools.

### 13.3 User Experience Enhancements

- [ ] Add interactive CLI mode with command completion.
- [ ] Implement colorized output for better readability.
- [ ] Add progressive disclosure of options for complex commands.
- [ ] Create config wizard for initial setup.
