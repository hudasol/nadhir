#!/usr/bin/env bash
# Extract OLCI bins per year (so partial progress survives interruption).
set -euo pipefail
for y in 2018 2019 2020 2021 2022 2023; do
  if [ -f data/derived/olci_bins_${y}.csv.gz ]; then echo "skip $y"; continue; fi
  python -m nadhir.olci_extract --start ${y}-01-01 --end ${y}-12-31 --tag ${y}
done
