# Homelab

Docker Compose stacks for my home server: public sites and game servers at
`*.sqweeb.net`, plus private services reachable only from home or over the VPN.

## Overview

```
Internet ──► home router ──┬─ TCP 80/443 ─► Traefik ─┬─ public sites and game servers
                           │                         └─ private services (LAN/VPN only, 403 otherwise)
                           ├─ TCP 25565 ─► Minecraft
                           └─ UDP 51820 ─► WireGuard (the way in to private services)
```

- **Host:** one Proxmox machine (16 GB RAM). Everything runs on a single Docker VM,
  **docker-04** (`192.168.1.248`). FreeNAS runs on a separate machine and provides the
  music share.
- **Ingress:** Traefik v3 routes by hostname. Each stack declares its routes with Docker
  labels.
- **TLS:** one Let's Encrypt wildcard certificate (`sqweeb.net`, `*.sqweeb.net`) from the
  DNS challenge through Route53. See [traefik/README.md](traefik/README.md).
- **DNS:** Route53, with no wildcard record: a hostname resolves only if it has its own
  record.
- **Planned:** move the private services to a second VM, **docker-private**. See
  [traefik-private/README.md](traefik-private/README.md).

## Stacks

### Public

| Stack                     | Hostname            | What it is                                                                                              | Updates    |
| ------------------------- | ------------------- | ------------------------------------------------------------------------------------------------------- | ---------- |
| [traefik](traefik/)       | —                   | Reverse proxy and TLS. Dashboard on `localhost:8888` (SSH tunnel)                                       | manual     |
| [index](index/)           | `sqweeb.net`, `www` | Landing page: nginx serving [index/site](index/site/)                                                   | manual     |
| [gridlock](gridlock/)     | `gridlock`          | Gridlock web game                                                                                       | Watchtower |
| [dungeons](dungeons/)     | `dungeons`          | Dungeon Loot Adventure; co-op server at `/ws`                                                           | Watchtower |
| [tgp](tgp/)               | `tgp`, `api.tgp`    | Tiny Game Platform: admin/player site, API (gRPC/Connect), Postgres. See [tgp/README.md](tgp/README.md) | Watchtower |
| [larpa](larpa/)           | `larpa`             | LARPA game server (Godot, WebSocket)                                                                    | Watchtower |
| [matchbox](matchbox/)     | `match`             | Matchbox WebRTC signaling server                                                                        | manual     |
| [minecraft](minecraft/)   | port 25565          | Paper server. Not behind Traefik. Console: `docker attach minecraft`                                    | manual     |
| [watchtower](watchtower/) | —                   | Checks every 60 s for new images of the stacks marked Watchtower                                        | manual     |

### Private (LAN and VPN only)

These routers use the `private-only` middleware ([traefik/rules.yml](traefik/rules.yml)),
so anyone outside the LAN, VPN and Docker networks gets 403, even if they send the
hostname to the public IP.

| Stack                       | Hostname                                            | What it is                                                                           |
| --------------------------- | --------------------------------------------------- | ------------------------------------------------------------------------------------ |
| [vaultwarden](vaultwarden/) | `vault`                                             | Password manager (Bitwarden-compatible)                                              |
| [gittea](gittea/)           | `git`                                               | Gitea and its Actions runner. Also the Go module host (`git.sqweeb.net/mikeder/...`) |
| [navidrome](navidrome/)     | `music`                                             | Music streaming from `/mnt/music` (FreeNAS)                                          |
| [wireguard](wireguard/)     | `wg` (admin page); `vpn` is the public VPN endpoint | wg-easy VPN                                                                          |

Not deployed yet: [traefik-private](traefik-private/), the Traefik for docker-private.

## Network and DNS

**Router port forwards to docker-04:** TCP 80, 443 and 25565; UDP 51820. Nothing else is
needed. Every web service goes through Traefik, and no stack publishes other ports.

**Public hostnames** are Route53 CNAMEs to `sqweeb.net`, whose A record is the home IP.
When the home IP changes, only that one record needs updating.

**Private hostnames** resolve to docker-04's LAN IP in two places:
- **Router local DNS** (`vault`, `git`, `music`, `wg` → `192.168.1.248`). LAN devices and VPN
  clients use this. The router won't pass private IPs from public DNS through, so these
  entries are required.
- **Route53** CNAMEs to `docker.sqweeb.net` (A `192.168.1.248`). These are for devices
  that skip the router's DNS, such as browsers with secure DNS turned on. From outside,
  they lead nowhere.

## Running it

Each VM runs the stacks listed in `hosts/<its hostname>` ([hosts/docker-04](hosts/docker-04)):

```bash
./start.sh      # docker compose up -d for each stack
./update.sh     # pull, down, up for each stack, then docker system prune -af
./restart.sh    # restart each stack
./update.sh docker-private   # or name the host list explicitly
```

To work on one stack: `docker compose -f <stack>/docker-compose.yml up -d`.

Traefik doesn't reload `traefik/rules.yml` after `git pull` replaces it (Docker keeps
the old file mounted), so restart Traefik after pulling a change to it.

## Secrets

Each stack that needs secrets reads them from its own `<stack>/.env` on the server.
These are never committed (`**/.env` is in [.gitignore](.gitignore)).

| Stack                    | Needs                                                                                        |
| ------------------------ | -------------------------------------------------------------------------------------------- |
| traefik, traefik-private | Route53 keys for the DNS challenge ([.env.example](traefik/.env.example))                    |
| tgp                      | `AUTH_KEY`, `TGP_DB_PASSWORD`, … ([tgp/README.md](tgp/README.md))                            |
| larpa, dungeons          | `TGP_SERVER_KEY`                                                                             |
| gittea                   | `GITEA_RUNNER_REGISTRATION_TOKEN`                                                            |
| wireguard                | `WG_HOST`, `WG_UI_DOMAIN`, `WG_ADMIN_PASSWORD_HASH` ([.env.example](wireguard/.env.example)) |

Data directories (`*/data`, `vaultwarden/vw-data`, `traefik/acme.json`, …) stay on the
server and are gitignored too.

## Adding a service

1. Create `<stack>/docker-compose.yml` on the external `proxy` network, with Traefik
   labels (the template below), and add the stack to `hosts/docker-04`.
2. **Public:** add a Route53 CNAME `<name>.sqweeb.net → sqweeb.net`.
   **Private:** add `middlewares=private-only@file` to the https router, plus a router
   DNS entry and a Route53 CNAME to `docker.sqweeb.net`.
3. For your own images that should deploy automatically, add the container name to
   the [watchtower](watchtower/docker-compose.yml) command.

```yaml
services:
  myapp:
    container_name: myapp
    image: mikeder/myapp:latest
    restart: unless-stopped
    networks:
      - proxy
    labels:
      - traefik.enable=true
      - traefik.http.routers.myapp-http.entrypoints=http
      - traefik.http.routers.myapp-http.rule=Host(`myapp.sqweeb.net`)
      - traefik.http.routers.myapp-http.middlewares=redirect-https
      - traefik.http.routers.myapp-https.entrypoints=https
      - traefik.http.routers.myapp-https.rule=Host(`myapp.sqweeb.net`)
      - traefik.http.routers.myapp-https.tls=true
      # no tls.certresolver: the wildcard certificate covers it
      # private only: - traefik.http.routers.myapp-https.middlewares=private-only@file
      # if the container listens on several ports:
      # - traefik.http.services.myapp.loadbalancer.server.port=8080
networks:
  proxy:
    external: true
```

Don't publish ports (`ports:`) for web services: a published port skips Traefik and the
host firewall.

## Proxmox VM configs

VM 100 `freenas` (on "pve" host)

```bash
# root@pve:/etc/pve/qemu-server# cat 100.conf
balloon: 0
boot: order=scsi0;ide2;net0
cores: 2
cpu: host
ide2: none,media=cdrom
memory: 16384
name: freenas
net0: virtio=3E:94:1D:50:03:30,bridge=vmbr0,firewall=1
numa: 1
onboot: 1
ostype: l26
scsi0: black1:100/vm-100-disk-1.raw,size=32G
scsi1: /dev/disk/by-id/ata-WDC_WD20EFRX-68EUZN0_WD-WMC4M1155464,size=2000G,serial=WMC4M1155464
scsi2: /dev/disk/by-id/ata-WDC_WD20EFRX-68EUZN0_WD-WCC4M2XPP587,size=2000G,serial=WCC4M2XPP587
scsi3: /dev/disk/by-id/ata-WDC_WD20EFRX-68EUZN0_WD-WCC4M0173865,size=2000G,serial=WCC4M0173865
scsi4: /dev/disk/by-id/ata-WDC_WD20EFRX-68EUZN0_WD-WCC4M7KDVTJ7,size=2000G,serial=WCC4M7KDVTJ7
scsi5: /dev/disk/by-id/ata-WDC_WD20EFRX-68EUZN0_WD-WCC4M6NXP2AJ,size=2000G,serial=WCC4M6NXP2AJ
scsi6: /dev/disk/by-id/ata-WD_Red_SA500_2.5_2TB_25109QD01575,size=1953514584K,serial=25109QD01575
scsihw: virtio-scsi-pci
smbios1: uuid=0469a370-945e-4225-a53e-9f2cc8b7b1ff
sockets: 1
startup: order=1
vmgenid: b74c87a6-b8f7-42ae-a47c-14c426cfb856
```


VM 101 `docker-04` on "liquidwhite" host

```bash
# root@liquidwhite:/etc/pve/qemu-server# cat 101.conf
balloon: 0
boot: order=scsi0;net0
cores: 4
cpu: host
memory: 12288
name: docker-04
net0: virtio=2E:4D:B8:80:EE:A3,bridge=vmbr0,firewall=1
numa: 1
onboot: 1
ostype: l26
scsi0: local-lvm:vm-101-disk-0,size=200G
scsihw: virtio-scsi-pci
smbios1: uuid=5a2f866b-1956-46d0-b5d6-652357a48c16
sockets: 1
startup: order=2
vmgenid: 937a6d16-dba1-484f-b25a-40a0d3a30e08
```
