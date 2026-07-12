
[0.9.0] - 2026-07-13

Added


nginx/nginx.conf — Nginx reverse proxy config with upstream block and proxy headers.
nginx service in docker-compose.yml on frontend network, publishing port 80.


Changed


web service no longer publishes port 5000 to the host — Flask is now internal only.
External traffic enters via Nginx on port 80, forwarded to web:5000 container-to-container.


Docker concepts covered


Reverse proxy pattern: single public entry point, internal app not exposed to host.
Bind mount with :ro flag — config file mounted read-only into Nginx container.
upstream block in Nginx using Compose service-name DNS (web:5000).
Proxy headers: X-Real-IP, X-Forwarded-For, Host — preserving client context through the proxy.
Port publishing shift: only the entry point service (nginx) publishes to host.



[0.8.0] - 2026-07-12

Changed


Dockerfile rewritten as a two-stage build: builder stage installs
dependencies into a venv, runtime stage copies only the venv and app code.


Added


PYTHONDONTWRITEBYTECODE=1 and PYTHONUNBUFFERED=1 runtime env vars.
ARG APP_DIR=/app used across both stages for consistent path config.


Docker concepts covered


Multi-stage builds: FROM ... AS name, COPY --from=name.
Virtual environment as a copyable artifact — clean transfer between stages.
ARG (build-time only) vs ENV (build + runtime) — when to use each.
PYTHONUNBUFFERED=1 — ensures logs appear in docker logs immediately.
PYTHONDONTWRITEBYTECODE=1 — suppresses .pyc files in the container.
Security benefit: pip absent from runtime image — attacker cannot install tools.

[0.7.0] - 2026-07-11

Added


.env.example committed as the credential contract for the project — documents required variables without exposing values.


Changed


docker-compose.yml replaces hardcoded environment: blocks with env_file: - .env on web and db services.
Healthcheck in db service uses ${DB_USER} and ${DB_NAME} variable substitution instead of hardcoded values.


Docker concepts covered


.env file as the gitignored secrets store for local dev.
.env.example as the committed contract documenting required variables.
env_file: vs environment: — file-based injection vs inline declaration.
Compose variable substitution (${VARIABLE}) vs container env injection (env_file) — different stages, different purposes.
Compose auto-loads .env for ${} substitution in the file itself without any config needed.
Upgrade path: hardcoded → .env file → Docker Secrets/Vault (production).


[0.6.0] - 2026-07-10

Added


Redis 7 (Alpine) service in docker-compose.yml on the backend network.
redis==5.0.4 added to requirements.txt.
/cache route in app/app.py demonstrating atomic INCR and Redis ephemerality.
Healthchecks on both db (pg_isready) and redis (redis-cli ping).
depends_on upgraded from simple list to condition: service_healthy — web
waits for both db and redis to pass healthchecks before starting.


Docker concepts covered


depends_on with condition: service_healthy vs service_started.
Healthcheck anatomy: test, interval, timeout, retries, start_period.
CMD vs CMD-SHELL in healthcheck test arrays.
Redis ephemerality: no volume means data resets on every down — contrast with PostgreSQL named volume.
Redis client connection at module level vs per-request — client manages its own pool.




[0.5.0] - 2026-07-10

Changed


docker-compose.yml split into two custom networks: frontend and backend.
web attached to both networks — receives external traffic on frontend, reaches db on backend.
db attached to backend only — isolated from frontend network, no ports published to host.


Docker concepts covered


Custom bridge networks vs default Compose network.
Network-level service isolation: db unreachable from frontend network.
ports vs expose — ports publishes to host, expose is documentation only.
Top-level networks: declaration block mirrors volumes: pattern.
docker network ls and docker network inspect for verifying topology.



[0.4.0] - 2026-07-04

Added


PostgreSQL 16 (Alpine) service in docker-compose.yml with a named volume postgres_data.
psycopg2-binary added to requirements.txt.
/db route in app/app.py that opens a connection and runs SELECT 1 to verify connectivity.
DB credentials injected via environment: block — not hardcoded in application code.


Docker concepts covered


Named volumes vs bind mounts vs anonymous volumes — what survives down vs down -v.
docker volume ls and docker volume inspect.
Official image env vars for first-run initialization (POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD).
depends_on: — starts db before web, but does not wait for PostgreSQL readiness (healthchecks in Phase 6).
Service-name DNS: DB_HOST=db resolves because Compose registers each service name as a hostname on the shared network.

[0.3.0] - 2026-07-04

Added


docker-compose.yml with a single web service: build, ports, environment.
APP_ENV env var read in app/app.py and returned in the health response — gives the environment: key a real purpose.


Docker concepts covered


Compose file schema: services, build vs image, ports, environment.
Compose CLI lifecycle: up --build, up -d, down, ps, logs -f.
Project naming: default (directory name) vs explicit -p flag; container/network naming convention.
What down removes (containers + network) vs what it keeps (images, named volumes).




[0.2.0] - 2026-06-27

Added


docs/phase-2-manual-container-lifecycle.md — documents manual multi-container wiring by hand and why it doesn't scale.


Docker concepts covered


Container inspection: docker top, docker stats, docker inspect, docker exec, docker logs -f.
Manual docker network create and explicit --network attachment per container.
Default container hostname (= container ID) vs name-based DNS on a custom network.


No application code changed this phase — operational/exploratory only.

[0.1.0] - 2026-06-27

Added


Minimal Flask app with a single / health endpoint.
First Dockerfile: FROM, WORKDIR, COPY, RUN, EXPOSE, CMD.
.dockerignore to keep build context minimal.


Docker concepts covered


Image layers and build-cache ordering (dependency install layer kept separate from, and ahead of, app-code layer).
CMD vs ENTRYPOINT semantics.
Manual lifecycle: docker build, docker run -p -d --rm --name, docker ps, docker logs, docker stop.
