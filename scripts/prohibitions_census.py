"""Перепись запретов планов вехи — СКЕЛЕТ ИНТЕРФЕЙСА (RED плана 15-01).

Поведения здесь нет намеренно: каждая функция возвращает пустое. Скелет существует
только затем, чтобы модуль `tests/test_planning/test_plan_prohibitions_census.py`
собирался и его сквозное правило падало на УТВЕРЖДЕНИИ («перепись дала 0»), а не на
импорте. Реализация — следующим коммитом плана.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

REGISTRY_RELATIVE_PATH = (
    ".planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-prohibitions-registry.yaml"
)


class CensusError(ValueError):
    """Отказ разбора шапки плана."""


@dataclass(frozen=True, order=True)
class ProhibitionIdentity:
    plan_path: str
    index: int


@dataclass(frozen=True)
class ProhibitionRecord:
    identity: ProhibitionIdentity
    phase: str
    statement: str
    verification: str | None
    status: str | None
    first_key: str


@dataclass(frozen=True)
class NetDecomposition:
    prohibitions: int
    first_key_elsewhere: int
    truths: int
    assumptions: int
    line_net: int

    @property
    def reconstructed(self) -> int:
        return 0


def phase_of(plan_path: str) -> str:
    return ""


def _plan_sources(root: Path) -> dict[str, str]:
    return {}


def parse_failures(sources: Mapping[str, str]) -> list[str]:
    return []


def census(sources: Mapping[str, str]) -> list[ProhibitionRecord]:
    return []


def decomposition(sources: Mapping[str, str]) -> NetDecomposition:
    return NetDecomposition(0, 0, 0, 0, 0)


def phase_breakdown(records) -> dict[str, int]:
    return {}


def load_registry(path: Path) -> dict:
    return {"rows": [], "rows_declared": 0}


def _registry_rows(document: Mapping) -> dict[ProhibitionIdentity, dict]:
    return {}
