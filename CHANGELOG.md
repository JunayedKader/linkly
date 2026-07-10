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
