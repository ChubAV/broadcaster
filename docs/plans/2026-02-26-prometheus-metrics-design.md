# Prometheus Metrics Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add Prometheus metrics to Broadcaster — HTTP metrics, Celery task metrics (via Flower), and business metrics from DB, with a separate Docker Compose monitoring stack (Prometheus + Grafana).

**Architecture:** HTTP metrics via `prometheus-fastapi-instrumentator` on the web service. Business metrics (active schedules, active users, messages sent) via Prometheus Gauges updated by a background asyncio task that queries the DB every 30s. Celery task metrics via Flower's built-in `/metrics` endpoint. Prometheus + Grafana in a separate `docker-compose.monitoring.yml` sharing a Docker network with the main stack.

**Tech Stack:** prometheus-fastapi-instrumentator, prometheus_client, Prometheus, Grafana, Docker Compose

---

### Task 1: Add prometheus-fastapi-instrumentator dependency

**Files:**
- Modify: `pyproject.toml:7-27`

**Step 1: Add dependency**

In `pyproject.toml`, add to `dependencies` list:

```
"prometheus-fastapi-instrumentator>=7.0.0",
```

After `"passlib[bcrypt]>=1.7.4",` (line 18).

**Step 2: Sync environment**

Run: `uv sync`
Expected: dependency installed, lock file updated

**Step 3: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "feat: add prometheus-fastapi-instrumentator dependency"
```

---

### Task 2: Create app/metrics.py — business metric definitions and updater

**Files:**
- Create: `app/metrics.py`
- Test: `tests/test_metrics.py`

**Step 1: Write the test**

Create `tests/test_metrics.py`:

```python
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from prometheus_client import REGISTRY, CollectorRegistry

from app.metrics import (
    ACTIVE_SCHEDULES,
    ACTIVE_USERS,
    MESSAGES_SENT,
    update_business_metrics,
)


@pytest_asyncio.fixture
async def db_session_with_data(db_session):
    """Seed DB with schedules, subscriptions, and send logs."""
    from datetime import datetime, timezone, timedelta
    from app.models.user import User
    from app.models.schedule import Schedule
    from app.models.subscription import Subscription
    from app.models.send_log import SendLog
    from app.models.ad import Ad
    from app.models.messenger_account import MessengerAccount

    user = User(
        email="metrics@test.com",
        password_hash="hash",
        name="Metrics User",
    )
    db_session.add(user)
    await db_session.flush()

    account = MessengerAccount(
        user_id=user.id,
        messenger_type="tg",
        session_name="test",
        status="active",
    )
    db_session.add(account)
    await db_session.flush()

    ad = Ad(user_id=user.id, title="Test Ad", text="text")
    db_session.add(ad)
    await db_session.flush()

    # 2 active schedules, 1 inactive
    for i in range(2):
        db_session.add(Schedule(
            ad_id=ad.id,
            account_id=account.id,
            is_active=True,
            group_ids=[1],
            days_of_week=[0],
            times_of_day=["12:00"],
        ))
    db_session.add(Schedule(
        ad_id=ad.id,
        account_id=account.id,
        is_active=False,
        group_ids=[1],
        days_of_week=[0],
        times_of_day=["12:00"],
    ))

    # 1 active subscription
    db_session.add(Subscription(
        user_id=user.id,
        plan="basic",
        is_active=True,
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    ))

    # Send logs: 3 tg success, 1 tg failed, 2 wa success
    for _ in range(3):
        db_session.add(SendLog(
            user_id=user.id,
            messenger_type="tg",
            status="sent",
            sent_at=datetime.now(timezone.utc),
        ))
    db_session.add(SendLog(
        user_id=user.id,
        messenger_type="tg",
        status="failed",
        sent_at=datetime.now(timezone.utc),
    ))
    for _ in range(2):
        db_session.add(SendLog(
            user_id=user.id,
            messenger_type="wa",
            status="sent",
            sent_at=datetime.now(timezone.utc),
        ))

    await db_session.commit()
    return db_session


@pytest.mark.asyncio
async def test_update_business_metrics(db_session_with_data):
    await update_business_metrics(db_session_with_data)

    assert ACTIVE_SCHEDULES._value.get() == 2
    assert ACTIVE_USERS._value.get() == 1
    assert MESSAGES_SENT.labels(messenger="tg", status="sent")._value.get() == 3
    assert MESSAGES_SENT.labels(messenger="tg", status="failed")._value.get() == 1
    assert MESSAGES_SENT.labels(messenger="wa", status="sent")._value.get() == 2
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_metrics.py -v`
Expected: FAIL — `app.metrics` module does not exist

**Step 3: Write app/metrics.py**

```python
import structlog
from prometheus_client import Gauge
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schedule import Schedule
from app.models.send_log import SendLog
from app.models.subscription import Subscription

logger = structlog.get_logger(__name__)

# Business gauges — updated by background task every 30s
ACTIVE_SCHEDULES = Gauge(
    "broadcaster_active_schedules",
    "Number of active schedules",
)
ACTIVE_USERS = Gauge(
    "broadcaster_active_users",
    "Number of users with active subscription",
)
MESSAGES_SENT = Gauge(
    "broadcaster_messages_sent_total",
    "Total messages sent (from send_logs)",
    ["messenger", "status"],
)


async def update_business_metrics(session: AsyncSession) -> None:
    """Query DB and update Prometheus gauge values."""
    result = await session.execute(
        select(func.count()).select_from(Schedule).where(Schedule.is_active == True)
    )
    ACTIVE_SCHEDULES.set(result.scalar_one())

    result = await session.execute(
        select(func.count()).select_from(Subscription).where(Subscription.is_active == True)
    )
    ACTIVE_USERS.set(result.scalar_one())

    result = await session.execute(
        select(SendLog.messenger_type, SendLog.status, func.count())
        .where(SendLog.messenger_type.isnot(None))
        .group_by(SendLog.messenger_type, SendLog.status)
    )
    for messenger, status, count in result:
        MESSAGES_SENT.labels(messenger=messenger, status=status).set(count)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_metrics.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/metrics.py tests/test_metrics.py
git commit -m "feat: add business metrics definitions and DB updater"
```

---

### Task 3: Integrate instrumentator and background updater in main.py

**Files:**
- Modify: `app/main.py:1-36` (imports + lifespan)
- Modify: `app/main.py:39-45` (create_app)

**Step 1: Write test for /metrics endpoint**

Add to `tests/test_metrics.py`:

```python
@pytest.mark.asyncio
async def test_metrics_endpoint(client):
    resp = await client.get("/metrics")
    assert resp.status_code == 200
    body = resp.text
    # Check instrumentator default metrics exist
    assert "http_request_duration_seconds" in body or "http_requests" in body
    # Check our custom gauges are present
    assert "broadcaster_active_schedules" in body
    assert "broadcaster_active_users" in body
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_metrics.py::test_metrics_endpoint -v`
Expected: FAIL — `/metrics` returns 404

**Step 3: Modify app/main.py**

Add imports at top of `app/main.py` (after line 6):

```python
import asyncio
from prometheus_fastapi_instrumentator import Instrumentator
```

Update lifespan function to start background metrics updater (replace lines 27-36):

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    engine = get_engine(settings.database_url)
    session_factory = get_session_factory(engine)
    init_db(session_factory)
    app.state.uow_factory = create_uow_factory(session_factory)

    # Start background business metrics updater
    from app.metrics import update_business_metrics

    async def _metrics_loop():
        while True:
            try:
                async with session_factory() as session:
                    await update_business_metrics(session)
            except Exception:
                logger.warning("metrics_update_failed", exc_info=True)
            await asyncio.sleep(30)

    metrics_task = asyncio.create_task(_metrics_loop())
    yield
    metrics_task.cancel()
    await engine.dispose()
```

In `create_app()`, after `app.add_middleware(RequestIdMiddleware)` (line 45), add:

```python
    Instrumentator(
        excluded_handlers=["/health", "/metrics"],
    ).instrument(app).expose(app, endpoint="/metrics")
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_metrics.py -v`
Expected: PASS

**Step 5: Run full test suite**

Run: `uv run pytest tests/ -v`
Expected: All tests pass

**Step 6: Commit**

```bash
git add app/main.py tests/test_metrics.py
git commit -m "feat: integrate Prometheus instrumentator and business metrics updater"
```

---

### Task 4: Add named Docker network and monitoring compose

**Files:**
- Modify: `docker-compose.yml` — add named network `broadcaster`
- Modify: `docker-compose.prod.yml` — add named network `broadcaster`
- Create: `docker-compose.monitoring.yml`
- Create: `monitoring/prometheus.yml`

**Step 1: Add named network to docker-compose.yml**

At the end of `docker-compose.yml`, after the `volumes:` section, add:

```yaml
networks:
  default:
    name: broadcaster
```

**Step 2: Add named network to docker-compose.prod.yml**

At the end of `docker-compose.prod.yml`, after the `volumes:` section, add:

```yaml
networks:
  default:
    name: broadcaster
```

**Step 3: Create monitoring/prometheus.yml**

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: "broadcaster-web"
    static_configs:
      - targets: ["web-broadcaster:8000"]

  - job_name: "broadcaster-flower"
    static_configs:
      - targets: ["flower-broadcaster:5555"]
```

**Step 4: Create docker-compose.monitoring.yml**

```yaml
services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus-broadcaster
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: grafana-broadcaster
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_ADMIN_PASSWORD:-admin}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning:ro
    ports:
      - "3001:3000"
    depends_on:
      - prometheus
    restart: unless-stopped

volumes:
  prometheus_data:
  grafana_data:

networks:
  default:
    name: broadcaster
    external: true
```

**Step 5: Commit**

```bash
git add docker-compose.yml docker-compose.prod.yml docker-compose.monitoring.yml monitoring/prometheus.yml
git commit -m "feat: add monitoring Docker stack with Prometheus"
```

---

### Task 5: Add Grafana provisioning (datasource + dashboard)

**Files:**
- Create: `monitoring/grafana/provisioning/datasources/prometheus.yml`
- Create: `monitoring/grafana/provisioning/dashboards/dashboards.yml`
- Create: `monitoring/grafana/provisioning/dashboards/broadcaster.json`

**Step 1: Create datasource provisioning**

`monitoring/grafana/provisioning/datasources/prometheus.yml`:

```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus-broadcaster:9090
    isDefault: true
```

**Step 2: Create dashboard provisioning config**

`monitoring/grafana/provisioning/dashboards/dashboards.yml`:

```yaml
apiVersion: 1

providers:
  - name: "default"
    orgId: 1
    folder: ""
    type: file
    options:
      path: /etc/grafana/provisioning/dashboards
```

**Step 3: Create Grafana dashboard JSON**

`monitoring/grafana/provisioning/dashboards/broadcaster.json`:

A dashboard with 3 rows:
1. **HTTP**: Request rate, latency p50/p95/p99, error rate
2. **Business**: Active schedules, active users, messages sent by messenger
3. **Celery** (from Flower): Task success/failure rates

The JSON is a standard Grafana dashboard. Key panels:

```json
{
  "dashboard": {
    "title": "Broadcaster",
    "uid": "broadcaster-main",
    "panels": [
      {
        "title": "HTTP Request Rate",
        "type": "timeseries",
        "targets": [{"expr": "rate(http_request_duration_seconds_count[1m])"}],
        "gridPos": {"h": 8, "w": 8, "x": 0, "y": 0}
      },
      {
        "title": "HTTP Latency (p95)",
        "type": "timeseries",
        "targets": [{"expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))"}],
        "gridPos": {"h": 8, "w": 8, "x": 8, "y": 0}
      },
      {
        "title": "HTTP Error Rate (5xx)",
        "type": "timeseries",
        "targets": [{"expr": "rate(http_request_duration_seconds_count{status=~\"5..\"}[1m])"}],
        "gridPos": {"h": 8, "w": 8, "x": 16, "y": 0}
      },
      {
        "title": "Active Schedules",
        "type": "stat",
        "targets": [{"expr": "broadcaster_active_schedules"}],
        "gridPos": {"h": 8, "w": 8, "x": 0, "y": 8}
      },
      {
        "title": "Active Users",
        "type": "stat",
        "targets": [{"expr": "broadcaster_active_users"}],
        "gridPos": {"h": 8, "w": 8, "x": 8, "y": 8}
      },
      {
        "title": "Messages Sent",
        "type": "timeseries",
        "targets": [{"expr": "broadcaster_messages_sent_total", "legendFormat": "{{messenger}} — {{status}}"}],
        "gridPos": {"h": 8, "w": 8, "x": 16, "y": 8}
      }
    ],
    "time": {"from": "now-1h", "to": "now"},
    "refresh": "15s"
  }
}
```

(Full valid Grafana JSON with proper schema version, templating, and panel IDs to be written during implementation.)

**Step 4: Commit**

```bash
git add monitoring/grafana/
git commit -m "feat: add Grafana provisioning with datasource and dashboard"
```

---

### Task 6: Update CLAUDE.md and verify

**Files:**
- Modify: `CLAUDE.md`

**Step 1: Add monitoring commands to CLAUDE.md**

Add to the Commands section:

```markdown
- **Monitoring stack**: `docker compose -f docker-compose.monitoring.yml up -d`
- **Prometheus UI**: http://localhost:9090
- **Grafana UI**: http://localhost:3001 (admin/admin)
```

**Step 2: Run full test suite**

Run: `uv run pytest tests/ -v`
Expected: All 223+ tests pass

**Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add monitoring stack commands to CLAUDE.md"
```
