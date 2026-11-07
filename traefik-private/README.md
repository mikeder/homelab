# Private VM (docker-private)

Runs the services only you use: Vaultwarden (`vault.sqweeb.net`), Gitea
(`git.sqweeb.net`), Navidrome (`music.sqweeb.net`) and WireGuard (endpoint
`vpn.sqweeb.net`, admin page `wg.sqweeb.net`).

- Their DNS records point at this VM's **LAN** IP, so they work at home and over the VPN
  and go nowhere from the internet. The names stay the same as before, so apps, git
  remotes and Go module paths (`git.sqweeb.net/...`) keep working.
- The router forwards no TCP ports here, only UDP 51820 for WireGuard.
- Every private router also uses the `private-only` middleware (LAN, VPN and Docker
  addresses only) as a second lock.
- The stacks it runs are listed in `hosts/docker-private`.

## One-time setup

1. In Proxmox, create `docker-private`: 4 GB RAM, 2 cores, a static LAN IP (called
   `PRIVATE_IP` below). Set the OS hostname to `docker-private`, since `start.sh` and
   the other scripts pick the stack list by hostname.
2. Install Docker. Clone this repo to `/home/meder/homelab`, because the compose files
   use absolute paths under it.
3. `docker network create proxy`
4. Mount the music share from FreeNAS at `/mnt/music` (in `/etc/fstab`).
5. Traefik:
   ```bash
   touch traefik-private/acme.json && chmod 600 traefik-private/acme.json
   cp traefik-private/.env.example traefik-private/.env   # same keys as traefik/.env
   ./start.sh
   docker logs -f traefik-private   # wait for the wildcard certificate
   ```
   Create `acme.json` before the first start. If it's missing, Docker creates a directory
   in its place and Traefik can't store certificates.

## Moving vault, git and music

One at a time. Navidrome first (least to lose), Gitea next, Vaultwarden last. Before
moving Vaultwarden, export your vault from the app as an extra backup.

| Stack | Data to copy (besides its `.env`, if any) |
|---|---|
| navidrome | `navidrome/data` |
| gittea | `gittea/data` (also holds the runner's registration) |
| vaultwarden | `vaultwarden/vw-data` |

For each one:

1. On docker-04: `docker compose -f <stack>/docker-compose.yml down`
2. On docker-private, copy its data, keeping owners and permissions:
   ```bash
   sudo rsync -aHAX --numeric-ids --rsync-path="sudo rsync" \
     meder@docker-04:/home/meder/homelab/<dir>/ /home/meder/homelab/<dir>/
   ```
3. Move its line from `hosts/docker-04` to `hosts/docker-private` (commit, pull on
   both VMs), then run `docker compose -f <stack>/docker-compose.yml up -d` on
   docker-private.
4. In Route53, point its A record at `PRIVATE_IP`. TTL is 300, so allow up to five
   minutes.
5. Check that it works from home and over the VPN, and returns 403 from your phone on
   cellular with the VPN off. Delete the old data on docker-04 after a week or so.

## Moving WireGuard

WireGuard changes more than the others: it switches to host networking so VPN
clients keep their `10.8.0.x` addresses (which `private-only` allows) instead of
appearing as a Docker address. Its compose file gets updated at that point.

1. Check which wg-easy version docker-04 runs (shown in the admin page footer).
   `:latest` is v15, which is set up in its admin page instead of the `WG_*` variables
   in `wireguard/docker-compose.yml`. The compose file has to match the version.
2. Stop it on docker-04 and copy `wireguard/config` (it holds the server and client
   keys, so existing clients keep working).
3. Router: forward UDP 51820 to `PRIVATE_IP` instead of docker-04.
4. Route53: add `wg.sqweeb.net` A `PRIVATE_IP` for the admin page. `vpn.sqweeb.net`
   stays a public record pointing at your home IP, because that's the VPN endpoint.
5. Start it on docker-private, then regenerate client configs if DNS or AllowedIPs
   changed (configs made before the stack is fully up can miss the DNS line).
