# DECISIONS

Format: decision · alternatives considered · reason · date (UTC).

## D-001 Chlorophyll source = Sentinel-3A OLCI L2 WFR via the MEEO AWS open-data mirror
- **Alternatives:** NASA OB.DAAC L3 (MODIS/VIIRS/SeaWiFS), NOAA CoastWatch ERDDAP, ESA OC-CCI, Copernicus Marine multi-sensor L3/L4, Google Earth Engine.
- **Reason:** every alternative host is blocked by the session egress policy (data/SOURCE_STATUS.md). The MEEO mirror is listed in the AWS Open Data Registry, serves the unmodified ESA/EUMETSAT L2 product files, and is reachable at ~20 MB/s. This is the brief's fallback step "another sensor covering the same period", applied to the only period any sensor is reachable for (2017-07 onward).
- **Consequence:** 2008–09 and 2013 events cannot be evaluated. They are kept and reported as NOT-EVALUATED, not dropped, not simulated.
- **Date:** 2026-09-28

## D-002 Use chl_oc4me (OC4Me), not chl_nn
- **Alternatives:** chl_nn (neural-net, Case-2 oriented), both.
- **Reason:** OC4Me is the band-ratio algorithm most comparable to the MODIS/SeaWiFS OCx chlorophyll used in the Gulf HAB literature, so a future multi-sensor extension stays consistent. chl_nn is retained as a named option in config for a later sensitivity check.
- **Date:** 2026-09-28

## D-003 Per-pixel geolocation from geo_coordinates.nc (no tie-point interpolation)
- **Alternatives:** tie_geo_coordinates.nc (1 MB, needs interpolation of lat/lon), HTTP range reads.
- **Reason:** avoids any interpolation step a reviewer could question; cost is ~60 MB per granule, affordable at 20 MB/s for the windows used.
- **Date:** 2026-09-28

## D-004 Search-engine evidence is UNVERIFIED
- **Alternatives:** treat WebSearch summaries as "fetched".
- **Reason:** WebFetch/curl to every news, publisher and agency host is blocked. The WebSearch tool returns URLs and model-written summaries, not the page text. Rule 3 requires fetched pages with verbatim excerpts for VERIFIED status, so every source in SOURCES.md found only by search is marked UNVERIFIED, and the excerpt field says "search-result summary, not verbatim page text". Event dates derived from them are inputs flagged as such; no headline number relies on a VERIFIED claim that we could not verify.
- **Date:** 2026-09-28

## D-005 Whole-object in-memory reads instead of HTTP range reads
- **Alternatives:** HTTP range reads of only the HDF5 chunks near each intake (implemented first).
- **Reason:** measured through this proxy: one 4 MB range request 1.2–1.3 s vs a full 60 MB object 2.6 s and ~300 MB/s aggregate across 16 parallel GETs. Range reads made the job ~10× slower. Whole files are streamed into memory, hashed (SHA-256), read, and discarded; nothing raw touches disk. Spatial subsetting is at granule level (only granules whose footprint reaches an intake zone are read) and pixel level (only pixels within 100 km of an intake are kept).
- **Date:** 2026-09-28

## D-006 MVP scope: chlorophyll anomaly only; SST, currents, winds and particle drift deferred
- **Alternatives:** add OISST SST anomaly (reachable on AWS), HYCOM reanalysis currents (reachable, but ends 2015 → no overlap with evaluable events), ERA5 winds (reachable) and Lagrangian drift.
- **Reason:** the only evaluable events are in 2018 and 2023. HYCOM GOFS 3.1 reanalysis stops in 2015, and Copernicus Marine / HYCOM analysis hosts are blocked, so no current field overlaps the evaluable events. A drift model without currents would have to invent them, which rule 1 forbids. Within the time budget, a clean, auditable chlorophyll detector is the defensible deliverable; windage/particle-count parameters are therefore absent from config (none is used).
- **Date:** 2026-09-28

## D-007 0.05° bins, geometric-mean aggregation of valid pixels only
- **Alternatives:** per-300 m-pixel climatology (too few clear samples per pixel in 3 years); 0.1° bins (coarser than the 25 km sensitivity zone allows).
- **Reason:** ~5 km bins give ~300 bins in a 50 km zone and enough clear days per bin-month for a climatology. Aggregation is a mean of log10(chl) over valid pixels only; empty bins stay empty.
- **Date:** 2026-09-28

## D-008 Watch radius 50 km primary, 25 and 100 km as sensitivity
- **Alternatives:** upstream corridor defined by currents (needs currents: D-006).
- **Reason:** radius is intake-centred and current-agnostic. The 25/100 km runs are frozen at the same time and reported alongside, so the radius is not tuned on events.
- **Date:** 2026-09-28

## D-009 Blind-protocol periods (revised before any detector output)
- **Original:** calibration 2017-07..2019-12, held-out quiet 2020–2022.
- **Revised:** calibration 2019-01..2021-12; held-out quiet 2022 (+ 2018/2023 days outside event windows, excluding Barka-2018 and Al Raha-2023).
- **Reason:** the index showed zero granules before 2018-01, and 2018 holds both evaluated 2018 events (their exclusion windows would remove almost all of 2018). The revision was driven solely by data availability (olci_index.csv), before any climatology, threshold or event statistic was computed. Caveat: undocumented blooms in 2019–2021 would inflate the calibrated threshold → fewer alarms (conservative for false alarms, pessimistic for lead time).
- **Date:** 2026-09-28

## D-010 Detector definition
- Per-bin z-score of daily log10(chl) against a calendar-month climatology (calibration years only). Zone-day anomaly fraction = share of observed bins with z ≥ 2. Zone-day is OBSERVED only if ≥ 10% of the zone's climatology bins have data, otherwise NO-DATA (a gap, never filled). Threshold f* = 95th percentile of the calibration-period anomaly fraction for that intake and radius (target 5% daily exceedance). ALERT on a day when f ≥ f* and at least one other observed day in the previous 7 days also had f ≥ f* (persistence). Episodes end after 2 consecutive observed non-exceeding days; NO-DATA days do not end an episode.
- **Alternatives:** absolute chl threshold (e.g. 10 mg m-3) — not site-adaptive; ML classifier — not auditable with 3 events.
- **Reason:** every parameter is either a stated design choice or fitted on calibration data only; a sceptical engineer can recompute it by hand from the committed bin tables.
- **Date:** 2026-09-28

## D-011 Processing-baseline change 002→003 is reported, not corrected
- **Finding (calibration data only, `data/derived/qa_baseline_step.csv`):** median per-bin-month difference in log10 chl, 2021 (collection 003) minus 2019–2020 (002), within 50 km: Al Raha −0.024, Barka −0.103 (≈ −21% chl), Kalba +0.015. This difference mixes the processing change with real interannual variability; the two cannot be separated with this data.
- **Alternatives:** per-collection climatologies (only one 003 calibration year → too few days per bin-month); an additive offset correction (would be an adjustment of real data with an unseparable confound).
- **Reason:** calibration spans both collections, so the climatology mixes them. Direction of possible bias: if 003 is genuinely lower at Barka, 2023 (003) z-scores at Barka are biased LOW → fewer alerts → the reported Barka-2023 lead time would be pessimistic, not flattering. Stated as a caveat in RESULTS.
- **Date:** 2026-09-28 (before freeze)

## D-012 Freeze
- Detector frozen from calibration years 2019–2021 at 2026-09-28T16:12Z, committed and tagged `frozen-detector-v1` before any event-year statistic was computed. Event-year bin files (2018 on disk; 2022–2023 still extracting) were not read by any analysis code before the tag.
- **Date:** 2026-09-28

## D-013 Tag `frozen-detector-v1` exists locally; the remote refused the tag push
- `git push origin frozen-detector-v1` → `error: RPC failed; HTTP 403` from the session git proxy (only the designated branch may be pushed). The frozen state is still verifiable remotely: commit `723212e` ("Freeze detector v1 …") was pushed to `claude/affectionate-bardeen-isp1tm` before any evaluation commit, and `config/frozen_detector_v1.yaml` records SHA-256 of the climatology and every calibration input. `make tag-check` accepts the local tag.
- **To publish the tag:** `git tag -a frozen-detector-v1 723212e -m "Frozen detector v1" && git push origin frozen-detector-v1` from any machine with push rights.
- **Date:** 2026-09-28

## D-014 Second frozen detector on MODIS-Aqua 2003–2014 (`frozen-detector-modis-v1`)
- **Data:** yearly NOAA CoastWatch ERDDAP subsets of `erdMH1chla1day` (MODIS-Aqua L3SMI daily 4 km chlorophyll, NASA OBPG R2018.1), box 48–60°E / 22–30°N, downloaded by the project owner on 2026-09-29 (ERDDAP request timestamps in file names and `history`) and shared read-only via github.com/hudasol/nadhir-raw-modis-data. SHA-256 of all 12 files: `data/derived/modis_objects.csv`.
- **What changes vs v1:** only the sensor, the sites (kalba, fujairah, rak, dibba) and the blind-protocol periods (`profiles.modis_v1` in config). **Detector parameters are identical** (same `detector` section, same radii); no parameter was tuned. Native 4 km L3 cells are used as bins (no re-gridding; each cell is already a NASA L3 average).
- **Periods:** calibration 2003–2007 (all full MODIS years before the first documented event, Aug 2008); held-out quiet 2010–2012 + 2014 (after the 2008–09 bloom; 2013 excluded because the Kalba event is dated only to the year).
- **Events:** E2008-RAK (month precision → scored with t_ref = 10 Sep 2008 upper bound), E2008-DIBBA (first public sighting "late August" → scored as "did the satellite see it before people did"), E2008-FUJ and E2013-KALBA (season/year precision → ACTIVITY-ONLY: alert activity over the documented period, no lead time).
- **Alternatives:** merge MODIS into v1 (would mix sensors in one climatology); re-tune thresholds for 4 km data (would break comparability and invite hindsight).
- **Caveat:** 4 km cells near the coast are often masked; a 50 km zone around a Gulf of Oman intake is partly land. Coverage is reported per year.
- **Date:** 2026-09-29 (before the MODIS freeze)

## D-015 Evidence upgrades from the owner's research repository (read-only)
- hudasol/HAB-hyperspectral records dated, fetched reads (2026-09-16) of the EAD 2022/2023 Marine Water Quality reports, the EAD HAB PDF, CrossRef records (Richlen 2010, Zhao & Ghedira 2014) and The National's "Desalination threat to the growing Gulf". These upgrade specific claims in SOURCES.md, each marked "via HAB-hyperspectral" with the date that project read it. They were not re-fetched in this session (hosts still blocked here).
- The Al Raha April 2023 *Pseudo-nitzschia multistriata* incident is therefore VERIFIED-PRIMARY for place/month/species. The "2018 Saadiyat closures" mentioned in that repository were not added: no date or desalination impact is recorded there.
- **Date:** 2026-09-29
