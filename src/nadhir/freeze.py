"""Blind calibration: build climatology and detector thresholds from calibration years ONLY.

Reads only data/derived/olci_bins_<year>.csv.gz for years inside periods.calibration — event-year
files are never opened here. Writes:
  data/derived/climatology_v1.csv.gz
  data/derived/zone_daily_calibration_v1.csv
  config/frozen_detector_v1.yaml  (thresholds + SHA-256 of every input + config hash + git commit)
The repo is then committed and tagged `frozen-detector-v1` BEFORE nadhir.evaluate runs.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import subprocess

import pandas as pd
import yaml

from nadhir import detector as D
from nadhir.config import CONFIG_PATH, load_config, repo_path


def sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo_path(".")).decode().strip()
    except Exception:
        return "unknown"


def tag_exists(tag: str) -> bool:
    return subprocess.run(["git", "rev-parse", "-q", "--verify", f"refs/tags/{tag}"], cwd=repo_path("."),
                          capture_output=True).returncode == 0


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true",
                    help="recompute into a scratch suffix and compare thresholds with the committed frozen file")
    ap.add_argument("--force", action="store_true", help="overwrite even if tag frozen-detector-v1 exists")
    a = ap.parse_args(argv)
    suffix = "_verify" if a.verify else ""
    if not a.verify and not a.force and tag_exists("frozen-detector-v1"):
        raise SystemExit("tag frozen-detector-v1 exists: refusing to overwrite (use --verify, or --force and log "
                         "the reason in DECISIONS.md)")
    cfg = load_config()
    det, per = cfg["detector"], cfg["periods"]
    cal = per["calibration"]
    years = range(int(cal[0][:4]), int(cal[1][:4]) + 1)
    ddir = repo_path(cfg["outputs"]["derived_dir"])
    files = [ddir / f"olci_bins_{y}.csv.gz" for y in years]
    bins = pd.concat([pd.read_csv(f) for f in files])
    daily = D.daily_bins(bins)
    daily = daily[D.in_period(daily["date"], cal)]
    clim = D.climatology(daily, det["min_clim_days"], det["min_clim_sd"])
    clim_path = ddir / f"climatology_v1{suffix}.csv.gz"
    clim.to_csv(clim_path, index=False, float_format="%.5f")

    dates = D.date_range(*cal)
    all_dates = {k: dates for k in cfg["intakes"]}
    radii = [cfg["zones"]["primary_radius_km"], *cfg["zones"]["sensitivity_radii_km"]]
    thresholds, zds = {}, []
    for r in radii:
        zd = D.zone_daily(daily, clim, r, det["z_threshold"], det["min_valid_bins_frac"], all_dates)
        zd["radius_km"] = r
        zds.append(zd)
        t = D.calibrate_threshold(zd, det["target_daily_false_alarm_rate"], det["min_f_threshold"])
        for _, row in t.iterrows():
            thresholds.setdefault(row["intake"], {})[f"r{r}km"] = {
                "f_threshold": round(float(row["f_threshold"]), 6),
                "f_quantile_raw": round(float(row["f_quantile"]), 6),
                "n_cal_observed_days": int(row["n_cal_obs_days"])}
    zpath = ddir / f"zone_daily_calibration_v1{suffix}.csv"
    pd.concat(zds).to_csv(zpath, index=False, float_format="%.5f")

    frozen = {
        "version": "frozen-detector-v1",
        "frozen_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "code_commit_at_freeze": git_head(),
        "note": "Computed from calibration years only; no event-year file was read. Tag this commit "
                "frozen-detector-v1 before running nadhir.evaluate.",
        "calibration_period": cal,
        "config_sha256": sha256(CONFIG_PATH),
        "detector_params": det,
        "radii_km": radii,
        "primary_radius_km": cfg["zones"]["primary_radius_km"],
        "inputs_sha256": {str(f.relative_to(repo_path("."))): sha256(f) for f in files},
        "climatology": {"path": str(clim_path.relative_to(repo_path("."))), "sha256": sha256(clim_path),
                        "n_bin_months": int(len(clim))},
        "zone_daily_calibration": {"path": str(zpath.relative_to(repo_path("."))), "sha256": sha256(zpath)},
        "thresholds": thresholds,
    }
    if a.verify:
        ref = yaml.safe_load(open(repo_path("config/frozen_detector_v1.yaml")))
        same = ref["thresholds"] == thresholds and ref["climatology"]["sha256"] == frozen["climatology"]["sha256"]
        clim_path.unlink()
        zpath.unlink()
        print("verify-freeze:", "IDENTICAL to committed frozen detector" if same else "DIFFERS from committed frozen detector")
        raise SystemExit(0 if same else 1)
    out = repo_path("config/frozen_detector_v1.yaml")
    with open(out, "w") as f:
        yaml.safe_dump(frozen, f, sort_keys=False)
    print(yaml.safe_dump(thresholds, sort_keys=False))


if __name__ == "__main__":
    main()
