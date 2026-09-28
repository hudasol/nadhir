"""Chlorophyll-anomaly detector: climatology, zone anomaly fraction, thresholds, alert episodes.

All functions are pure (DataFrame in, DataFrame out) so the logic is unit-testable on tiny
synthetic fixtures and recomputable by hand from the committed bin tables.

Day states (never filled or interpolated):
  NODATA  – zone not observed (no granule, clouds, glint, or <min_valid_bins_frac coverage)
  QUIET   – observed, anomaly fraction below threshold
  EXCEED  – observed, anomaly fraction >= threshold, persistence not (yet) met
  ALERT   – observed, >= threshold AND persistence met
"""

from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd


# ---------------------------------------------------------------- aggregation
def daily_bins(bins: pd.DataFrame) -> pd.DataFrame:
    """Combine granules of the same day: pixel-weighted mean of log10 chl per (intake, date, bin)."""
    g = bins.groupby(["intake", "date", "bin_lat", "bin_lon"], as_index=False).agg(
        n=("n", "sum"), s1=("s1", "sum"), dist_km=("dist_km", "first"))
    g["logchl"] = g["s1"] / g["n"]
    g["month"] = pd.to_datetime(g["date"]).dt.month
    return g[["intake", "date", "month", "bin_lat", "bin_lon", "dist_km", "n", "logchl"]]


def in_period(dates: pd.Series, period) -> pd.Series:
    return (dates >= period[0]) & (dates <= period[1])


# ---------------------------------------------------------------- climatology
def climatology(daily: pd.DataFrame, min_days: int, min_sd: float) -> pd.DataFrame:
    """Per (intake, bin, calendar month): mean and SD of daily bin log10 chl. Caller passes only
    calibration-period, non-excluded days."""
    c = daily.groupby(["intake", "bin_lat", "bin_lon", "month"]).agg(
        clim_mean=("logchl", "mean"), clim_sd=("logchl", "std"), clim_ndays=("logchl", "count"),
        dist_km=("dist_km", "first")).reset_index()
    c = c[c["clim_ndays"] >= min_days].copy()
    c["clim_sd"] = c["clim_sd"].clip(lower=min_sd)
    return c


def zone_daily(daily: pd.DataFrame, clim: pd.DataFrame, radius_km: float, z_thr: float,
               min_valid_frac: float, all_dates: dict[str, list[str]] | None = None) -> pd.DataFrame:
    """Per (intake, date): observed bins, anomalous bins, anomaly fraction, observed flag.

    all_dates: optional {intake: [dates]} so days with no granule at all appear explicitly as NODATA.
    """
    cz = clim[clim["dist_km"] <= radius_km]
    d = daily[daily["dist_km"] <= radius_km].merge(
        cz[["intake", "bin_lat", "bin_lon", "month", "clim_mean", "clim_sd"]],
        on=["intake", "bin_lat", "bin_lon", "month"], how="inner")
    d["z"] = (d["logchl"] - d["clim_mean"]) / d["clim_sd"]
    agg = d.groupby(["intake", "date"]).agg(n_obs=("z", "size"), n_anom=("z", lambda v: int((v >= z_thr).sum())),
                                            max_z=("z", "max"), median_logchl=("logchl", "median")).reset_index()
    # denominator: bins in zone having a climatology for that month
    nclim = cz.groupby(["intake", "month"]).size().rename("n_clim").reset_index()
    if all_dates is not None:
        base = pd.DataFrame([(k, x) for k, v in all_dates.items() for x in v], columns=["intake", "date"])
        agg = base.merge(agg, on=["intake", "date"], how="left")
    agg["month"] = pd.to_datetime(agg["date"]).dt.month
    agg = agg.merge(nclim, on=["intake", "month"], how="left")
    agg[["n_obs", "n_anom", "n_clim"]] = agg[["n_obs", "n_anom", "n_clim"]].fillna(0).astype(int)
    agg["coverage"] = np.where(agg["n_clim"] > 0, agg["n_obs"] / agg["n_clim"].where(agg["n_clim"] > 0, 1), 0.0)
    agg["observed"] = agg["coverage"] >= min_valid_frac
    agg["anom_frac"] = np.where(agg["observed"], agg["n_anom"] / agg["n_obs"].where(agg["n_obs"] > 0, 1), np.nan)
    return agg.sort_values(["intake", "date"]).reset_index(drop=True)


# ---------------------------------------------------------------- calibration
def calibrate_threshold(zd_cal: pd.DataFrame, target_rate: float, floor: float) -> pd.DataFrame:
    """f* per intake = (1 - target_rate) quantile of anomaly fraction on observed calibration days."""
    obs = zd_cal[zd_cal["observed"]]
    q = obs.groupby("intake")["anom_frac"].quantile(1 - target_rate).rename("f_quantile")
    n = obs.groupby("intake").size().rename("n_cal_obs_days")
    t = pd.concat([q, n], axis=1).reset_index()
    t["f_threshold"] = t["f_quantile"].clip(lower=floor)
    return t


# ---------------------------------------------------------------- alert states
def day_states(zd: pd.DataFrame, f_thr: float, persistence_obs: int, window_days: int) -> pd.DataFrame:
    """Assign NODATA/QUIET/EXCEED/ALERT to one intake's zone-daily series (sorted by date)."""
    z = zd.sort_values("date").reset_index(drop=True).copy()
    dates = pd.to_datetime(z["date"])
    exceed = z["observed"] & (z["anom_frac"] >= f_thr)
    state = np.where(~z["observed"], "NODATA", np.where(exceed, "EXCEED", "QUIET")).astype(object)
    ex_dates = dates[exceed].tolist()
    for i in np.where(exceed)[0]:
        lo = dates[i] - pd.Timedelta(days=window_days)
        cnt = sum(1 for d in ex_dates if lo <= d <= dates[i])  # includes today
        if cnt >= persistence_obs:
            state[i] = "ALERT"
    z["state"] = state
    return z


def episodes(z: pd.DataFrame, break_quiet_obs: int) -> pd.DataFrame:
    """Alert episodes: start at an ALERT day; the persistence-triggering EXCEED days immediately before
    it (no QUIET in between) are the episode's first detection. End after `break_quiet_obs`
    consecutive QUIET observed days. NODATA never ends an episode."""
    rows, cur, quiet_run, pending = [], None, 0, None
    for _, r in z.iterrows():
        s = r["state"]
        if s == "NODATA":
            continue
        if cur is None:
            if s == "EXCEED":
                pending = pending or r["date"]
            elif s == "ALERT":
                cur = {"first_exceed": pending or r["date"], "first_alert": r["date"], "last_exceed": r["date"],
                       "closed_on": None}
                quiet_run = 0
            else:
                pending = None
            continue
        if s in ("EXCEED", "ALERT"):
            cur["last_exceed"] = r["date"]
            quiet_run = 0
        else:
            quiet_run += 1
            if quiet_run >= break_quiet_obs:
                cur["closed_on"] = r["date"]
                rows.append(cur)
                cur, pending, quiet_run = None, None, 0
    if cur is not None:
        rows.append(cur)
    return pd.DataFrame(rows, columns=["first_exceed", "first_alert", "last_exceed", "closed_on"])


def last_quiet_before(z: pd.DataFrame, date: str) -> str | None:
    q = z[(z["state"] == "QUIET") & (z["date"] < date)]
    return q["date"].max() if len(q) else None


def lead_time(z: pd.DataFrame, eps: pd.DataFrame, t_ref: str, t_ref_earliest: str, max_lookback: int,
              data_start: str, late_window: int) -> dict:
    """Score one documented event against the alert episodes of its intake.

    DETECTED : an episode with first_alert <= t_ref that was still open at t_ref (not closed by
               quiet observations before t_ref) and whose last exceedance is inside the lookback.
    LATE     : no such episode, but one starts within late_window days after t_ref.
    MISS     : observed days exist in the lookback but neither of the above.
    NO-DATA  : zero observed days in the lookback.

    Lead-time bounds (days):
      lead_alert_days      = t_ref - first_alert           (when an alert would have been issued)
      lead_alert_min_days  = t_ref_earliest - first_alert  (if impact began as early as sources allow)
      lead_first_exceed    = t_ref - first_exceed          (first anomalous observation of the episode)
      lead_max_days        = t_ref - last QUIET obs before first_exceed (bloom arrived after this)
    """
    tr, tre = pd.Timestamp(t_ref), pd.Timestamp(t_ref_earliest)
    lo = max(tr - pd.Timedelta(days=max_lookback), pd.Timestamp(data_start))
    dz = pd.to_datetime(z["date"])
    win = z[(dz >= lo) & (dz <= tr)]
    out = {"t_ref": t_ref, "t_ref_earliest": t_ref_earliest, "lookback_start": lo.date().isoformat(),
           "days_in_lookback": int((tr - lo).days) + 1, "obs_days_in_lookback": int(win["observed"].sum())}
    if len(eps):
        fa = pd.to_datetime(eps["first_alert"])
        closed = pd.to_datetime(eps["closed_on"])
        active = eps[(fa <= tr) & (closed.isna() | (closed > tr)) & (pd.to_datetime(eps["last_exceed"]) >= lo)]
        late = eps[(fa > tr) & (fa <= tr + pd.Timedelta(days=late_window))]
    else:
        active = late = eps
    if len(active):
        ep = active.sort_values("first_alert").iloc[-1]
        fa, fe = pd.Timestamp(ep["first_alert"]), pd.Timestamp(ep["first_exceed"])
        lq = last_quiet_before(z, ep["first_exceed"])
        out.update(outcome="DETECTED", first_exceed=ep["first_exceed"], first_alert=ep["first_alert"],
                   last_exceed=ep["last_exceed"], lead_alert_days=int((tr - fa).days),
                   lead_alert_min_days=int((tre - fa).days), lead_first_exceed_days=int((tr - fe).days),
                   last_quiet_before=lq, lead_max_days=int((tr - pd.Timestamp(lq)).days) if lq else None,
                   censored_at_data_start=bool(lq is None or pd.Timestamp(lq) < lo))
    elif len(late):
        ep = late.sort_values("first_alert").iloc[0]
        out.update(outcome="LATE", first_exceed=ep["first_exceed"], first_alert=ep["first_alert"],
                   last_exceed=ep["last_exceed"], lead_alert_days=int((tr - pd.Timestamp(ep["first_alert"])).days))
    elif out["obs_days_in_lookback"] == 0:
        out.update(outcome="NO-DATA")
    else:
        out.update(outcome="MISS")
    return out


def exclusion_mask(dates: pd.Series, t_refs: list[str], before: int, after: int) -> pd.Series:
    d = pd.to_datetime(dates)
    m = pd.Series(False, index=dates.index)
    for t in t_refs:
        t = pd.Timestamp(t)
        m |= (d >= t - pd.Timedelta(days=before)) & (d <= t + pd.Timedelta(days=after))
    return m


def date_range(start: str, end: str) -> list[str]:
    s, e = dt.date.fromisoformat(start), dt.date.fromisoformat(end)
    return [(s + dt.timedelta(i)).isoformat() for i in range((e - s).days + 1)]
