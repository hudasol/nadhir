# Nadhir Hindcast MVP — `make all` reproduces everything from raw download to charts.
# Raw granules are streamed into memory and never stored; derived bin tables are committed.
PY ?= .venv/bin/python
.PHONY: all setup index extract freeze tag-check evaluate report test clean-derived

all: setup index extract freeze evaluate report

setup:
	uv venv -q .venv -p 3.11 || python3 -m venv .venv
	uv pip install -q -p .venv -e ".[dev]" || .venv/bin/pip install -q -e ".[dev]"

index:          ## list OLCI granules overlapping the region (metadata only)
	$(PY) -m nadhir.olci_index

extract:        ## stream granules, flag-screen, bin around intakes (per year, resumable)
	PATH=.venv/bin:$$PATH scripts/extract_all.sh

freeze:         ## BLIND: climatology + thresholds from calibration years only
	$(PY) -m nadhir.freeze
	@echo ">>> Now commit and tag: git tag frozen-detector-v1 — BEFORE 'make evaluate'"

tag-check:
	@git rev-parse -q --verify refs/tags/frozen-detector-v1 >/dev/null || \
	  (echo "refusing: tag frozen-detector-v1 missing (blind protocol)"; exit 1)
	@git diff --quiet frozen-detector-v1 -- config/frozen_detector_v1.yaml data/derived/climatology_v1.csv.gz || \
	  (echo "refusing: frozen detector differs from tag"; exit 1)

evaluate: tag-check
	$(PY) -m nadhir.evaluate --frozen frozen_detector_v1

report:
	$(PY) -m nadhir.report --frozen frozen_detector_v1

test:
	$(PY) -m pytest -q
