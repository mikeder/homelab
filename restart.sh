#!/bin/bash
# Usage: ./restart.sh [host]   (default: this machine's hostname)
# Runs the stacks listed in hosts/<host>, in order.
set -uo pipefail  # keep going if one stack fails
cd "$(dirname "$0")"

host=${1:-$(hostname -s)}
list=hosts/$host
if [ ! -f "$list" ]; then
    echo "No stack list for '$host'. Known hosts: $(ls hosts | tr '\n' ' ')" >&2
    exit 1
fi

for d in $(grep -vE '^[[:space:]]*(#|$)' "$list"); do
    echo "$d"
    docker compose -f "$d/docker-compose.yml" restart
done
