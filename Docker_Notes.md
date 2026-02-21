# Docker Notes

## Overview

Docker is a containerization platform that packages applications with their dependencies into isolated containers.

## Key Concepts

### Images

- Blueprints for containers
- Built from Dockerfile
- Immutable snapshots of application code and dependencies

### Containers

- Running instances of images
- Lightweight and isolated environments
- Can be started, stopped, and removed

### Dockerfile

- Instructions to build Docker images
- Line-by-line commands executed sequentially
- Common commands: FROM, RUN, COPY, WORKDIR, ENV, EXPOSE, CMD, ENTRYPOINT

### Docker Compose

- Tool for defining and running multi-container applications
- Uses docker-compose.yml file
- Manages networking and volume mounting between containers

## Common Docker Commands

### Image Management

```bash
docker build -t image_name:tag .              # Build image from Dockerfile
docker images                                  # List all images
docker rmi image_id                            # Remove image
docker pull image_name                         # Pull image from registry
docker push image_name                         # Push image to registry
```

### Container Management

```bash
docker run -d image_name                       # Run container in background
docker ps                                      # List running containers
docker ps -a                                   # List all containers
docker stop container_id                       # Stop running container
docker start container_id                      # Start stopped container
docker rm container_id                         # Remove container
docker logs container_id                       # View container logs
docker exec -it container_id /bin/bash         # Execute command in container
```

### Docker Compose Commands

```bash
docker-compose up                              # Start services
docker-compose up -d                           # Start services in background
docker-compose down                            # Stop and remove services
docker-compose ps                              # List services
docker-compose logs service_name               # View service logs
docker-compose exec service_name bash          # Execute command in service
docker-compose build                           # Build/rebuild services
```

## Dockerfile Best Practices

1. **Use specific base image tags** - Avoid `latest` tag
2. **Minimize layers** - Combine RUN commands with `&&`
3. **Use .dockerignore** - Exclude unnecessary files
4. **Order instructions** - Put frequently changing instructions last
5. **Keep images small** - Use multi-stage builds if needed
6. **Run as non-root** - Create and use application user
7. **Document** - Add labels and comments

## Docker Compose Best Practices

1. **Version control** - Commit docker-compose.yml
2. **Environment files** - Use .env for configuration
3. **Network isolation** - Define custom networks
4. **Volume mounting** - Persist data with volumes
5. **Logging** - Configure logging drivers
6. **Resource limits** - Set CPU and memory limits

## Useful Tips

- Use `docker-compose.override.yml` for development overrides
- Tag images meaningfully (e.g., `app:v1.0.0`)
- Use health checks in containers
- Monitor container resource usage: `docker stats`
- Clean up unused resources: `docker system prune`
- Use named volumes instead of bind mounts for production

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Container exits immediately | Check logs: `docker logs container_id` |
| Port already in use | Change port mapping or stop conflicting container |
| Permission denied | Run with sudo or add user to docker group |
| Out of disk space | Run `docker system prune` |
| Container can't access network | Check docker network configuration |

## References

- [Docker Documentation](https://docs.docker.com)
- [Docker Compose Documentation](https://docs.docker.com/compose)
- [Dockerfile Reference](https://docs.docker.com/engine/reference/builder/)

## Quick Command Reference

### Container Operations

| Action | Command |
|--------|---------|
| Check running containers | `docker ps` |
| Stop containers | `docker compose stop` |
| Stop + remove containers | `docker compose down` |
| Remove containers + volumes | `docker compose down -v` |

### Build & Start

| Action | Command |
|--------|---------|
| Build images | `docker compose build` |
| Start containers | `docker compose up` |
| Start in background | `docker compose up -d` |

### Database & Migrations

| Action | Command |
|--------|---------|
| Create migrations | `docker compose run backend python manage.py makemigrations` |
| Apply migrations | `docker exec mapwala_backend python manage.py migrate` |
| Access database | `docker exec -it mapwala_db psql -U postgres -d mapwala_db` |

---

## 📌 Quick Command Summary (Cheat Sheet)

| Action | Command |
|------|--------|
| Check running containers | `docker ps` |
| Check all containers (running + stopped) | `docker ps -a` |
| Stop containers (keep them) | `docker compose stop` |
| Stop + remove containers | `docker compose down` |
| Stop + remove containers + volumes (⚠️ DB reset) | `docker compose down -v` |
| Build Docker images | `docker compose build` |
| Build images without cache | `docker compose build --no-cache` |
| Start containers | `docker compose up` |
| Start containers in background | `docker compose up -d` |
| Start containers & remove orphans | `docker compose up --remove-orphans` |

---
