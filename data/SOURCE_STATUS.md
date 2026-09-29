# Data source connectivity — preflight 2026-09-28 (UTC ~15:43)

Tested from the cloud session container. Each test = one tiny HTTPS request (`curl -m 25`).
"blocked" = the session's egress proxy refused the CONNECT with HTTP 403 (organisation network
policy), recorded by the proxy as `connect_rejected: gateway answered 403 to CONNECT (policy denial
or upstream failure)`. No credentials were ever sent to a blocked host; credential validity is therefore
**untested**, not failed.

Credential presence (values never printed): EARTHDATA_USERNAME set, EARTHDATA_PASSWORD set,
EARTHDATA_TOKEN set, COPERNICUSMARINE_SERVICE_USERNAME set, COPERNICUSMARINE_SERVICE_PASSWORD set,
CDSAPI_URL missing, CDSAPI_KEY missing.

## Primary archives and official mirrors named in the brief

| Source | Host | Result |
|---|---|---|
| NASA Earthdata login | urs.earthdata.nasa.gov | blocked (403 CONNECT) |
| NASA CMR search | cmr.earthdata.nasa.gov | blocked |
| NASA OB.DAAC (SeaWiFS/MODIS/VIIRS/MERIS L3) | oceandata.sci.gsfc.nasa.gov | blocked |
| NASA OB.DAAC Earthdata Cloud | obdaac-tea.earthdatacloud.nasa.gov | blocked |
| NASA PO.DAAC | archive.podaac.earthdata.nasa.gov, podaac-opendap.jpl.nasa.gov | blocked |
| NOAA CoastWatch ERDDAP (West Coast) | coastwatch.pfeg.noaa.gov | blocked |
| NOAA CoastWatch ERDDAP (central) | coastwatch.noaa.gov | blocked |
| NOAA PolarWatch ERDDAP | polarwatch.noaa.gov | blocked |
| NOAA NCEI (OISST primary) | www.ncei.noaa.gov | blocked |
| ESA OC-CCI | www.oceancolour.org (+ /thredds) | blocked |
| Copernicus Marine auth / data / STAC / S3 | auth.marine.copernicus.eu, data.marine.copernicus.eu, stac.marine.copernicus.eu, s3.waw3-1.cloudferro.com | blocked |
| Copernicus CDS (ERA5) | cds.climate.copernicus.eu | blocked (and CDSAPI_* credentials missing) |
| HYCOM THREDDS / NCSS | tds.hycom.org, ncss.hycom.org | blocked |
| CEDA (OC-CCI mirror) | dap.ceda.ac.uk, data.ceda.ac.uk | blocked |
| Microsoft Planetary Computer | planetarycomputer.microsoft.com | blocked |
| Zenodo, PANGAEA, Hugging Face | zenodo.org, www.pangaea.de, huggingface.co | blocked |

## Reachable official open-data mirrors (AWS Open Data Registry / Google Cloud public data)

| Dataset | Bucket | Result | Notes |
|---|---|---|---|
| NOAA OISST v2.1 daily 0.25° SST (NOAA CDR, NODD) | noaa-cdr-sea-surface-temp-optimum-interpolation-pds (us-east-1) | **reachable** (HTTP 200 anonymous list) | official NOAA distribution on AWS |
| Sentinel-3A/B OLCI L2 WFR (chlorophyll OC4Me, flags, geolocation) | meeo-s3 (eu-central-1), NTC/ | **reachable** (HTTP 200); 20 MB/s measured | MEEO-operated mirror listed in AWS registry; unpacked SAFE folders; registry says data from July 2017. S3B folders listed but empty for 2018 (0 products Aug–Oct 2018). Mirror holds ~700 S3A WFR granules/month — a subset of the global acquisitions, but frame 2520 (18.5–31.5°N) over the Gulf is present on most days. |
| HYCOM GOFS 3.1 reanalysis (1994–2015 currents) | hycom-gofs-3pt1-reanalysis (us-west-2) | **reachable** (HTTP 200) | not used in MVP (see DECISIONS D-006) |
| NSF NCAR ERA5 | nsf-ncar-era5 (us-west-2) | **reachable** (HTTP 200) | not used in MVP |
| ERA5 (Planet OS) | era5-pds (us-east-1) | 403 (bucket no longer public) | — |
| Google ARCO ERA5 | gcp-public-data-arco-era5 (GCS) | **reachable** (HTTP 200) | not used in MVP |
| MUR SST zarr | mur-sst (us-west-2) | **reachable** | not used in MVP |
| NOAA JPSS (SNPP / NOAA-20) | noaa-nesdis-snpp-pds, noaa-nesdis-n20-pds | reachable, but **no ocean-colour product** in bucket listing (SDR/EDR land/atmosphere only) | not usable for chlorophyll |
| IMOS/AODN satellite chlorophyll (MODIS-Aqua, VIIRS) | AODN buckets (ap-southeast-2) | not tested for data: Australian-region products per registry | outside AOI |

## Consequence for sensor coverage

| Sensor | Period | Route available here? |
|---|---|---|
| SeaWiFS | 1997–Dec 2010 | **No** — only OB.DAAC/ERDDAP/OC-CCI, all blocked |
| MODIS-Aqua / Terra | 2002– / 2000– | **No** — same |
| MERIS | 2002–Apr 2012 | **No** — ESA/OC-CCI blocked |
| VIIRS-SNPP | 2012– | **No** ocean colour on NOAA JPSS AWS bucket; OB.DAAC blocked |
| Sentinel-3A OLCI | 2016– (mirror from 2017-07) | **Yes** — MEEO AWS mirror |
| Sentinel-3B OLCI | 2018– | Mirror folders empty for 2018 test months |

**Therefore the 2008–09 and 2013 events cannot be evaluated with chlorophyll in this session.**
They stay in `events/events.yaml` as documented events with status `NOT-EVALUATED: no reachable
ocean-colour data for that period`. Nothing is simulated for them.

## Literature / news hosts (Phase 1)

WebFetch and curl to publisher and news hosts are blocked by the same policy (gulfnews.com,
khaleejtimes.com, arabianbusiness.com, thenationalnews.com, sciencedirect.com, link.springer.com,
researchgate.net, doi.org, arxiv.org, whoi.edu, ead.gov.ae, moccae.gov.ae, sewa.gov.ae, wikipedia,
europepmc, web.archive.org, crossref, openalex — all HTTP 403 CONNECT). Only the server-side
WebSearch tool works; it returns titles, URLs and search-engine summaries, **not fetched page text**.
See SOURCES.md for how this limits claim status.

## Fix for the user

Add the blocked hosts above to the environment's allowed domains (cloud environment menu → Edit →
Network access; https://code.claude.com/docs/en/claude-code-on-the-web), then run `make all`.

## Update 2026-09-29 — owner-supplied data (route around the blocked hosts)

| Dataset | Route | Result |
|---|---|---|
| MODIS-Aqua L3SMI daily 4 km chlorophyll, 2003–2014 (`erdMH1chla1day`) | Downloaded by the project owner from NOAA CoastWatch ERDDAP on 2026-09-29 (server-side subset 48–60°E, 22–30°N, one file per year), shared via github.com/hudasol/nadhir-raw-modis-data (**public repository**), cloned read-only here | **used** — 12 files, SHA-256 in `data/derived/modis_objects.csv`; metadata confirms NASA OBPG R2018.1 via ERDDAP |
| Owner's research repository (EAD reports read-through, CrossRef checks, EnMAP/S2/Landsat/MODIS-monthly/CMEMS provenance tables) | github.com/hudasol/HAB-hyperspectral, attached **read-only**; clone write-protected (`chmod -R a-w`) | **used for evidence only** (SOURCES.md upgrades); its >6 GB imagery is not in the repository and was not needed |
