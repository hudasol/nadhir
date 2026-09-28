"""Calibration-period QA (allowed before the freeze: reads calibration years only).

Processing-baseline step: 2018–2020 granules on the mirror are OLCI collection 002, 2021+ are 003
(data/derived/olci_index.csv). Compare per-bin monthly mean log10 chl between 2019–2020 (002) and
2021 (003) for the same bin and calendar month. A systematic offset would bias z-scores in 2023
(003) relative to 2018 (002). Output: data/derived/qa_baseline_step.csv (per intake) — reported, not corrected.
"""

from __future__ import annotations

import pandas as pd

from nadhir import detector as D
from nadhir.config import load_config, repo_path


def main():
    cfg = load_config()
    dd = repo_path(cfg["outputs"]["derived_dir"])
    daily = D.daily_bins(pd.concat([pd.read_csv(dd / f"olci_bins_{y}.csv.gz") for y in (2019, 2020, 2021)]))
    daily = daily[daily["dist_km"] <= cfg["zones"]["primary_radius_km"]]
    daily["coll"] = (daily["date"].str[:4] == "2021").map({True: "003", False: "002"})
    m = daily.groupby(["intake", "bin_lat", "bin_lon", "month", "coll"])["logchl"].mean().unstack("coll").dropna()
    m["diff_003_minus_002"] = m["003"] - m["002"]
    q = m.groupby("intake")["diff_003_minus_002"].agg(
        n_bin_months="count", median="median", mean="mean",
        p25=lambda v: v.quantile(0.25), p75=lambda v: v.quantile(0.75)).reset_index()
    q["median_ratio_chl"] = 10 ** q["median"]
    q.to_csv(dd / "qa_baseline_step.csv", index=False, float_format="%.4f")
    print(q.to_string())


if __name__ == "__main__":
    main()
