# Tiny Game Platform

Admin site at https://tgp.sqweeb.net, API at https://api.tgp.sqweeb.net. Watchtower
updates the `api`, `site` and `migrate` images as they're published.

## Secrets: `tgp/.env` (on the server, never committed)

```bash
AUTH_KEY=...          # signs login tokens; at least 32 characters: openssl rand -base64 48
AUTH_ISSUER=api.tgp.sqweeb.net
DB_DATABASEHOST=db
TGP_DB_PASSWORD=...   # Postgres password for the tgp user: openssl rand -hex 32
SERVER_PORT=8080
```

Compose refuses to start the stack if `TGP_DB_PASSWORD` is missing.

## Changing the database password

`POSTGRES_PASSWORD` only applies when the data directory is first created, so for the
existing database change it in Postgres first, then in `tgp/.env`:

```bash
NEW=$(openssl rand -hex 32)
docker exec -it tinygameplatform-db psql -U tgp -d tgp -c "ALTER USER tgp PASSWORD '$NEW';"
echo "TGP_DB_PASSWORD=$NEW" >> tgp/.env      # (replace the line if it's already there)
docker compose -f tgp/docker-compose.yml up -d   # restart api and migrate with it
```

Between the `ALTER USER` and the `up -d`, the running API keeps its open connections but
can't open new ones, so run the steps back to back.

## Rotating AUTH_KEY

Put a new value in `tgp/.env` and run `docker compose -f tgp/docker-compose.yml up -d`.
Every player and dashboard user is logged out (their tokens were signed with the old
key) and has to log in again.

## Client IPs

The API counts login attempts per client IP. Traefik passes the real one in
`X-Real-Ip` (`SERVER_CLIENTIPHEADER=X-Real-IP`). That's only trustworthy because the API
has no published ports, so every request comes through Traefik, which overwrites the
header. Keep it that way.
