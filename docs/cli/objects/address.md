# Address Objects

This page documents the commands for managing address objects in PAN-OS using the CLI.

## Overview

Address objects are used to identify network resources (hosts, networks, ranges) that can be used in security policy rules and other contexts within PAN-OS.

## Commands

### Creating Address Objects

```bash
pan-os-cli set objects address [OPTIONS]
```

#### Create Command Options

| Option | Description | Required |
|--------|-------------|----------|
| `--name` | Name of the address object | Yes |
| `--ip-netmask` | IP address with netmask (e.g., 192.168.1.1/32) | No* |
| `--ip-range` | IP address range (e.g., 192.168.1.1-192.168.1.10) | No* |
| `--fqdn` | Fully qualified domain name | No* |
| `--description` | Description of the address object | No |
| `--tags` | Tags to apply to the address object | No |
| `--device-group` | Device group (Panorama only, default: "Shared") | No |
| `--vsys` | Virtual system name (default: "vsys1") | No |

\* One of `--ip-netmask`, `--ip-range`, or `--fqdn` is required.

#### Create Command Examples

Create an address object with an IP netmask:

```bash
pan-os-cli set objects address --name web-server --ip-netmask 192.168.1.100/32 --description "Web Server" --tags web,production
```

Create an address object with an IP range:

```bash
pan-os-cli set objects address --name client-range --ip-range 192.168.10.1-192.168.10.50 --description "Client IP Range"
```

Create an address object with an FQDN:

```bash
pan-os-cli set objects address --name google-dns --fqdn dns.google.com
```

### Getting Address Objects

```bash
pan-os-cli get objects address [OPTIONS]
```

#### Get Command Options

| Option | Description | Required |
|--------|-------------|----------|
| `--name` | Name of the address object (if omitted, lists all) | No |
| `--device-group` | Device group (Panorama only, default: "Shared") | No |
| `--vsys` | Virtual system name (default: "vsys1") | No |
| `--output` | Output format (json, table, yaml) | No |

#### Get Command Examples

List all address objects:

```bash
pan-os-cli get objects address
```

Get a specific address object:

```bash
pan-os-cli get objects address --name web-server
```

List address objects in JSON format:

```bash
pan-os-cli get objects address --output json
```

### Deleting Address Objects

```bash
pan-os-cli delete objects address [OPTIONS]
```

#### Delete Command Options

| Option | Description | Required |
|--------|-------------|----------|
| `--name` | Name of the address object to delete | Yes |
| `--device-group` | Device group (Panorama only, default: "Shared") | No |
| `--vsys` | Virtual system name (default: "vsys1") | No |

#### Delete Command Examples

Delete an address object:

```bash
pan-os-cli delete objects address --name web-server
```

### Showing Detailed Address Information

```bash
pan-os-cli show addresses [OPTIONS]
```

#### Show Command Options

| Option | Description | Required |
|--------|-------------|----------|
| `--name` | Name of the address object (if omitted, shows all) | No |
| `--device-group` | Device group (Panorama only, default: "Shared") | No |
| `--vsys` | Virtual system name (default: "vsys1") | No |
| `--output` | Output format (json, table, yaml) | No |

#### Show Command Examples

Show details for all address objects:

```bash
pan-os-cli show addresses
```

Show details for a specific address object:

```bash
pan-os-cli show addresses --name web-server
```

### Bulk Loading Address Objects

```bash
pan-os-cli load objects address [OPTIONS]
```

#### Load Command Options

| Option | Description | Required |
|--------|-------------|----------|
| `--file` | Path to YAML file containing address objects | Yes |
| `--device-group` | Device group (Panorama only, default: "Shared") | No |
| `--vsys` | Virtual system name (default: "vsys1") | No |
| `--threads` | Number of threads for parallel processing | No |
| `--wait` | Wait for completion of all operations | No |

#### Load Command Examples

Load address objects from a YAML file:

```bash
pan-os-cli load objects address --file addresses.yaml
```

## YAML Structure for Bulk Loading

For bulk loading operations, use the following YAML structure:

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

  - name: dns-server
    fqdn: dns.example.com
    description: "DNS Server"
    tags:
      - dns
