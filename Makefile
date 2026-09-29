# Nadhir Hindcast MVP — `make all` reproduces everything end-to-end.
# Two blind-frozen detectors share one code path and one set of detector parameters:
#   olci_v1  (Sentinel-3 OLCI 2018–2023, streamed from AWS; raw granules never stored)
#   modis_v1 (MODIS-Aqua L3 2003–2014, ERDDAP files from github.com/hudasol/nadhir-raw-modis-data;
#             clone it to /home/user/hudasol/nadhir-raw-modis-data or set NADHIR_MODIS_DIR)
# On a fresh clone the tags exist: `all` re-derives everything and VERIFIES each frozen detector
# (identical thresholds + climatology content) instead of re-freezing.
PY ?= .venv/bin/python
.PHONY: all setup olci modis index extract extract-modis verify-freeze verify-freeze-modis \
        tag-check tag-check-modis evaluate evaluate-modis report report-modis test

all: setup olci modis

olci: index extract verify-freeze evaluate report
modis: extract-modis verify-freeze-modis evaluate-modis report-modis

setup:
	uv venv -q .venv -p 3.11 || python3 -m venv .venv
	uv pip install -q -p .venv -e ".[dev]" || .venv/bin/pip install -q -e ".[dev]"

index:          ## list OLCI granules overlapping the region (metadata only)
	$(PY) -m nadhir.olci_index

extract:        ## stream OLCI granules, flag-screen, bin around intakes (per year, resumable)
	PATH=.venv/bin:$$PATH scripts/extract_all.sh

extract-modis:  ## read the 12 yearly ERDDAP files (read-only) into 4 km bin tables
	$(PY) -m nadhir.modis_extract --profile modis_v1

verify-freeze:
	$(PY) -m nadhir.freeze --verify
verify-freeze-modis:
	$(PY) -m nadhir.freeze --profile modis_v1 --verify

tag-check:
	@git rev-parse -q --verify refs/tags/frozen-detector-v1 >/dev/null || \
	  (echo "refusing: tag frozen-detector-v1 missing (blind protocol)"; exit 1)
	@git diff --quiet frozen-detector-v1 -- config/frozen_detector_v1.yaml data/derived/climatology_v1.csv.gz || \
	  (echo "refusing: frozen detector differs from tag"; exit 1)
tag-check-modis:
	@git rev-parse -q --verify refs/tags/frozen-detector-modis-v1 >/dev/null || \
	  (echo "refusing: tag frozen-detector-modis-v1 missing (blind protocol)"; exit 1)
	@git diff --quiet frozen-detector-modis-v1 -- config/frozen_detector_modis_v1.yaml data/derived/climatology_modis_v1.csv.gz || \
	  (echo "refusing: frozen MODIS detector differs from tag"; exit 1)

evaluate: tag-check
	$(PY) -m nadhir.evaluate --profile olci_v1
evaluate-modis: tag-check-modis
	$(PY) -m nadhir.evaluate --profile modis_v1

report:
	$(PY) -m nadhir.report --profile olci_v1
report-modis:
	$(PY) -m nadhir.report --profile modis_v1

test:
	$(PY) -m pytest -q
