# E2008-RAK re-score (2026-09-30) — frozen-detector-modis-v1, no parameter changes

Ground truth corrected under D-016: Al Ghalileh closure **Thu 30 Oct 2008** (day ±3 d; t_ref 2008-10-30,
t_ref_earliest 2008-10-27), from S-NATIONAL-RAK and S-NATIONAL-REOPEN (VERIFIED-SECONDARY).
Source of every number below: `event_lead_times.csv` and `zone_daily_r{25,50,100}.csv` in this folder.

## Outcome exactly as the frozen rules produce it
| Radius | f* (frozen) | Clear days in 121-day lookback (2 Jul–30 Oct) | Exceedances | Alerts | Outcome |
|---|---|---|---|---|---|
| **50 km (primary)** | 0.309 | 9 (none before 4 Sep) | 1 (20 Oct) | 0 | **MISS** |
| 25 km | 0.400 | 6 | 0 before t_ref (one on 31 Oct, after) | 0 | MISS |
| 100 km (sensitivity) | 0.251 | 10 | 20 Oct | from 22 Oct | DETECTED: 8 d before 30 Oct (5 d vs 27 Oct); bloom entered zone between 13 Oct (last quiet) and 20 Oct |

The headline result is the primary radius: **MISS**. The 100 km detection is a pre-registered sensitivity
run (frozen with the same commit), reported alongside, not substituted for the primary result.

## POST-HOC OBSERVATION (not a detection claim)
At 50 km the single exceedance on 20 Oct (anomaly fraction 0.326) was followed by clear days on 22, 27, 29
and 31 Oct with fractions 0.153, 0.147, 0.207, 0.153: well above the 0.00–0.03 seen on 4 Sep–13 Oct, but
below the frozen f* = 0.309, so the persistence rule never fired. An elevated, sub-threshold anomaly was
present in the zone during the 10 days before the closure. This is noted for future detector design only.
**The detector was not changed because of it, and no lead time is claimed from it.**

## Coverage context (the MODIS summer blind spot)
Zero clear days at 50 km from 2 Jul to 3 Sep 2008. The first clear day in the lookback is 4 Sep, when S-NATIONAL-RAK
places the Diba Husn fish kill ("two months earlier" than 2 Nov). July–August coverage is zero in every MODIS year
2003–2014 (`zone_daily_r50.csv`; the 2008 Dibba lookback has 0 clear days).
