# Product Requirements Document (PRD): `panos-cli`

## 1. Overview

### 1.1 Product Name

`panos-cli`

### 1.2 Purpose

`panos-cli` is a command-line interface (CLI) tool designed for network engineers to efficiently provision and manage Palo Alto Networks Strata PAN-OS configurations. It leverages the `pan-os-python` library for API interactions and Typer for a modern CLI experience, with a strong emphasis on performance through multi-threaded API handling.

### 1.3 Objectives

- Provide an intuitive, network engineer-friendly CLI for PAN-OS management.
- Support key configuration objects: addresses, address groups, security zones, and security rules.
- Enable bulk operations via YAML files with high performance.
- Ensure all API interactions are handled with multi-threading to optimize speed and scalability.
- Include a mock mode for testing without live API calls.
- Offer flexible authentication and comprehensive documentation.

### 1.4 Stakeholders

- **Primary Users**: Network engineers managing PAN-OS firewalls.
- **Developers**: Calvin Remsburg (lead), open-source contributors.
- **Organization**: xAI (hypothetical sponsor), open-source community.

## 2. Requirements

### 2.1 Functional Requirements

#### 2.1.1 CLI Structure

- **Command Pattern**: `panos-cli <action> <object-type> <object> [options]`
  - Actions: `set` (create/update), `delete`, `load` (bulk import).
  - Object Types: `objects`, `network`, `security`.
- **Supported Objects**:
  - `objects`: Address, AddressGroup.
  - `network`: SecurityZone.
  - `security`: SecurityRule.

#### 2.1.2 API Interactions

- **Multi-Threading Mandate**: All API interactions with PAN-OS **must** use multi-threading to handle concurrent requests efficiently.
  - Use Python’s `concurrent.futures.ThreadPoolExecutor` for parallel execution.
  - Example: Bulk operations (e.g., loading 100 addresses) must distribute API calls across threads.
  - Thread pool size: Configurable, default to 10 threads.
- **Library**: Utilize `pan-os-python` for all PAN-OS API calls.
- **Performance Goal**: Process 100 objects in <10 seconds (assuming network latency <500ms per call).

#### 2.1.3 Authentication

- **Methods**:
  - Environment variables: `panos_username`, `panos_password`, `panos_host`.
  - Config file: `~/.panos-cli/config.yaml`.
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

- `panos-cli set objects address --devicegroup Shared --name web-server --ip-netmask 192.168.1.100/32`
- `panos-cli load objects address --file addresses.yaml`
- `panos-cli delete security rule --devicegroup Shared --name Allow-Web`

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

## 3. Technical Design

### 3.1 Project Structure

```bash
panos-cli/
├── src/panos_cli/
│   ├── main.py         # CLI entry point
│   ├── config.py       # Authentication and settings
│   ├── client.py       # Multi-threaded PAN-OS client
│   ├── utils.py        # Helpers (YAML parsing, logging)
│   ├── models/         # Pydantic models
│   └── commands/       # Action-specific modules
├── tests/              # Test suite
├── docs/               # MkDocs documentation
└── pyproject.toml      # Dependencies and config
```

### 3.2 Dependencies

- **Core**: `typer`, `pyyaml`, `pydantic`, `pan-os-python`, `dynaconf`.
- **Dev**: `pytest`, `ruff`, `mkdocs`, etc.
- **Python**: `>=3.10, <3.14`.

### 3.3 Key Components

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
  def set_address(name: str, ip_netmask: str, devicegroup: str = "-shared", mock: bool = False):
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

### 4.1 Phase 1: Core Functionality

- Config and client setup with multi-threading.
- `set` and `delete` for `objects` (Address, AddressGroup).
- Basic tests and docs.

### 4.2 Phase 2: Expanded Features

- `load` with multi-threaded bulk operations.
- `network` and `security` commands.
- Mock mode implementation.

### 4.3 Phase 3: Polish & Release

- Full test coverage (>80%).
- Comprehensive MkDocs site.
- PyPI release (`v0.2.1`).

## 5. Success Criteria

- CLI processes 100 objects in <10s with multi-threading.
- 100% of API interactions use threading.
- Positive feedback from 5+ network engineers.
- No critical bugs in v0.2.1.

## 6. Risks & Mitigations

- **Risk**: Multi-threading complexity.
  - **Mitigation**: Use well-tested `ThreadPoolExecutor`, add logging.
- **Risk**: API rate limits.
  - **Mitigation**: Configurable thread pool size, retry logic.

## 7. Appendix

### 7.1 Example Config File

```yaml
username: "admin"
password: "secret"
hostname: "panorama.example.com"
thread_pool_size: 10
```

### 7.2 Reference

- [pan-os-python Docs](https://pan-os-python.readthedocs.io/)
- [Typer Docs](https://typer.tiangolo.com/)
