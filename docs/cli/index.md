# CLI Reference

This section provides detailed documentation for all PAN-OS CLI commands. The commands are organized by category.

## Command Structure

PAN-OS CLI follows a consistent command structure:

```
pan-os-cli <action> <category> <object-type> [options]
```

### Actions

- `set`: Create or update an object
- `get`: Retrieve information about objects
- `delete`: Remove an object
- `load`: Bulk import objects from YAML
- `show`: Display detailed information
- `commit`: Apply changes to the device

### Categories

- `objects`: Address objects, address groups, etc.
- `network`: Interfaces, zones, etc.
- `security`: Security policies, profiles, etc.
- `operations`: Commit operations, validations, etc.

## Global Options

These options can be used with any command:

| Option | Description |
|--------|-------------|
| `--help`, `-h` | Show help message |
| `--version` | Show version information |
| `--debug` | Enable debug logging |
| `--config` | Specify a custom config file path |

## Authentication Options

| Option | Description |
|--------|-------------|
| `--username` | Username for PAN-OS device |
| `--password` | Password for PAN-OS device |
| `--hostname` | Hostname or IP of PAN-OS device |
| `--api-key` | API key for PAN-OS device |

## Location Options

| Option | Description |
|--------|-------------|
| `--device-group` | Panorama device group (default: "Shared") |
| `--vsys` | Virtual system (default: "vsys1") |

## Command Examples

Here are some examples of common commands:

```bash
# Create an address object
pan-os-cli set objects address --name web-server --ip-netmask 192.168.1.100/32

# List all address groups
pan-os-cli get objects address-group

# Get details of a specific security policy
pan-os-cli show security policy --name "Allow Web Traffic"

# Bulk load address objects from YAML
pan-os-cli load objects address --file addresses.yaml

# Commit changes
pan-os-cli commit objects changes
```

## Categories Overview

- [Objects](objects/address.md): Manage address objects, address groups, and other objects
- [Network](network/interfaces.md): Configure interfaces, zones, and other network settings
- [Security](security/policies.md): Manage security policies and profiles
- [Operations](operations/commit.md): Perform operations like commits and validations
