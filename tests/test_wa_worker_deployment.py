"""Offline deployment contracts for the dynamic WhatsApp worker image.

Mirror of ``tests/test_max_worker_deployment.py`` (PHONE-16, D-06, owner
decision OQ2 of Phase 19): the deploy recipes must rebuild the WA worker image
before the running WA worker containers are torn down, so that a change to
``wa_worker/`` reaches production together with the application code.

Every check runs ``just --dry-run`` only; no recipe is executed for real.
"""

import subprocess
from pathlib import Path

from app.services.wa_container_manager import WA_WORKER_IMAGE


ROOT = Path(__file__).resolve().parents[1]

WA_TEARDOWN_MARKER = "label=broadcaster.role=wa-worker"


def dry_run(*words: str) -> str:
    result = subprocess.run(
        ["just", "--dry-run", *words],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout + result.stderr


def assert_wa_build_precedes_wa_worker_teardown(output: str, build_line: str):
    assert build_line in output, (
        f"{build_line!r} is missing from the recipe output"
    )
    build = output.index(build_line)
    teardown = output.index(WA_TEARDOWN_MARKER)
    assert build < teardown, (
        "the WA worker image is built after the WA worker containers are stopped"
    )


def test_prod_deploy_builds_the_wa_image_before_any_wa_worker_teardown():
    output = dry_run("prod-deploy")

    assert "just wa-worker-build" in output, (
        "prod-deploy не пересобирает образ WA-воркера"
    )
    assert_wa_build_precedes_wa_worker_teardown(output, "just wa-worker-build")
    assert "just wa-worker-build --no-cache" not in output


def test_wa_worker_build_hands_its_arguments_to_docker_build_with_the_manager_tag():
    output = dry_run("wa-worker-build", "--no-cache")

    assert (
        "docker build --no-cache -t broadcaster-wa-worker:latest ./wa_worker"
        in output
    )
    assert f"-t {WA_WORKER_IMAGE} ./wa_worker" in output
