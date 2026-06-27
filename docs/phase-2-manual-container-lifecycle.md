Phase 2 — Manual Container Lifecycle

Goal: feel the operational pain Compose exists to remove, using only docker run / docker network primitives — no new code this phase.

Commands exercised

docker run -d -p 5000:5000 --name linkly-app linkly:0.1

docker top linkly-app
docker stats --no-stream linkly-app
docker inspect linkly-app
docker exec -it linkly-app /bin/bash
docker logs -f linkly-app

docker network create linkly-net
docker run -d --name linkly-redis --network linkly-net redis:7-alpine
docker stop linkly-app && docker rm linkly-app
docker run -d -p 5000:5000 --name linkly-app --network linkly-net linkly:0.1

Key takeaways


Container hostname defaults to the container ID unless attached to a custom network with name-based DNS — relevant once Compose auto-creates a network in Phase 3+.
docker stats reports live cgroup-enforced resource usage even with no explicit limits set — limits exist by default, just not ones you chose.
Wiring a second container by hand means: manual network create, manual --network flag on every container, and manual stop/rm/recreate of any container whose config needs to change. This does not scale past two services — the exact gap docker-compose.yml fills starting Phase 3.


Cleanup

docker stop linkly-app linkly-redis
docker rm linkly-app linkly-redis
docker network rm linkly-net
