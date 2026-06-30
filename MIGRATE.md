# Portainer Migration Script

Containerized script to migrate Docker Compose stacks to Portainer.

## Quick Start

1. Get your Portainer API token:
   - Log into Portainer (docker.sqweeb.net)
   - Settings → Users → Your Profile
   - Generate an API token

2. Run the migration (dry-run by default):
   ```bash
   export PORTAINER_TOKEN="your-token-here"
   ./migrate.sh
   ```

## Usage

**Dry-run (preview changes):**
```bash
export PORTAINER_TOKEN="your-token"
./migrate.sh --dry-run
```

**Create stacks:**
```bash
export PORTAINER_TOKEN="your-token"
./migrate.sh
```

**Create stacks and cleanup unmanaged ones:**
```bash
export PORTAINER_TOKEN="your-token"
./migrate.sh --cleanup
```

**Dry-run cleanup only:**
```bash
export PORTAINER_TOKEN="your-token"
./migrate.sh --cleanup --dry-run
```

## Environment Variables per Stack

Create a `.env` file in each stack directory to pass environment variables:

```bash
# traefik/.env
ACME_EMAIL=admin@example.com
LOG_LEVEL=INFO
```

The script automatically loads these and passes them to Portainer.

## Files

- `migrate_to_portainer.py` — Main migration script
- `Dockerfile.migrate` — Docker container definition
- `docker-compose.migrate.yml` — Docker Compose configuration
- `migrate.sh` — Helper script for easy execution

## Manual Docker Commands

If you prefer not to use the helper script:

```bash
# Build the image
docker build -f Dockerfile.migrate -t portainer-migrate .

# Run migration (dry-run)
docker run --rm \
  -e PORTAINER_TOKEN="your-token" \
  -v $(pwd):/app \
  portainer-migrate --dry-run

# Run migration (create stacks)
docker run --rm \
  -e PORTAINER_TOKEN="your-token" \
  -v $(pwd):/app \
  portainer-migrate

# Run with cleanup
docker run --rm \
  -e PORTAINER_TOKEN="your-token" \
  -v $(pwd):/app \
  portainer-migrate --cleanup
```
