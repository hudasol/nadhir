"""Evaluate the FROZEN detector: event lead times, out-of-sample false alarms, coverage and gaps.

Refuses to run unless config/frozen_detector_v1.yaml exists and its climatology hash matches.
Writes outputs/*.csv, outputs/*.png and outputs/RESULTS.md, each stamped with provenance.
"""

from __future__ import annotations

import argparse
import json
import subprocess

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import yaml  # noqa: E402

from nadhir import detector as D  # noqa: E402
from nadhir.config import load_config, repo_path  # noqa: E402
from nadhir.freeze import sha256  # noqa: E402


def git(*args) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=repo_path(".")).decode().strip()
    except Exception:
        return "unknown"


def load_frozen(name: str) -> dict:
    fz = yaml.safe_load(open(repo_path(f"config/{name}.yaml")))
    cp = repo_path(fz["climatology"]["path"])
    if sha256(cp) != fz["climatology"]["sha256"]:
        raise SystemExit(f"climatology hash mismatch for {cp}: refusing to evaluate")
    return fz


def quiet_mask(z: pd.DataFrame, intake: str, cfg: dict, events: list[dict]) -> pd.Series:
    per = cfg["periods"]
    d = z["date"]
    m = D.in_period(d, per["heldout_quiet"])
    excl_years = set(per.get("quiet_exclude", {}).get(intake, []))
    for y in per["extra_quiet_years"]:
        if y not in excl_years:
            m |= d.str[:4] == str(y)
    trefs = [e["t_ref"] for e in events if e.get("intake_key") == intake and e.get("t_ref")]
    m &= ~D.exclusion_mask(d, trefs, per["event_exclusion_before_days"], per["event_exclusion_after_days"])
    return m


def false_alarm_stats(z: pd.DataFrame, eps: pd.DataFrame, mask: pd.Series) -> dict:
    q = z[mask]
    obs = q[q["observed"]]
    qdates = set(q["date"])
    n_ep = int(sum(1 for d in eps["first_alert"] if d in qdates)) if len(eps) else 0
    n_days = len(q)
    return {"quiet_days": n_days, "quiet_observed_days": len(obs),
            "alert_days": int((obs["state"] == "ALERT").sum()),
            "alert_day_rate_of_observed": round(float((obs["state"] == "ALERT").mean()), 4) if len(obs) else None,
            "alert_episodes_started": n_ep,
            "episodes_per_365_days": round(n_ep * 365 / n_days, 2) if n_days else None,
            "episodes_per_100_observed_days": round(n_ep * 100 / len(obs), 2) if len(obs) else None}


def coverage_stats(z: pd.DataFrame) -> dict:
    obs = z["observed"].values
    gaps, run = [], 0
    for o in obs:
        if o:
            if run:
                gaps.append(run)
            run = 0
        else:
            run += 1
    if run:
        gaps.append(run)
    return {"days": len(z), "observed_days": int(obs.sum()), "observed_frac": round(float(obs.mean()), 3),
            "median_gap_days": float(np.median(gaps)) if gaps else 0.0,
            "p90_gap_days": float(np.percentile(gaps, 90)) if gaps else 0.0,
            "max_gap_days": int(max(gaps)) if gaps else 0}


def plot_event(z, thr, ev, res, radius, path, stamp):
    tr = pd.Timestamp(ev["t_ref"])
    lo, hi = tr - pd.Timedelta(days=150), tr + pd.Timedelta(days=60)
    w = z[(pd.to_datetime(z["date"]) >= lo) & (pd.to_datetime(z["date"]) <= hi)].copy()
    w["d"] = pd.to_datetime(w["date"])
    fig, ax = plt.subplots(figsize=(10, 4.2))
    colors = {"QUIET": "#6b7280", "EXCEED": "#d97706", "ALERT": "#b91c1c"}
    for s, c in colors.items():
        ww = w[w["state"] == s]
        ax.scatter(ww["d"], ww["anom_frac"], s=18, c=c, label=s, zorder=3)
    nd = w[w["state"] == "NODATA"]
    ax.scatter(nd["d"], np.full(len(nd), -0.04), marker="|", s=40, c="#9ca3af", label="NO-DATA (gap, not filled)")
    ax.axhline(thr, ls="--", c="#111827", lw=1, label=f"frozen threshold f* = {thr:.3f}")
    ax.axvline(tr, c="#1d4ed8", lw=2, label=f"t_ref {ev['t_ref']} (report date)")
    if ev.get("t_ref_earliest"):
        ax.axvspan(pd.Timestamp(ev["t_ref_earliest"]), tr, color="#bfdbfe", alpha=0.4, label="t_ref uncertainty")
    if res.get("first_alert"):
        ax.axvline(pd.Timestamp(res["first_alert"]), c="#b91c1c", lw=1, ls=":", label=f"first alert {res['first_alert']}")
    ax.set_ylim(-0.08, 1.02)
    ax.set_ylabel(f"share of observed bins with z≥2 (≤{radius} km)")
    ax.set_title(f"{ev['id']} — outcome {res['outcome']}"
                 + (f", lead {res['lead_alert_days']} d" if res.get("lead_alert_days") is not None else ""), fontsize=11)
    ax.legend(fontsize=7, loc="upper left", ncol=2, frameon=False)
    ax.grid(alpha=0.25)
    fig.text(0.01, 0.005, stamp, fontsize=6, color="#6b7280")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(path, dpi=130)
    plt.close(fig)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--frozen", default="frozen_detector_v1")
    a = ap.parse_args(argv)
    cfg = load_config()
    fz = load_frozen(a.frozen)
    det = fz["detector_params"]
    events = yaml.safe_load(open(repo_path("events/events.yaml")))["events"]
    ddir, odir = repo_path(cfg["outputs"]["derived_dir"]), repo_path(cfg["outputs"]["out_dir"]) / a.frozen
    odir.mkdir(parents=True, exist_ok=True)

    files = sorted(ddir.glob("olci_bins_20*.csv.gz"))
    data_sha = {f.name: sha256(f) for f in files}
    bins = pd.concat([pd.read_csv(f) for f in files])
    daily = D.daily_bins(bins)
    clim = pd.read_csv(repo_path(fz["climatology"]["path"]))
    start = cfg["periods"]["data_start"]
    end = max(daily["date"])
    dates = D.date_range(start, end)
    commit = git("rev-parse", "--short", "HEAD")
    tag_commit = git("rev-list", "-n", "1", "--abbrev-commit", a.frozen.replace("_", "-"))
    stamp = f"Nadhir hindcast | detector {a.frozen} (tag commit {tag_commit}) | code {commit} | " \
            f"data: Sentinel-3 OLCI L2 WFR OC4Me via AWS meeo-s3 mirror; bins sha256 in outputs/{a.frozen}/provenance.json"

    lead_rows, far_rows, cov_rows, lim_rows = [], [], [], []
    for r in fz["radii_km"]:
        zd = D.zone_daily(daily, clim, r, det["z_threshold"], det["min_valid_bins_frac"],
                          {k: dates for k in cfg["intakes"]})
        allz = []
        for intake in cfg["intakes"]:
            thr = fz["thresholds"][intake][f"r{r}km"]["f_threshold"]
            z = D.day_states(zd[zd["intake"] == intake], thr, det["persistence_obs"], det["persistence_window_days"])
            eps = D.episodes(z, det["episode_break_quiet_obs"])
            z["radius_km"] = r
            allz.append(z)
            eps.assign(intake=intake, radius_km=r).to_csv(odir / f"episodes_{intake}_r{r}.csv", index=False)
            for y, zz in z.groupby(z["date"].str[:4]):
                cov_rows.append({"intake": intake, "radius_km": r, "year": y, **coverage_stats(zz)})
            qm = quiet_mask(z, intake, cfg, events)
            far_rows.append({"intake": intake, "radius_km": r, "f_threshold": thr, "set": "heldout_quiet",
                             **false_alarm_stats(z, eps, qm)})
            cm = D.in_period(z["date"], fz["calibration_period"])
            far_rows.append({"intake": intake, "radius_km": r, "f_threshold": thr, "set": "calibration (in-sample)",
                             **false_alarm_stats(z, eps, cm)})
            for ev in events:
                if ev.get("intake_key") != intake or ev.get("evaluation") not in ("EVALUATED", "LIMITATION-TEST"):
                    continue
                res = D.lead_time(z, eps, ev["t_ref"], ev["t_ref_earliest"], det["max_lookback_days"],
                                  start, det["late_window_days"])
                lead_rows.append({"event": ev["id"], "evaluation": ev["evaluation"], "intake": intake,
                                  "radius_km": r, "f_threshold": thr, "date_precision": ev["date_precision"],
                                  "evidence_status": ev["evidence_status"], **res})
                plot_event(z, thr, ev, res, r, odir / f"event_{ev['id']}_r{r}.png", stamp)
                if ev.get("bloom_period_start"):
                    bp = z[D.in_period(z["date"], [ev["bloom_period_start"], ev["bloom_period_end"]])]
                    lim_rows.append({"event": ev["id"], "intake": intake, "radius_km": r, "f_threshold": thr,
                                     "period": f'{ev["bloom_period_start"]}..{ev["bloom_period_end"]}',
                                     "days": len(bp), "observed_days": int(bp["observed"].sum()),
                                     "exceed_or_alert_days": int(bp["state"].isin(["EXCEED", "ALERT"]).sum()),
                                     "alert_days": int((bp["state"] == "ALERT").sum()),
                                     "max_anom_frac": round(float(bp["anom_frac"].max()), 4),
                                     "median_anom_frac": round(float(bp["anom_frac"].median()), 4)})
        pd.concat(allz).to_csv(odir / f"zone_daily_r{r}.csv", index=False, float_format="%.4f")

    leads = pd.DataFrame(lead_rows)
    leads.to_csv(odir / "event_lead_times.csv", index=False)
    far = pd.DataFrame(far_rows)
    far.to_csv(odir / "false_alarms.csv", index=False)
    pd.DataFrame(lim_rows).to_csv(odir / "limitation_test.csv", index=False)
    cov = pd.DataFrame(cov_rows)
    cov.to_csv(odir / "coverage.csv", index=False)
    prov = {"detector": a.frozen, "tag_commit": tag_commit, "code_commit": commit,
            "config_sha256": sha256(repo_path("config/nadhir.yaml")),
            "frozen_config_sha256": sha256(repo_path(f"config/{a.frozen}.yaml")),
            "events_sha256": sha256(repo_path("events/events.yaml")),
            "olci_bins_sha256": data_sha,
            "olci_objects_manifests": sorted(p.name for p in ddir.glob("olci_objects_*.csv")),
            "note": "Every source granule file is listed with SHA-256/ETag in data/derived/olci_objects_<year>.csv"}
    json.dump(prov, open(odir / "provenance.json", "w"), indent=1)
    print(leads.to_string())
    print(far.to_string())


if __name__ == "__main__":
    main()
