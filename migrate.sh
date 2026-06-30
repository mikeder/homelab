#!/bin/bash
# Helper script to run the Portainer migration in Docker

set -e

if [ -z "$PORTAINER_TOKEN" ]; then
    echo "Error: PORTAINER_TOKEN environment variable not set"
    echo "Usage: export PORTAINER_TOKEN='your-token' && ./migrate.sh [options]"
    exit 1
fi

ARGS="${@:---dry-run}"

docker-compose -f docker-compose.migrate.yml run --rm migrate $ARGS
