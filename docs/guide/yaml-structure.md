# YAML Structure

This guide details the YAML file structures used for bulk operations with PAN-OS CLI.

## Overview

YAML files are used to define multiple objects for bulk operations. Each object type has a specific structure that must be followed for successful importing.

## Address Objects

Address objects are defined under the `addresses` key:

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
```

### Address Object Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `name` | string | Yes | Name of the address object |
| `ip_netmask` | string | * | IP with netmask (e.g., 192.168.1.1/32) |
| `ip_range` | string | * | IP range (e.g., 192.168.1.1-192.168.1.10) |
| `fqdn` | string | * | Fully qualified domain name |
| `description` | string | No | Description of the address object |
| `tags` | list | No | List of tags to apply |

\* One of `ip_netmask`, `ip_range`, or `fqdn` is required.

## Address Groups

Address groups are defined under the `address_groups` key:

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

### Address Group Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `name` | string | Yes | Name of the address group |
| `static_members` | list | * | List of address objects for static groups |
| `dynamic_filter` | string | * | Tag expression for dynamic groups |
| `description` | string | No | Description of the address group |
| `tags` | list | No | List of tags to apply |

\* Either `static_members` or `dynamic_filter` is required, but not both.

## Security Policies

Security policies are defined under the `security_policies` key:

```yaml
security_policies:
  - name: Allow Web Traffic
    source_zones:
      - untrust
    destination_zones:
      - trust
    source_addresses:
      - any
    destination_addresses:
      - web-servers
    applications:
      - web-browsing
      - ssl
    services:
      - application-default
    action: allow
    description: "Allow web traffic to internal servers"
    log_start: false
    log_end: true
    disabled: false
    tags:
      - web
```

### Security Policy Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `name` | string | Yes | Name of the security policy |
| `source_zones` | list | Yes | List of source zones |
| `destination_zones` | list | Yes | List of destination zones |
| `source_addresses` | list | Yes | List of source addresses |
| `destination_addresses` | list | Yes | List of destination addresses |
| `applications` | list | Yes | List of applications |
| `services` | list | Yes | List of services |
| `action` | string | Yes | Action to take (allow, deny, drop) |
| `description` | string | No | Description of the policy |
| `log_start` | boolean | No | Whether to log at session start |
| `log_end` | boolean | No | Whether to log at session end |
| `disabled` | boolean | No | Whether the rule is disabled |
| `tags` | list | No | List of tags to apply |

## YAML Best Practices

### Formatting

- Use consistent indentation (2 spaces recommended)
- Use quotes for strings containing special characters
- Use proper list formatting for lists

### Organization

- Group related objects together
- Add comments to explain complex configurations
- Use descriptive names for objects

### Validation

Before using your YAML files, validate them with a YAML linter or the built-in validation command:

```bash
pan-os-cli validate objects address --file addresses.yaml
```

## Example Files

### Combined File Example

You can define multiple object types in a single file:

```yaml
# Address objects
addresses:
  - name: web-server-1
    ip_netmask: 192.168.1.10/32
    tags:
      - web
      - production

# Address groups
address_groups:
  - name: web-servers
    static_members:
      - web-server-1
    tags:
      - web
```

However, it's recommended to keep different object types in separate files for better organization and to use the appropriate load command for each type.

## Templating

For more advanced use cases, you can use templating tools like Jinja2 to generate YAML files programmatically:

```python
# Example of generating YAML with Jinja2
from jinja2 import Template

template = Template("""
addresses:
{% for server in servers %}
  - name: {{ server.name }}
    ip_netmask: {{ server.ip }}/32
    description: "{{ server.description }}"
    tags:
{% for tag in server.tags %}
      - {{ tag }}
{% endfor %}
{% endfor %}
""")

servers = [
    {
        "name": "web-1",
        "ip": "192.168.1.10",
        "description": "Web Server 1",
        "tags": ["web", "production"]
    },
    {
        "name": "web-2",
        "ip": "192.168.1.11",
        "description": "Web Server 2",
        "tags": ["web", "production"]
    }
]

result = template.render(servers=servers)
with open("addresses.yaml", "w") as f:
    f.write(result)
```

This approach is especially useful when generating configurations for multiple environments or when integrating with other systems.
