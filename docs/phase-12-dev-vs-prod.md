# Phase 12 — Dev vs Prod Compose Workflows

## File structure

| File | Purpose | Auto-loaded |
|---|---|---|
| `docker-compose.yml` | Base config — shared across all environments | Yes, always |
| `docker-compose.override.yml` | Dev overrides — bind mounts, debug mode, exposed ports | Yes, automatically in dev |
| `docker-compose.prod.yml` | Prod overrides — Gunicorn, immutable images, no exposed ports | No — explicit `-f` only |

## Commands

### Dev
\`\`\`bash
# Compose merges docker-compose.yml + docker-compose.override.yml automatically
docker compose up --build -d

# See the effective merged config without running it
docker compose config
\`\`\`

### Prod
\`\`\`bash
# Explicit file list — override.yml is NOT loaded
docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d

# See what prod config looks like
docker compose -f docker-compose.yml -f docker-compose.prod.yml config
\`\`\`

## Merge rules
- Scalar values (string, number): override replaces base
- Maps (environment, labels): merged, override wins on conflicts
- Lists (volumes, ports): appended together
