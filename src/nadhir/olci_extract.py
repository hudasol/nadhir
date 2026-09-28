"""Extract flag-screened OLCI OC4Me chlorophyll around each intake into 0.05° bin statistics.

For each granule in data/derived/olci_index.csv that could reach an intake's largest watch radius:
  1. read tie_geo_coordinates.nc (small) to choose a pixel window around the intake (selection only);
  2. read that window of geo_coordinates.nc, chl_oc4me.nc and wqsf.nc via HTTP range requests
     (whole objects are fetched into memory, never written to disk; see RemoteFile);
  3. discard every pixel with any reject flag, or a fill value;
  4. aggregate the remaining pixels per 0.05° bin: n, sum(log10 chl), sum(log10 chl ^ 2).

Nothing is interpolated or filled: a bin with no valid pixels simply has no row.
Provenance: every remote object read is logged with its S3 ETag, size and Last-Modified in
data/derived/olci_objects.csv, so each derived number traces to identified source files.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import math
import sys
import threading
from concurrent.futures import ProcessPoolExecutor, as_completed

import h5py
import numpy as np
import pandas as pd
import requests

from nadhir.config import load_config, repo_path

_tls = threading.local()


def _session() -> requests.Session:
    if not hasattr(_tls, "s"):
        _tls.s = requests.Session()
    return _tls.s


class RemoteFile(io.BytesIO):
    """Whole remote object fetched into memory (never written to disk), with provenance.

    Full GETs measured at ~300 MB/s aggregate vs ~3 MB/s per HTTP range request through this
    environment's proxy (data/SOURCE_STATUS.md), so whole-object reads are used; the server-side
    subsetting happens at granule level (only granules overlapping an intake zone are read).
    """

    def __init__(self, url: str, attempts: int = 4):
        for attempt in range(attempts):
            try:
                r = _session().get(url, timeout=300)
                r.raise_for_status()
                break
            except requests.RequestException:
                if attempt == attempts - 1:
                    raise
        super().__init__(r.content)
        self.size = len(r.content)
        self.etag = r.headers.get("ETag", "").strip('"')
        self.last_modified = r.headers.get("Last-Modified", "")
        self.sha256 = hashlib.sha256(r.content).hexdigest()


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dp, dl = p2 - p1, np.radians(np.asarray(lon2) - lon1)
    a = np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * r * np.arcsin(np.sqrt(a))


def reject_mask(flag_names: list[str], flag_masks, reject: list[str]) -> np.uint64:
    lookup = dict(zip(flag_names, [int(m) for m in flag_masks]))
    missing = [f for f in reject if f not in lookup]
    if missing:
        raise KeyError(f"reject flags not in product: {missing}")
    m = 0
    for f in reject:
        m |= lookup[f]
    return np.uint64(m)


def bin_pixels(lat, lon, logchl, bin_deg, min_px, intake_lat, intake_lon, radius_km):
    """Aggregate valid pixels to bins; returns DataFrame (bin_lat, bin_lon, n, s1, s2, dist_km)."""
    ib = np.floor(lat / bin_deg).astype(np.int64)
    jb = np.floor(lon / bin_deg).astype(np.int64)
    df = pd.DataFrame({"ib": ib, "jb": jb, "x": logchl})
    g = df.groupby(["ib", "jb"])["x"].agg(n="count", s1="sum", s2=lambda v: float(np.sum(v * v)))
    g = g[g["n"] >= min_px].reset_index()
    g["bin_lat"] = np.round((g["ib"] + 0.5) * bin_deg, 4)
    g["bin_lon"] = np.round((g["jb"] + 0.5) * bin_deg, 4)
    g["dist_km"] = haversine_km(intake_lat, intake_lon, g["bin_lat"].values, g["bin_lon"].values)
    g = g[g["dist_km"] <= radius_km]
    return g[["bin_lat", "bin_lon", "n", "s1", "s2", "dist_km"]]


def window_from_tiepoints(tlat, tlon, lat0, lon0, radius_km, margin, sub):
    d = haversine_km(lat0, lon0, tlat, tlon)
    rr, cc = np.where(d <= radius_km + 5)
    if rr.size == 0:
        return None
    r0, r1 = max(0, rr.min() - margin), min(tlat.shape[0], rr.max() + margin + 1)
    c0, c1 = max(0, cc.min() * sub - margin), (cc.max() + 1) * sub + margin
    return r0, r1, c0, c1


def process_granule(row: dict, cfg: dict) -> tuple[list[pd.DataFrame], list[dict], list[dict]]:
    o = cfg["sources"]["olci"]
    base = f'{o["bucket_url"]}/{row["prefix"]}'
    radius = max([cfg["zones"]["primary_radius_km"], *cfg["zones"]["sensitivity_radii_km"]])
    out, objs, cov = [], [], []

    tie = RemoteFile(base + "tie_geo_coordinates.nc")
    with h5py.File(tie, "r") as h:
        tlat = h["latitude"][:] * h["latitude"].attrs["scale_factor"][0]
        tlon = h["longitude"][:] * h["longitude"].attrs["scale_factor"][0]
        sub = int(h.attrs["ac_subsampling_factor"][0])  # tie-point column spacing, from file
    objs.append(_obj(row, "tie_geo_coordinates.nc", tie))

    files = {}
    for name, ic in cfg["intakes"].items():
        win = window_from_tiepoints(tlat, tlon, ic["lat"], ic["lon"], radius, o["window_margin_px"], sub)
        if win is None:
            continue
        if not files:
            files = {f: RemoteFile(base + f) for f in o["files"]}
        r0, r1, c0, c1 = win
        with h5py.File(files["geo_coordinates.nc"], "r") as g:
            c1 = min(c1, g["latitude"].shape[1])
            lat = g["latitude"][r0:r1, c0:c1] * g["latitude"].attrs["scale_factor"][0]
            lon = g["longitude"][r0:r1, c0:c1] * g["longitude"].attrs["scale_factor"][0]
        with h5py.File(files["chl_oc4me.nc"], "r") as c:
            v = c[o["chl_variable"]]
            raw = v[r0:r1, c0:c1]
            fill = v.attrs["_FillValue"][0]
            logchl = raw.astype(np.float64) * float(v.attrs["scale_factor"][0]) + float(v.attrs["add_offset"][0])
        with h5py.File(files["wqsf.nc"], "r") as w:
            wv = w["WQSF"]
            fl = wv[r0:r1, c0:c1]
            rm = reject_mask(wv.attrs["flag_meanings"].decode().split(), wv.attrs["flag_masks"], o["reject_flags"])
            water_bit = reject_mask(wv.attrs["flag_meanings"].decode().split(), wv.attrs["flag_masks"], ["WATER"])
        d = haversine_km(ic["lat"], ic["lon"], lat, lon)
        inzone = d <= radius
        water = inzone & ((fl & water_bit) != 0)
        valid = water & ((fl & rm) == 0) & (raw != fill)
        cov.append({"granule": row["prefix"].split("/")[-2], "date": row["date"], "intake": name,
                    "start_utc": row["start_utc"], "n_water_px": int(water.sum()), "n_valid_px": int(valid.sum())})
        if valid.any():
            b = bin_pixels(lat[valid], lon[valid], logchl[valid], cfg["grid"]["bin_deg"],
                           cfg["grid"]["min_pixels_per_bin"], ic["lat"], ic["lon"], radius)
            b.insert(0, "intake", name)
            b.insert(0, "start_utc", row["start_utc"])
            b.insert(0, "date", row["date"])
            b.insert(0, "granule", row["prefix"].split("/")[-2])
            out.append(b)
    for f, fh in files.items():
        objs.append(_obj(row, f, fh))
    return out, objs, cov


def _obj(row, fname, fh: RemoteFile) -> dict:
    return {"granule": row["prefix"].split("/")[-2], "file": fname, "size": fh.size, "sha256": fh.sha256,
            "etag": fh.etag, "last_modified": fh.last_modified}


def granule_may_reach_intake(row, cfg, radius_km) -> bool:
    pad = radius_km / 100.0 + 0.1  # degrees; generous bbox pre-filter only
    for ic in cfg["intakes"].values():
        if (row["lat_min"] - pad <= ic["lat"] <= row["lat_max"] + pad
                and row["lon_min"] - pad <= ic["lon"] <= row["lon_max"] + pad):
            return True
    return False


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", default="data/derived/olci_index.csv")
    ap.add_argument("--start")
    ap.add_argument("--end")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--tag", default="all")
    a = ap.parse_args(argv)
    cfg = load_config()
    radius = max([cfg["zones"]["primary_radius_km"], *cfg["zones"]["sensitivity_radii_km"]])
    idx = pd.read_csv(repo_path(a.index), dtype={"relorb": str, "frame": str, "baseline": str})
    if a.start:
        idx = idx[idx["date"] >= a.start]
    if a.end:
        idx = idx[idx["date"] <= a.end]
    rows = [r for r in idx.to_dict("records") if granule_may_reach_intake(r, cfg, radius)]
    if a.limit:
        rows = rows[: a.limit]
    print(f"{len(rows)} candidate granules", file=sys.stderr)
    bins, objs, cov, fails = [], [], [], []
    with ProcessPoolExecutor(cfg["sources"]["olci"]["workers"]) as ex:
        futs = {ex.submit(process_granule, r, cfg): r for r in rows}
        for i, f in enumerate(as_completed(futs)):
            r = futs[f]
            try:
                b, o, c = f.result()
                bins += b
                objs += o
                cov += c
            except Exception as e:  # logged as a gap, never filled
                fails.append({"granule": r["prefix"], "date": r["date"], "error": repr(e)[:300]})
            if i % 50 == 0:
                print(f"{i}/{len(rows)} done, {len(fails)} failed", file=sys.stderr, flush=True)
    d = repo_path(cfg["outputs"]["derived_dir"])
    d.mkdir(parents=True, exist_ok=True)
    if bins:
        pd.concat(bins).sort_values(["intake", "date", "start_utc", "bin_lat", "bin_lon"]).to_csv(
            d / f"olci_bins_{a.tag}.csv.gz", index=False, float_format="%.5f")
    pd.DataFrame(objs).sort_values(["granule", "file"]).to_csv(d / f"olci_objects_{a.tag}.csv", index=False)
    pd.DataFrame(cov).sort_values(["intake", "date", "start_utc"]).to_csv(d / f"olci_coverage_{a.tag}.csv", index=False)
    pd.DataFrame(fails, columns=["granule", "date", "error"]).to_csv(d / f"olci_failures_{a.tag}.csv", index=False)
    print(f"done: {len(rows)} granules, {len(fails)} failed", file=sys.stderr)


if __name__ == "__main__":
    main()
