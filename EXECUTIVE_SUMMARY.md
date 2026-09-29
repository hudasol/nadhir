# Nadhir — Executive Summary (2026-09-30)

**What Nadhir is:** a concept and working prototype for warning UAE and Gulf of Oman desalination plants that a
harmful algal bloom (red tide) is approaching, so operators can prepare instead of reacting.

**What was tested:** a blind hindcast on real satellite data. Detection thresholds were fitted on quiet years and
frozen in git before any documented event was scored. Two sensors were used: Sentinel-3 OLCI (2018–2023) and MODIS-Aqua (2003–2014).
Every number traces to a CSV in `outputs/` and a source ID in `SOURCES.md`.

## Findings, strongest first
1. **The protocol itself.** Both detectors are frozen (`723212e`, `0eef7be`), reproducible bit-for-bit (`make verify-freeze`),
   and re-scored after today's ground-truth corrections with no parameter changes (DECISIONS D-016).
2. **MODIS summer blind spot.** MODIS L3 had zero clear days in July–August within 50 km of the Gulf of Oman
   coast in every year from 2003 to 2014. OLCI had 6–21 per month over the same months (2018–2023). The 2008 bloom was first seen in late
   August, inside that blind window (`outputs/RESULTS.md` §2).
3. **Al Raha, April 2023.** EAD documented a toxic *Pseudo-nitzschia multistriata* red tide. Broadband chlorophyll
   showed no anomaly on daily OLCI or on the owner's independent monthly MODIS/CMEMS check. This is the case for a species layer (§3).
4. **Scorecard (50 km, frozen rules).** 1 of 4 observable dated disruptions produced an alert before the public record:
   - **Kalba 2018:** alert on 7 Sep 2018, 8 days before the first public report (WAM/Gulf News, 15 Sep 2018). The source does not state when the halt began, so the true lead time relative to the shutdown is unknown and could be shorter.
   - **Misses:** Barka 2018, Barka 2023, and RAK 2008 (closure Thu 30 Oct 2008 ±3 d). For RAK, the pre-registered 100 km sensitivity run alerted 8 days before closure, but the primary result is a miss (§4).
5. **False alarms:** 1.0–2.6 alert episodes per year per site in held-out quiet years. These are upper bounds (§5).

## Honest limits
- The sample is tiny.
- Disruption dates are news or operator report dates.
- Intake coordinates are estimated.
- There is no current/drift model yet.
- Broadband chlorophyll cannot identify species.
- Renewable-energy integration is planned, not built.
