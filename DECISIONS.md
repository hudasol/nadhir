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
