# Nadhir Hindcast MVP — pre-submission corrections

Head: `claude/affectionate-bardeen-isp1tm`. Base: `main`, created at `ca484e2` (pre-correction state).
Opened as https://github.com/hudasol/nadhir/pull/1.

## Changed claims
- **RAK 2008 (E2008-RAK):** closure date "early Sep 2008" → **Thu 30 Oct 2008 (±3 d)**. Source: The National, 2 Nov 2008 ("four days starting Thursday") and 6 Nov 2008 ("closed on Thursday" of the previous week). "Early September" phrase withdrawn. VERIFIED-SECONDARY.
- **S-NATIONAL-REOPEN:** no loss figures in fetched text → withdrew the Master Plan US$100k/day figure and "eight months" phrase from this source (figure remains attributed only to S-NATIONAL-VEOLIA / HAB-hyperspectral).
- **Kalba 2018:** WAM/Gulf News 15 Sep 2018 → VERIFIED-SECONDARY; wording now "alert on 7 Sep 2018, 8 days before the first public report … true lead time relative to the shutdown is unknown and could be shorter". 8 days is no longer a headline.
- **Barka 2018:** operator disclosure ("starting in February 2018", ~RO 330,000) + 25 Feb 2018 committee report → VERIFIED-SECONDARY.
- **Barka 2023:** Nama statement 24 Jul 2023 → VERIFIED-SECONDARY.
- **Kalba 2013:** preprint quote confirmed verbatim; SECONDARY, year precision.
- Khaleej Times / Arabian Business 2018: fetch failed → still UNVERIFIED.

## RAK re-score (frozen-detector-modis-v1, no parameter change)
| Radius | Clear days in lookback | Result |
|---|---|---|
| 50 km (primary) | 9 | **MISS** (1 exceedance 20 Oct, no persistence) |
| 25 km | 6 | MISS |
| 100 km (pre-registered sensitivity) | 10 | DETECTED — alert 22 Oct, 8 d before 30 Oct (5 d vs 27 Oct) |

Post-hoc (not a detection claim): sub-threshold elevated anomaly 22–31 Oct at 50 km. OLCI results unchanged.

## Other
- New: EXECUTIVE_SUMMARY.md, docs/MBR_SUBMISSION_BRIEF.md, outputs/frozen_detector_modis_v1/POSTHOC_E2008-RAK.md.
- Findings reordered by strength; "What is NOT built yet" section (drift, hyperspectral layer, operator logs, PV integration — planned only).
- ruff added (pinned) and clean; 12 tests pass; `make verify-freeze verify-freeze-modis` identical; frozen files untouched (D-016).

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_018ixFkyPrbcfsbmuviDyM9r
