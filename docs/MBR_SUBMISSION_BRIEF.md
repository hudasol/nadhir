# Nadhir — early warning of red tides for desalination intakes
**Mohammed Bin Rashid Al Maktoum Global Water Award · Innovative Individual Award (Youth)**

Structured around the category weights as supplied by the applicant from the award's published criteria:
creativity & innovation 50%, engagement/awareness 25%, technology & process design 15%, health/safety/environment 10%.
Pointers in [brackets] lead to the evidence: source IDs in `SOURCES.md`, numbers in `outputs/…csv`.

## 1. The problem
Harmful algal blooms ("red tides") clog the filters and membranes of seawater desalination plants. Plants then cut or stop
production, and communities that depend on them lose water. Verified examples:
- **Ras Al Khaimah, 2008:** the Al Ghalileh plant closed because of a toxic red tide. Homes in Al Jeil were without water for
  four days, starting Thursday 30 Oct 2008 [S-NATIONAL-RAK, S-NATIONAL-REOPEN; date derivation in DECISIONS D-016].
- **Kalba (Sharjah), 2018:** SEWA halted its desalination units in Kalba "due to Red Tide concerns", as reported on 15 Sep 2018 [S-GULFNEWS-2018].
- **Barka (Oman), 2018:** red tide affected the Barka II plant "starting in February 2018", with losses of about RO 330,000 [S-OBSERVER-SMN].
- **Barka (Oman), 2023:** Nama Water Services reported "reduction and even cessation in desalinated water production" on 24 Jul 2023 [S-MUSCATDAILY-2023].

Today, plants mostly react after the bloom reaches the intake.

## 2. What is new (creativity & innovation — 50%)
- **An intake-specific, species-aware warning concept.** The watch zone is centred on each intake, not on the whole Gulf. The target
  output is *which* bloom is coming and *when*, so operators can adjust coagulant dosing, switch DAF mode, clean filters early and pre-fill storage.
- **A blind hindcast, not a demo.** Detector thresholds were fitted on quiet years and frozen in git *before* any
  historical event was scored. There are two independent frozen detectors: Sentinel-3 OLCI (2018–2023) and MODIS-Aqua (2003–2014).
  Anyone can re-run it with `make all`, and `make verify-freeze` reproduces the thresholds bit-for-bit [DECISIONS D-010, D-012, D-014].
- **Two findings that change how such a system should be built:**
  1. **Summer blind spot.** The widely used MODIS L3 chlorophyll product had **zero** clear days in July–August near the
     Gulf of Oman coast in every year from 2003 to 2014. Sentinel-3 OLCI had 6–21 per month [MODIS and OLCI `zone_daily_r50.csv`; `outputs/RESULTS.md` §2].
     The 2008 bloom was first seen in late August, inside that window.
  2. **Species matters.** A toxic *Pseudo-nitzschia multistriata* red tide documented by EAD at Al Raha in April 2023
     [S-EAD-MWQ-2023] showed **no** broadband chlorophyll anomaly on daily OLCI or on monthly MODIS/CMEMS
     [OLCI `period_activity.csv`; S-HABHYP-BROADBAND]. Chlorophyll alone cannot warn about some toxic blooms, so a hyperspectral species layer is needed.

## 3. Evidence: hindcast scorecard (technology & process design — 15%)
Primary 50 km watch radius, frozen rules, no tuning after scoring [`outputs/RESULTS.md` §4].

| Event | Result |
|---|---|
| Kalba 2018 | Alert on 7 Sep 2018, 8 days before the first public report (15 Sep). The halt start date is not stated, so the true lead time is unknown and could be shorter [OLCI `event_lead_times.csv`]. |
| Barka Feb 2018 | Miss [OLCI `event_lead_times.csv`] |
| Barka Jul 2023 | Miss [OLCI `event_lead_times.csv`] |
| RAK 30 Oct 2008 (±3 d) | Miss at 50 km. The pre-registered 100 km run alerted 8 days before closure [MODIS `event_lead_times.csv`; `POSTHOC_E2008-RAK.md`]. |
| False alarms | 1.0–2.6 alert episodes per year per site in quiet years (upper bounds) [both `false_alarms.csv`] |

**Plain reading:** 1 of 4 observable dated disruptions was flagged before the public record. This is a first honest baseline to beat, not proof of operational skill.

**Process design:**
- Every source file is hashed (SHA-256).
- Every parameter is in one config file with its origin.
- Every decision is logged (DECISIONS.md).
- Gaps in satellite data are shown, never filled.

## 4. Health, safety & environment (10%)
- **Health:** earlier warning protects drinking-water supply (Al Jeil lost water for 4 days in 2008 [S-NATIONAL-RAK]). It also flags toxin-producing species that chlorophyll misses (Al Raha, domoic-acid-producing *P. multistriata* [S-EAD-MWQ-2023]).
- **Environment:** planned, pre-emptive operation can replace emergency chemical dosing and abrupt shutdowns.
- **Renewable-energy link — PLANNED, NOT IMPLEMENTED:**
  - **Idea:** use the warning lead time to schedule storage pre-fill and pre-emptive cleaning during daytime solar-PV output at plants with on-site PV.
  - **Example context:** Taweelah's ~70 MWp captive PV (figure supplied by the applicant; not verified in this repository).
  - **Status:** no energy modelling has been done.

## 5. Engagement & awareness (25%)
- **Open by design:** code, frozen detectors, decisions and source audit trail in one reproducible repository. Engineers at
  EWEC, DEWA, SEWA, EtihadWE, EAD or MOCCAE can re-run and challenge every number.
- **The two findings are directly useful to regulators and operators:** don't rely on MODIS L3 for summer warnings on this coast, and chlorophyll alone misses some toxic blooms.
- **Next engagement step:** request plant shutdown logs and intake coordinates from operators (SEWA, SMN Barka, Nama) to validate lead times against real operations.

## 6. Limitations (stated plainly)
- **Tiny sample:** 4 observable dated disruptions and 1 alert.
- **Event dates come from news reports or operator disclosures, not plant logs.** Kalba 2018 and Barka 2023 dates are report dates (upper bounds).
- **Intake coordinates are ESTIMATED** (plant or town positions).
- **No current or drift model yet.** Watch zones are circles, not upstream corridors [DECISIONS D-006].
- **Broadband chlorophyll cannot identify species.** The hyperspectral layer is a concept backed by the Al Raha evidence, not yet built.

## 7. How it was built
- **Who:** the applicant designed and directed the project: problem framing, the rules (real data only, blind protocol, traceability), data sourcing and all decisions. Implementation was done with AI coding assistants (Claude Code), under the applicant's direction and review.
- **Data sources and routes:**
  - Sentinel-3 OLCI Level-2 (ESA/EUMETSAT) via the AWS Open Data Registry mirror (`meeo-s3`), 2,399 granules [`data/derived/olci_objects_*.csv`].
  - MODIS-Aqua L3 daily chlorophyll (NASA OBPG) via NOAA CoastWatch ERDDAP, downloaded by the applicant, 12 yearly files [`data/derived/modis_objects.csv`].
  - EAD Marine Water Quality reports and news/operator sources, as listed and graded in `SOURCES.md`.
