"""Shared test fixtures."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from otelfl.core.flagd_client import FlagdClient
from otelfl.core.experiment_logger import ExperimentLogger

# Path to the real flagd config for reference data
REAL_CONFIG = Path(__file__).parent.parent.parent / "opentelemetry-demo/src/flagd/demo.flagd.json"


@pytest.fixture
def sample_config() -> dict:
    """A minimal flagd config for testing."""
    return {
        "$schema": "https://flagd.dev/schema/v0/flags.json",
        "flags": {
            "boolFlag": {
                "description": "A boolean flag",
                "state": "ENABLED",
                "variants": {"on": True, "off": False},
                "defaultVariant": "off",
            },
            "multiFlag": {
                "description": "A multi-variant flag",
                "state": "ENABLED",
                "variants": {"off": 0, "low": 25, "high": 75, "full": 100},
                "defaultVariant": "off",
            },
        },
    }


@pytest.fixture
def config_file(tmp_path: Path, sample_config: dict) -> Path:
    """Write sample config to a temp file and return its path."""
    path = tmp_path / "demo.flagd.json"
    path.write_text(json.dumps(sample_config, indent=2) + "\n")
    return path


@pytest.fixture
def flagd_client(config_file: Path) -> FlagdClient:
    return FlagdClient(config_file)


@pytest.fixture
def experiment_logger() -> ExperimentLogger:
    return ExperimentLogger()


@pytest.fixture
def real_config_file(tmp_path: Path) -> Path | None:
    """Copy the real flagd config to tmp_path for integration-style tests."""
    if not REAL_CONFIG.exists():
        pytest.skip("Real flagd config not found")
    dest = tmp_path / "demo.flagd.json"
    shutil.copy(REAL_CONFIG, dest)
    return dest
