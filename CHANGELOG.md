# Changelog
 
Format loosely follows [Keep a Changelog](https://keepachangelog.com/). Every entry lists not just what changed, but which Docker concept it exists to exercise — that mapping is the point of this project.
 

## [0.13.0] - 2026-07-15

### Added
- `.github/workflows/ci.yml` — GitHub Actions pipeline: builds image on PRs
  (smoke test, no push), builds and pushes to Docker Hub on merge to main.
- Docker Hub image tagging: `sha-*` per commit, `main` branch tag, `latest` on main.
- Layer caching via GitHub Actions cache (`type=gha`) to speed up rebuilds.

### Changed
- `docker-compose.prod.yml` — `web` service now references registry image
  (`your-dockerhub-username/linkly-web:v0.13.0`) instead of building locally.

### Docker concepts covered
- Image tagging conventions: semver pin (`v0.13.0`), minor alias (`v0.13`), `latest`.
- Why prod pins to exact version tag, never `latest`.
- Manual push flow: `docker login`, `docker tag`, `docker push`, `docker pull`.
- `docker/build-push-action` with BuildKit and layer caching.
- GitHub Actions: `on.push`, `on.pull_request`, `jobs`, `steps`, `uses`, `with`.
- GitHub Secrets for credential injection — never hardcoded in workflow files.
- `push: false` on PRs vs `push: true` on main merge — build vs build+publish.
- Smoke test on PR: verifies image starts correctly before merge is allowed.


## [0.12.0] - 2026-07-15

### Added
- `docker-compose.override.yml` — dev overrides: bind-mount source code,
  Flask debug+reload mode, db and redis ports published to host.
- `docker-compose.prod.yml` — prod overrides: Gunicorn WSGI server,
  no source code mounts, no db/redis ports published, restart: always.
- `docs/phase-12-dev-vs-prod.md` — documents file layering workflow and merge rules.
- `gunicorn==22.0.0` added to `requirements.txt`.

### Docker concepts covered
- Compose file layering: base + override merged at runtime.
- `docker-compose.override.yml` auto-loaded in dev, explicit `-f` required for prod.
- Merge rules: scalars replace, maps merge, lists append.
- `docker compose config` — inspect the final merged effective configuration.
- Bind mount for live code reload in dev vs immutable built image in prod.
- Flask dev server vs Gunicorn WSGI in prod — why the built-in server is not production-safe.
- Port exposure strategy: db and redis exposed in dev only, internal-only in prod.

## [0.11.0] - 2026-07-15
 
### Added
- `prometheus/prometheus.yml` — scrape config for Prometheus self-monitoring and cAdvisor.
- `cadvisor` service in `docker-compose.yml` — collects container CPU, memory, network metrics from host kernel interfaces.
- `prometheus` service in `docker-compose.yml` — scrapes cAdvisor every 15s, persists data to `prometheus_data` named volume.
- `grafana` service in `docker-compose.yml` — visualises Prometheus data, persists dashboards to `grafana_data` named volume.
- `monitoring` network — isolates the observability stack from app networks.
- Two new named volumes: `prometheus_data`, `grafana_data`.

### Changed
- `docker-compose.yml` — added `logging` block with `json-file` driver and log rotation (`max-size: 10m`, `max-file: 3`) on all four existing services.

### Docker concepts covered
- `json-file` logging driver with `max-size` and `max-file` rotation options — prevents unbounded disk growth.
- Logging driver alternatives: `syslog`, `journald`, `fluentd`, `awslogs` — `json-file` correct for single-host.
- cAdvisor bind mounts to host kernel interfaces (`/sys`, `/proc`, `/var/run`, `/rootfs`) — how container metrics are collected.
- Docker socket (`/var/run/docker.sock`) mount — how cAdvisor gets container metadata from Docker daemon.
- Prometheus scrape model: pull-based, `scrape_interval`, `job_name`, `static_configs`.
- Grafana datasource wiring using Compose service-name DNS (`http://prometheus:9090`).
- `monitoring` network isolation — observability stack separated from app traffic.


## [0.10.0] - 2026-07-15
 
### Changed
- `docker-compose.yml` — added `restart: unless-stopped` on all four services.
- `docker-compose.yml` — added `deploy.resources` with `limits` and `reservations` on all four services.
- `docker-compose.yml` — added `healthcheck` on `web` service using `urllib.request`.
- `docker-compose.yml` — upgraded `nginx` `depends_on` to `condition: service_healthy` now that `web` has a healthcheck.
- `nginx/nginx.conf` — added inline comments explaining every directive for documentation.

### Docker concepts covered
- Restart policies: `no`, `on-failure`, `always`, `unless-stopped` — when to use each.
- `deploy.resources.limits` — hard kernel-enforced ceiling via cgroups (CPU and memory).
- `deploy.resources.reservations` — soft minimum, informational in plain Compose.
- Healthcheck on `web` using Python stdlib `urllib.request` — no extra packages needed.
- Full startup chain enforcement: `db` healthy → `redis` healthy → `web` healthy → `nginx` starts.
- Scaling with `--scale web=3` — multiple replicas behind Nginx round-robin load balancing.
- Nginx upstream block resolving multiple replicas via Compose service-name DNS.
 


## [0.9.0] - 2026-07-13
 
### Added
- `nginx/nginx.conf` — Nginx reverse proxy config with upstream block and proxy headers.
- `nginx` service in `docker-compose.yml` on `frontend` network, publishing port 80.

### Changed
- `web` service no longer publishes port 5000 to the host — Flask is now internal only.
- External traffic enters via Nginx on port 80, forwarded to `web:5000` container-to-container.

### Docker concepts covered
- Reverse proxy pattern: single public entry point, internal app not exposed to host.
- Bind mount with `:ro` flag — config file mounted read-only into Nginx container.
- `upstream` block in Nginx using Compose service-name DNS (`web:5000`).
- Proxy headers: `X-Real-IP`, `X-Forwarded-For`, `Host` — preserving client context through the proxy.
- Port publishing shift: only the entry point service (`nginx`) publishes to host.


## [0.8.0] - 2026-07-12
 
### Changed
- `Dockerfile` rewritten as a two-stage build: `builder` stage installs
  dependencies into a venv, `runtime` stage copies only the venv and app code.

### Added
- `PYTHONDONTWRITEBYTECODE=1` and `PYTHONUNBUFFERED=1` runtime env vars.
- `ARG APP_DIR=/app` used across both stages for consistent path config.

### Docker concepts covered
- Multi-stage builds: `FROM ... AS name`, `COPY --from=name`.
- Virtual environment as a copyable artifact — clean transfer between stages.
- `ARG` (build-time only) vs `ENV` (build + runtime) — when to use each.
- `PYTHONUNBUFFERED=1` — ensures logs appear in `docker logs` immediately.
- `PYTHONDONTWRITEBYTECODE=1` — suppresses `.pyc` files in the container.
- Security benefit: pip absent from runtime image — attacker cannot install tools.


## [0.7.0] - 2026-07-11
 
### Added
- `.env.example` committed as the credential contract for the project — documents required variables without exposing values.

### Changed
- `docker-compose.yml` replaces hardcoded `environment:` blocks with `env_file: - .env` on `web` and `db` services.
- Healthcheck in `db` service uses `${DB_USER}` and `${DB_NAME}` variable substitution instead of hardcoded values.

### Docker concepts covered
- `.env` file as the gitignored secrets store for local dev.
- `.env.example` as the committed contract documenting required variables.
- `env_file:` vs `environment:` — file-based injection vs inline declaration.
- Compose variable substitution (`${VARIABLE}`) vs container env injection (`env_file`) — different stages, different purposes.
- Compose auto-loads `.env` for `${}` substitution in the file itself without any config needed.
- Upgrade path: hardcoded → `.env` file → Docker Secrets/Vault (production).


## [0.6.0] - 2026-07-10
 
### Added
- Redis 7 (Alpine) service in `docker-compose.yml` on the `backend` network.
- `redis==5.0.4` added to `requirements.txt`.
- `/cache` route in `app/app.py` demonstrating atomic `INCR` and Redis ephemerality.
- Healthchecks on both `db` (`pg_isready`) and `redis` (`redis-cli ping`).
- `depends_on` upgraded from simple list to `condition: service_healthy` — web
  waits for both db and redis to pass healthchecks before starting.

### Docker concepts covered
- `depends_on` with `condition: service_healthy` vs `service_started`.
- Healthcheck anatomy: `test`, `interval`, `timeout`, `retries`, `start_period`.
- `CMD` vs `CMD-SHELL` in healthcheck `test` arrays.
- Redis ephemerality: no volume means data resets on every `down` — contrast with PostgreSQL named volume.
- Redis client connection at module level vs per-request — client manages its own pool.
 


## [0.5.0] - 2026-07-10

### Changed
- `docker-compose.yml` split into two custom networks: `frontend` and `backend`.
- `web` attached to both networks — receives external traffic on `frontend`, reaches `db` on `backend`.
- `db` attached to `backend` only — isolated from frontend network, no ports published to host.

### Docker concepts covered
- Custom bridge networks vs default Compose network.
- Network-level service isolation: `db` unreachable from frontend network.
- `ports` vs `expose` — `ports` publishes to host, `expose` is documentation only.
- Top-level `networks:` declaration block mirrors `volumes:` pattern.
- `docker network ls` and `docker network inspect` for verifying topology.

## [0.4.0] - 2026-07-04

### Added
- PostgreSQL 16 (Alpine) service in `docker-compose.yml` with a named volume `postgres_data`.
- `psycopg2-binary` added to `requirements.txt`.
- `/db` route in `app/app.py` that opens a connection and runs `SELECT 1` to verify connectivity.
- DB credentials injected via `environment:` block — not hardcoded in application code.

### Docker concepts covered
- Named volumes vs bind mounts vs anonymous volumes — what survives `down` vs `down -v`.
- `docker volume ls` and `docker volume inspect`.
- Official image env vars for first-run initialization (`POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`).
- `depends_on:` — starts `db` before `web`, but does not wait for PostgreSQL readiness (healthchecks in Phase 6).
- Service-name DNS: `DB_HOST=db` resolves because Compose registers each service name as a hostname on the shared network.

## [0.3.0] - 2026-07-04

### Added
- `docker-compose.yml` with a single `web` service: `build`, `ports`, `environment`.
- `APP_ENV` env var read in `app/app.py` and returned in the health response — gives the `environment:` key a real purpose.

### Docker concepts covered
- Compose file schema: `services`, `build` vs `image`, `ports`, `environment`.
- Compose CLI lifecycle: `up --build`, `up -d`, `down`, `ps`, `logs -f`.
- Project naming: default (directory name) vs explicit `-p` flag; container/network naming convention.
- What `down` removes (containers + network) vs what it keeps (images, named volumes).


## [0.2.0] - 2026-06-27

### Added
- `docs/phase-2-manual-container-lifecycle.md` — documents manual multi-container wiring by hand and why it doesn't scale.

### Docker concepts covered
- Container inspection: `docker top`, `docker stats`, `docker inspect`, `docker exec`, `docker logs -f`.
- Manual `docker network create` and explicit `--network` attachment per container.
- Default container hostname (= container ID) vs name-based DNS on a custom network.

No application code changed this phase — operational/exploratory only.

## [0.1.0] - 2026-06-27

### Added
- Minimal Flask app with a single `/` health endpoint.
- First `Dockerfile`: `FROM`, `WORKDIR`, `COPY`, `RUN`, `EXPOSE`, `CMD`.
- `.dockerignore` to keep build context minimal.

### Docker concepts covered
- Image layers and build-cache ordering (dependency install layer kept separate from, and ahead of, app-code layer).
- `CMD` vs `ENTRYPOINT` semantics.
- Manual lifecycle: `docker build`, `docker run -p -d --rm --name`, `docker ps`, `docker logs`, `docker stop`.
