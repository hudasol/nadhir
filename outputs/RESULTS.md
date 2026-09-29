# Nadhir Hindcast MVP — answer and caveats

Two detectors were each frozen **before** any event was scored. Both use the same detector rules
(DECISIONS D-010) with thresholds fitted only on quiet calibration years:

| Detector | Satellite data | Years | Calibration (thresholds) | Frozen at commit |
|---|---|---|---|---|
| `frozen-detector-v1` | Sentinel-3 OLCI, 300 m, daily (AWS mirror) | 2018–2023 | 2019–2021 | `723212e` |
| `frozen-detector-modis-v1` | MODIS-Aqua L3, 4 km, daily (NOAA ERDDAP, downloaded by the project owner) | 2003–2014 | 2003–2007 | `0eef7be` |

Every number below is copied from `outputs/frozen_detector_v1/*.csv` or `outputs/frozen_detector_modis_v1/*.csv`.
Each of those folders has an auto-generated `RESULTS.md` with the full tables and provenance hashes.

## 1. How many days of warning would Nadhir have given?

All figures use the primary 50 km watch radius. Sensitivity runs at 25 km and 100 km are in each folder's `event_lead_times.csv`.

| Event | Detector | Outcome | Warning | Why |
|---|---|---|---|---|
| **SEWA Kalba shutdown, Sep 2018** | OLCI | **Detected** | alert 7 Sep, **8 days** before the 15 Sep report (plausible range −6 to +8 d) | clear anomaly (60–80% of zone) from 3 Sep |
| Barka II disruption, Feb 2018 | OLCI | Missed | — | 20 clear days in lookback, no alert |
| Barka disruption, Jul 2023 | OLCI | Missed | — | 66 clear days, no exceedance 3 May–23 Aug |
| RAK Al Ghalilah closure, Sep 2008 | MODIS | **Not observable** | — | 1 clear day in the 121 days before (MODIS summer blind spot) |
| First public sighting, Dibba, late Aug 2008 | MODIS | **Not observable** | — | 0 clear days in the 121 days before |
| Fujairah SWRO, 2008–09 (no shutdown date exists) | MODIS | Activity only | first alert **16 Nov 2008**, about 11–12 weeks after the Dibba sighting | no clear data Jul–Sep 2008; anomaly appears once coverage returns |
| Kalba 2013 (year only) | MODIS | Activity only | alert episode starting 18 May 2013; exceedances from 21 Jan | no date to compare against |

**So, of the 5 dated disruptions:** 1 was detected (Kalba 2018), 2 were missed (Barka 2018, 2023), and 2 were not
observable (RAK 2008, and the Dibba 2008 sighting that marks the bloom's arrival).

**How confident is the 8-day number? Low, and it should not be a headline.**
- n = 1 detection.
- The anchor is a news report date (Gulf News, 15 Sep 2018), which is UNVERIFIED because the page could not be fetched. If SEWA halted on 1 Sep, the alert was 6 days late.
- The bloom entered the 50 km zone between 31 Aug (last clear quiet day) and 3 Sep (first anomalous day). The 2-day persistence rule delayed the alert to 7 Sep.
- At 100 km the warning is 11 days; at 25 km it is 8 days. All radii were frozen before scoring.

## 2. How often does it alarm when nothing documented is happening?

Held-out years, 50 km (`false_alarms.csv`). These are **upper bounds**, because undocumented real blooms may occur in those years.

| Site | Detector | Alert episodes per year | Share of clear days in alert |
|---|---|---|---|
| Kalba | OLCI (2022 + parts of 2018/2023) | 2.20 | 4.5% |
| Barka | OLCI | 2.35 | 4.9% |
| Al Raha | OLCI | 2.56 | 3.0% |
| Kalba | MODIS (2010–12, 2014) | 1.00 | 1.9% |
| Fujairah | MODIS | 1.25 | 2.2% |
| RAK | MODIS | 1.50 | 2.0% |
| Dibba | MODIS | 1.50 | 3.1% |

MODIS raises fewer alarms per year partly because it sees far fewer days: 16–29% of days are observable, against 30–70% for OLCI.

## 3. The biggest finding: broadband MODIS is blind in the Gulf of Oman summer

Within 50 km of Dibba, MODIS L3 daily had **zero** usable days in July and August in **every** year from
2003 to 2014, and 0–9 days per month in May, June and September (`zone_daily_r50.csv`; the MODIS climatology has no July/August
bins at all). OLCI over the same coast had **6–21 usable days per month in July–August** in every year 2018–2023.
The 2008 bloom began in late August and the 2018 Kalba shutdown was in September, both inside this window.
- **Implication for Nadhir:** a MODIS-era (2002–2016) archive cannot show early warning for late-summer blooms on this coast. Sentinel-3 OLCI observed it (6–21 clear days/month) at Kalba and Barka.
- **Cause (hypothesis, not tested here):** the standard NASA L3 masks (aerosol/dust, sun glint, stray light) remove summer retrievals. Custom L2 processing might recover some days.

## 4. Documented-limitation case: Al Raha, April 2023 (*Pseudo-nitzschia multistriata*)
This case is now **VERIFIED-PRIMARY** via EAD's 2023 Marine Water Quality report, as read by the owner's HAB-hyperspectral project.
- **Daily OLCI:** no alerts in April–August 2023, and the median anomaly fraction was 0.0 over 102 clear days. There were two short alert episodes in September 2023 (`period_activity.csv`).
- **Independent monthly MODIS/CMEMS check (HAB-hyperspectral):** 2.25 and 2.03 mg/m³ in April 2023, within the normal range.
- Two sensors at two time resolutions agree: **a toxic diatom bloom that EAD documented produced no broadband chlorophyll anomaly.** This is the case for Nadhir's hyperspectral species layer.

## 5. Why the Barka misses may have happened (hypotheses, not findings)
1. Barka's Feb 2018 disruption falls in the winter bloom season, when the February climatology is already high.
2. Dense near-shore red tides can be removed by quality flags or sit in land-adjacent pixels.
3. The OLCI processing change (collection 002 to 003) lowers Barka chlorophyll by a median 0.10 log10 (D-011). That biases 2023 z-scores down.
4. July–August have the fewest OLCI clear days at Barka (6–20 per month).

## Bottom line for a utility engineer
In this blind hindcast, a broadband chlorophyll-anomaly watch caught **1 of 3 observable dated disruptions**. That one catch came about a week before the public report. The other **2 dated disruptions fell in the MODIS summer blind spot**. The watch raises about 1–2.5 alert episodes per year per site when nothing documented is happening. This is **not yet evidence of operational skill**. It is a reproducible, blind baseline, and it gives three concrete engineering lessons:
1. Use OLCI-class sensors, not MODIS L3, for summer coverage.
2. Expect species-level misses (Al Raha) that only a hyperspectral layer can address.
3. Get operator log dates. The report-date anchor is the largest uncertainty in every lead time.
