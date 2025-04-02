# Bulk Operations

One of the key features of PAN-OS CLI is the ability to perform bulk operations using YAML files. This guide explains how to use this powerful capability.

## Overview

Bulk operations allow you to:

- Create multiple objects at once
- Update existing objects in batches
- Apply consistent configurations across your environment
- Integrate with version control and CI/CD pipelines

## Supported Object Types

PAN-OS CLI supports bulk operations for various object types:

- Address objects
- Address groups
- Security zones
- Security policies
- And more...

## YAML File Structure

Each object type has a specific YAML structure. The files typically follow this pattern:

```yaml
object_type_plural:
  - name: object-name-1
    property1: value1
    property2: value2

  - name: object-name-2
    property1: value1
    property2: value2
```

### Example: Address Objects YAML

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

### Example: Address Groups YAML

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

  - name: production-servers
    dynamic_filter: "'production' in tags"
    description: "All Production Servers"
    tags:
      - dynamic
```

## Executing Bulk Operations

Use the `load` command to execute bulk operations:

```bash
pan-os-cli load objects address --file addresses.yaml
```

### Options

| Option | Description |
|--------|-------------|
| `--file` | Path to the YAML file |
| `--device-group` | Device group (Panorama only) |
| `--vsys` | Virtual system |
| `--threads` | Number of threads for parallel processing |
| `--wait` | Wait for completion of operations |
| `--mock` | Run in mock mode without making changes |

## Parallel Processing

PAN-OS CLI can speed up bulk operations by processing multiple objects in parallel using threads. You can control the number of threads using the `--threads` option:

```bash
pan-os-cli load objects address --file addresses.yaml --threads 20
```

The default thread count can be configured in your config file:

```yaml
default:
  # Application settings
  thread_pool_size: 10
  mock_mode: false
```

## Best Practices

### Organizing YAML Files

- Keep related objects in the same file
- Use clear, descriptive names
- Add comments to document complex configurations
- Split large configurations into multiple files

### Version Control

Store your YAML files in a version control system like Git:

```bash
# Example Git workflow
git add addresses.yaml
git commit -m "Add new web servers"
git push
```

### Testing Changes

Use mock mode to test your changes before applying them:

```bash
pan-os-cli load objects address --file addresses.yaml --mock
```

### Validation

Validate your YAML files before running bulk operations:

```bash
pan-os-cli validate objects address --file addresses.yaml
```

## Common Patterns

### Creating Development/Test/Production Configurations

Maintain separate YAML files for different environments:

```text
configs/
  ├── dev/
  │   ├── addresses.yaml
  │   └── address-groups.yaml
  ├── test/
  │   ├── addresses.yaml
  │   └── address-groups.yaml
  └── prod/
      ├── addresses.yaml
      └── address-groups.yaml
```

### Templating YAML Files

For advanced use cases, you can use a templating engine like Jinja2 to generate YAML files dynamically:

```python
import jinja2
import yaml

template = jinja2.Template("""
addresses:
{% for server in servers %}
  - name: {{ server.name }}
    ip_netmask: {{ server.ip }}/32
    description: "{{ server.description }}"
    tags:
      - {{ server.role }}
      - {{ environment }}
{% endfor %}
""")

servers = [
    {"name": "web-1", "ip": "192.168.1.10", "description": "Web Server 1", "role": "web"},
    {"name": "web-2", "ip": "192.168.1.11", "description": "Web Server 2", "role": "web"},
    {"name": "db-1", "ip": "192.168.2.10", "description": "Database Server", "role": "db"}
]

rendered = template.render(servers=servers, environment="production")
with open("addresses.yaml", "w") as f:
    f.write(rendered)
```

## Handling Errors

When running bulk operations, the tool will continue processing even if some operations fail. A summary of successes and failures will be displayed at the end.

For objects that failed to be created or updated, check:

1. That all referenced objects exist
2. There are no naming conflicts
3. The structure of your YAML file is correct

## Real-World Example

This example shows a typical workflow for managing a set of servers in different environments:

1. Create your YAML files (e.g., `addresses.yaml`, `address-groups.yaml`)
2. Store the files in version control
3. Apply changes to development environment
4. Test the changes
5. Apply changes to production environment

```bash
# Step 1: Apply to development
pan-os-cli load objects address --file addresses.yaml --device-group "Development"
pan-os-cli load objects address-group --file address-groups.yaml --device-group "Development"
pan-os-cli commit objects changes --device-group "Development" --description "Add new web servers"

# Step 2: Test the changes
# ...testing happens here...

# Step 3: Apply to production
pan-os-cli load objects address --file addresses.yaml --device-group "Production"
pan-os-cli load objects address-group --file address-groups.yaml --device-group "Production"
pan-os-cli commit objects changes --device-group "Production" --description "Add new web servers"
