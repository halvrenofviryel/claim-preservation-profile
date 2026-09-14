"""Shared fixtures. Makes `conformance/validate.py` importable as `validate`."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = REPO_ROOT / "conformance"
SPEC_DIR = REPO_ROOT / "spec" / "v0.1"

sys.path.insert(0, str(CONFORMANCE))


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def spec_text() -> str:
    return (SPEC_DIR / "CLAIM_PRESERVATION_PROFILE.md").read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def negative_fixtures() -> list[dict]:
    return _load(CONFORMANCE / "negative-fixtures.json")


@pytest.fixture(scope="session")
def positive_fixtures() -> list[dict]:
    return _load(CONFORMANCE / "positive-fixtures.json")


@pytest.fixture(scope="session")
def report():
    import validate

    return validate.build_report(CONFORMANCE, SPEC_DIR / "CLAIM_PRESERVATION_PROFILE.md")


@pytest.fixture(scope="session")
def evaluations_by_id(report) -> dict[str, dict]:
    return {e["case_id"]: e for e in report["evaluations"]}
