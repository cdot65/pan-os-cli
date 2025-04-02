# Getting Started

This guide will help you get up and running with PAN-OS CLI quickly.

## Initial Configuration

Before using PAN-OS CLI, you need to set up the connection to your PAN-OS device.

### Using Environment Variables

You can set environment variables for your PAN-OS device credentials:

```bash
export panos_username="EXAMPLE_USERNAME_HERE"
export panos_password="EXAMPLE_PASSWORD_HERE" # pragma: allowlist secret
export panos_host="EXAMPLE_HOSTNAME_HERE"
```

### Using Configuration File

Alternatively, create a YAML configuration file at `~/.pan-os-cli/config.yaml`:

```yaml
# PAN-OS CLI Configuration

default:
  # Authentication settings
  username: "EXAMPLE_USERNAME_HERE"
  password: "EXAMPLE_PASSWORD_HERE" # pragma: allowlist secret
  hostname: "EXAMPLE_HOSTNAME_HERE"
  # api_key: "EXAMPLE_API_KEY_HERE" # Optional: Use instead of username/password # pragma: allowlist secret

  # Application settings
  thread_pool_size: 10
  mock_mode: false
```

## Basic Commands

Here are some basic commands to get you started:

### Check Version

```bash
pan-os-cli --version
```

### Getting Help

```bash
pan-os-cli --help
```

To get help for specific commands:

```bash
pan-os-cli objects address --help
```

### Managing Address Objects

Create a new address object:

```bash
pan-os-cli set objects address --name web-server --ip-netmask 192.168.1.100/32
```

List all address objects:

```bash
pan-os-cli get objects address
```

Get details for a specific address object:

```bash
pan-os-cli show addresses --name web-server
```

### Bulk Operations with YAML

Create a YAML file (e.g., `addresses.yaml`):

```yaml
addresses:
  - name: web-server-1
    ip_netmask: 192.168.1.10/32
    description: "Primary web server"
    tags:
      - web
      - production
  - name: db-server-1
    ip_netmask: 192.168.2.20/32
    description: "Database server"
    tags:
      - db
      - production
```

Load the address objects:

```bash
pan-os-cli load objects address --file addresses.yaml
```

## Working with Device Groups

If you're using Panorama, you can specify the device group:

```bash
pan-os-cli set objects address --name app-server --ip-netmask 10.0.0.10/32 --device-group "Production"
```

## Committing Changes

After making changes, you may need to commit them:

```bash
pan-os-cli commit objects changes
```

## Next Steps

Now that you're familiar with the basic commands, explore the [CLI Reference](../cli/index.md) to learn about all available commands and options. You can also look at the [User Guide](../guide/configuration.md) for more advanced usage scenarios.
