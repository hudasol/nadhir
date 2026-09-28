"""Logic tests. Inputs are SYNTHETIC TEST FIXTURES — not real data (see tests/fixtures/README.md)."""

from pathlib import Path

import numpy as np
import pandas as pd

from nadhir import detector as D
from nadhir.olci_extract import bin_pixels, haversine_km, reject_mask

FIX = Path(__file__).parent / "fixtures"


def zfix():
    return pd.read_csv(FIX / "synthetic_zone_daily.csv", comment="#")


def test_reject_mask_combines_named_bits():
    m = reject_mask(["A", "B", "C"], [1, 2, 8], ["A", "C"])
    assert int(m) == 9


def test_reject_mask_unknown_flag_raises():
    try:
        reject_mask(["A"], [1], ["Z"])
    except KeyError:
        return
    raise AssertionError("expected KeyError")


def test_haversine_one_degree_lat():
    assert abs(float(haversine_km(0, 0, 1, 0)) - 111.19) < 0.1


def test_bin_pixels_min_pixels_and_no_fill():
    lat = np.array([25.01, 25.02, 25.03, 25.21])
    lon = np.array([56.01, 56.02, 56.03, 56.21])
    x = np.array([0.0, 1.0, 2.0, 5.0])
    b = bin_pixels(lat, lon, x, 0.05, 2, 25.0, 56.0, 100)
    assert len(b) == 1                      # lone pixel bin dropped, nothing invented
    assert b.iloc[0]["n"] == 3 and abs(b.iloc[0]["s1"] - 3.0) < 1e-9


def test_states_nodata_is_never_filled_and_persistence():
    z = D.day_states(zfix(), f_thr=0.25, persistence_obs=2, window_days=7)
    s = dict(zip(z["date"], z["state"]))
    assert s["2020-01-02"] == "NODATA"
    assert s["2020-01-03"] == "EXCEED"     # first exceedance, persistence not met
    assert s["2020-01-05"] == "ALERT"      # second exceedance within 7 days
    assert s["2020-01-11"] == "ALERT"      # 01-06 is within 7 days of 01-11 (inclusive window)


def test_episode_closes_after_two_quiet_obs_ignoring_nodata():
    z = D.day_states(zfix(), f_thr=0.25, persistence_obs=2, window_days=7)
    e = D.episodes(z, break_quiet_obs=2)
    assert e.iloc[0]["first_exceed"] == "2020-01-03"
    assert e.iloc[0]["first_alert"] == "2020-01-05"
    assert e.iloc[0]["closed_on"] == "2020-01-10"   # quiet 08 and 10; NODATA 09 ignored


def test_lead_time_detected_and_bounds():
    z = D.day_states(zfix(), f_thr=0.25, persistence_obs=2, window_days=7)
    e = D.episodes(z, break_quiet_obs=2)
    r = D.lead_time(z, e, "2020-01-07", "2020-01-06", 120, "2019-12-01", 30)
    assert r["outcome"] == "DETECTED"
    assert r["lead_alert_days"] == 2 and r["lead_alert_min_days"] == 1
    assert r["lead_first_exceed_days"] == 4
    assert r["last_quiet_before"] == "2020-01-01" and r["lead_max_days"] == 6


def test_lead_time_closed_episode_is_not_a_warning():
    z = D.day_states(zfix(), f_thr=0.25, persistence_obs=2, window_days=7)
    e = D.episodes(z, break_quiet_obs=2)
    r = D.lead_time(z, e, "2020-01-10", "2020-01-10", 120, "2019-12-01", 30)
    assert r["outcome"] == "LATE"          # first episode closed on 01-10; next alert 01-11


def test_lead_time_no_data():
    z = D.day_states(zfix(), f_thr=0.25, persistence_obs=2, window_days=7)
    e = D.episodes(z, break_quiet_obs=2)
    r = D.lead_time(z, e, "2019-06-01", "2019-06-01", 30, "2019-01-01", 0)
    assert r["outcome"] == "NO-DATA"


def test_climatology_and_zone_fraction():
    rows = []
    for day in range(1, 11):  # 10 calibration days, two bins, constant values -> sd floored
        for lat, v in ((25.025, 0.0), (25.075, 0.1)):
            rows.append(dict(intake="x", date=f"2019-03-{day:02d}", bin_lat=lat, bin_lon=56.025,
                             n=10, s1=10 * v, dist_km=5.0))
    daily = D.daily_bins(pd.DataFrame(rows))
    clim = D.climatology(daily, min_days=8, min_sd=0.05)
    assert len(clim) == 2 and (clim["clim_sd"] == 0.05).all()
    test = D.daily_bins(pd.DataFrame([
        dict(intake="x", date="2020-03-01", bin_lat=25.025, bin_lon=56.025, n=10, s1=10 * 0.2, dist_km=5.0)]))
    zd = D.zone_daily(test, clim, 50, 2.0, 0.10, {"x": ["2020-03-01", "2020-03-02"]})
    r = zd.set_index("date")
    assert r.loc["2020-03-01", "observed"] and r.loc["2020-03-01", "anom_frac"] == 1.0  # z = 4
    assert not r.loc["2020-03-02", "observed"] and np.isnan(r.loc["2020-03-02", "anom_frac"])


def test_calibrate_threshold_floor():
    zd = pd.DataFrame({"intake": ["x"] * 20, "observed": [True] * 20, "anom_frac": [0.0] * 20})
    t = D.calibrate_threshold(zd, 0.05, 0.05)
    assert t.iloc[0]["f_threshold"] == 0.05


def test_exclusion_mask():
    d = pd.Series(["2020-01-01", "2020-03-01", "2020-06-01"])
    m = D.exclusion_mask(d, ["2020-03-10"], 20, 10)
    assert m.tolist() == [False, True, False]
