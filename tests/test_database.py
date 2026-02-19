import pytest
from app.database import Base, get_engine


def test_base_has_metadata():
    assert Base.metadata is not None


def test_get_engine_returns_engine():
    engine = get_engine("sqlite+aiosqlite:///test.db")
    assert engine is not None
