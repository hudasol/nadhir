# STATUS — 2026-09-30 (pre-submission corrections)

## What changed today
1. The page text for 7 news and preprint sources (fetched 2026-09-30 by the owner's assistant) is recorded in SOURCES.md. The Kalba 2018, Barka 2018 and Barka 2023 events and the RAK 2008 event are now VERIFIED-SECONDARY.
2. **RAK 2008 closure date corrected** from "early Sep" to **Thu 30 Oct 2008 (±3 d)**, from two independent articles in The National. The US$100k/day and "eight months" claims are removed from S-NATIONAL-REOPEN (D-016).
3. **RAK re-scored with the frozen MODIS detector, unchanged: MISS at the primary 50 km radius** (9 clear days, 1 exceedance, no alert). The pre-registered 100 km run alerted on 22 Oct, 8 days before closure. OLCI results are identical.
4. The Kalba 2018 wording is corrected: the alert came 8 days before the first *public report*; the halt start date is unknown.
5. New files: EXECUTIVE_SUMMARY.md, docs/MBR_SUBMISSION_BRIEF.md, outputs/frozen_detector_modis_v1/POSTHOC_E2008-RAK.md. Findings are reordered by strength, and a "What is NOT built yet" section is added.

---

# STATUS — 2026-09-29 (submission day, updated 2026-09-30)

**Read first:** `outputs/RESULTS.md` (the answer, in plain terms) → `DECISIONS.md` → `SOURCES.md`.

## Headline
Two blind, reproducible hindcasts on real satellite data:
- **Sentinel-3 OLCI, 2018–2023:** Kalba 2018: alert on 7 Sep 2018, 8 days before the first public report (WAM/Gulf News, 15 Sep 2018). The halt start date is not stated, so the true lead time is unknown and could be shorter. Barka 2018 and 2023 were missed.
- **MODIS-Aqua, 2003–2014:** RAK closure (30 Oct 2008, corrected) is a **MISS** at 50 km, and the 100 km sensitivity run alerted 8 d before. The Dibba first sighting (late Aug 2008) was **not observable**: MODIS L3 has zero usable days in July–August on this coast in every year. In the Fujairah 2008–09 bloom, the first alert came on 16 Nov 2008.
- **False alarms:** about 1–2.5 alert episodes per year per site in held-out quiet years (upper bounds).
- **Al Raha April 2023** (EAD-verified *P. multistriata*): no broadband anomaly on daily OLCI. This is the documented case for a hyperspectral species layer.

## Done
| Item | Where |
|---|---|
| Connectivity tests; blocked hosts listed; owner-supplied routes logged | data/SOURCE_STATUS.md |
| OLCI: 2,399 granules streamed, 0 failures, SHA-256 per file | data/derived/olci_*.csv(.gz) |
| MODIS: 12 yearly ERDDAP files (owner download), SHA-256 per file | data/derived/modis_*.csv(.gz) |
| Events: 8 rows, date precision, evidence status; Al Raha VERIFIED-PRIMARY; Kalba 2018, Barka 2018/2023, RAK 2008 VERIFIED-SECONDARY (2026-09-30) | events/events.yaml |
| Sources: 21 search-located + 8 upgrades via the owner's HAB-hyperspectral repo (read-only) | SOURCES.md |
| Blind protocol ×2: freeze → commit → tag → evaluate. `frozen-detector-v1` @ `723212e` (calibration 2019–21); `frozen-detector-modis-v1` @ `0eef7be` (calibration 2003–07). Same detector parameters; `verify-freeze` recomputes both bit-identically | config/frozen_detector_*.yaml, DECISIONS D-012, D-014 |
| Evaluation: lead times + bounds, activity over imprecise periods, held-out false alarms, coverage/gaps, 3 radii, charts | outputs/frozen_detector_v1/, outputs/frozen_detector_modis_v1/ |
| 12 unit tests (synthetic fixtures, labelled as such); `make all` for both detectors | tests/, Makefile |

## Limits a reviewer should know
- **Event dates:** Kalba 2018, Barka 2018/2023 and RAK 2008 are now VERIFIED-SECONDARY (page text fetched 2026-09-30 by the owner's assistant). They are still news or operator dates, not plant logs. Kalba 2013 is year-only (preprint). The Dibba "late August" date remains UNVERIFIED.
- **Intake coordinates:** all ESTIMATED (plant or town positions).
- **Tags:** exist locally only, because the session's git proxy refuses tag pushes (HTTP 403). The frozen commits are on the pushed branch (D-013).
- **Evidence-sharing repo:** `hudasol/nadhir-raw-modis-data` is public on GitHub.
- **Not done:** sea temperature, currents and drift modelling (D-006); the Barka miss diagnosis (hypotheses only in RESULTS §5).

## Next steps after submission
1. Re-try the two failed fetches (Khaleej Times 2018, Arabian Business 2018) and confirm the Dibba "late August 2008" phrase in Zhao & Ghedira (2014) full text; everything else in SOURCES.md is now fetched or verified.
2. Get operator shutdown logs and intake coordinates (SEWA, SMN Barka, Nama). These are the largest lead-time uncertainty.
3. Publish the tags from a machine with push rights:
   `git tag -a frozen-detector-v1 723212e -m v1 && git tag -a frozen-detector-modis-v1 0eef7be -m modis-v1 && git push origin --tags`
4. Test custom MODIS L2 processing or VIIRS for the summer blind spot. Test an OLCI 002→003 consistent reprocessing for Barka.
