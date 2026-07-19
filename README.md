# Linkly — Docker & Compose Mastery Project

A URL shortener API built from scratch as a **phased, hands-on Docker learning project**. Each phase adds real functionality while deliberately exercising a specific set of Docker and DevOps concepts. The goal: demonstrate practical depth across the full Docker/Compose skill set through a single, coherent project.

> **Stack:** Python 3.12 / Flask · PostgreSQL 16 · Redis 7 · Nginx 1.27 · Prometheus · Grafana · cAdvisor

---

## Architecture

```
Internet
   │
   ▼
Nginx (port 80)          ← reverse proxy, single public entry point
   │
   ▼
Flask / Gunicorn          ← application layer, non-root, read-only filesystem
   ├── templates/index.html   ← server-rendered frontend (GET /ui)
   ├── PostgreSQL         ← persistent storage, named volume, schema bootstrapped from db/init.sql
   └── Redis              ← ephemeral cache, atomic operations, 1hr TTL on link lookups
Monitoring stack (isolated network)
   ├── Prometheus         ← metrics scraping and storage
   ├── Grafana            ← dashboard visualisation
   └── cAdvisor           ← container resource metrics
```

---

## Quick start

```bash
git clone git@github.com:JunayedKader/linkly.git
cd linkly
cp .env.example .env
docker compose up --build -d
```

On first startup with an empty data volume, PostgreSQL automatically runs `db/init.sql` (mounted read-only into `docker-entrypoint-initdb.d`) to create the schema. This only happens once — if you need to re-run it, you must `docker compose down -v` to wipe the volume first.

```bash
curl localhost              # {"status":"ok","env":"development"}
curl localhost/db           # {"db":"connected"}
curl localhost/cache        # {"cache":"connected","hit_count":1}
curl localhost/ui           # serves the frontend

curl -X POST localhost/shorten \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com"}'
# {"short_url":"http://localhost/aB3xY9","short_code":"aB3xY9","original_url":"https://example.com","created_at":"..."}

curl -L localhost/aB3xY9    # redirects to https://example.com
curl localhost/links        # lists all shortened URLs with click counts
```

### Production mode

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
```

Runs Gunicorn instead of Flask dev server. No source code bind mounts. No db/redis ports exposed to host.

---

## API endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Health check — returns app status and environment |
| `/ui` | GET | Serves the frontend (`templates/index.html`) |
| `/db` | GET | PostgreSQL connectivity check via `SELECT 1` |
| `/cache` | GET | Redis connectivity check with atomic hit counter |
| `/shorten` | POST | Creates a short link. Body: `{"url": "https://..."}`. Returns 400 if body/field missing, 422 if URL fails validation, 201 on success |
| `/<short_code>` | GET | Redirects to the original URL (302). Checks Redis first, falls back to PostgreSQL on cache miss, repopulates cache. Returns 404 if code doesn't exist |
| `/links` | GET | Lists all shortened URLs with click counts, newest first |

Short codes are 6 characters from `[a-zA-Z0-9]` (62^6 ≈ 56 billion combinations), generated with up to 5 collision-retry attempts before failing with a 500.

---

## Project structure

```
linkly/
├── .github/
│   └── workflows/
│       └── ci.yml                  # GitHub Actions CI/CD pipeline
├── app/
│   ├── app.py                      # Flask application
│   └── templates/
│       └── index.html              # Frontend UI
├── db/
│   └── init.sql                    # Schema bootstrap — runs once via docker-entrypoint-initdb.d
├── docs/
│   ├── phase-2-manual-container-lifecycle.md
│   └── phase-12-dev-vs-prod.md
├── nginx/
│   └── nginx.conf                  # Reverse proxy config
├── prometheus/
│   └── prometheus.yml              # Scrape config
├── .dockerignore
├── .env.example                    # Credential contract — copy to .env
├── .gitignore
├── CHANGELOG.md                    # Phase-by-phase Docker concept log
├── Dockerfile                      # Multi-stage build
├── docker-compose.yml              # Base Compose config
├── docker-compose.override.yml     # Dev overrides (auto-loaded)
├── docker-compose.prod.yml         # Prod overrides (explicit -f)
└── requirements.txt
```

---

## Phases completed

Each phase targets a specific Docker concept. Full details in [CHANGELOG.md](CHANGELOG.md).

| Phase | What was built | Docker concepts |
|---|---|---|
| 1 | Base Flask app + first Dockerfile | `FROM`, `WORKDIR`, `COPY`, `RUN`, `EXPOSE`, `CMD` vs `ENTRYPOINT`, layer cache ordering, `.dockerignore` |
| 2 | Manual container lifecycle | `docker top/stats/inspect/exec/logs`, manual network wiring |
| 3 | Compose basics | `docker-compose.yml` schema, `build` vs `image`, `ports`, `environment`, `up/down/ps/logs` |
| 4 | PostgreSQL + volumes | Named vs bind vs anonymous volumes, `down` vs `down -v`, service-name DNS |
| 5 | Custom networks | Frontend/backend isolation, `ports` vs `expose`, `docker network inspect` |
| 6 | Redis + healthchecks | `depends_on` conditions, `service_healthy`, healthcheck anatomy, `CMD` vs `CMD-SHELL` |
| 7 | Secrets handling | `.env` file, `env_file:`, variable substitution, credential management upgrade path |
| 8 | Multi-stage builds | `FROM ... AS`, `COPY --from=`, `ARG` vs `ENV`, `PYTHONUNBUFFERED` |
| 9 | Nginx reverse proxy | Reverse proxy pattern, bind mount `:ro`, upstream DNS, proxy headers |
| 10 | Scaling + resource limits | `--scale`, `deploy.resources`, restart policies, full startup chain healthchecks |
| 11 | Logging + monitoring | `json-file` driver with rotation, Prometheus scrape model, Grafana datasource wiring, monitoring network isolation |
| 12 | Dev vs prod workflows | Compose file layering, `override.yml` auto-load, `docker compose config`, Gunicorn vs dev server |
| 13 | Image distribution + CI/CD | Docker Hub push, image tagging conventions, GitHub Actions pipeline, BuildKit layer caching |
| 14 | Security hardening | Non-root container user, `cap_drop: ALL`, selective `cap_add`, `read_only: true`, `tmpfs`, `no-new-privileges` |
| 15 | Swarm/K8s orientation | Where Compose stops being enough, Swarm vs Kubernetes, concept mapping |

---

## CI/CD pipeline

Every pull request targeting `main`:
- Builds the Docker image
- Runs a smoke test against the `/` endpoint
- Blocks merge if the image fails to start

Every merge to `main`:
- Builds and pushes to Docker Hub with three tags:
  - `sha-<commit>` — immutable, traceable to exact commit
  - `main` — always points to latest main build
  - `latest` — conventional Docker Hub tag

```bash
docker pull junayedkader/linkly-web:latest
```

---

## Security hardening (Phase 14)

Applied consistently across `web` and `db` services:

- Containers run as non-root system accounts (`appuser` for web, `postgres` for db)
- `cap_drop: ALL` on all services — capabilities added back only as needed:
  - `web`: minimal set required for Gunicorn under a read-only filesystem
  - `db`: `CHOWN`, `FOWNER`, `SETUID`, `SETGID`, `DAC_OVERRIDE` — required by PostgreSQL to take ownership of and access `/var/lib/postgresql/data` before dropping privileges
- `read_only: true` on web container — filesystem immutable at runtime
- `tmpfs` mounts for `/tmp` and `__pycache__` — writable in-memory only
- `no-new-privileges: true` on all services — blocks setuid privilege escalation
- Resource limits (`deploy.resources`) on all services — prevents any single container from starving the host
- No credentials in images or committed files — `.env` gitignored, `.env.example` documents required variables

---

## Monitoring

```bash
# cAdvisor — raw container metrics
http://<host>:8080

# Prometheus — query interface
http://<host>:9090

# Grafana — dashboards (admin/admin)
http://<host>:3000
# Add datasource: http://prometheus:9090
# Import dashboard ID: 19792
```

---

## License

MIT — see [LICENSE](LICENSE)
