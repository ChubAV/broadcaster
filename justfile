# Broadcaster — command runner
# https://github.com/casey/just

set dotenv-load

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
monitoring:
    docker compose -f docker-compose.monitoring.yml up -d

# Stop monitoring stack
monitoring-down:
    docker compose -f docker-compose.monitoring.yml down

# Show Docker logs (follow)
logs *args:
    docker compose logs -f {{ args }}

# Start Docker prod environment
prod-start:
    docker compose -f docker-compose.prod.yml up -d

# Stop Docker prod environment
prod-stop:
    docker compose -f docker-compose.prod.yml down

# Stop Docker prod environment
prod-hard-restart:
    docker compose -f docker-compose.prod.yml down && \\
    docker compose -f docker-compose.prod.yml up -d

# Clean stale group IDs in prod Docker (dry-run by default)
prod-cleanup-schedules *args:
    docker compose -f docker-compose.prod.yml exec web uv run python scripts/cleanup_schedules.py {{ args }}

# Stop Docker prod environment
prod-deploy:
    git pull && \\
    docker compose -f docker-compose.prod.yml build --no-cache && \\
    docker compose -f docker-compose.prod.yml down \\
    && docker compose -f docker-compose.prod.yml up -d
