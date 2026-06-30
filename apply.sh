#!/usr/bin/env bash
set -euo pipefail

# Apply all Kubernetes manifests for the homelab stack.
# Requires kubectl configured to point at the k3s cluster.
#
# Prerequisites (run once):
#   kubectl apply -f https://github.com/cert-manager/cert-manager/releases/latest/download/cert-manager.yaml
#   kubectl apply -f k8s/traefik/helmchart-values.yaml
#
# For each service with secrets, copy secret.yaml.example to secret.yaml,
# fill in real values, then apply before running this script:
#   cp k8s/<service>/secret.yaml.example k8s/<service>/secret.yaml
#   kubectl apply -f k8s/<service>/secret.yaml

kubectl apply -f k8s/namespaces.yaml
kubectl apply -f k8s/cert-manager/
kubectl apply -f k8s/traefik/

# Tier 1 — stateless
kubectl apply -f k8s/index/
kubectl apply -f k8s/netdash/
kubectl apply -f k8s/dungeons/
kubectl apply -f k8s/matchbox/
kubectl apply -f k8s/rustadmin/

# Tier 2 — stateful, no DB
kubectl apply -f k8s/larpa/
kubectl apply -f k8s/navidrome/
kubectl apply -f k8s/vaultwarden/
kubectl apply -f k8s/wireguard/

# Tier 3 — stateful + DB (postgres first, then migrate, then app)
kubectl apply -f k8s/clicker/postgres.yaml
kubectl apply -f k8s/tgp/postgres.yaml
kubectl wait --for=condition=Ready pod -l app=clicker-db -n homelab --timeout=120s
kubectl wait --for=condition=Ready pod -l app=tgp-db -n homelab --timeout=120s
kubectl apply -f k8s/clicker/migrate.yaml
kubectl apply -f k8s/tgp/migrate.yaml
kubectl apply -f k8s/clicker/app.yaml
kubectl apply -f k8s/tgp/app.yaml

# Tier 4 — infrastructure/CI
kubectl apply -f k8s/gittea/app.yaml
kubectl wait --for=condition=Ready pod -l app=gitea -n homelab --timeout=180s
kubectl apply -f k8s/gittea/runner.yaml

echo "All manifests applied. Check status with:"
echo "  kubectl get pods -n homelab"
echo "  kubectl get ingress -n homelab"
echo "  kubectl get certificates -n homelab"
