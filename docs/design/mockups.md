# Everest Frontend UI — Screen Mockups (EV-UI-001)

**Design basis:** `docs/design/DESIGN.md` (dark mission-control aesthetic,
`#0B0E14` base, 400 px right rail, 8 px grid). All text English MVP, tabular
numerals, units on every value, UTC `Z`.

## S1. Main dashboard

```
+--------------------------------------------------------------------------------+
|  EVEREST · Summit Window             [⌚ 2026-08-24T06:00Z] [↻] [︙ menu]        |
+--------------------------------------+-----------------------------------------+
|                                      |  SUMMIT WINDOW                [GO ●]    |
|                                      |  valid 2026-08-25T00:00:00Z             |
|       3D Cesium scene (S2)           |  ▲ temp -32°C · wind 14 m/s · 45°       |
|   - terrain layer toggle             |  visibility 22000 m · precip 0 mm       |
|   - satellite layer toggle           |  basis: IFS 00Z L+24 · flags: clean     |
|   - observation markers              +-----------------------------------------+
|   - AOI boundary overlay             |  FORECAST  [IFS][AIFS][GFS][ICON]  [▶]  |
|   - time scrubber (bottom)           |  06Z 09Z 12Z ... (mini chart, step-only)|
|                                      +-----------------------------------------+
|                                      |  PROFILE  EBC C1 C2 C3 C4 SUMMIT        |
|                                      |  (altitude ladder / chart)              |
|                                      +-----------------------------------------+
|                                      |  OBSERVATIONS  Base Camp · Camp 2 · SC  |
|                                      |  -4.8°C · RH 62% · 0 mm                 |
|                                      +-----------------------------------------+
|                                      |  SOURCES / HEALTH  [table]              |
+--------------------------------------+-----------------------------------------+
```

## S2. 3D scene layers (gis-3d)

- **Terrain layer** (GLO-30 via `/api/terrain/tile`): basemap height from the
  retained tile; toggle in the scene toolbar. "No tile for this point" renders
  the ellipsoid + note.
- **Satellite layer** (Himawari via `/api/satellite/segments`): band imagery
  toggle; where band decoding is pending (JMA guide), the toggle shows an
  honest "decode pending" state, never fabricated imagery.
- **Observation markers** (via `/api/observations/current`): Everest AWS
  stations at API-provided coordinates only (Base Camp / Camp 2 / South Col),
  styled `everest-aws` orange, distinct from forecast markers.
- Markers at record lat/lon/altitude, NOT terrain-clamped (FR-MAP-003).
- Overlapping markers collapse into a **marker group** — count badge, single
  tab stop, arrow-key member selection, record-picker list (each row
  provenance-traceable), plus a "Skip map markers" link for keyboard users
  (DESIGN.md §7.2.1).

## S3. Summit Window scoreboard

Green/amber/red disc/triangle/square (color + shape + text), per-source
agreement bars, staleness note; labeled "non-authoritative presentation layer".

## S4. Provenance popover

Click any value -> panel: timestamp, source, model, cycle, lead, spatial_key,
record_type, quality_flags + source lifecycle/health (no restricted fields).

## S5. Time animation

Play/pause/step/scrub over present valid times only (no fabricated
intermediates); 750 ms/step at 1×; `prefers-reduced-motion` disables autoplay.

## S6. Empty / error / loading

Distinct: "no data for this selection" (empty) vs "API unreachable" (error with
retry + X-Correlation-ID). Loading shells per panel.
