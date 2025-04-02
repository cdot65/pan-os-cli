# Configuration

This guide explains how to configure the PAN-OS CLI tool for connecting to your Palo Alto Networks devices.

## Authentication Methods

`pan-os-cli` offers multiple ways to configure your authentication credentials:

1. Environment variables
2. Configuration file
3. Command-line arguments (coming soon)

## Environment Variables

Environment variables provide a quick way to set your credentials without modifying files. These variables are read each time you run a command.

### Recommended Method (Uppercase with PANOS\_ prefix)

```bash
export PANOS_USERNAME="your-username"
export PANOS_PASSWORD="your-password" # pragma: allowlist secret
export PANOS_HOSTNAME="panorama.example.com"
```

These uppercase environment variables with the `PANOS_` prefix are the **recommended and most reliable** way to set your credentials.

> **Important**: While the application also checks for lowercase environment variables, these may not be recognized in all scenarios. We recommend using the uppercase `PANOS_` prefixed variables for consistent behavior.

## Configuration File

For persistent configuration, you can create a YAML configuration file at `~/.pan-os-cli/config.yaml`:

```yaml
# PAN-OS CLI Configuration

default:
  # Authentication settings
  username: "your-username"
  password: "your-password" # pragma: allowlist secret
  hostname: "panorama.example.com"
  # api_key: "your-api-key"  # pragma: allowlist secret

  # Application settings
  thread_pool_size: 10 # Number of concurrent threads
  mock_mode: false # Whether to run in mock mode
```

### Configuration File Location

By default, the CLI looks for a configuration file at `~/.pan-os-cli/config.yaml`. You can create this file manually or specify a different path using command-line options.

## Configuration Precedence

When multiple configuration methods are used, the CLI follows this precedence order (highest to lowest):

1. Command-line arguments (when implemented)
2. Environment variables (uppercase `PANOS_` prefix)
3. Environment variables (lowercase)
4. Configuration file
5. Default values

## Testing Your Configuration

You can verify that your configuration is working properly by running:

```bash
pan-os-cli test auth
```

This command will connect to your PAN-OS device and display information about the successful connection.

## Setting Up Different Environments

Dynaconf (the configuration library used by `pan-os-cli`) supports environment-specific configuration. You can define different environments in your config file:

```yaml
default:
  username: "default-username"
  password: "default-password" # pragma: allowlist secret
  hostname: "default-hostname.example.com"

development:
  hostname: "dev-panorama.example.com"

production:
  hostname: "prod-panorama.example.com"
```

To use a specific environment, set the `PANOS_ENV` environment variable:

```bash
export PANOS_ENV=production
pan-os-cli test auth  # Uses production settings
```

## Troubleshooting

If you're experiencing connection issues:

1. Ensure you're using the uppercase `PANOS_` prefixed environment variables
2. Verify the hostname is correct and the device is reachable
3. Check your credentials are correct
4. Run with `--mock` flag to test without making actual API calls
5. Check the error messages for specific connection issues

## Security Best Practices

- Never store credentials in scripts or version control
- Consider using API keys instead of username/password when possible
- Use environment variables for ephemeral access
- Restrict file permissions on your configuration file: `chmod 600 ~/.pan-os-cli/config.yaml`
