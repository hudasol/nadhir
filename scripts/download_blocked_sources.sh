#!/usr/bin/env bash
# Exact acquisition commands for the sources that were BLOCKED in the 2026-09-28 session
# (data/SOURCE_STATUS.md). They extend the hindcast to the 2008–09 and 2013 events. Not run by
# `make all` because the hosts were unreachable; run once the environment allows these domains.
# Credentials are read from the environment and never echoed.
set -euo pipefail
REGION="48,60,22,30"            # lon_min,lon_max,lat_min,lat_max — keep in sync with config/nadhir.yaml
OUT=data/raw; mkdir -p $OUT/erddap $OUT/obdaac $OUT/cmems

# 1) NOAA CoastWatch ERDDAP (no auth) — server-side subset, daily MODIS-Aqua chl-a (2002–present).
#    Dataset IDs are from the CoastWatch catalogue; verify the ID resolves before a long run.
for Y in 2008 2009 2013; do
  curl -fsS -o $OUT/erddap/modisa_chla_${Y}.nc \
   "https://coastwatch.pfeg.noaa.gov/erddap/griddap/erdMH1chla1day.nc?chlorophyll%5B(${Y}-01-01T00:00:00Z):1:(${Y}-12-31T00:00:00Z)%5D%5B(30):1:(22)%5D%5B(48):1:(60)%5D"
done
# SeaWiFS (1997–2010) daily: erdSW2018chla1day (same query pattern).

# 2) NASA OB.DAAC L3 mapped daily (Earthdata login). File search API + authenticated download.
#    ~/.netrc must hold: machine urs.earthdata.nasa.gov login $EARTHDATA_USERNAME password $EARTHDATA_PASSWORD
#    (.netrc is gitignored). Example: MODIS-Aqua daily 4 km chl, Aug–Dec 2008.
curl -fsS "https://oceandata.sci.gsfc.nasa.gov/api/file_search?sensor_id=7&dtid=1043&sdate=2008-08-01&edate=2008-12-31&subType=1&addurl=1&results_as_file=1&search=*DAY*CHL*4km*" \
  | grep -E '\.nc$' > $OUT/obdaac/urls.txt || true
while read -r u; do
  curl -fsS -n -L -c /tmp/cj -b /tmp/cj -o "$OUT/obdaac/$(basename "$u")" "$u"
done < $OUT/obdaac/urls.txt

# 3) Copernicus Marine multi-sensor L3 daily chl (1997–present), server-side subset.
#    uses COPERNICUSMARINE_SERVICE_USERNAME / _PASSWORD from the environment.
pip install -q copernicusmarine
copernicusmarine subset --dataset-id cmems_obs-oc_glo_bgc-plankton_my_l3-multi-4km_P1D \
  --variable CHL --minimum-longitude 48 --maximum-longitude 60 --minimum-latitude 22 --maximum-latitude 30 \
  --start-datetime 2008-01-01 --end-datetime 2013-12-31 --output-directory $OUT/cmems

echo "Then add a reader for these gridded L3 products (same bins/climatology code applies) and re-run the blind protocol with a new frozen tag."
