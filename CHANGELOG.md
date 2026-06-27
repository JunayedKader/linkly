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
