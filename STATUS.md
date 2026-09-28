# STATUS (draft — updated as work proceeds)

Session 2026-09-28. See README.md for layout.

## Done
- Preflight: credentials present (CDS missing); connectivity tested for every source → data/SOURCE_STATUS.md.
  All NASA / NOAA ERDDAP / Copernicus / ESA / CEDA / HYCOM hosts blocked by egress policy (HTTP 403 CONNECT).
- Reachable real chlorophyll: Sentinel-3 OLCI L2 WFR on the AWS `meeo-s3` mirror (2018-01 onward for the Gulf).
- Granule index 2017-07..2023-12 (4,787 granules over the region; none before 2018-01).
- Phase 1 events + sources (search-located, all UNVERIFIED because page fetch is blocked).
- Pipeline: index → extract → freeze (blind) → evaluate → report; 12 unit tests on synthetic fixtures.

## In progress
- OLCI extraction per year (2018, 2019 done at time of writing).

## Next steps if this session ends here
1. `make extract` (resumes; skips finished years).
2. `make freeze`, commit, `git tag frozen-detector-v1`, push tag.
3. `make evaluate report`.
