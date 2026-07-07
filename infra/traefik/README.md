# traefik/ — legacy docker-compose stack

`docker-compose.yml` / `traefik.yml` / `rules.yml` here are the **original**
Traefik, still running on the docker-compose VM and still serving real
production traffic (`git.sqweeb.net`, `vault.sqweeb.net`, etc.).

The k8s replacement (MetalLB + cert-manager + Traefik) that used to be
hand-deployed from this directory via `deploy.sh` is now managed by Flux —
see [`../../infrastructure/README.md`](../../infrastructure/README.md).
`deploy.sh` and the `metallb/`, `cert-manager/`, `traefik/` subdirectories
that used to live here are gone; their content moved to
[`../../infrastructure/`](../../infrastructure/) as Flux `HelmRelease`s.

## Cutover checklist (still not done)

- [ ] Make each app in `../../apps/` reachable from the cluster (publish
      LAN ports on the docker VM, or migrate the app into the cluster)
- [ ] Recreate each app's routes as `IngressRoute`/`Middleware` CRDs
      (today's per-app Traefik labels are the reference for the rules)
- [ ] Point router's WAN 80/443 port-forward at the cluster Traefik's
      LoadBalancer IP
- [ ] Point DNS at whatever's in front of that (if it changes)
- [ ] Decommission this docker-compose stack once traffic is confirmed
      flowing through k8s
