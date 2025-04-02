# panos-cli

A CLI tool for efficiently managing PAN-OS configurations with multi-threading support.

[![License](https://img.shields.io/github/license/cdot65/panos-cli)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![Poetry](https://img.shields.io/badge/poetry-dependency%20management-blue)](https://python-poetry.org/)

## Overview

`panos-cli` provides a command-line interface for managing Palo Alto Networks firewalls and Panorama appliances. It uses concurrent processing to handle bulk operations efficiently, making it ideal for:

- **Address Object Management**: Create, update, delete, and bulk load address objects
- **Address Group Management**: Manage static and dynamic address groups
- **Multi-Threading**: Process API requests in parallel for improved performance
- **Commit Operations**: Commit configuration changes with status tracking

> **Note**: This tool focuses specifically on address object management and uses multi-threading to optimize performance when dealing with large numbers of objects.

## Features

- **Efficient Multi-Threading**: Configurable thread pool for parallel API operations
- **Bulk Operations**: Load hundreds of objects from YAML files with a single command
- **Comprehensive Error Handling**: Built-in retry mechanism with exponential backoff
- **Configurable**: Works with environment variables or configuration file
- **Mock Mode**: Test commands without making actual API calls
- **Rich Console Output**: Clear, informative output with status indicators

## Installation

### Using pip

```bash
pip install panos-cli
```

### Using Poetry (for development)

```bash
git clone https://github.com/cdot65/panos-cli.git
cd panos-cli
poetry install
```

## Configuration

`panos-cli` can be configured in multiple ways:

### Environment Variables

```bash
export panos_username="admin"
export panos_password="your-password"
export panos_host="panorama.example.com"
```

### Configuration File

Create a YAML file at `~/.panos-cli/config.yaml`:

```yaml
credentials:
  username: "admin"
  password: "your-password"
  hostname: "panorama.example.com"
  api_key: "your-api-key"  # Optional: Use instead of username/password

settings:
  thread_pool_size: 10
  mock_mode: false
```

## Usage

### Command Pattern

```
panos-cli <action> <object-type> <object> [options]
```

### Examples

#### Address Object Management

```bash
# Create an address object
panos-cli set objects address --name web-server --ip-netmask 192.168.1.100/32

# Delete an address object
panos-cli delete objects address --name web-server

# Bulk load address objects from YAML
panos-cli load objects address --file addresses.yaml

# Get address objects (specific or all)
panos-cli get objects address --name web-server
panos-cli get objects address  # Lists all

# Show detailed address information
panos-cli show addresses --device-group "Shared"
panos-cli show addresses --name web-server
```

#### Address Group Management

```bash
# Create a static address group
panos-cli set objects address-group --name internal-servers --static-members web-server,db-server

# Create a dynamic address group
panos-cli set objects address-group --name dynamic-servers --dynamic-filter "'server' in tags"

# Delete an address group
panos-cli delete objects address-group --name internal-servers

# Bulk load address groups from YAML
panos-cli load objects address-group --file address-groups.yaml
```

#### Commit Operations

```bash
# Commit changes
panos-cli commit objects changes

# Commit with description and wait for completion
panos-cli commit objects changes --description "Update address objects" --wait

# Check commit status
panos-cli commit objects check-commit --job-id 12345
```

#### Testing Connectivity

```bash
# Test authentication to PAN-OS device
panos-cli test auth

# Test in mock mode without making API calls
panos-cli test auth --mock
```

### YAML Format for Bulk Loading

#### Address Objects (addresses.yaml)
```yaml
addresses:
  - name: web-server-1
    ip_netmask: 192.168.1.10/32
    description: Primary web server
    tags:
      - web
      - production
  
  - name: app-server-1
    ip_netmask: 192.168.1.20/32
    description: Application server
    tags:
      - app
      - production
      
  - name: db-server-1
    ip_netmask: 192.168.1.30/32
    description: Database server
    tags:
      - db
      - production
```

#### Address Groups (address-groups.yaml)
```yaml
address_groups:
  - name: web-servers
    static_members:
      - web-server-1
      - web-server-2
    description: All web servers
    tags:
      - web
      - servers
  
  - name: dynamic-web-servers
    dynamic_filter: "'web' in tags"
    description: Dynamic group for web servers
    tags:
      - web
      - dynamic
```

## Development

### Prerequisites

- Python 3.8+
- Poetry

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/cdot65/panos-cli.git
cd panos-cli

# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

### Development Commands

The project includes a Makefile with useful commands:

```bash
# Format code with ruff
make ruff

# Run linters (flake8, yamllint)
make lint

# Rebuild and reinstall the package
make reinstall

# Clean up build artifacts
make clean

# View all available commands
make help
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- Built with [pan-os-python](https://github.com/PaloAltoNetworks/pan-os-python)
- CLI interface powered by [Typer](https://typer.tiangolo.com/)
- Console output enhanced with [Rich](https://github.com/Textualize/rich)