"""Offline deployment contracts for the dynamic MAX worker image."""

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def dry_run(recipe: str) -> str:
    result = subprocess.run(
        ["just", "--dry-run", recipe],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout + result.stderr


def assert_max_build_precedes_worker_teardown(output: str):
    build = output.index("just max-worker-build")
    teardown = output.index('label=broadcaster.role=max-worker')
    assert build < teardown


def test_prod_build_builds_the_dynamic_max_image_after_compose():
    output = dry_run("prod-build")

    assert output.index("docker compose -f docker-compose.prod.yml build") < output.index(
        "just max-worker-build"
    )


def test_prod_deploy_builds_max_image_before_any_dynamic_worker_teardown():
    output = dry_run("prod-deploy")

    assert_max_build_precedes_worker_teardown(output)


def test_prod_hard_deploy_rebuilds_max_image_without_cache_before_teardown():
    output = dry_run("prod-hard-deploy")

    assert "docker compose -f docker-compose.prod.yml build --no-cache" in output
    assert "just max-worker-build --no-cache" in output
    assert_max_build_precedes_worker_teardown(output)


def test_max_worker_build_propagates_git_revision_and_dockerfile_exposes_it():
    output = dry_run("max-worker-build")
    dockerfile = (ROOT / "max_worker" / "Dockerfile").read_text()

    assert "--build-arg MAX_WORKER_BUILD_REVISION=" in output
    assert "broadcaster-max-worker:latest ./max_worker" in output
    assert "ARG MAX_WORKER_BUILD_REVISION=unknown" in dockerfile
    assert "org.opencontainers.image.revision" in dockerfile
    assert "MAX_WORKER_BUILD_REVISION" in dockerfile


def test_max_worker_image_preserves_package_layout_for_module_entrypoint():
    dockerfile = (ROOT / "max_worker" / "Dockerfile").read_text()

    assert "COPY . ./max_worker" in dockerfile
    assert 'CMD ["python", "-m", "max_worker.main"]' in dockerfile
