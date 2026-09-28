"""Load config/nadhir.yaml. Every tunable value lives there, with a cited comment."""

from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / "config" / "nadhir.yaml"


def load_config(path: Path | str | None = None) -> dict:
    with open(path or CONFIG_PATH) as f:
        return yaml.safe_load(f)


def repo_path(rel: str) -> Path:
    return REPO_ROOT / rel
