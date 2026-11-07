# Traefik

Routes every public hostname to its container. Certificates come from Let's Encrypt
using the DNS challenge through Route53: one wildcard (`sqweeb.net`, `*.sqweeb.net`)
requested by the `wildcard-cert` router in `rules.yml`.

Routers for `*.sqweeb.net` hostnames set `tls=true` and **no** `tls.certresolver`.
Traefik serves them the wildcard by hostname. Adding a certresolver to a router makes
Traefik request a separate certificate for it, which puts that hostname in public
certificate logs. The exception is wg-easy, whose hostname comes from
`wireguard/.env` and may be on another domain.

## Secrets: `traefik/.env` (on the server, never committed)

Copy `.env.example` and fill it in. Compose refuses to start Traefik without it.

## Route53 access (one-time)

Create an IAM user that can only write `_acme-challenge` TXT records in the zone:

```bash
ZONE_ID=$(aws route53 list-hosted-zones-by-name --dns-name sqweeb.net \
  --query 'HostedZones[0].Id' --output text | cut -d/ -f3)
sed "s/ZONE_ID/$ZONE_ID/" traefik/iam-acme-policy.json > /tmp/acme-policy.json

aws iam create-user --user-name traefik-acme
aws iam put-user-policy --user-name traefik-acme --policy-name route53-acme \
  --policy-document file:///tmp/acme-policy.json
aws iam create-access-key --user-name traefik-acme   # -> traefik/.env
```

## Dashboard

Localhost only (`api.insecure` has no login): `ssh -L 8888:localhost:8888 <server>`,
then open http://localhost:8888.
