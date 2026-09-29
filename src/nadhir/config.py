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


# Profiles let the same frozen-detector code run on a different sensor/period without touching
# detector parameters. The default profile reproduces the original OLCI run exactly.
DEFAULT_PROFILE = {
    "name": "olci_v1", "bins_prefix": "olci", "version": "v1", "frozen_name": "frozen_detector_v1",
    "tag": "frozen-detector-v1",
    "data_label": "Sentinel-3 OLCI L2 WFR OC4Me via AWS meeo-s3 mirror",
}


def profile(cfg: dict, name: str | None = None) -> dict:
    """Return cfg with the named profile's overrides (intakes, periods) applied and cfg['profile'] set."""
    import copy
    out = copy.deepcopy(cfg)
    if name in (None, "olci_v1"):
        out["profile"] = dict(DEFAULT_PROFILE)
        return out
    p = copy.deepcopy(cfg["profiles"][name])
    for k in ("intakes", "periods"):
        if k in p:
            out[k] = p.pop(k)
    out["profile"] = {"name": name, **p}
    return out
