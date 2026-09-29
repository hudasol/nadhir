# Nadhir — Hindcast MVP

Nadhir is an early-warning system for harmful algal blooms (HABs) reaching UAE and Gulf of Oman desalination
intakes. This repository answers one question using only real historical data: **for each documented
bloom-related desalination disruption, how many days of warning would a satellite chlorophyll-anomaly
detector have given, how confident is that number, and how often does it alarm in quiet periods?**

Start with **STATUS.md** (what was done and what wasn't) and **outputs/RESULTS.md** (numbers + caveats).

## What is real and what is not
- **Data (two detectors, same rules):**
  - Sentinel-3A/B OLCI Level-2 Water Full Resolution granules (ESA/EUMETSAT, 300 m), 2018–2023, chlorophyll
    `CHL_OC4ME` + `WQSF` flags + per-pixel geolocation, read from the MEEO mirror in the AWS Open Data Registry.
    Every source object is listed with its SHA-256 and S3 ETag in `data/derived/olci_objects_<year>.csv`.
  - MODIS-Aqua L3 daily 4 km chlorophyll, 2003–2014 (NASA OBPG via NOAA CoastWatch ERDDAP `erdMH1chla1day`),
    downloaded by the project owner and read from github.com/hudasol/nadhir-raw-modis-data (read-only).
    SHA-256 per file in `data/derived/modis_objects.csv`.
- **Nothing is simulated, interpolated or gap-filled.** Days without a usable observation are recorded as
  `NODATA` and shown in every chart.
- **Tests** in `tests/` use tiny hand-made inputs in `tests/fixtures/`, labelled
  **SYNTHETIC TEST FIXTURE — not real data**. They test code logic only and are never used in any result.
- **Events** (`events/events.yaml`) and **sources** (`SOURCES.md`): the evidence was located by web search, but the
  pages could not be fetched from this environment, so every source is currently **UNVERIFIED**.
- **Intake coordinates** are plant/town positions, all marked **ESTIMATED**.

## Blind protocol (applied twice)
1. `python -m nadhir.freeze --profile <p>` builds the climatology and thresholds from calibration years only
   (OLCI 2019–2021; MODIS 2003–2007). It never opens event-year files.
2. The frozen config is committed and tagged (`frozen-detector-v1` @ 723212e, `frozen-detector-modis-v1` @ 0eef7be).
3. Only then does evaluation (which refuses to run if the frozen files differ from the tag) score events.

## Reproduce
```
make all        # both detectors: extract → verify-freeze → evaluate → report (OLCI streaming ~30 min)
make modis      # MODIS only (needs the nadhir-raw-modis-data clone; set NADHIR_MODIS_DIR if elsewhere)
make test
```
Raw granules are streamed into memory and never written to disk. Derived bin tables (~tens of MB) are committed.

## Layout
```
config/nadhir.yaml              every parameter, each with a cited or DESIGN-CHOICE comment
config/frozen_detector_v1.yaml        OLCI frozen thresholds + input hashes (blind protocol)
config/frozen_detector_modis_v1.yaml  MODIS frozen thresholds + input hashes
events/events.yaml              documented events, date precision, evidence status
SOURCES.md                      every source, URL, access date, excerpt, status
DECISIONS.md                    every decision, its alternatives and the reason for it
data/SOURCE_STATUS.md           connectivity test of every data source
data/derived/                   granule index, per-granule bin statistics, object manifests (committed)
src/nadhir/                     olci_index → olci_extract → freeze → evaluate → report
outputs/RESULTS.md              the answer and caveats, both detectors
outputs/frozen_detector_v1/     OLCI: lead times, false alarms, coverage, period activity, charts, provenance.json
outputs/frozen_detector_modis_v1/  MODIS: same set
scripts/download_blocked_sources.sh   exact commands for the sources that were blocked (2008–2013 events)
```
