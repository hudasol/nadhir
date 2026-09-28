# STATUS — end of session 2026-09-28 (~16:40 UTC)

**Headline:** a blind, reproducible hindcast ran on **real Sentinel-3 OLCI chlorophyll (2018–2023)**. 2,399
granules were streamed with 0 failures and every source file was SHA-256 hashed. 1 of 3 scoreable
disruptions was detected (Kalba, Sep 2018: alert 8 days before the public report, plausible range −6 to +8 d).
Both Barka events were missed. Held-out false alarms run about 2.2–2.6 episodes per year per site.
Read `outputs/RESULTS.md`. The pre-2018 events could **not** be evaluated because every NASA, NOAA-ERDDAP,
Copernicus and ESA host is blocked by this environment's network policy.

## Done
| Item | Where |
|---|---|
| Credential presence check (values never printed); CDSAPI_* missing | data/SOURCE_STATUS.md |
| Connectivity test of every source; fallbacks tried and logged | data/SOURCE_STATUS.md |
| Real data route found: OLCI L2 WFR on AWS `meeo-s3` mirror | DECISIONS D-001 |
| Granule index 2017-07..2023-12 (4,787 over region; none before 2018-01) | data/derived/olci_index.csv (+ .log.csv) |
| Extraction of 2,399 granules near 3 sites, flag-screened, 0.05° bins, no filling | data/derived/olci_bins_*.csv.gz |
| Per-file provenance (SHA-256, ETag, Last-Modified) for every object read | data/derived/olci_objects_*.csv |
| Phase 1: 7 events, 21 sources, date precision, evidence status | events/events.yaml, SOURCES.md |
| Blind protocol: freeze from 2019–2021 only → commit 723212e, local tag `frozen-detector-v1`; `verify-freeze` recomputes identical thresholds | config/frozen_detector_v1.yaml, DECISIONS D-012 |
| Evaluation: lead times + bounds, held-out false alarms, coverage/gaps, radius sensitivity, Al Raha limitation test, 12 charts | outputs/frozen_detector_v1/ |
| Unit tests (12, synthetic fixtures labelled as such) | tests/ |
| Makefile end-to-end (`make all`), pinned deps | Makefile, pyproject.toml |

## Partial
- **Evidence verification:** every source was *located* with web search, but no page could be fetched
  (egress-blocked). All sources are therefore **UNVERIFIED**, including the event dates used as t_ref. Only the AWS registry entry is VERIFIED-PRIMARY.
- **Intake coordinates:** all ESTIMATED (plant or town positions). Kalba has no sourced coordinate.
- **Tag push refused** by the session git proxy (HTTP 403). The tag exists locally, and commit 723212e is on the remote branch (DECISIONS D-013).
- **Mirror gaps:** 62–79-day gaps in 2021–2022 and almost nothing for Nov–Dec 2022. 2023 ends in early November. These are reported in coverage.csv and not filled.

## Not done / failed, and why
- **2008–09 and 2013 events:** no ocean-colour data before 2018 was reachable (SOURCE_STATUS.md).
- **SST (OISST), currents, winds, particle drift:** deferred (D-006). OISST and ERA5 are reachable on AWS/GCS,
  but the HYCOM reanalysis ends in 2015, and no current field overlaps the 2018/2023 events without blocked hosts.
  No windage or particle parameters exist in config because none is used.
- **Brief's Al Raha claim** (EAD, *P. multistriata*, April 2023, no anomaly): no source found. We tested it with data
  instead: no alerts Apr–Aug 2023, two short episodes in Sep 2023.

## Exact next steps
1. **Allow the blocked hosts** (cloud environment → Edit → Network access; list in data/SOURCE_STATUS.md), then:
   - fetch every URL in SOURCES.md, paste verbatim excerpts, and set VERIFIED-PRIMARY/SECONDARY;
   - run `scripts/download_blocked_sources.sh` (MODIS/SeaWiFS/CMEMS) and add an L3 reader, so 2008–09 and 2013 can be scored under a **new** frozen tag (v2). Report v1 and v2 side by side.
2. Publish the tag from a machine with push rights: `git tag -a frozen-detector-v1 723212e -m "Frozen detector v1" && git push origin frozen-detector-v1`.
3. Ask SEWA / Nama / SMN Barka for **operational log dates** (shutdown start/end) and **intake coordinates**. These are the largest uncertainty in the lead time.
4. Investigate the Barka misses (hypotheses in outputs/RESULTS.md): winter climatology level, flag removal of dense near-shore bloom pixels, and the 002→003 collection step (D-011).
5. Add OISST SST anomaly (reachable now) as a second covariate, as a new frozen version.

## Reproduce
`make all` (setup → index → extract ≈ 30 min streaming, no raw files kept → verify-freeze → evaluate → report); `make test`.
