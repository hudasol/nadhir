# Nadhir — Hindcast MVP

Nadhir is an early-warning system for harmful algal blooms (HABs) reaching UAE and Gulf of Oman desalination
intakes. This repository answers one question using only real historical data: **for each documented
bloom-related desalination disruption, how many days of warning would a satellite chlorophyll-anomaly
detector have given, how confident is that number, and how often does it alarm in quiet periods?**

Start with **STATUS.md** (what was done and what wasn't) and **outputs/RESULTS.md** (numbers + caveats).

## What is real and what is not
- **Data:** Sentinel-3A/B OLCI Level-2 Water Full Resolution granules (ESA/EUMETSAT, 300 m), chlorophyll
  `CHL_OC4ME` + `WQSF` flags + per-pixel geolocation, read from the MEEO mirror in the AWS Open Data Registry.
  Every source object is listed with its SHA-256 and S3 ETag in `data/derived/olci_objects_<year>.csv`.
- **Nothing is simulated, interpolated or gap-filled.** Days without a usable observation are recorded as
  `NODATA` and shown in every chart.
- **Tests** in `tests/` use tiny hand-made inputs in `tests/fixtures/`, labelled
  **SYNTHETIC TEST FIXTURE — not real data**. They test code logic only and are never used in any result.
- **Events** (`events/events.yaml`) and **sources** (`SOURCES.md`): the evidence was located by web search, but the
  pages could not be fetched from this environment, so every source is currently **UNVERIFIED**.
- **Intake coordinates** are plant/town positions, all marked **ESTIMATED**.

## Blind protocol
1. `make freeze` builds the climatology and thresholds from **calibration years 2019–2021 only**. It never opens
   event-year files.
2. The resulting `config/frozen_detector_v1.yaml` is committed and tagged **`frozen-detector-v1`**.
3. Only then does `make evaluate` (which refuses to run without the tag) compute event lead times and
   false-alarm rates.

## Reproduce
```
make all        # setup → index → extract (streams ~2,400 granules, ~30 min) → verify-freeze → evaluate → report
make test
```
Raw granules are streamed into memory and never written to disk. Derived bin tables (~tens of MB) are committed.

## Layout
```
config/nadhir.yaml              every parameter, each with a cited or DESIGN-CHOICE comment
config/frozen_detector_v1.yaml  frozen thresholds + input hashes (blind protocol)
events/events.yaml              documented events, date precision, evidence status
SOURCES.md                      every source, URL, access date, excerpt, status
DECISIONS.md                    every decision, its alternatives and the reason for it
data/SOURCE_STATUS.md           connectivity test of every data source
data/derived/                   granule index, per-granule bin statistics, object manifests (committed)
src/nadhir/                     olci_index → olci_extract → freeze → evaluate → report
outputs/frozen_detector_v1/     lead times, false alarms, coverage, charts, provenance.json
scripts/download_blocked_sources.sh   exact commands for the sources that were blocked (2008–2013 events)
```
