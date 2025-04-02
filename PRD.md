# Product Requirements Document (PRD): `pan-os-cli`

## 1. Overview

### 1.1 Product Name

`pan-os-cli`

### 1.2 Purpose

`pan-os-cli` is a command-line interface (CLI) tool designed for network engineers to efficiently provision and manage Palo Alto Networks Strata PAN-OS configurations. It leverages the `pan-os-python` library for API interactions and Typer for a modern CLI experience, with a strong emphasis on performance through multi-threaded API handling.

### 1.3 Objectives

- Provide an intuitive, network engineer-friendly CLI for PAN-OS management.
- Support key configuration objects: addresses, address groups, security zones, security rules, services, service groups, and tags.
- Enable bulk operations via YAML files with high performance.
- Ensure all API interactions are handled with multi-threading to optimize speed and scalability.
- Include a mock mode for testing without live API calls.
- Offer flexible authentication and comprehensive documentation.
- Support extensibility for additional configuration constructs.

### 1.4 Stakeholders

- **Primary Users**: Network engineers managing PAN-OS firewalls.
- **Developers**: Calvin Remsburg (lead), open-source contributors.
- **Organization**: xAI (hypothetical sponsor), open-source community.

## 2. Requirements

### 2.1 Functional Requirements

#### 2.1.1 CLI Structure

- **Command Pattern**: `pan-os-cli <action> <object-type> <object> [options]`
  - Actions: `set` (create/update), `delete`, `load` (bulk import).
  - Object Types: `objects`, `network`, `security`, `services`.
- **Supported Objects**:
  - `objects`: Address, AddressGroup, Tag.
  - `network`: SecurityZone, Interface.
  - `security`: SecurityRule.
  - `services`: Service, ServiceGroup.

#### 2.1.2 API Interactions

- **Multi-Threading Mandate**: All API interactions with PAN-OS **must** use multi-threading to handle concurrent requests efficiently.
  - Use Python's `concurrent.futures.ThreadPoolExecutor` for parallel execution.
  - Example: Bulk operations (e.g., loading 100 addresses) must distribute API calls across threads.
  - Thread pool size: Configurable, default to 10 threads.
- **Library**: Utilize `pan-os-python` for all PAN-OS API calls.
- **Performance Goal**: Process 100 objects in <10 seconds (assuming network latency <500ms per call).

#### 2.1.3 Authentication

- **Methods**:
  - Environment variables: `PANOS_USERNAME`, `PANOS_USERNAME`, `PANOS_HOST`.
  - Config file: `~/.pan-os-cli/config.yaml`.
- **Config Structure**:

```yaml
default:
  # Authentication settings
  username: "EXAMPLE_USERNAME_HERE"
  password: "EXAMPLE_PASSWORD_HERE"
  hostname: "EXAMPLE_HOSTNAME_HERE"
  # api_key: "EXAMPLE_API_KEY_HERE" # Optional: Use instead of username/password

  # Application settings
  thread_pool_size: 10
  mock_mode: false
```

- **Validation**: Use Pydantic to enforce required fields.
- **API Key**: Auto-generate if not provided.

#### 2.1.4 Bulk Operations

- **Input**: YAML files defining multiple objects.
- **Execution**: Multi-threaded API calls to create/update objects in parallel.
- **Example YAML**:

```yaml
addresses:
  - name: web-server-1
    ip_netmask: 192.168.1.100/32
  - name: web-server-2
    ip_netmask: 192.168.1.101/32
```

#### 2.1.5 Mock Mode

- **Purpose**: Simulate API calls without network interaction.
- **Implementation**: Log commands and responses to stdout instead of calling the API.

#### 2.1.6 Example Commands

- `pan-os-cli set objects address --name web-server --ip-netmask 192.168.1.100/32`
- `pan-os-cli load objects address --file addresses.yaml`
- `pan-os-cli delete security rule --name Allow-Web`

### 2.2 Non-Functional Requirements

#### 2.2.1 Performance

- **API Throughput**: Handle 100+ concurrent API requests via multi-threading.
- **Latency**: Minimize delays by parallelizing operations (target <10s for 100 objects).

#### 2.2.2 Scalability

- Support managing configurations across multiple device groups and large object sets.

#### 2.2.3 Reliability

- Graceful error handling for API failures (e.g., timeouts, authentication errors).
- Retry mechanism: 3 attempts with exponential backoff for transient failures.

#### 2.2.4 Maintainability

- Modular code structure with clear separation of concerns.
- Comprehensive unit and integration tests (target >80% coverage).

#### 2.2.5 Documentation

- Inline docstrings for all functions and classes.
- User-facing docs via MkDocs on GitHub Pages.
- Detailed command references with examples.

## 3. Technical Design

### 3.1 Project Structure

```bash
pan-os-cli/
├── src/pan_os_cli/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── client.py
│   ├── utils.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── objects.py
│   │   ├── services.py
│   │   ├── network.py
│   │   └── security.py
│   └── commands/
│       ├── __init__.py
│       ├── objects.py
│       ├── network.py
│       └── security.py
├── tests/
├── docs/
└── pyproject.toml
```

### 3.2 Core Technologies

- **Core**: `typer`, `pyyaml`, `pydantic`, `pan-os-python`, `dynaconf`.
- **Dev**: `pytest`, `ruff`, `mkdocs`, `mkdocs-material`, `mkdocstrings`, etc.
- **Python**: `>=3.10, <3.14`.

### 3.3 API Design

#### 3.3.1 Configuration (`config.py`)

- Load settings with `dynaconf`.
- Model:

```python
class PanosConfig(BaseModel):
    username: str
    password: str
    hostname: str
    api_key: str | None
    mock_mode: bool = False
    thread_pool_size: int = 10
```

#### 3.3.2 PAN-OS Client (`client.py`)

- **Multi-Threading**: Use `ThreadPoolExecutor` for all API operations.
- **Example**:

```python
from concurrent.futures import ThreadPoolExecutor
from panos.panorama import Panorama
from .config import PanosConfig

class PanosClient:
    def __init__(self, config: PanosConfig):
        self.config = config
        self.client = Panorama(...) if not config.mock_mode else None
        self.executor = ThreadPoolExecutor(max_workers=config.thread_pool_size)

    def add_objects(self, objects: list):
        if self.config.mock_mode:
            print("Mock adding objects")
            return
        futures = [self.executor.submit(self.client.add, obj) for obj in objects]
        for future in futures:
            future.result()  # Wait and handle exceptions

    def commit(self):
        if self.config.mock_mode:
            print("Mock commit")
        else:
            self.client.commit()
```

#### 3.3.3 Models (`models/`)

- Pydantic models for validation (e.g., `Address`, `SecurityRule`).

#### 3.3.4 Commands (`commands/`)

- **Set Example**:

```python
@set_app.command("address")
def set_address(name: str, ip_netmask: str, devicegroup: str = "Shared", mock: bool = False):
    config = PanosConfig(mock_mode=mock)
    client = PanosClient(config)
    addr = AddressObject(name=name, value=ip_netmask)
    client.add_objects([addr])
    client.commit()
```

- **Load Example**:

```python
@load_app.command("address")
def load_address(file: str, devicegroup: str = "Shared", mock: bool = False):
    config = PanosConfig(mock_mode=mock)
    client = PanosClient(config)
    with open(file, "r") as f:
        data = yaml.safe_load(f)
    objects = [AddressObject(name=a["name"], value=a["ip_netmask"]) for a in data["addresses"]]
    client.add_objects(objects)  # Multi-threaded
    client.commit()
```

### 3.4 Error Handling

- Catch `PanosAPIError` and retry with backoff.
- User-friendly error messages via Typer.

## 4. Milestones & Deliverables

### 4.1 Phase 1: Core Functionality (Current Phase)

- Config and client setup with multi-threading.
- `set`, `delete`, and `commit` operations for `objects` (Address, AddressGroup).
- Documentation with MkDocs.
- Basic tests.

### 4.2 Phase 2: Extended Objects (Next Phase)

- Support for Tags and Tag operations.
- Services and Service Groups.
- Improved bulk operations for all object types.

### 4.3 Phase 3: Network & Security (Future)

- SecurityZone and Interface commands.
- SecurityRule operations with dependencies.
- NAT rule configuration support.

### 4.4 Phase 4: Advanced Features

- Dashboard command for status overview.
- Configuration validation before commit.
- Export/import of full configurations.
- Support for Panorama template and template-stack operations.

### 4.5 Phase 5: Polish & Release

- Full test coverage (>80%).
- Comprehensive MkDocs site with all commands documented.
- PyPI release (`v1.0.0`).

## 5. Success Criteria

- CLI processes 100 objects in <10s with multi-threading.
- 100% of API interactions use threading.
- Supports all planned configuration object types.
- Comprehensive documentation with examples for each command.
- Positive feedback from 5+ network engineers.
- No critical bugs in v1.0.0.

## 6. Risks & Mitigations

- **Risk**: Multi-threading complexity.
  - **Mitigation**: Use well-tested `ThreadPoolExecutor`, add logging.
- **Risk**: API rate limits.
  - **Mitigation**: Configurable thread pool size, retry logic.
- **Risk**: Object dependencies during bulk operations.
  - **Mitigation**: Implement dependency resolution and ordered creation.
- **Risk**: Complex security policy configurations.
  - **Mitigation**: Comprehensive validation and detailed error messages.

## 7. Appendix

### 7.1 Example Config File

```yaml
default:
  # Authentication settings
  username: "EXAMPLE_USERNAME_HERE"
  password: "EXAMPLE_PASSWORD_HERE"
  hostname: "EXAMPLE_HOSTNAME_HERE"
  # api_key: "EXAMPLE_API_KEY_HERE" # Optional: Use instead of username/password

  # Application settings
  thread_pool_size: 10
  mock_mode: false
```

### 7.2 Reference

- [pan-os-python Docs](https://pan-os-python.readthedocs.io/)
- [Typer Docs](https://typer.tiangolo.com/)
- [MkDocs Documentation](https://cdot65.github.io/pan-os-cli/)
