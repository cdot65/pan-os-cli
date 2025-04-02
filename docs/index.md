# PAN-OS CLI

A command-line interface (CLI) for managing Palo Alto Networks PAN-OS configurations.

## Overview

PAN-OS CLI is a powerful tool designed to simplify the management of Palo Alto Networks firewalls and Panorama appliances. It provides a straightforward command-line interface to perform common operations, such as:

- Managing address objects and address groups
- Configuring network settings
- Managing security policies
- Performing bulk operations through YAML files

## Features

- **Intuitive Command Structure**: Easy-to-remember commands that follow a consistent pattern
- **Bulk Operations**: Import and configure multiple objects at once using YAML files
- **Multi-Threading Support**: Speed up operations with concurrent API calls
- **Flexible Authentication**: Support for username/password or API key authentication
- **Rich Output Formats**: View results in tables, JSON, or other formats

## Quick Start

```bash
# Installation
pip install pan-os-cli

# Set environment variables
export panos_username="EXAMPLE_USERNAME_HERE"
export panos_password="EXAMPLE_PASSWORD_HERE" # pragma: allowlist secret
export panos_host="EXAMPLE_HOSTNAME_HERE"

# Create an address object
pan-os-cli set objects address --name web-server --ip-netmask 192.168.1.100/32

# Bulk load address objects from YAML
pan-os-cli load objects address --file addresses.yaml
```

## Example YAML Structure

```yaml
addresses:
  - name: web-server-1
    ip_netmask: 192.168.1.10/32
    description: "Primary web server"
    tags:
      - web
      - production
```

Check out the [Getting Started](about/getting-started.md) guide for more detailed instructions.
