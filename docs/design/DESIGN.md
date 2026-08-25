# Everest Frontend UI — Design System (EV-UI-001)

**Delivery:** EV-UI-001 — Frontend UI, Milestone 1: Weather / Forecast Display
**Stage:** UI (`/plan-design-review` input) per `AGENTS.md`
**Author:** UI Designer (frontend line) — design handoff for EV-UI-001
**Last Updated:** 2026-08-24
**Authorization:** ADR-017 (frontend line), ADR-018 (five scope expansions),
ADR-019 (terrain / satellite / observation backend APIs)
**Normative inputs:** `docs/product/PRD.md` v0.2, `docs/architecture/architecture.md`
(EV-UI-001 section), `docs/meteorology/weather-spec.md`,
`docs/gis/terrain-spec.md`, `docs/management/decisions.md` (ADR-004/017/018/019)
**Status:** Proposed — design-system foundation for implementation under
`apps/web/`; the Cesium scene paths (`apps/web/src/cesium*`, `apps/web/src/map*`)
are gis-3d owned and consume these tokens and component contracts.

This document defines the visual and interaction system for the Everest Summit
Window decision surface. It is a **design contract**: exact hex, exact px,
exact ratios, grounded in PRD requirement IDs. It contains no application code.

> **Docs reconciliation (2026-08-24):** The PRD v0.2 non-goals that listed
> terrain, satellite, and observation surfaces as out of scope are superseded
> by ADR-019, which authorizes the 8-API display surface (the five weather APIs
> of ADR-015 plus terrain, satellite, and observations). The three new endpoint
> contracts (`GET /api/terrain/tile`, `GET /api/satellite/segments`,
> `GET /api/observations/current`) are consumed at §7.2/§7.3 and **should be
> added to `docs/api/API.md`** by the backend line before implementation.

---

## 1. Design Principles

**P1 — Truthfulness before polish.** Every rendered value is a canonical record
value with its canonical unit and UTC `Z` timestamp. Null is rendered
"unavailable", never zero or imputed (FR-SW-004, FR-ERR-005, AC-04). Stale,
flagged, `unknown`, and `failed` states are rendered as what they are; the UI
never implies data that is not there (NFR-AVAIL-002, FR-SRC-004). Presence is
never rendered as `verified` or `healthy`.

**P2 — Decision-signal discipline.** The only saturated decision accent in the
product is the Summit Window green/amber/red state. That palette is used for
nothing else — not buttons, not charts, not health dots, not errors. One glance
at a saturated green/amber/red element means one thing: Summit Window state
(FR-SW-006..008). All other semantics use the neutral, source, and health
palettes defined below.

**P3 — Precision at a glance.** Life-critical values must be readable without
decoding: unit on every value, UTC time on every basis, tabular numerals for
all numbers, stable column order across panels (FR-WX-002, FR-WX-007, US-10).
A climber under time pressure finds the current Summit-region wind in under 30 s
(success metric, PRD §4).

**P4 — Accessibility is a baseline, not a polish pass.** WCAG 2.1 AA applies to
all UI chrome (NFR-ACC-001). The 3D canvas is never the only view of the data:
a non-visual textual table of loaded canonical records is always available
(NFR-ACC-002), error/empty states announce to assistive technology
(NFR-ACC-003), and every color-coded meaning is paired with shape/icon/text
(colorblind-safe).

**P5 — No fabrication, no decoration that implies data.** No invented camp or
route geometry (FR-MAP-004), no fabricated timestamps in time animation
(FR-TIME-005), no interpolated chart values, no cached-fallback data rendered as
canonical (FR-ERR-005). Visual effects (shadows, glows, gradients) must never
create the impression of a value or a data source that does not exist.

**P6 — Calm under load.** Data-dense but visually quiet: 1 px borders, flat
surfaces, restrained motion, no decorative animation. The interface must stay
responsive on the documented record counts (NFR-PERF-002/003) — every decorative
choice has a performance cost and is weighed against it.

---

## 2. Aesthetic / Art Direction

The Everest UI is a **mission-control instrument panel for high-altitude
decision-making** — the aesthetic of a professional meteorology workstation
crossed with an expedition operations desk, not a consumer app. The stage is a
dark, near-black blue (`#0B0E14`) with light, cool-gray text (`#E6EAF2`) that
reads like instrument labels on a backlit panel. Surfaces are flat and
hairline-edged; elevation is communicated by border brightness and 1 px rules,
not by shadows. The 3D scene occupies the majority of the screen as the
"window" onto the mountain; the right rail is a stack of dense, precise data
panels whose rows align to a strict 8 px grid and tabular numerals, so columns
of numbers read like a telemetry strip. Color is rationed: source identity uses
cool technical hues (cyan, indigo, violet, teal), decision state uses exactly
three saturated signal colors, and everything else stays neutral or status-quiet.
Typography is Swiss-technical: a single clean sans (Inter) for labels and
values, tabular figures for every number, and a monospace face only where
identity must be copied or compared exactly (spatial keys, correlation IDs,
provenance timestamps). The overall impression must be: *this instrument tells
you the truth about the mountain, including when it does not know.*

---

## 3. Color System

All contrast ratios below are WCAG 2.1 relative-luminance ratios against the
stated background. Every ratio marked **AA-text** is ≥ 4.5:1 (normal text);
**AA-large** is ≥ 3:1. Colors are expressed as CSS custom properties with an
`--ev-` prefix so the system is a single source of truth.

### 3.1 Dark base palette (surfaces, text, rules)

| Token | Hex | Usage | Contrast on `#0B0E14` |
| --- | --- | --- | --- |
| `--ev-bg-base` | `#0B0E14` | App background; map stage behind scene | — |
| `--ev-surface` | `#111623` | Panel surface, header, time bar | text-primary 15.0:1 AA-text |
| `--ev-surface-2` | `#161D2E` | Raised: hover states, chips, popover, table header row | text-primary 13.94:1 AA-text |
| `--ev-border` | `#232C40` | Panel/component borders (1 px) | — |
| `--ev-border-subtle` | `#1A2132` | Inner rules, row separators | — |
| `--ev-text-primary` | `#E6EAF2` | Body, data values, headings | 16.0:1 AA-text |
| `--ev-text-secondary` | `#9AA5B8` | Labels, units, captions, secondary values | 7.8:1 AA-text |
| `--ev-text-muted` | `#5C6678` | Placeholder / decorative chrome only — never data values, null-state, or "unavailable" text | 3.34:1 AA-large only (WCAG 1.4.3 placeholder/decorative exception applies) |
| `--ev-focus-ring` | `#7FB4FF` | Focus indicator (2 px ring, 2 px offset) | 9.1:1 AA-text |
| `--ev-overlay` | `#0B0E14CC` | Scrim behind popovers (80 % opacity) | — |

Rules: text below 18 px / 14 px bold must use `--ev-text-primary` or
`--ev-text-secondary`; `--ev-text-muted` is reserved for placeholder and
purely decorative chrome only — it is never used for rendered data values,
null-state `unavailable` text (which must use `--ev-text-secondary`, AA at
caption size), or any informative label (WCAG 1.4.3 exception). Borders never
carry meaning alone (always paired with text/icon).

### 3.2 Semantic decision palette — Summit Window (RESERVED)

> **Hard rule:** the three colors below are used **only** for the Summit Window
> state / scoreboard (FR-SW-006..008). They must never appear on buttons,
> charts, markers, health dots, links, or errors. Source colors and health
> colors are deliberately chosen to not collide with them.

| Token | Hex | State | Label text (always rendered) | Shape glyph (always rendered) |
| --- | --- | --- | --- | --- |
| `--ev-decision-green` | `#2FBF71` | GO — window open | `GO` | filled disc ● |
| `--ev-decision-amber` | `#E8A33D` | CAUTION — marginal | `CAUTION` | filled triangle ▲ |
| `--ev-decision-red` | `#EF5350` | STOP — window closed | `STOP` | filled square ■ |

Contrast on `--ev-bg-base`: green 8.1:1, amber 9.0:1, red 5.5:1 — all AA-text.
State is never conveyed by hue alone: **color + shape + text label** are always
rendered together (colorblind-safe; see §3.5). The band thresholds behind each
state are config-driven and presentation-only (FR-SW-003/006); this document
fixes the visual encoding, not the thresholds (OQ-03).

The "unavailable" reading of a Summit value (record with a non-clean
`quality_flags` entry, FR-SW-004) renders as `— unavailable` in
`--ev-text-secondary` with the flag chip (§7.7) — never as a fourth decision
color and never in `--ev-text-muted` (muted is 3.34:1 and fails AA at 12 px
caption size).

### 3.3 Source / model identification palette

Source colors identify **provenance**, never quality. They are used for:
source chips, map marker fill/stroke, chart series, per-source agreement rows.
Each is paired with the source/model text label. Contrast on `--ev-bg-base` is
listed; all pass AA-text.

| Token | Hex | Source | Model / identity | Used for |
| --- | --- | --- | --- | --- |
| `--ev-src-ifs` | `#38BDF8` | `ecmwf-ifs` | `IFS` | Forecast (ECMWF) |
| `--ev-src-aifs` | `#818CF8` | `ecmwf-aifs` | `AIFS` | Forecast (ECMWF AI) |
| `--ev-src-gfs` | `#C084FC` | `noaa-gfs` | `GFS` | Forecast (NOAA) |
| `--ev-src-icon` | `#2DD4BF` | `dwd-icon` | `ICON` | Forecast (DWD) |
| `--ev-src-aws` | `#FB923C` | `everest-aws` | Everest AWS stations | Observations |
| `--ev-src-himawari` | `#F472B6` | `himawari` | Himawari-8/9 | Satellite |
| `--ev-src-copernicus` | `#94A3B8` | `copernicus-dem` | Copernicus DEM GLO-30 | Terrain |

Contrast on `--ev-bg-base`: IFS 9.0:1, AIFS 6.5:1, GFS 7.3:1, ICON 10.4:1,
AWS 8.5:1, Himawari 7.3:1, Copernicus 7.53:1 — all AA-text. Usage rules:

- Source colors never express health, staleness, or decision state.
- IFS (cyan) vs AIFS (indigo) are distinct but related — intentional: AIFS is
  the IFS-family AI model; the model label `IFS` / `AIFS` is always shown with
  the color (FR-WX-003).
- Marker fill/stroke uses the source color at 100 % against the dark scene;
  selected markers add a white halo ring (never a color change).

### 3.4 Health / quality palette

Health colors indicate **current operational health** from `GET /api/data-health`
(ADR-004 semantics). They are a separate, quieter family from the decision
palette and are **always rendered with an icon + text label** (never hue-only).
`unknown` health is a first-class, truthful state (FR-SRC-004, AC-05).

| Token | Hex | Health status | Icon | Contrast on `#0B0E14` |
| --- | --- | --- | --- | --- |
| `--ev-health-healthy` | `#4FA3C2` | `healthy` | check ✓ | 6.8:1 AA-text |
| `--ev-health-degraded` | `#A793D6` | `degraded` | half-circle ◐ | 7.2:1 AA-text |
| `--ev-health-stale` | `#6E84A8` | `stale` | clock ⏱ | 5.1:1 AA-text |
| `--ev-health-unknown` | `#8B93A5` | `unknown` | question ? | 6.3:1 AA-text |
| `--ev-health-failed` | `#B678A4` | `failed` | cross ✕ | 5.7:1 AA-text |
| `--ev-health-disabled` | `#9AA5B8` | `disabled` | slash / | 7.8:1 AA-text (reuses `--ev-text-secondary`; icon + label always shown) |

The health family uses cool blue/violet/slate hues only — deliberately off the
decision green/amber/red hues and their CVD appearance: healthy cyan-blue never
maps to decision-green, degraded/stale blue-violet/slate never map to
decision-amber, and failed plum never maps to decision-red under a
deuteranopia/protanopia CVD simulator. The palette must be re-validated with a
CVD simulator (e.g., Coblis) before implementation, in addition to the ratio
table above.

**Lifecycle status** (`planned`, `configured`, `connected`, `verified`,
`degraded`, `disabled`) is rendered as neutral chips — `--ev-surface-2`
background, `--ev-text-secondary` text, 1 px `--ev-border` — with a small icon,
so lifecycle and health are two **visually distinct, labeled fields**
(FR-SRC-002). `verified` is a historical lifecycle fact, never a health claim.

**Quality flags** (`quality_flags` additive labels from
`docs/meteorology/weather-spec.md`) render as warning chips: `--ev-surface-2`
background, `#D8B36A` text/border, warning-triangle icon, flag label text.
Contrast of `#D8B36A` on `--ev-surface-2` ≈ 8.5:1 AA-text. `clean` renders no
chip (a neutral `clean` chip appears in provenance only). All non-clean flags
share one warning treatment — severity is not graded per flag, because each
flag already carries its exact label.

### 3.5 Colorblind-safety rules (global)

1. **Never hue-only.** Every color-coded meaning has a redundant channel:
   shape (decision), icon (health), or text label (source, quality).
2. Decision GO/CAUTION/STOP use **disc / triangle / square** glyphs, so
   red-green confusion cannot invert the decision.
3. Source hues are spread across the blue→violet→teal family plus distinct warm
   hues for observations/satellite; adjacent source hues (IFS/AIFS) are always
   disambiguated by the model label text.
4. Health states each have a unique icon in addition to color; the health
   family is validated with a CVD simulator to stay off the decision hues
   (§3.4).
5. All primary text/label contrast passes WCAG AA against `--ev-bg-base` and
   `--ev-surface`.

---

## 4. Typography

### 4.1 Stacks

| Role | Stack | Notes |
| --- | --- | --- |
| UI + data | `Inter`, `system-ui`, `-apple-system`, `Segoe UI`, sans-serif | All UI text, all numeric values |
| Monospace | `JetBrains Mono`, `SFMono-Regular`, `Consolas`, monospace | Identity strings: `spatial_key`, provenance timestamps, source IDs, `X-Correlation-ID`, lat/lon in provenance |

No other fonts in the MVP (NFR-PERF-001: self-hosted woff2, `font-src 'self'`).

### 4.2 Scale

| Step | px / line-height | Weight | Usage |
| --- | --- | --- | --- |
| `--ev-type-overline` | 11 / 16 | 600, uppercase, letter-spacing 0.08em | Micro-labels: panel kickers, table column headers |
| `--ev-type-caption` | 12 / 18 | 400 | Captions, "unavailable" notes, provenance meta |
| `--ev-type-data` | 13 / 18 | 400 | Data values in tables/ladders (tabular) |
| `--ev-type-body` | 14 / 21 | 400 | Default panel body text |
| `--ev-type-label` | 14 / 21 | 500 | Field labels, buttons, chips |
| `--ev-type-title` | 16 / 22 | 600 | Panel titles |
| `--ev-type-subhead` | 18 / 24 | 600 | Section subheads |
| `--ev-type-page` | 20 / 26 | 600 | Page/app title (header) |
| `--ev-type-score` | 24 / 28 | 700 | Summit Window state value, scoreboard big numbers |

Dense panels operate at 12–14 px deliberately; 11 px is the minimum text size
and is used only for overline/caption chrome, never for data.

### 4.3 Numeric conventions (US-10, FR-WX-002)

- **Tabular numerals everywhere a number appears**: `font-variant-numeric:
  tabular-nums` on all data, units, and timestamps so columns align.
- **Units always shown** with a non-breaking space: `−3.6 °C`, `2.1 m/s`,
  `259 °`, `864 m`, `0.9 mm`, `500 m` (visibility is rendered in meters per
  the canonical contract — there is no canonical km field). No value is
  rendered without its unit.
- **Null values** render `unavailable` in `--ev-text-secondary` (AA at caption size, FR-SW-004); zero is
  only rendered when the canonical value is actually `0` (e.g., calm wind `0.0
  m/s`).
- **Timestamps** are always UTC ISO-8601 with trailing `Z` (FR-TIME-003,
  FR-WX-002). Local time, if ever added, is explicitly labeled and never
  replaces UTC.
- **Rounding:** display rounding is presentation-only and documented per field
  (temperature 1 decimal, wind speed 1 decimal, direction integer degrees,
  altitude integer m, visibility integer m, precipitation 2 decimals for mm).
  Rounding never changes the provenance payload.

---

## 5. Layout & Spacing

### 5.1 Page composition (desktop ≥ 1280 px)

```
┌─────────────────────────────────────────────────────────────────────────┐
│ Header 48px: mark · validation-run badge · UTC clock · refresh-all      │
├──────────────────────────────────────────────┬──────────────────────────┤
│ Map stage (flex 1, min 0)                    │ Panel rail 400px (scroll)│
│  · Cesium scene (gis-3d)                     │  · Summit Window card     │
│  · map toolbar (top-left, §7.3)              │  · Current weather        │
│  · layer toggles                             │  · Forecast + filters     │
│  · markers (§7.2)                            │  · Profile / ladder       │
│  · WebGL fallback / table alternative        │  · Disagreement           │
├──────────────────────────────────────────────┤  · Sources / health       │
│ Time bar 72px (map column bottom, §7.9)      │                          │
└──────────────────────────────────────────────┴──────────────────────────┘
```

- Grid: `grid-template-columns: minmax(0, 1fr) 400px`; panel rail becomes
  440 px at ≥ 1440 px.
- The map stage owns the center; all data panels live in the right rail and
  share one visual language so the rail reads as a single instrument stack.
- The map receives validated records and the active valid time as props
  (architecture §5); the design contract keeps panels fetch-owned and the scene
  fetch-free.

### 5.2 Breakpoints

| Breakpoint | Layout behavior |
| --- | --- |
| < 640 px (base/mobile) | Single column: header 48 px → map 50 vh → time bar → panels stacked full width. Panels collapse to single-column cards. |
| 640–1023 px (tablet) | Map 55 vh full width → time bar → panels in a 2-column grid below. |
| 1024–1279 px (desktop) | Map + 400 px rail. |
| ≥ 1280 px | Map + 400 px rail; ≥ 1440 px rail 440 px. |

The map never requests global data (FR-MAP-006) and the layout never forces
panels to overflow invisibly; the rail scrolls independently.

### 5.3 Spacing scale (8 px base)

`--ev-space-1: 4px · 2: 8px · 3: 12px · 4: 16px · 6: 24px · 8: 32px · 12: 48px · 16: 64px`

| Context | Value |
| --- | --- |
| Panel padding | 16 px (`--ev-space-4`) |
| Panel gap in rail | 12 px (`--ev-space-3`) |
| Section gap inside panel | 24 px (`--ev-space-6`) |
| Row gap in data tables | 8 px (`--ev-space-2`) |
| Chip/label internal padding | 4 px vertical / 8 px horizontal |
| Touch target | ≥ 32 px; 44 px recommended for primary controls (WCAG 2.2 §2.5.8 min 24 px, exceeded) |
| Border radius | Panels/popover 8 px; chips/buttons 4 px; markers circular |

### 5.4 Elevation & z-index

Flat surfaces, 1 px borders, no drop shadows on panels. Depth is expressed as:
scrim `--ev-overlay` above the map, `--ev-surface-2` for raised elements, and
z-order:

`map 0 → map toolbar 10 → panels 20 → popover/dialog 40 → toast/status 50`

---

## 6. Motion

### 6.1 Tokens

| Token | Value | Use |
| --- | --- | --- |
| `--ev-dur-fast` | 120 ms | Hover, focus, chip state |
| `--ev-dur-base` | 200 ms | Panel content swap, marker selection |
| `--ev-dur-slow` | 300 ms | Popover/dialog open-close (opacity + 8 px translate) |
| easing | `ease-out` (entrances), `ease-in-out` (state changes) | — |

Only `opacity` and `transform` animate. No layout-thrash animations, no
bouncing, no parallax on data chrome. Loading uses CSS-only skeleton shimmer
(`opacity` pulse), no JS animation loop (NFR-PERF-003).

### 6.2 Time animation pacing (FR-TIME-004/005, US-16)

- Default play rate: **1 valid-time step per 750 ms at 1×**; presets
  `0.5× / 1× / 2×`.
- Steps snap to the **distinct valid times present in the fetched forecast
  extent** — intermediate timestamps are never fabricated (US-16).
- Play stops at the extent end by default (configurable to loop); navigation is
  clamped to the fetched extent and the active server range (FR-TIME-002).
- Scrubbing snaps to the nearest present valid time; the active time drives the
  forecast panel and map markers, and every rendered value stays
  provenance-traceable (FR-TIME-004).

### 6.3 Reduced motion (`prefers-reduced-motion: reduce`)

- Autoplay is disabled; the time bar renders as manual step/scrub only.
- All transitions collapse to opacity-only ≤ 60 ms.
- Skeleton shimmer becomes a static placeholder.
- Popovers open instantly (no translate). No feature is unavailable under
  reduced motion — only motion is removed (WCAG 2.3.3).

---

## 7. Component Specs

### 7.1 Data panel (base pattern)

Visual: `--ev-surface` card, 1 px `--ev-border`, radius 8 px, padding 16 px.
Header row: panel title (`--ev-type-title`) + basis line (`--ev-type-caption`,
UTC `Z`) + action controls (refresh, filter chips) right-aligned.

Content rows: label (`--ev-type-caption`, `--ev-text-secondary`) above value
(`--ev-type-data`, tabular, `--ev-text-primary`) + unit; or label/value inline
for compact fields. Every value is clickable to provenance (§7.6).

States: **loading** (skeleton rows, `aria-busy`), **success**, **empty**
(§7.7), **error** (§7.7). All async panels implement these four states
(FR-ERR-004). Accessibility: panel `aria-labelledby` by title; error/empty
states use `role="status"` live region (NFR-ACC-003); refresh button has a
visible label.

### 7.2 Map markers (gis-3d owned; visual contract here)

Markers render canonical records at record `latitude`/`longitude`/`altitude` on
the ellipsoid, **not terrain-clamped** (clamping would invent ground height;
height-datum approximation documented in terrain-spec). Markers pass the 100 km
geodesic-membership test from AOI center `27.98806, 86.92528` (FR-MAP-002/003).

Shape encodes `record_type` (colorblind-safe):

| `record_type` | Marker | Size / style |
| --- | --- | --- |
| `forecast` | filled circle | 12 px, fill = source color |
| `observation` | ring (open circle) | 16 px, 2 px stroke = source color, transparent fill |
| `satellite` | square | 12 px, fill = source color |
| `derived` | triangle | 14 px, fill = source color |

- Fill/stroke by source color (§3.3) — always paired with a marker
  `aria-label` naming source, model, record type, UTC time, and key values.
- Selected marker: 2 px `--ev-text-primary` halo ring + label callout
  (panel-styled, §7.1) showing canonical values with units and UTC; click opens
  provenance (§7.6) (FR-PRV-001).
- **Observation stations** (Everest AWS — Base Camp / Camp 2 / South Col,
  ADR-019): larger ring markers (20 px, `--ev-src-aws`) at the **API-provided
  station coordinates** with the station-name label from the API. The UI never
  fabricates station/camp coordinates from labels (FR-MAP-004); camp labels in
  panels remain filter labels.
- Markers are focusable buttons (`aria-label`; Enter/Space opens provenance).
  The 3D canvas itself is not focusable; the non-visual table (§8) is the
  keyboard alternative (NFR-ACC-002).

#### 7.2.1 Marker groups — overlap strategy

When two or more markers' **screen-space** targets come within a 6 px cluster
tolerance at the current camera distance, they collapse into one **marker
group** so no record is hidden or occluded:

- **Group render:** a source-neutral `--ev-surface-2` disc (16 px, 1 px
  `--ev-border`) with a count badge (`≥2`) in `--ev-text-secondary`. The group
  is anchored at the mean of its member records' projected positions — a UI
  anchor, never a fabricated coordinate (FR-MAP-004); every member's true
  `latitude`/`longitude`/`altitude` is shown in the picker.
- **Keyboard:** the group is **one tab stop**. Arrow keys (←/→, ↑/↓) move
  focus between member records within the group (roving tabindex); Enter/Space
  opens the group's **record picker list** — a popover (§7.6 pattern) listing
  each member record (source, model, record type, UTC time, key values), each
  row opening provenance on activation (FR-PRV-001). Esc closes and returns
  focus to the group.
- **Skip link:** a persistent **"Skip map markers"** link is placed before the
  map stage; it moves focus to the panel rail / non-visual table (§8,
  NFR-ACC-002) so keyboard users can bypass all marker groups.
- Zoom out increases collapse; zoom in dissolves groups back to individual
  markers. Grouping never merges, averages, or fabricates record values.

### 7.3 Terrain / satellite layer toggles (ADR-019)

Map toolbar (top-left of stage, `--ev-surface-2`, radius 4 px, segmented):
**AOI overlay** (default on), **Terrain GLO-30**, **Satellite Himawari**. Each
is a toggle button with icon + label, `aria-pressed`, 32 px minimum height,
focus ring per §8.

- **Terrain layer** — consumes `GET /api/terrain/tile?lat&lon` metadata; the
  scene renders a hillshade/sampled surface from the Everest-owned tile
  (`--ev-src-copernicus`-tinted steel ramp `#203044` low → `#5B6B80` high,
  never data-semantic). Elevation tinting is restrained and labeled "GLO-30
  hillshade" in the legend; it is not a data layer.
- **Satellite layer** — consumes `GET /api/satellite/segments?band=`; a band
  selector (e.g., band 3) chooses segments to composite. Where full band
  decode/calibration is pending (terrain-spec/weather-spec status), the layer
  renders an honest placeholder: "Segment metadata available · full decode
  pending" — never a fabricated image.
- Layer states: off / loading / on / error / empty — each rendered per §7.7.
- Toggles are keyboard-operable (Tab + Enter/Space); toolbar is a
  `role="toolbar"` with arrow-key navigation between buttons.

### 7.4 Summit Window scoreboard card

Structure (FR-SW-001..009, AC-11):

1. **State header** — the only place the decision palette appears: state glyph
   (disc/triangle/square) + state text (`GO` / `CAUTION` / `STOP`) +
   `--ev-type-score` value; the basis value shown beneath (UTC `Z`, source,
   lead). A persistent label: "Presentation-layer framing of canonical values —
   not a Risk-engine or AI result" (FR-SW-008).
2. **Value grid** — `temperature`, `wind_speed`, `wind_direction`,
   `visibility`, `precipitation` with canonical units; each cell clickable to
   provenance (FR-PRV-001). Non-clean-flag or null values render
   `unavailable` in `--ev-text-secondary` + flag chip (FR-SW-004).
3. **Per-source agreement** — one row per present source/model: source-color
   chip + source/model label + band glyph (`GO/CAUTION/STOP` with shape) +
   staleness indicator (from record `timestamp` and `last_success_at`,
   FR-SW-007). Disagreement and stale data are shown, never hidden.
4. **Degradation** — composed from successfully loaded inputs only; failed
   inputs listed as unavailable with error hint; zero inputs → empty state, not
   a fabricated score (FR-SW-009).

Accessibility: state conveyed by glyph + text (not hue); the scoreboard is a
semantic list/table; live region announces state changes; every cell is a
keyboard-focusable provenance trigger.

### 7.5 Camp altitude ladder (FR-LAD-001/002, AC-13)

Vertical strip of six rungs, EBC → C1 → C2 → C3 → C4 → SUMMIT (top = SUMMIT or
bottom = EBC per design review; default EBC at bottom, climbing order upward).
Each rung: label chip + **actual record altitude in m** (never the label as
altitude, FR-PRO-003) + `temperature`, `wind_speed`, `wind_direction`,
`visibility` in tabular cells.

- **Compact cell format (fits the 368 px rail content width):** units appear
  once in the column header (`alt m · temp °C · wind m/s · dir ° · vis m`);
  cells render bare tabular numerals with the unit repeated only where
  legibility requires it, e.g. `32.4°`, `14.2`, `259`, `500`. When a rung
  would overflow 368 px (400 px rail − 2×16 px padding), it wraps to a
  two-column rung (identity/altitude left, values right); at ≥ 1440 px the
  values row may scroll horizontally within the rung. Numerals never wrap or
  truncate, so tabular columns stay aligned (NFR-ACC-001, US-10).

- Rung states: data / empty (explanation: no records match label, FR-PRO-004)
  / error (partial degradation, FR-LAD-002). Failed rungs render
  "unavailable + error hint"; the ladder never substitutes values.
- Forecast vs observation rendered distinctly (solid vs dashed value style or
  type chip) and toggleable (FR-PRO-002).
- Implemented as a semantic `<table>`-equivalent list (real text, proper
  headers) — the strip is a visual presentation of the same content
  (NFR-ACC-001/002). Six parallel profile queries per architecture §5.

### 7.6 Provenance popover (FR-PRV-001/002, AC-12)

Triggered by clicking any displayed value (map marker, panel cell, ladder cell,
scoreboard cell, disagreement point). Dialog, `--ev-surface`, 1 px `--ev-border`,
radius 8 px, scrim `--ev-overlay`, `--ev-dur-slow` opacity+translate.

Content (canonical record identity only):
`timestamp` (UTC Z), `source`, `model`, `forecast_cycle`, `forecast_lead_time`,
`spatial_key`, `record_type`, `quality_flags` chips, plus the record's source
lifecycle and operational health from already-loaded sources/health payloads
(no extra fetch, FR-PRV-002). No restricted fields ever: no endpoints,
credentials, raw paths, hashes, retention, hold, or audit data (FR-SRC-005).

Accessibility: `role="dialog"`, `aria-labelledby` (record identity), focus
trapped, Esc closes and returns focus to the trigger, no scroll lock that
breaks keyboard navigation.

### 7.7 Error / empty / loading states (FR-ERR-001..005, AC-06)

Three visually and semantically distinct states, each with a live region
(`role="status"`):

- **Loading** — skeleton rows (shimmer) in the panel shape; `aria-busy`;
  never a spinner that implies content that isn't there (FR-ERR-004).
- **Empty** — neutral, dashed `--ev-border`, `∅` glyph, text "No data for this
  selection" + the most likely cause when known (e.g., null `route_profile`,
  empty UTC range) (FR-ERR-003). Distinguishable from error at a glance
  (FR-WX-005).
- **Error** — 2 px left border in `--ev-health-failed`, `!` icon, message
  distinguishing 4xx (422: name the offending parameter, FR-ERR-002) from
  5xx/network (actionable + retry, FR-ERR-001), and the `X-Correlation-ID`
  echoed value displayed (FR-ERR-001). Retry button labeled "Retry".
  FR-ERR-005: errors never render fabricated/cached fallback data as canonical.

### 7.8 Source / health table (FR-SRC-001..005, AC-05)

Columns: **Source** (name + model) · **Lifecycle** · **Health** · **Last
success** (UTC Z) · **Last failure** (UTC Z). Lifecycle and Health are two
distinct, labeled columns (ADR-004; FR-SRC-002). Health renders per §3.4
palette with icon + text; `unknown` renders truthfully as `unknown` — presence
never implies `verified` or `healthy` (FR-SRC-004, US-12). Rows use
`--ev-type-caption` headers, 8 px row gaps, tabular timestamps. Implemented as
a real `<table>` with `th` scope headers (NFR-ACC-001). Only public allow-list
fields are requested/rendered (FR-SRC-005).

### 7.9 Time scrubber (FR-TIME-001..005, AC-14)

Bottom bar (map column), `--ev-surface`, 72 px: **play/pause**, **step back**,
**step forward**, **scrub slider**, current UTC valid-time label
(`--ev-type-data` tabular), extent labels (start/end UTC Z), speed selector
(`0.5×/1×/2×`).

- Slider `min`/`max` = first/last distinct valid time in the fetched extent;
  value = active valid time; **snaps to present valid times only** (no
  fabricated intermediates, US-16).
- Keyboard: ←/→ step, Home/End jump, Space toggles play; `role="slider"` with
  numeric `aria-valuenow` (index of the active valid time within the fetched
  extent, or epoch seconds) and `aria-valuetext` = the formatted UTC ISO-8601
  `Z` time; a live region announces the active time on change.
- Active time drives forecast panel + map markers (FR-TIME-004); every value at
  a scrubbed time stays provenance-traceable. Play is clamped to the fetched
  extent and active server range (FR-TIME-002/005).

### 7.10 Profile chart & model disagreement (FR-PRO-*, FR-DIS-*, AC-13)

- **Profile chart** (Recharts, per architecture): Y = record actual `altitude`
  (m), X = selected canonical variable (`temperature`, `wind_speed`,
  `visibility`); one series per source in source colors; forecast solid,
  observation dashed; per-label filter chips (EBC..SUMMIT, FR-PRO-001);
  forecast/observation toggle (FR-PRO-002); point click → provenance. Chart has
  a **textual data-table alternative** beside it for assistive tech (§8) and
  `aria-label` describing axes and units.
- **Disagreement view**: for selected valid time + variable, min/max/median
  across present sources with source points plotted (FR-DIS-001). Points are
  colorblind-safe: source color + source label always on the point/tooltip.
  Alignment rule disclosed ("nearest valid time used" when grids differ) and
  the view labeled presentation-layer, never a derived record (FR-DIS-002).
  Absent sources noted, never imputed.

- **Forecast mini chart (time strip)** (forecast panel header, FR-WX-007,
  US-10): one small series per present source/model across the fetched valid
  times. Encoding is **point/step-only**: a 4 px disc in the source color at
  each present valid time, optionally joined by a right-angle **step** for time
  continuity; a straight interpolating line between values is never drawn,
  because it would fabricate intermediate values (P5, FR-ERR-005). Missing
  valid times render as gaps, never bridged. Focus/hover shows the exact
  canonical value + UTC at that point; the chart carries an `aria-label` and
  a textual data-table alternative (§8).

### 7.11 Header refresh-all control (FR-ERR-001, NFR-PERF-003)

Header control (right side of the 48 px header, §5.1) refetches **only the
panels' backend endpoints** — the A-F display surface: `GET /api/weather/current`,
`GET /api/weather/forecast`, `GET /api/weather/profile`,
`GET /api/weather/sources`, and `GET /api/data-health`. It never calls external
sources directly (frontend fetch-free rule) and does not refetch the Cesium
scene or gis-3d layer toggles.

- **In-flight:** the button disables and shows a compact progress state; each
  rail panel re-enters its loading skeleton with `aria-busy` (§7.1/§7.7).
  Refetch never shows cached/fallback data as canonical (FR-ERR-005).
- **Live region:** a `role="status"` region announces "Refreshing all panels"
  on start, "All panels updated · <UTC Z>" on success, and the error message +
  `X-Correlation-ID` on failure (§7.7).
- **Scope guard:** identical in-flight requests are deduplicated per endpoint;
  a second click while in-flight is ignored; unchanged panels are not
  re-rendered.

---

## 8. Accessibility Baseline (WCAG 2.1 AA)

| Requirement | Design response | PRD ref |
| --- | --- | --- |
| Contrast | All text ≥ 4.5:1 (AA-text) against `--ev-bg-base` / `--ev-surface`; large text ≥ 3:1; disabled per WCAG 1.4.3 exception | NFR-ACC-001 |
| Focus visible | 2 px `--ev-focus-ring` ring, 2 px offset, on all interactive elements; never removed without a replacement indicator | NFR-ACC-001 |
| Keyboard operable | All chrome reachable by Tab; arrows on toolbar, scrubber, chips; Enter/Space activates; popover Esc closes; no keyboard traps | NFR-ACC-001 |
| Marker-group navigation | One tab stop per marker group; arrows select members; Enter/Space opens the record picker; "Skip map markers" link jumps to the panel rail / table (§7.2.1) | NFR-ACC-001/002, FR-MAP-007 |
| Semantic markup | Real headings, `<table>` for tabular data, `aria-labelledby` panels, `aria-pressed` toggles, `role="dialog"` popovers, `role="slider"` scrubber with numeric `aria-valuenow` + `aria-valuetext` (UTC) | NFR-ACC-001 |
| Non-visual map alternative | A textual data table of loaded canonical records is always available (toggle in header), independent of WebGL; map markers also expose `aria-label`s | NFR-ACC-002, FR-MAP-007 |
| Live regions | Error/empty states announce via `role="status"`; time-scrubber announces active time | NFR-ACC-003 |
| Reduced motion | `prefers-reduced-motion: reduce` handled per §6.3; no information conveyed by motion | WCAG 2.3.3 |
| Touch targets | ≥ 32 px interactive; 44 px for primary controls (≥ WCAG 2.2 §2.5.8 min 24 px) | NFR-ACC-001 |
| WebGL fallback | Without WebGL2: clear fallback message in map area; all panels + table alternative remain functional | FR-MAP-007, US-14 |
| Screen-reader labels | All icons have accessible names; marker `aria-label`s name source/model/type/time/values | NFR-ACC-001 |

---

## 9. i18n Note (NFR-I18N-001)

All user-facing strings live in the typed message catalog
(`src/i18n/messages.ts`, English MVP) accessed via a typed `t(key)` helper; no
hard-coded UI text in components. Canonical technical labels (units, field
names, record types, lifecycle/health enums, quality flags, source/model
identities) render from constants shared with the API contracts so vocabulary
cannot drift from the canonical contract (architecture §8). The catalog is
structured so a future language milestone adds a second catalog and locale
selector without component refactoring. Decision labels (`GO`/`CAUTION`/`STOP`),
state text, and error messages are catalog keys.

---

## Appendix A — Design token summary (handoff)

```css
:root {
  /* Base */
  --ev-bg-base: #0B0E14; --ev-surface: #111623; --ev-surface-2: #161D2E;
  --ev-border: #232C40; --ev-border-subtle: #1A2132;
  --ev-text-primary: #E6EAF2; --ev-text-secondary: #9AA5B8; --ev-text-muted: #5C6678;
  --ev-focus-ring: #7FB4FF; --ev-overlay: #0B0E14CC;

  /* Decision (Summit Window only) */
  --ev-decision-green: #2FBF71; --ev-decision-amber: #E8A33D; --ev-decision-red: #EF5350;

  /* Sources / models */
  --ev-src-ifs: #38BDF8; --ev-src-aifs: #818CF8; --ev-src-gfs: #C084FC;
  --ev-src-icon: #2DD4BF; --ev-src-aws: #FB923C;
  --ev-src-himawari: #F472B6; --ev-src-copernicus: #94A3B8;

  /* Health (cool family, off the decision hues; CVD-validated) */
  --ev-health-healthy: #4FA3C2; --ev-health-degraded: #A793D6;
  --ev-health-stale: #6E84A8; --ev-health-unknown: #8B93A5;
  --ev-health-failed: #B678A4; --ev-health-disabled: #9AA5B8;

  /* Quality-flag chip */
  --ev-flag-warning: #D8B36A;

  /* Typography */
  --ev-font-ui: 'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif;
  --ev-font-mono: 'JetBrains Mono', 'SFMono-Regular', Consolas, monospace;
  --ev-type-overline: 11px/16px 600; --ev-type-caption: 12px/18px 400;
  --ev-type-data: 13px/18px 400; --ev-type-body: 14px/21px 400;
  --ev-type-label: 14px/21px 500; --ev-type-title: 16px/22px 600;
  --ev-type-subhead: 18px/24px 600; --ev-type-page: 20px/26px 600;
  --ev-type-score: 24px/28px 700;

  /* Spacing (8 px base) */
  --ev-space-1: 4px; --ev-space-2: 8px; --ev-space-3: 12px; --ev-space-4: 16px;
  --ev-space-6: 24px; --ev-space-8: 32px; --ev-space-12: 48px; --ev-space-16: 64px;

  /* Motion */
  --ev-dur-fast: 120ms; --ev-dur-base: 200ms; --ev-dur-slow: 300ms;
  --ev-ease-out: cubic-bezier(0.22, 1, 0.36, 1); --ev-ease-in-out: cubic-bezier(0.45, 0, 0.55, 1);

  /* Layout */
  --ev-rail-width: 400px; --ev-rail-width-xl: 440px;
  --ev-header-h: 48px; --ev-timebar-h: 72px;
  --ev-radius-panel: 8px; --ev-radius-chip: 4px;
}
```

## Appendix B — Grounding map (key PRD/ADR refs)

| Design element | Requirement(s) |
| --- | --- |
| Decision palette usage rules | FR-SW-006..008; AC-11 |
| Truthful health rendering | FR-SRC-002/004; ADR-004; AC-05 |
| Null = unavailable | FR-SW-004; FR-ERR-005; AC-04 |
| Units + UTC Z always | FR-WX-002; FR-TIME-003; US-10 |
| No invented geometry / markers at record coords | FR-MAP-003/004; AC-03 |
| Terrain / satellite / observation layers | ADR-019; terrain-spec; weather-spec §new-source |
| Provenance on every value | FR-PRV-001/002; AC-12 |
| Ladder partial degradation | FR-LAD-002; AC-13 |
| Disagreement from present sources only | FR-DIS-001/002; AC-13 |
| Time animation bounds | FR-TIME-001..005; AC-14 |
| Error/empty/loading distinct | FR-ERR-001..005; AC-06 |
| Accessibility baseline | NFR-ACC-001..003; FR-MAP-007 |
| i18n catalog | NFR-I18N-001 |
| Performance targets | NFR-PERF-001..003 |

*End of DESIGN.md — design-system handoff for EV-UI-001; next stage:
`/plan-design-review`.*
