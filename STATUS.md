# STATUS — 2026-09-29 (submission day)

**Read first:** `outputs/RESULTS.md` (the answer, in plain terms) → `DECISIONS.md` → `SOURCES.md`.

## Headline
Two blind, reproducible hindcasts on real satellite data:
- **Sentinel-3 OLCI, 2018–2023:** Kalba Sep 2018 detected, with an alert 8 days before the public report (plausible range −6 to +8 d). Barka 2018 and 2023 were missed.
- **MODIS-Aqua, 2003–2014:** the 2008 RAK closure and the Dibba first sighting were **not observable**. MODIS L3 has zero usable days in July–August on this coast in every year. In the Fujairah 2008–09 bloom, the first alert came on 16 Nov 2008.
- **False alarms:** about 1–2.5 alert episodes per year per site in held-out quiet years (upper bounds).
- **Al Raha April 2023** (EAD-verified *P. multistriata*): no broadband anomaly on daily OLCI. This is the documented case for a hyperspectral species layer.

## Done
| Item | Where |
|---|---|
| Connectivity tests; blocked hosts listed; owner-supplied routes logged | data/SOURCE_STATUS.md |
| OLCI: 2,399 granules streamed, 0 failures, SHA-256 per file | data/derived/olci_*.csv(.gz) |
| MODIS: 12 yearly ERDDAP files (owner download), SHA-256 per file | data/derived/modis_*.csv(.gz) |
| Events: 8 rows, date precision, evidence status; Al Raha upgraded to VERIFIED-PRIMARY | events/events.yaml |
| Sources: 21 search-located + 8 upgrades via the owner's HAB-hyperspectral repo (read-only) | SOURCES.md |
| Blind protocol ×2: freeze → commit → tag → evaluate. `frozen-detector-v1` @ `723212e` (calibration 2019–21); `frozen-detector-modis-v1` @ `0eef7be` (calibration 2003–07). Same detector parameters; `verify-freeze` recomputes both bit-identically | config/frozen_detector_*.yaml, DECISIONS D-012, D-014 |
| Evaluation: lead times + bounds, activity over imprecise periods, held-out false alarms, coverage/gaps, 3 radii, charts | outputs/frozen_detector_v1/, outputs/frozen_detector_modis_v1/ |
| 12 unit tests (synthetic fixtures, labelled as such); `make all` for both detectors | tests/, Makefile |

## Limits a reviewer should know
- **Event dates:** the Kalba 2013/2018, Barka 2018/2023, RAK 2008 and Dibba 2008 dates come from news reports found by search. The pages could not be fetched here, so they stay **UNVERIFIED**. Only Al Raha (EAD) and the 2008–09 Fujairah losses (The National) are verified, via the owner's research project.
- **Intake coordinates:** all ESTIMATED (plant or town positions).
- **Tags:** exist locally only, because the session's git proxy refuses tag pushes (HTTP 403). The frozen commits are on the pushed branch (D-013).
- **Evidence-sharing repo:** `hudasol/nadhir-raw-modis-data` is public on GitHub.
- **Not done:** sea temperature, currents and drift modelling (D-006); the Barka miss diagnosis (hypotheses only in RESULTS §5).

## Next steps after submission
1. Fetch and paste verbatim excerpts for the UNVERIFIED news sources (Gulf News 2018, Oman Observer 2018, Muscat Daily 2023, The National RAK 2008).
2. Get operator shutdown logs and intake coordinates (SEWA, SMN Barka, Nama). These are the largest lead-time uncertainty.
3. Publish the tags from a machine with push rights:
   `git tag -a frozen-detector-v1 723212e -m v1 && git tag -a frozen-detector-modis-v1 0eef7be -m modis-v1 && git push origin --tags`
4. Test custom MODIS L2 processing or VIIRS for the summer blind spot. Test an OLCI 002→003 consistent reprocessing for Barka.
