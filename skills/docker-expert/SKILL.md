---
name: docker-expert
description: >
  This skill MUST be invoked when user says "docker", "container", "compose", "dockerfile".
  SHOULD also invoke when working with CT100, CT104 containers or Proxmox Docker infrastructure.
  Do NOT use for Kubernetes or cloud container services.
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
---

# Docker Expert

Patterns for Docker on Proxmox infrastructure (CT100, 192.168.0.101).

## docker-compose

Always use explicit file path:
```bash
docker compose -f /opt/project/docker-compose.yml up -d
docker compose -f /opt/project/docker-compose.yml logs --tail 50
```

Always include resource limits and restart policy:
```yaml
services:
  app:
    restart: unless-stopped
    mem_limit: 512m
    memswap_limit: 512m
```

## Health checks

Prefer TCP over HTTP for SSE or long-poll endpoints (HTTP check hangs):
```yaml
healthcheck:
  test: ["CMD", "nc", "-z", "localhost", "8080"]
  interval: 30s
  timeout: 5s
  retries: 3
```

Use HTTP only for standard request/response endpoints:
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
```

## Debugging

```bash
docker logs --tail 50 <container>       # recent logs
docker logs --since 5m <container>      # last 5 minutes
docker exec -it <container> sh          # shell into container
docker stats --no-stream                # resource usage snapshot
docker inspect <container> | jq '.[0].State'
```

## Image builds — multi-stage for Python

```dockerfile
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY . .
CMD ["python", "main.py"]
```

Pin base image versions. Never use `latest`.

## Container naming

Pattern: `project-service`. Examples: `rlm-mcp`, `ct100-gitea`, `arqa-proxy`.

## Cleanup

```bash
docker system prune -f          # remove stopped containers + dangling images
docker image prune -a -f        # remove all unused images
```
