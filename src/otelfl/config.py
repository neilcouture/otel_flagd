"""Configuration with env var overrides."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Settings:
    flagd_config: Path = field(
        default_factory=lambda: Path(
            os.environ.get(
                "OTELFL_FLAGD_CONFIG",
                os.path.expanduser("~/sideProjects/opentelemetry-demo/src/flagd/demo.flagd.json"),
            )
        )
    )
    locust_url: str = field(
        default_factory=lambda: os.environ.get(
            "OTELFL_LOCUST_URL", "http://10.0.0.5:8080/loadgen/"
        )
    )
    poll_interval: float = field(
        default_factory=lambda: float(os.environ.get("OTELFL_POLL_INTERVAL", "2.0"))
    )
