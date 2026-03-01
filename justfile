# Broadcaster — command runner
# https://github.com/casey/just


# List available recipes
default:
    @just --list

# Run dev server with hot reload
run:
    uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Run tests
test *args:
    uv run pytest tests/ -v {{ args }}

# Run tests with coverage
test-cov:
    uv run pytest tests/ --cov=app --cov-report=term-missing

# Start Docker dev environment
dev:
    docker compose -f docker-compose.yml -f docker-compose.dev.yml up


# Stop all Docker containers
down:
    docker compose down

# Create Alembic migration
migrate message:
    uv run alembic revision --autogenerate -m "{{ message }}"

# Apply Alembic migrations
upgrade:
    uv run alembic upgrade head

# Start Celery worker
worker:
    uv run celery -A app.worker.celery_app worker --loglevel=info

# Start Celery beat scheduler
beat:
    uv run celery -A app.worker.celery_app beat --loglevel=info

# Start both worker and beat (requires worker running separately)
celery:
    uv run celery -A app.worker.celery_app worker --beat --loglevel=info

# Sync uv environment
sync:
    uv sync

# Add a dependency
add *packages:
    uv add {{ packages }}

# Start monitoring stack (Prometheus + Grafana + Loki)
monitoring-start:
    docker compose -f docker-compose.monitoring.yml up -d

# Stop monitoring stack
monitoring-down:
    docker compose -f docker-compose.monitoring.yml down

# Restart monitoring stack
monitoring-restart:
    docker compose -f docker-compose.monitoring.yml restart

# Start Docker prod environment
prod-start:
    docker compose -f docker-compose.prod.yml up -d

# Stop Docker prod environment (including wa-worker and max-worker containers)
prod-stop:
    docker ps -q --filter "label=broadcaster.role=wa-worker" | xargs -r docker stop
    docker ps -aq --filter "label=broadcaster.role=wa-worker" | xargs -r docker rm
    docker ps -q --filter "label=broadcaster.role=max-worker" | xargs -r docker stop
    docker ps -aq --filter "label=broadcaster.role=max-worker" | xargs -r docker rm
    docker compose -f docker-compose.prod.yml down

# Restart Docker prod environment
prod-restart:
    docker compose -f docker-compose.prod.yml restart

# Hard restart Docker prod environment (stop and start)
prod-hard-restart:
    docker ps -q --filter "label=broadcaster.role=wa-worker" | xargs -r docker stop && \
    docker ps -aq --filter "label=broadcaster.role=wa-worker" | xargs -r docker rm; \
    docker ps -q --filter "label=broadcaster.role=max-worker" | xargs -r docker stop && \
    docker ps -aq --filter "label=broadcaster.role=max-worker" | xargs -r docker rm; \
    docker compose -f docker-compose.prod.yml down && \
    docker compose -f docker-compose.prod.yml up -d

# Clean stale group IDs in prod Docker (dry-run by default)
prod-cleanup-schedules *args:
    docker compose -f docker-compose.prod.yml exec web uv run python scripts/cleanup_schedules.py {{ args }}

# Hard deploy to prod environment (build --no-cache and deploy)
prod-hard-deploy:
    git pull && \
    docker compose -f docker-compose.prod.yml build --no-cache && \
    docker ps -q --filter "label=broadcaster.role=wa-worker" | xargs -r docker stop && \
    docker ps -aq --filter "label=broadcaster.role=wa-worker" | xargs -r docker rm; \
    docker ps -q --filter "label=broadcaster.role=max-worker" | xargs -r docker stop && \
    docker ps -aq --filter "label=broadcaster.role=max-worker" | xargs -r docker rm; \
    docker compose -f docker-compose.prod.yml down && \
    docker compose -f docker-compose.prod.yml up -d

# Soft deploy to prod environment (build and deploy)
prod-deploy:
    git pull && \
    docker compose -f docker-compose.prod.yml build && \
    docker ps -q --filter "label=broadcaster.role=wa-worker" | xargs -r docker stop && \
    docker ps -aq --filter "label=broadcaster.role=wa-worker" | xargs -r docker rm; \
    docker ps -q --filter "label=broadcaster.role=max-worker" | xargs -r docker stop && \
    docker ps -aq --filter "label=broadcaster.role=max-worker" | xargs -r docker rm; \
    docker compose -f docker-compose.prod.yml down && \
    docker compose -f docker-compose.prod.yml up -d

# Build Docker image for prod environment
prod-build:
    docker compose -f docker-compose.prod.yml build

# Show Docker logs (follow)
prod-logs *args:
    docker compose -f docker-compose.prod.yml logs -f {{ args }}

# Build wa-worker Docker image
wa-worker-build:
    docker build -t broadcaster-wa-worker:latest ./wa_worker

# List running wa-worker containers
wa-workers:
    docker ps --filter "label=broadcaster.role=wa-worker" --format "table {{{{.Names}}\t{{{{.Status}}\t{{{{.Ports}}"

# Stop all wa-worker containers
wa-workers-stop:
    docker ps -q --filter "label=broadcaster.role=wa-worker" | xargs -r docker stop
    docker ps -aq --filter "label=broadcaster.role=wa-worker" | xargs -r docker rm

# Build max-worker Docker image
max-worker-build:
    docker build -t broadcaster-max-worker:latest ./max_worker

# List running max-worker containers
max-workers:
    docker ps --filter "label=broadcaster.role=max-worker" --format "table {{{{.Names}}\t{{{{.Status}}\t{{{{.Ports}}"

# Stop all max-worker containers
max-workers-stop:
    docker ps -q --filter "label=broadcaster.role=max-worker" | xargs -r docker stop
    docker ps -aq --filter "label=broadcaster.role=max-worker" | xargs -r docker rm
