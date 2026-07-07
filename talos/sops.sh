#!/usr/bin/env bash
# Encrypt/decrypt talos/ secret files with sops.
#
# controlplane.yaml and worker.yaml are talosctl-generated configs full of
# doc comments; sops's YAML store mangles them on round-trip, so those two
# are encrypted as opaque binary blobs instead of field-by-field YAML.
set -euo pipefail

cmd="${1:-}"
dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

yaml_files=("$dir/secrets.yaml" "$dir/kubeconfig" "$dir/talosconfig")
binary_files=("$dir/controlplane.yaml" "$dir/worker.yaml")

case "$cmd" in
  encrypt)
    for f in "${yaml_files[@]}"; do sops -e -i "$f"; done
    for f in "${binary_files[@]}"; do sops -e -i --input-type binary --output-type binary "$f"; done
    ;;
  decrypt)
    for f in "${yaml_files[@]}"; do sops -d -i "$f"; done
    for f in "${binary_files[@]}"; do sops -d -i --input-type binary --output-type binary "$f"; done
    ;;
  edit)
    file="${2:?usage: sops.sh edit <file>}"
    case "$file" in
      *controlplane.yaml|*worker.yaml) sops --input-type binary --output-type binary "$file" ;;
      *) sops "$file" ;;
    esac
    ;;
  *)
    echo "usage: $0 {encrypt|decrypt|edit <file>}" >&2
    exit 1
    ;;
esac
