#!/usr/bin/env python3
"""
Migrate Docker Compose stacks to Portainer via API.
Pulls compose files from GitHub and creates stacks in Portainer.

Usage:
    export PORTAINER_TOKEN="your-api-token"
    python3 migrate_to_portainer.py [--cleanup] [--dry-run]

Options:
    --cleanup   Remove unmanaged stacks (stacks not in STACKS list)
    --dry-run   Show what would be done without making changes
"""

import os
import sys
import json
import requests
import argparse
from pathlib import Path
from typing import Optional

PORTAINER_URL = "https://docker.sqweeb.net"
ENDPOINT_ID = 2
GITHUB_REPO = "https://raw.githubusercontent.com/mikeder/homelab/main"
LOCAL_REPO_PATH = Path(__file__).parent

# Stack definitions mapping directory to stack name
STACKS = {
    "matchbox": "Matchbox",
    "navidrome": "Navidrome",
    "dungeons": "Dungeons",
    "larpa": "LARPA",
    "index": "Index",
    "rustadmin": "Rust Admin",
    "clicker": "Clicker",
    "vaultwarden": "Vaultwarden",
    "netdash": "Netdash",
    "gittea": "Gitea",
    "tgp": "TGP",
    "wireguard": "WireGuard",
}


class PortainerAPI:
    def __init__(self, url: str, token: str, dry_run: bool = False):
        self.url = url.rstrip("/")
        self.token = token
        self.dry_run = dry_run
        self.session = requests.Session()
        self.session.headers.update({"X-API-Key": token})
        self.session.verify = False  # Disable SSL verification for self-signed certs
        requests.packages.urllib3.disable_warnings()

    def _request(
        self, method: str, endpoint: str, json_data: Optional[dict] = None, **kwargs
    ) -> dict:
        """Make an API request to Portainer."""
        if self.dry_run and method != "GET":
            return {"dry_run": True}

        url = f"{self.url}/api{endpoint}"
        response = self.session.request(method, url, json=json_data, **kwargs)
        if not response.ok:
            raise requests.HTTPError(
                f"{response.status_code} {response.reason} for url: {url}\nBody: {response.text}",
                response=response,
            )
        return response.json() if response.text else {}

    def get_endpoints(self) -> list:
        """Get all available endpoints/environments."""
        return self._request("GET", "/endpoints")

    def get_stacks(self) -> list:
        """Get all existing stacks."""
        return self._request("GET", "/stacks")

    def get_status(self) -> dict:
        """Get Portainer status (no auth required)."""
        url = f"{self.url}/api/status"
        response = self.session.get(url)
        return response.json() if response.ok else {}

    def create_stack(
        self,
        name: str,
        compose_url: str,
        env_vars: Optional[list] = None,
    ) -> dict:
        """Create a new stack from a compose file URL."""
        payload = {
            "name": name,
            "stackFileContent": self._fetch_compose_file(compose_url),
            "env": env_vars or [],
        }

        return self._request(
            "POST",
            f"/stacks/create/standalone/string?endpointId={ENDPOINT_ID}",
            json_data=payload,
        )

    def delete_stack(self, stack_id: int) -> dict:
        """Delete a stack by ID."""
        return self._request("DELETE", f"/stacks/{stack_id}?endpointId={ENDPOINT_ID}")

    def _fetch_compose_file(self, url: str) -> str:
        """Fetch compose file content from URL."""
        response = requests.get(url, verify=False)
        response.raise_for_status()
        return response.text

    def stack_exists(self, name: str) -> bool:
        """Check if a stack with given name already exists."""
        stacks = self.get_stacks()
        return any(stack["Name"] == name for stack in stacks)

    def get_stack_by_name(self, name: str) -> Optional[dict]:
        """Get stack details by name."""
        stacks = self.get_stacks()
        return next((s for s in stacks if s["Name"] == name), None)

    def get_unmanaged_stacks(self, managed_names: list) -> list:
        """Get stacks that are not in the managed list."""
        all_stacks = self.get_stacks()
        return [s for s in all_stacks if s["Name"] not in managed_names]


def parse_env_file(env_path: Path) -> list:
    """Parse .env file and return list of {"name": key, "value": value} dicts."""
    if not env_path.exists():
        return []

    env_vars = []
    try:
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    env_vars.append({"name": key.strip(), "value": value.strip()})
    except Exception as e:
        print(f"  Warning: Failed to parse {env_path}: {e}")

    return env_vars


def main():
    parser = argparse.ArgumentParser(description="Migrate stacks to Portainer")
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Remove unmanaged stacks (not in STACKS list)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    args = parser.parse_args()

    token = os.getenv("PORTAINER_TOKEN")
    if not token:
        print("Error: PORTAINER_TOKEN environment variable not set")
        print("Usage: export PORTAINER_TOKEN='your-token' && python3 migrate_to_portainer.py")
        sys.exit(1)

    api = PortainerAPI(PORTAINER_URL, token, dry_run=args.dry_run)

    if args.dry_run:
        print("[DRY RUN MODE] No changes will be made\n")

    print(f"Connecting to Portainer at {PORTAINER_URL}...")
    try:
        status = api.get_status()
        print(f"✓ Portainer version: {status.get('Version', 'unknown')}")
        endpoints = api.get_endpoints()
        print("✓ Available endpoints:")
        for ep in endpoints:
            print(f"    [{ep['Id']}] {ep['Name']} ({ep['Type']})")
        api.get_stacks()
        print("✓ Auth token valid\n")
    except Exception as e:
        print(f"✗ Failed to connect: {e}")
        sys.exit(1)

    created = []
    skipped = []
    failed = []

    # Create/update managed stacks
    for directory, stack_name in STACKS.items():
        compose_url = f"{GITHUB_REPO}/{directory}/docker-compose.yml"

        print(f"Processing {stack_name}...")

        if api.stack_exists(stack_name):
            print(f"  → Skipped (already exists)\n")
            skipped.append(stack_name)
            continue

        try:
            # Load environment variables from local .env file
            env_path = LOCAL_REPO_PATH / directory / ".env"
            env_vars = parse_env_file(env_path)
            if env_vars:
                print(f"  → Loaded {len(env_vars)} environment variables")

            result = api.create_stack(stack_name, compose_url, env_vars)
            if args.dry_run:
                print(f"  ✓ Would create stack\n")
            else:
                print(f"  ✓ Created stack (ID: {result.get('Id')})\n")
            created.append(stack_name)
        except Exception as e:
            print(f"  ✗ Failed: {e}\n")
            failed.append((stack_name, str(e)))

    # Cleanup unmanaged stacks
    if args.cleanup:
        print("\n" + "=" * 50)
        print("Cleanup: Finding unmanaged stacks...")
        print("=" * 50 + "\n")

        managed_names = list(STACKS.values())
        unmanaged = api.get_unmanaged_stacks(managed_names)

        if not unmanaged:
            print("No unmanaged stacks found.\n")
        else:
            print(f"Found {len(unmanaged)} unmanaged stack(s):\n")
            for stack in unmanaged:
                print(f"  - {stack['Name']} (ID: {stack['Id']})")

            if not args.dry_run:
                response = input(
                    "\nDelete these unmanaged stacks? (yes/no): "
                ).strip().lower()
                if response == "yes":
                    for stack in unmanaged:
                        try:
                            api.delete_stack(stack["Id"])
                            print(f"  ✓ Deleted {stack['Name']}")
                        except Exception as e:
                            print(f"  ✗ Failed to delete {stack['Name']}: {e}")
                    print()
                else:
                    print("Skipping cleanup.\n")
            else:
                print("\n[DRY RUN] Would delete these stacks\n")

    # Print summary
    print("=" * 50)
    print("Migration Summary")
    print("=" * 50)
    print(f"Created:  {len(created)}")
    if created:
        for name in created:
            print(f"  ✓ {name}")
    print(f"\nSkipped:  {len(skipped)} (already exist)")
    if skipped:
        for name in skipped:
            print(f"  → {name}")
    print(f"\nFailed:   {len(failed)}")
    if failed:
        for name, error in failed:
            print(f"  ✗ {name}: {error}")

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
