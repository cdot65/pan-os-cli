# panos-cli

A command-line interface (CLI) tool for efficiently managing Palo Alto Networks Strata PAN-OS configurations with multi-threading support.

## Features

- Intuitive CLI for PAN-OS management
- Multi-threaded API handling for high performance
- Support for address objects, address groups, security zones, and security rules
- Bulk operations via YAML files
- Mock mode for testing without live API calls
- Flexible authentication methods

## Installation

```bash
pip install panos-cli
```

Or from source:

```bash
git clone https://github.com/cdot65/panos-cli.git
cd panos-cli
poetry install
```

## Usage

Basic command pattern:

```
panos-cli <action> <object-type> <object> [options]
```

Examples:

```bash
# Set a single address object
panos-cli set objects address --devicegroup Shared --name web-server --ip-netmask 192.168.1.100/32

# Bulk load address objects from YAML file with multi-threading
panos-cli load objects address --file addresses.yaml

# Delete a security rule
panos-cli delete security rule --devicegroup Shared --name Allow-Web
```

## Configuration

Authentication methods:

1. Environment variables:
   ```bash
   export panos_username="admin"
   export panos_password="password"
   export panos_host="192.168.1.1"
   ```

2. Config file (~/.panos-cli/config.yaml):
   ```yaml
   username: admin
   password: password
   hostname: 192.168.1.1
   thread_pool_size: 10
   mock_mode: false
   ```

## Technologies Used

- [Typer](https://typer.tiangolo.com/): Modern CLI framework
- [pan-os-python](https://github.com/PaloAltoNetworks/pan-os-python): Official PAN-OS SDK
- [Pydantic](https://docs.pydantic.dev/): Data validation
- [Concurrent Futures](https://docs.python.org/3/library/concurrent.futures.html): Multi-threading
