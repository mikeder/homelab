# talos/

Talos Linux cluster config and secrets. Everything in this directory except
this README and `sops.sh` is **encrypted at rest with [sops](https://github.com/getsops/sops)**
using [age](https://github.com/FiloSottile/age) — do not commit plaintext
versions of these files.

## Files

| File                | Contents                                                              | sops format |
|---------------------|------------------------------------------------------------------------|-------------|
| `secrets.yaml`       | Cluster/etcd CA keys, service account key, bootstrap tokens (`talosctl gen secrets`) | YAML (per-field) |
| `controlplane.yaml`  | Control plane machine config, embeds the same PKI/tokens               | binary blob |
| `worker.yaml`        | Worker machine config, embeds the same PKI/tokens                      | binary blob |
| `kubeconfig`         | Cluster admin kubeconfig                                               | YAML (per-field) |
| `talosconfig`        | Talos API client config/credentials                                    | YAML (per-field) |

`controlplane.yaml` and `worker.yaml` are encrypted as opaque binary blobs
rather than field-by-field YAML. They're `talosctl`-generated and full of
doc comments, which sops's YAML store mangles on round-trip (comments can
cause a MAC mismatch on decrypt). Encrypting the whole file as binary sidesteps
that — there's no partial-field readability lost anyway since nearly the
whole file is either secret material or comments.

Encryption rules live in [`.sops.yaml`](../.sops.yaml) at the repo root.

## Prerequisites

```
brew install sops age
```

You need the **age private key** that these files were encrypted with. It is
*not* stored in this repo. sops looks for it at:

```
~/Library/Application Support/sops/age/keys.txt   # macOS
~/.config/sops/age/keys.txt                        # Linux
```

(or wherever `$SOPS_AGE_KEY_FILE` points). If you're setting up a new machine,
copy that key file into place before trying to decrypt anything here.

**The age private key is the only way to decrypt these secrets.** It is not
recoverable if lost — back it up in a password manager or other durable,
private storage. Losing it while the cluster is still running just means
re-provisioning the encryption (you can re-encrypt with a new key using the
existing decrypted files); losing it *and* the cluster means regenerating
cluster PKI from scratch.

## Working with these files

Use `./sops.sh` rather than calling `sops` directly — it knows which files
need the binary-mode flags.

```sh
./sops.sh decrypt          # decrypt everything in place
# ...edit files...
./sops.sh encrypt          # re-encrypt everything in place before committing

./sops.sh edit secrets.yaml   # decrypt-edit-reencrypt a single file in $EDITOR
```

Never `git add` these files while they're in decrypted form. `.gitignore` at
the repo root blocks `talos/*.bak` and `talos/*.dec.yaml` as a backstop, but
there's nothing stopping you from `git add`-ing a file you forgot to
re-encrypt in place — check `git diff --staged` looks like ciphertext
(`ENC[AES256_GCM,...`) before committing.

## Rotating the age key

1. Generate a new key: `age-keygen -o new-keys.txt`
2. Add the new public key to `.sops.yaml` (you can list multiple recipients
   during a transition)
3. `./sops.sh decrypt && ./sops.sh encrypt` to re-encrypt under the new rule
4. Remove the old public key from `.sops.yaml` and re-encrypt again
5. Distribute the new private key, retire the old one
