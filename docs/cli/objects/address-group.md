# Address Groups

This page documents the commands for managing address groups in PAN-OS using the CLI.

## Overview

Address groups allow you to combine multiple address objects into a single object that can be referenced in security policies and other contexts. PAN-OS supports two types of address groups:

- **Static**: Contains a fixed list of address objects
- **Dynamic**: Uses tags to dynamically include address objects

## Commands

### Creating Address Groups

```bash
pan-os-cli set objects address-group [OPTIONS]
```

#### Create Group Options

| Option | Description | Required |
|--------|-------------|----------|
| `--name` | Name of the address group | Yes |
| `--static-members` | Comma-separated list of address objects (for static groups) | No* |
| `--dynamic-filter` | Tag expression (for dynamic groups) | No* |
| `--description` | Description of the address group | No |
| `--tags` | Tags to apply to the address group | No |
| `--device-group` | Device group (Panorama only, default: "Shared") | No |
| `--vsys` | Virtual system name (default: "vsys1") | No |

\* Either `--static-members` or `--dynamic-filter` is required, but not both.

#### Create Group Examples

Create a static address group:

```bash
pan-os-cli set objects address-group --name web-servers --static-members web-server-1,web-server-2 --description "Web Servers" --tags web,servers
```

Create a dynamic address group:

```bash
pan-os-cli set objects address-group --name production-servers --dynamic-filter "'production' in tags" --description "All Production Servers"
```

### Getting Address Groups

```bash
pan-os-cli get objects address-group [OPTIONS]
```

#### Get Group Options

| Option | Description | Required |
|--------|-------------|----------|
| `--name` | Name of the address group (if omitted, lists all) | No |
| `--device-group` | Device group (Panorama only, default: "Shared") | No |
| `--vsys` | Virtual system name (default: "vsys1") | No |
| `--output` | Output format (json, table, yaml) | No |

#### Get Group Examples

List all address groups:

```bash
pan-os-cli get objects address-group
```

Get a specific address group:

```bash
pan-os-cli get objects address-group --name web-servers
```

List address groups in JSON format:

```bash
pan-os-cli get objects address-group --output json
```

### Deleting Address Groups

```bash
pan-os-cli delete objects address-group [OPTIONS]
```

#### Delete Group Options

| Option | Description | Required |
|--------|-------------|----------|
| `--name` | Name of the address group to delete | Yes |
| `--device-group` | Device group (Panorama only, default: "Shared") | No |
| `--vsys` | Virtual system name (default: "vsys1") | No |

#### Delete Group Examples

Delete an address group:

```bash
pan-os-cli delete objects address-group --name web-servers
```

### Showing Detailed Address Group Information

```bash
pan-os-cli show address-groups [OPTIONS]
```

#### Show Group Options

| Option | Description | Required |
|--------|-------------|----------|
| `--name` | Name of the address group (if omitted, shows all) | No |
| `--device-group` | Device group (Panorama only, default: "Shared") | No |
| `--vsys` | Virtual system name (default: "vsys1") | No |
| `--output` | Output format (json, table, yaml) | No |

#### Show Group Examples

Show details for all address groups:

```bash
pan-os-cli show address-groups
```

Show details for a specific address group:

```bash
pan-os-cli show address-groups --name web-servers
```

### Bulk Loading Address Groups

```bash
pan-os-cli load objects address-group [OPTIONS]
```

#### Load Group Options

| Option | Description | Required |
|--------|-------------|----------|
| `--file` | Path to YAML file containing address groups | Yes |
| `--device-group` | Device group (Panorama only, default: "Shared") | No |
| `--vsys` | Virtual system name (default: "vsys1") | No |
| `--threads` | Number of threads for parallel processing | No |
| `--wait` | Wait for completion of all operations | No |

#### Load Group Examples

Load address groups from a YAML file:

```bash
pan-os-cli load objects address-group --file address-groups.yaml
```

## YAML Structure for Bulk Loading

For bulk loading operations, use the following YAML structure:

```yaml
address_groups:
  - name: web-servers
    static_members:
      - web-server-1
      - web-server-2
    description: "Web Servers Group"
    tags:
      - web
      - servers

  - name: database-servers
    static_members:
      - db-server-1
      - db-server-2
    description: "Database Servers Group"
    tags:
      - database

  - name: production-servers
    dynamic_filter: "'production' in tags"
    description: "All Production Servers"
    tags:
      - dynamic
```

## Working with Member Objects

When creating or modifying static address groups, all referenced member objects must already exist in the system. If you need to create both address objects and groups, you should:

1. Create the address objects first
2. Then create the address groups referring to those objects

For dynamic address groups, tags must be properly defined on the address objects for the filter to work correctly.
