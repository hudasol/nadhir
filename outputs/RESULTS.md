# Nadhir Hindcast MVP — findings and caveats (corrected 2026-09-30)

Every number below is copied from `outputs/frozen_detector_v1/*.csv` (OLCI) or
`outputs/frozen_detector_modis_v1/*.csv` (MODIS). Each folder has an auto-generated `RESULTS.md` with the full
tables and provenance hashes. Source IDs refer to `SOURCES.md`; decisions to `DECISIONS.md`.

## Findings, ordered by strength

### 1. A blind, reproducible hindcast protocol, with thresholds frozen before scoring
| Detector | Satellite data | Years | Calibration (thresholds) | Frozen at commit |
|---|---|---|---|---|
| `frozen-detector-v1` | Sentinel-3 OLCI, 300 m, daily (AWS mirror) | 2018–2023 | 2019–2021 | `723212e` |
| `frozen-detector-modis-v1` | MODIS-Aqua L3, 4 km, daily (NOAA ERDDAP, downloaded by the owner) | 2003–2014 | 2003–2007 | `0eef7be` |

- Both detectors use identical rules (D-010). Thresholds were fitted on quiet years only, committed, and then events were scored.
- `make verify-freeze verify-freeze-modis` recomputes both detectors bit-identically. `make tag-check` refuses to evaluate if a frozen file changes.
- The 2026-09-30 corrections (D-016) changed event ground truth only. No threshold, radius or persistence rule changed, and OLCI results are identical after the re-run.

### 2. Broadband MODIS L3 is blind in July–August on the Gulf of Oman coast; OLCI is not
- **MODIS:** zero clear days within 50 km of Dibba in July and August in every year from 2003 to 2014, and 0–9 per month in May, June and September (MODIS `zone_daily_r50.csv`). The MODIS climatology has no July/August bins at all.
- **OLCI:** 6–21 clear days per month in July–August at Kalba and Barka in every year from 2018 to 2023 (OLCI `zone_daily_r50.csv`).
- **2008 evidence:**
  - The bloom was first sighted at Dibba in late August 2008 (S-ZHAO2014, date UNVERIFIED). About 20,000 fish died at Diba Husn around early September (S-NATIONAL-RAK, VERIFIED-SECONDARY).
  - The MODIS Dibba zone had **0 clear days** in the 121 days before 31 Aug.
  - The RAK zone had no clear day from 2 Jul to 3 Sep (`POSTHOC_E2008-RAK.md`).
- **Implication:** an archive built on MODIS L3 cannot give early warning for late-summer blooms on this coast. OLCI-class data can at least observe them.
- **Cause (hypothesis, untested):** standard L3 masking (dust/aerosol, glint).

### 3. Al Raha, April 2023: an EAD-verified toxic diatom bloom was invisible to broadband chlorophyll on two sensors
- **Event:** EAD's 2023 Marine Water Quality report documents a *Pseudo-nitzschia multistriata* red tide at Al Raha Beach in April 2023 (S-EAD-MWQ-2023, VERIFIED-PRIMARY via HAB-hyperspectral).
- **Daily OLCI:** no alerts in April–August 2023, and a median anomaly fraction of 0.0 over 102 clear days. There were two short alert episodes in September (OLCI `period_activity.csv`).
- **Monthly MODIS and CMEMS (owner's independent check):** 2.25 and 2.03 mg/m³ in April 2023, within the normal range (S-HABHYP-BROADBAND).
- **Why it matters:** this is the documented case for a species-level (hyperspectral) layer.

### 4. Hit/miss scorecard for dated disruptions (primary 50 km radius, frozen rules)
| Event | Sensor | Outcome | Detail |
|---|---|---|---|
| SEWA Kalba halt, 2018 (S-GULFNEWS-2018, VERIFIED-SECONDARY) | OLCI | **Alert raised** | Alert on 7 Sep 2018, 8 days before the first public report (WAM/Gulf News, 15 Sep 2018). The source does not state when the halt began, so the true lead time relative to the shutdown is unknown and could be shorter. |
| Barka II, Feb 2018 (S-OBSERVER-SMN, VERIFIED-SECONDARY) | OLCI | Miss | 20 clear days in the lookback (data start 1 Jan 2018), no alert |
| Barka, Jul 2023 (S-MUSCATDAILY-2023, VERIFIED-SECONDARY) | OLCI | Miss | 66 clear days in the lookback; no exceedance 3 May–23 Aug |
| RAK Al Ghalileh closure, Thu 30 Oct 2008 ±3 d (S-NATIONAL-RAK, S-NATIONAL-REOPEN, VERIFIED-SECONDARY) | MODIS | **Miss** | 9 clear days in the lookback, 1 exceedance (20 Oct), no alert. The pre-registered **100 km sensitivity run did alert on 22 Oct**, 8 days before closure (5 days vs 27 Oct). See `POSTHOC_E2008-RAK.md`. |

**Summary at the primary radius:** 1 of 4 observable dated disruptions produced an alert before the public record.

**Not scoreable:**
- Dibba sighting, Aug 2008: 0 clear days in the lookback.
- Fujairah 2008–09: no shutdown date exists. The first MODIS alert came on 16 Nov 2008.
- Kalba 2013: year only. There was an alert episode from 18 May 2013.

**Caveats:**
- n is tiny.
- Dates are news or operator report dates (upper bounds), except RAK, which is dated to ±3 days.
- Intake coordinates are ESTIMATED.

### 5. False-alarm upper bounds (held-out quiet years, 50 km; `false_alarms.csv`)
| Site | Detector | Alert episodes per year | Share of clear days in alert |
|---|---|---|---|
| Kalba | OLCI | 2.20 | 4.5% |
| Barka | OLCI | 2.35 | 4.9% |
| Al Raha | OLCI | 2.56 | 3.0% |
| Kalba | MODIS | 1.00 | 1.9% |
| Fujairah | MODIS | 1.25 | 2.2% |
| RAK | MODIS | 1.50 | 2.0% |
| Dibba | MODIS | 1.50 | 3.1% |

These are upper bounds, because undocumented real blooms may fall in the "quiet" years. MODIS raises fewer alarms partly because it sees fewer days.

## Why the misses may have happened (hypotheses, not findings)
1. **Barka, Feb 2018:** this is the winter bloom season, when the February climatology is already high.
2. **Near-shore pixels:** dense near-shore blooms can be removed by quality flags or sit in land-adjacent pixels.
3. **Processing change:** the OLCI collection 002→003 change lowers Barka chlorophyll by a median 0.10 log10, which biases 2023 z-scores down (D-011).
4. **RAK, 2008:** an elevated but sub-threshold signal was present on 22–31 Oct at 50 km. This is labelled POST-HOC, and nothing was tuned on it.

## What is NOT built yet
- **Current and drift tracking toward intakes (D-006).** Watch zones are intake-centred circles, not upstream corridors.
- **Hyperspectral species layer.** Broadband chlorophyll cannot identify species (finding 3).
- **Validation against operator logs.** No plant shutdown or intake-water-quality log has been obtained. All disruption dates come from news or operator disclosures.
- **Renewable-energy integration (PLANNED, NOT IMPLEMENTED).** The idea is to use warning lead time to schedule storage pre-fill and pre-emptive cleaning during daytime solar-PV output at plants with on-site PV. No energy modelling has been done.
