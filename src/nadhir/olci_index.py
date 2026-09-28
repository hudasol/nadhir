"""Index Sentinel-3 OLCI L2 WFR granules on the MEEO AWS mirror that overlap the region.

Writes data/derived/olci_index.csv: one row per granule with its footprint bounding box, so the
download step fetches only granules that intersect the configured region (no global pulls).
Every attempted listing is logged; a day with zero granules is recorded as a gap, never filled.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
import sys
from concurrent.futures import ThreadPoolExecutor

import requests

from nadhir.config import load_config, repo_path

NAME_RE = re.compile(
    r"(?P<plat>S3[AB])_OL_2_WFR____(?P<start>\d{8}T\d{6})_(?P<stop>\d{8}T\d{6})_\d{8}T\d{6}_"
    r"(?P<dur>\d{4})_(?P<cycle>\d{3})_(?P<relorb>\d{3})_(?P<frame>\d{4})_\w+?_(?P<baseline>\d{3})\.SEN3"
)
POS_RE = re.compile(r"<gml:posList>([^<]+)</gml:posList>")
KEY_RE = re.compile(r"<Prefix>([^<]+\.SEN3/)</Prefix>")

SESSION = requests.Session()


def list_day(base: str, prefix: str) -> list[str]:
    r = SESSION.get(f"{base}/", params={"list-type": "2", "prefix": prefix, "delimiter": "/",
                                        "max-keys": "1000"}, timeout=60)
    r.raise_for_status()
    return KEY_RE.findall(r.text)


def footprint(base: str, product_prefix: str) -> tuple[float, float, float, float] | None:
    r = SESSION.get(f"{base}/{product_prefix}xfdumanifest.xml", timeout=60)
    r.raise_for_status()
    m = POS_RE.search(r.text)
    if not m:
        return None
    vals = [float(v) for v in m.group(1).split()]
    lats, lons = vals[0::2], vals[1::2]  # posList is "lat lon lat lon ..."
    return min(lons), max(lons), min(lats), max(lats)


def overlaps(bb, reg) -> bool:
    lo0, lo1, la0, la1 = bb
    return not (lo1 < reg["lon_min"] or lo0 > reg["lon_max"] or la1 < reg["lat_min"] or la0 > reg["lat_max"])


def index_day(day: dt.date, cfg: dict) -> tuple[list[dict], list[dict]]:
    ocfg, reg = cfg["sources"]["olci"], cfg["region"]
    base = ocfg["bucket_url"]
    rows, log = [], []
    for plat in ocfg["platforms"]:
        prefix = ocfg["prefix_template"].format(platform=plat, yyyy=f"{day:%Y}", mm=f"{day:%m}", dd=f"{day:%d}")
        try:
            prods = list_day(base, prefix)
        except Exception as e:  # logged, not hidden
            log.append({"date": day.isoformat(), "platform": plat, "status": "list-failed", "detail": str(e)[:200]})
            continue
        log.append({"date": day.isoformat(), "platform": plat, "status": "listed", "detail": f"{len(prods)} products"})
        for p in prods:
            m = NAME_RE.search(p)
            if not m:
                continue
            t = dt.datetime.strptime(m["start"], "%Y%m%dT%H%M%S")
            h = t.hour + t.minute / 60
            if not (ocfg["utc_start_hour_min"] <= h <= ocfg["utc_start_hour_max"]):
                continue
            try:
                bb = footprint(base, p)
            except Exception as e:
                log.append({"date": day.isoformat(), "platform": plat, "status": "manifest-failed",
                            "detail": f"{p}: {str(e)[:150]}"})
                continue
            if bb and overlaps(bb, reg):
                rows.append({"date": day.isoformat(), "platform": plat, "start_utc": t.isoformat(),
                             "relorb": m["relorb"], "frame": m["frame"], "baseline": m["baseline"],
                             "lon_min": bb[0], "lon_max": bb[1], "lat_min": bb[2], "lat_max": bb[3],
                             "prefix": p})
    return rows, log


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--start")
    ap.add_argument("--end")
    ap.add_argument("--out", default="data/derived/olci_index.csv")
    ap.add_argument("--workers", type=int, default=16)
    a = ap.parse_args(argv)
    cfg = load_config()
    s = dt.date.fromisoformat(a.start or cfg["sources"]["olci"]["index_start"])
    e = dt.date.fromisoformat(a.end or cfg["sources"]["olci"]["index_end"])
    days = [s + dt.timedelta(d) for d in range((e - s).days + 1)]
    all_rows, all_log = [], []
    with ThreadPoolExecutor(a.workers) as ex:
        for i, (rows, log) in enumerate(ex.map(lambda d: index_day(d, cfg), days)):
            all_rows += rows
            all_log += log
            if i % 100 == 0:
                print(f"{days[i]} granules so far: {len(all_rows)}", file=sys.stderr, flush=True)
    out = repo_path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = ["date", "platform", "start_utc", "relorb", "frame", "baseline",
              "lon_min", "lon_max", "lat_min", "lat_max", "prefix"]
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fields)
        w.writeheader()
        w.writerows(sorted(all_rows, key=lambda r: r["start_utc"]))
    with open(out.with_suffix(".log.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, ["date", "platform", "status", "detail"])
        w.writeheader()
        w.writerows(all_log)
    print(f"wrote {len(all_rows)} granules to {out}")


if __name__ == "__main__":
    main()
