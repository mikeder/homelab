# infrastructure/

Cluster infrastructure (MetalLB, cert-manager, Traefik), managed by Flux.
Reconciled by the `infrastructure` Flux `Kustomization` in
[`../clusters/homelab/infrastructure.yaml`](../clusters/homelab/infrastructure.yaml).

This replaces the old `infra/traefik/deploy.sh` manual-install flow — see
[`../infra/traefik/README.md`](../infra/traefik/README.md) for that history.
The three `HelmRelease`s here are pinned to the exact chart versions that
`deploy.sh` had already installed, so Flux's first reconcile adopts the
existing Helm releases rather than reinstalling anything.

## Layout

| Dir            | What                                                          |
|----------------|----------------------------------------------------------------|
| `sources/`     | `HelmRepository` objects (metallb, jetstack, traefik), all in `flux-system` namespace |
| `metallb/`     | LoadBalancer IPs on the LAN. `namespace.yaml` carries the privileged Pod Security Admission override MetalLB's speaker/frr-k8s pods need — see the comment in that file |
| `cert-manager/`| TLS certs via Let's Encrypt HTTP-01, into k8s Secrets |
| `traefik/`     | The proxy itself |

## Bootstrapping Flux (one-time, not done by Claude)

```
brew install fluxcd/tap/flux
export GITHUB_TOKEN=<a PAT with repo scope>   # or `gh auth login` first
flux bootstrap github \
  --owner=mikeder --repository=homelab --branch=main \
  --path=clusters/homelab --personal --token-auth
```

This installs the Flux controllers into the cluster, commits
`clusters/homelab/flux-system/` back to this repo, and starts reconciling —
which picks up this `infrastructure/` tree immediately.

## SOPS secret (required before the `infrastructure` Kustomization goes Ready)

The `infrastructure` Kustomization requests SOPS decryption using a Secret
named `sops-age` in `flux-system`, which does not exist until you create it
(it's never committed to git). There are no encrypted files under
`infrastructure/` yet, but decryption is configured up front so the day one
shows up, no plumbing changes are needed. The corresponding age key is
already in your local sops keyring (`~/Library/Application Support/sops/age/keys.txt`
on macOS) and its public key is registered in [`../.sops.yaml`](../.sops.yaml)
for `infrastructure/**/*.sops.yaml` and `apps-k8s/**/*.sops.yaml`.

Create the secret after bootstrapping:

```
kubectl create secret generic sops-age \
  -n flux-system \
  --from-file=age.agekey=<path to a file containing just the AGE-SECRET-KEY-... line>
```

## Verifying

```
flux get sources helm -A
flux get helmreleases -A
flux get kustomizations -A
kubectl get pods -A
```
