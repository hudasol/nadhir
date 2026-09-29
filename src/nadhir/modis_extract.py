"""Extract MODIS-Aqua daily L3 chlorophyll (ERDDAP erdMH1chla1day subsets) around each intake.

Input: the yearly NetCDF subsets downloaded by the project owner from NOAA CoastWatch ERDDAP
(repo hudasol/nadhir-raw-modis-data, opened READ-ONLY; path in config profiles.modis_v1.data_dir).
Each native 4 km L3 cell is one bin (no re-gridding). NaN cells (cloud, land, no retrieval) produce
no row — nothing is interpolated or filled.

Output (same schema as olci_bins so the frozen detector code is reused unchanged):
  data/derived/modis_bins_<year>.csv.gz   granule(file), date, start_utc, intake, bin_lat, bin_lon, n, s1, s2, dist_km
  data/derived/modis_objects.csv          per source file: sha256, size, time range, ERDDAP history line
"""

from __future__ import annotations

import argparse
import glob
import os

import numpy as np
import pandas as pd
import xarray as xr

from nadhir.config import load_config, profile, repo_path
from nadhir.freeze import sha256
from nadhir.olci_extract import haversine_km


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="modis_v1")
    a = ap.parse_args(argv)
    cfg = profile(load_config(), a.profile)
    p = cfg["profile"]
    data_dir = os.environ.get("NADHIR_MODIS_DIR", p["data_dir"])
    radius = max([cfg["zones"]["primary_radius_km"], *cfg["zones"]["sensitivity_radii_km"]])
    ddir = repo_path(cfg["outputs"]["derived_dir"])
    objs = []
    for f in sorted(glob.glob(os.path.join(data_dir, p["file_glob"]))):
        ds = xr.open_dataset(f)
        lat, lon = ds["latitude"].values.astype(float), ds["longitude"].values.astype(float)
        LAT, LON = np.meshgrid(lat, lon, indexing="ij")
        t = pd.to_datetime(ds["time"].values)
        year = t[0].year
        objs.append({"file": os.path.basename(f), "sha256": sha256(f), "size": os.path.getsize(f),
                     "time_start": t[0].date().isoformat(), "time_end": t[-1].date().isoformat(), "n_days": len(t),
                     "title": ds.attrs.get("title", ""), "processing_version": ds.attrs.get("processing_version", ""),
                     "erddap_history_last": ds.attrs.get("history", "").strip().splitlines()[-1][:200]})
        chl = ds[p["variable"]].values  # (time, lat, lon), mg m-3, NaN where no retrieval
        rows = []
        for name, ic in cfg["intakes"].items():
            d = haversine_km(ic["lat"], ic["lon"], LAT, LON)
            m = d <= radius
            ii, jj = np.where(m)
            sub = chl[:, ii, jj]
            for k in range(len(t)):
                v = sub[k]
                ok = np.isfinite(v) & (v > 0)
                if not ok.any():
                    continue
                x = np.log10(v[ok])
                rows.append(pd.DataFrame({
                    "granule": os.path.basename(f), "date": t[k].date().isoformat(), "start_utc": "",
                    "intake": name, "bin_lat": np.round(LAT[ii[ok], jj[ok]], 4), "bin_lon": np.round(LON[ii[ok], jj[ok]], 4),
                    "n": 1, "s1": x, "s2": x * x, "dist_km": d[ii[ok], jj[ok]]}))
        out = pd.concat(rows) if rows else pd.DataFrame()
        out.to_csv(ddir / f"{p['bins_prefix']}_bins_{year}.csv.gz", index=False, float_format="%.5f")
        print(f"{os.path.basename(f)}: {year}, {len(out)} bin-days", flush=True)
    pd.DataFrame(objs).sort_values("time_start").to_csv(ddir / f"{p['bins_prefix']}_objects.csv", index=False)


if __name__ == "__main__":
    main()
