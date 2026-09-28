# Nadhir Hindcast MVP — answer and caveats

Detector: `frozen-detector-v1` (commit `723212e`, frozen from 2019–2021 data only before any event
was scored). Every number here is copied from `outputs/frozen_detector_v1/*.csv`; the auto-generated
tables with provenance hashes are in `outputs/frozen_detector_v1/RESULTS.md`.

## The question, answered with what the data supports

**How many days of warning would Nadhir have given?** Of 7 documented events, 3 disruptions could be
scored, because only 2018+ satellite data was reachable (`event_lead_times.csv`, `events/events.yaml`):

| Event | Outcome (50 km watch radius) | Warning vs. public report date | Plausible range |
|---|---|---|---|
| SEWA Kalba shutdown, Sep 2018 (E2018-KALBA) | **Detected** | alert 2018-09-07, **8 days** before the 15 Sep report | −6 to +8 days (see below) |
| Barka II disruption, Feb 2018 (E2018-BARKA) | **Missed** | 20 clear observations in the 56 days before 25 Feb; one isolated exceedance (8 Jan, no persistence), no alert | — |
| Barka disruption, Jul 2023 (E2023-BARKA) | **Missed** | 66 clear observations in the 121-day lookback; a short alert on 12 Apr closed long before; no exceedance at all from 3 May to 23 Aug | — |

**How confident is the 8-day number? Low. It should not be used as a headline.**
- n = 1 detection. Nothing can be said about typical skill from a single event.
- The anchor date is a news report date (Gulf News, 15 Sep 2018). That page could not be fetched, so the
  source is UNVERIFIED (`SOURCES.md` S-GULFNEWS-2018). The actual halt may have come earlier. If it came
  on 1 Sep, the alert would have been 6 days late (`lead_alert_min_days = -6`).
- Satellite sampling: the last clear, quiet observation was 31 Aug and the first anomalous one 3 Sep, so
  the bloom entered the 50 km zone between those dates (`lead_max_days = 15`, `lead_first_exceed_days = 12`).
  The 2-observation persistence rule delayed the alert to 7 Sep.
- Radius sensitivity: 25 km gives 8 d and 100 km gives 11 d (`event_lead_times.csv`). All three radii were frozen before scoring.
- Kalba also had a separate alert episode from 15 to 27 Jul 2018, which closed 7 Aug (`episodes_kalba_r50.csv`).
  It falls inside the event exclusion window, so it isn't counted as a false alarm, but we cannot tell
  whether it was a precursor, a separate bloom, or a false alarm.

**How often does it alarm in quiet periods?** Held-out periods with no documented disruption (2022, plus 2018/2023
outside event windows), 50 km (`false_alarms.csv`):

| Intake | Alert episodes per year | Share of clear days in alert |
|---|---|---|
| Kalba | 2.20 | 4.5% |
| Barka | 2.35 | 4.9% |
| Al Raha | 2.56 | 3.0% |

These are **upper bounds** on false alarms, because undocumented real blooms may fall in these periods.
The share of clear days in alert (3.0–4.9%) is comparable to the 5% daily-exceedance design target, so the calibration did not degrade badly out of sample.
At 100 km the rate rises to 3.1–4.6 episodes/yr.

## Documented-limitation case (Al Raha 2023)
Over the documented bloom period of 1 Apr–9 Oct 2023, there were 102 clear days at 50 km. The median anomaly fraction was
0.0, with no alerts in April–August and two short alert episodes in September (6 Sep; 25–27 Sep)
(`limitation_test.csv`, `episodes_alraha_r50.csv`). This agrees with the brief's point that broadband chlorophyll did not
flag the spring bloom. However, the specific claim (EAD, *Pseudo-nitzschia multistriata*, April 2023, "no
anomaly") was **not found in any source we could locate** (`SOURCES.md` S-EAD-MWQ-2023). The species is
unconfirmed.

## Why the two Barka misses happened (hypotheses, not findings)
1. Barka's Feb 2018 disruption falls in the Gulf of Oman winter bloom season, and the Feb climatology (2019–2021)
   already contains high chlorophyll, so a bloom may not be *anomalous* for February. Testable: inspect
   `data/derived/climatology_v1.csv.gz` for Barka bins in month 2 against `zone_daily_r50.csv`.
2. Dense near-shore red tides can be removed by quality flags (cloud / atmospheric-correction failures)
   or sit inside the first 300 m pixels, which are land-adjacent. The detector counts only valid pixels.
3. At Barka, 2021+ data (processing collection 003) runs a median 0.10 log10 lower than 2019–20 (002)
   in the same bin-month (`data/derived/qa_baseline_step.csv`, DECISIONS D-011). That biases 2023 z-scores down.
4. July is the season of highest data loss (monsoon haze, glint): see NO-DATA density in `event_E2023-BARKA_r50.png`.

## Not evaluated
The 2008–09 *Cochlodinium* events (Fujairah SWRO, RAK Al Ghalilah) and the 2013 Kalba shutdown predate the only
reachable ocean-colour source. SeaWiFS, MODIS, MERIS and OC-CCI hosts were all blocked (`data/SOURCE_STATUS.md`).
Exact commands to add them are in `scripts/download_blocked_sources.sh`.

## Bottom line for a utility engineer
In this hindcast, a broadband chlorophyll-anomaly watch around the intake caught 1 of 3 documented disruptions
it could see. The one catch came about a week before the public report. It raises about 2–2.5 alert episodes
per year per site when nothing documented is happening. That is not yet evidence of operational skill. It is a
reproducible, blind baseline that the next steps must beat: 2008–2013 events via MODIS/SeaWiFS once hosts are
allowed, verified event dates from operators, and currents-based upstream zones.
