# Commit Operations

This page documents the commands for performing commit operations in PAN-OS using the CLI.

## Overview

After making changes to objects, policies, or other configurations in PAN-OS, you need to commit those changes for them to take effect. The PAN-OS CLI provides commands to manage the commit process.

## Commands

### Committing Changes

```bash
pan-os-cli commit objects changes [OPTIONS]
```

#### Commit Command Options

| Option | Description | Required |
|--------|-------------|----------|
| `--description` | Description for the commit | No |
| `--async` | Perform an asynchronous commit | No |
| `--timeout` | Timeout in seconds for commit operation (default: 600) | No |
| `--device-group` | Device group (Panorama only) | No |
| `--device` | Specific device to commit to (Panorama only) | No |
| `--push` | Push to devices after commit (Panorama only) | No |

#### Commit Command Examples

Commit changes:

```bash
pan-os-cli commit objects changes
```

Commit changes with a description:

```bash
pan-os-cli commit objects changes --description "Updated address objects"
```

Asynchronous commit with a timeout:

```bash
pan-os-cli commit objects changes --async --timeout 1200
```

For Panorama, commit and push changes to devices:

```bash
pan-os-cli commit objects changes --push --device-group "Production"
```

### Checking Commit Status

```bash
pan-os-cli show commit-status [OPTIONS]
```

#### Options

| Option | Description | Required |
|--------|-------------|----------|
| `--job-id` | Job ID to check (required for async commits) | No |
| `--output` | Output format (json, table, yaml) | No |

#### Examples

Check the status of a commit:

```bash
pan-os-cli show commit-status --job-id 123
```

## Tips for Efficient Commits

- Group related changes together to minimize the number of commits
- Use the `--async` option for long-running commits
- Add meaningful descriptions to commits for tracking changes
- For Panorama, use device groups to commit changes to specific sets of devices

## Error Handling

Common commit errors and how to resolve them:

| Error | Cause | Solution |
|-------|-------|----------|
| "Another commit in progress" | A commit is already running | Wait for the current commit to complete |
| "Validation failed" | Configuration has errors | Fix the validation errors and try again |
| "Commit timed out" | Commit took too long | Increase the timeout value |
| "Permission denied" | User lacks commit privileges | Use an account with sufficient privileges |

## Commit Best Practices

1. **Test Before Commit**: Validate configurations before committing
2. **Commit During Maintenance Windows**: Schedule commits during low-traffic periods
3. **Descriptive Commit Messages**: Use clear descriptions for audit purposes
4. **Staged Commits**: For large environments, commit to test devices first
5. **Backup Before Commit**: Export a backup of the configuration before major changes
