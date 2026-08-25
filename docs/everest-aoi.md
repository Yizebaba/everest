# Everest Area of Interest Authority

**Assignment:** EV-DATA-001-REM-01-AOI-APPROVE  
**Classification:** GIS documentation and governance only  
**Authority owner:** Everest Manager  
**Geometry steward:** GIS/3D owner  
**AOI identifier:** `everest-south-route`  
**AOI version:** `everest-south-route-v1.0`  
**Effective approval date:** 2026-08-21  
**Approval status:** Approved for the radius definitions in this document

## Purpose

This document is the authoritative AOI handoff for Everest project data
acquisition. It records the Manager-approved Mount Everest summit reference
center, the default operational AOI, one explicitly approved expansion, and the
approved serialized geometry for that expansion. It does not provide route
line, camp point, or other named-feature geometry.

## Reference Center and Coordinate Convention

The AOI center is the Mount Everest summit in WGS 84 (`EPSG:4326`):

| Field | Approved value |
| --- | --- |
| Latitude | `27.98806` degrees north |
| Longitude | `86.92528` degrees east |
| Center DMS | `27°59′17″N, 86°55′31″E` |
| CRS | WGS 84 (`EPSG:4326`) |
| Prose axis order | latitude, longitude |
| GeoJSON coordinate order | `[longitude, latitude]` |
| GeoJSON center coordinate | `[86.92528, 27.98806]` |

The decimal coordinate is the authoritative center for calculations. The DMS
value is a supplied display record and must not replace the decimal value in
spatial processing.

## AOI Definitions

### Default Operational AOI

The default operational AOI is a 100 km geodesic radius from the approved
summit center. This is the project default, not a general authorization to
retrieve data outside that radius.

Its approved operational scope includes the Everest south-side route; EBC, C1,
C2, C3, C4, and Summit; Khumbu Icefall; Western Cwm; and Lhotse Face, only to
the extent they fall within the 100 km radius. This statement does not define
or assert route, camp, or named-feature geometries.

### Approved Expanded AOI

The Everest Manager explicitly approved a 2,000 km geodesic radius expansion
from the same summit center on 2026-08-21. This expansion is an approved
exception to the default operational 100 km AOI; it does not change the default
AOI or supersede its use where the default is sufficient.

## Calculation Rule and Geometry Constraints

Each radius is the locus of points whose shortest surface geodesic distance from
the approved WGS 84 summit center is less than or equal to the applicable
radius: 100,000 m for the default AOI or 2,000,000 m for the approved expansion.
Distance calculations must use the WGS 84 ellipsoid, not a planar projection or
degree-based approximation.

The approved default geometry is a center point plus a geodesic-radius rule. A
system may calculate a default-AOI membership test from that rule. The approved
expanded geometry is separately published in the canonical GeoJSON artifact
recorded below. This document does not approve or imply any of the following:

- A default-AOI bounding box or polygon.
- Any expanded-AOI geometry other than the approved canonical artifact recorded
  below.
- Route geometry for the Everest south-side route.
- Point or area geometries for EBC, C1, C2, C3, C4, Summit, Khumbu Icefall,
  Western Cwm, or Lhotse Face.
- Any coordinate transformation, simplification tolerance, or antimeridian
  representation for a future serialized boundary.

Any future boundary change must be a separately versioned GIS artifact, validated
against this center and radius rule, and approved by the Everest Manager before
operational use.

## Deterministic Expanded-AOI Geometry Derivation

**Assignment:** `EV-DATA-001-REM-01-AOI-GENERATE`  
**Scope:** Deterministic local derivation of the Manager-approved 2,000 km
expansion. It publishes only the resulting geodesic circle boundary; it does
not create or infer route, camp, or other named-feature geometries.

### Fixed Inputs and Conventions

| Field | Required value |
| --- | --- |
| AOI identifier | `everest-south-route` |
| AOI version to derive | `everest-south-route-v1.0` |
| Center latitude | `27.98806` decimal degrees |
| Center longitude | `86.92528` decimal degrees |
| Reference ellipsoid | WGS 84: semi-major axis `6378137.0` m; flattening `1/298.257223563` |
| Distance model | Ellipsoidal direct geodesic |
| Radius | `2000000` m exactly |
| Geographic ordinate units | Decimal degrees |
| Prose axis order | latitude, longitude |
| GeoJSON position order | `[longitude, latitude]` |
| Longitude normalization | `[-180, 180)` degrees |
| Unique boundary vertices | `360` |
| Initial azimuth | `0` degrees true north |
| Azimuth increment | `1` degree |
| Winding | Clockwise when traversing azimuths `0` through `359` from north |
| Ring closure | Append an exact copy of the first position after vertex `359`; serialized ring length is `361` positions |

The radius is a surface geodesic distance in metres. It is not a planar buffer,
projected distance, spherical great-circle approximation, or a radius expressed
in angular degrees.

### Required Generation Algorithm

The generator must use an ellipsoidal direct-geodesic implementation configured
with the fixed WGS 84 parameters above. The required local generation environment
is Python with `geographiclib==2.1`; if that exact package is unavailable, no
serialized polygon or bbox may be emitted under this specification.

For each integer `i` from `0` through `359`, inclusive:

1. Set `azimuth_degrees = i`.
2. Solve the WGS 84 direct geodesic from latitude `27.98806`, longitude
   `86.92528`, initial azimuth `azimuth_degrees`, and distance `2000000` m.
3. Normalize the returned longitude to `[-180, 180)`.
4. Record the resulting position as `[longitude, latitude]` without rounding
   before validation.

The resulting 360 unique positions, followed by the copied first position,
form the canonical geodesic ring. A generator must record its full dependency
version, Python version, operating system, exact command or script content, and
UTC generation timestamp. It must not substitute a planar buffer operation,
interpolate route or feature coordinates, or add named-feature geometry.

### Antimeridian and GeoJSON Serialization

Longitude normalization is applied to every generated position before
serialization. The generator must inspect every consecutive pair in the closed
ring. If the absolute normalized-longitude difference is greater than `180`
degrees, the corresponding geodesic edge crosses the antimeridian and must be
split at the antimeridian before GeoJSON serialization. The serialized boundary
must then be a valid GeoJSON `MultiPolygon` with no ring edge that jumps across
more than `180` degrees of normalized longitude.

If no such edge exists, the serialized boundary is a GeoJSON `Polygon` with the
single canonical ring. The geometry type is therefore a derived result, not a
preselected assertion. Antimeridian splitting must preserve the same ellipsoidal
boundary and must be included in the generator script and hash input; it must
not be approximated by joining coordinates across the world map.

### Validation and Derived Bounding Box

Before an artifact is accepted, the generator must validate all of the
following:

- The source center and radius equal the fixed values in this section.
- There are exactly 360 unique pre-closure direct-geodesic vertices, generated
  for every integer azimuth from `0` through `359` exactly once.
- Every latitude is within `[-90, 90]` and every normalized longitude is within
  `[-180, 180)`.
- Every non-closure vertex is finite, and no adjacent non-closure positions are
  identical.
- The final ring position is byte-for-byte equal to the first serialized
  position.
- The winding follows increasing azimuth from `0` to `359`; validation must use
  this declared geodesic traversal rather than a planar signed-area inference.
- Each generated vertex, when checked by the same WGS 84 inverse-geodesic
  implementation against the approved center, is `2000000` m within a recorded
  numerical tolerance. The tolerance value and measured maximum residual must
  be recorded with the artifact.
- Any antimeridian crossing is split as specified above, and every serialized
  ring is closed and has at least four positions.

After validation and antimeridian handling, derive the GeoJSON bbox from the
serialized coordinate positions only: `[minimum_longitude, minimum_latitude,
maximum_longitude, maximum_latitude]`. The bbox is a coordinate envelope for the
serialized geometry, not a replacement for the geodesic radius rule. Do not
calculate it from planar distance, degree offsets, or an assumed longitude span.

### Artifact Identity and Generation Record

The canonical artifact must be UTF-8 GeoJSON serialized with a documented,
deterministic JSON representation: object keys in lexicographic order, compact
separators `,` and `:`, no insignificant whitespace, and numbers emitted by the
generator without an undocumented display-rounding step. Compute `SHA-256` over
those exact UTF-8 bytes. Record the artifact filename, geometry type, coordinate
reference system statement, vertex count, bbox, SHA-256, generator script hash,
and dependency lock or package hash.

The canonical artifact was generated locally on 2026-08-21 at
`2026-08-21T03:51:11.131328Z`:

| Field | Recorded value |
| --- | --- |
| Artifact filename | `docs/everest-south-route-v1.0-expanded-2000km.geojson` |
| Serialized GeoJSON geometry type | `Polygon` |
| Coordinate reference system | WGS 84 (`EPSG:4326`); GeoJSON positions are `[longitude, latitude]` in decimal degrees |
| Ellipsoid | WGS 84; semi-major axis `6378137.0` m; flattening `1/298.257223563` |
| Center | latitude `27.98806`, longitude `86.92528` |
| Radius | `2000000` m exactly |
| Direct-geodesic tool | GeographicLib Python package `2.1` (`geographiclib.geodesic.Geodesic.WGS84`) |
| Official documentation consulted | `https://geographiclib.sourceforge.io/html/python/` (GeographicLib Python `2.1` documentation, dated 2025-08-21) |
| Python runtime | `3.14.5 (tags/v3.14.5:5607950, May 10 2026, 10:43:50) [MSC v.1944 64 bit (AMD64)]` |
| Operating system | `Windows-11-10.0.26200-SP0` |
| Exact generation command | `python "C:\Users\Hongke\AppData\Local\Temp\opencode\generate_everest_aoi.py"` |
| Generator script SHA-256 | `e7db19f585bb2cec4528f9f84fd5af0f79ade4c9c718982c92edecd79e59d699` |
| Geometry SHA-256 | `b21ce4c8fe8d0fae15e0723e54fa3224f06e253b2662cdaee58e8efe1bb290ac` |
| Canonical UTF-8 payload size | `14070` bytes |
| Serialized bbox | `[66.49531953902317,9.921015585444335,107.3552404609768,46.00929037112946]` |
| Unique direct-geodesic vertices | `360`, for integer azimuths `0` through `359` |
| Serialized ring positions | `361`, including an exact copy of vertex `0` as closure |
| Antimeridian result | No crossing; maximum consecutive normalized-longitude difference was `0.4432877630360963` degrees, so the serialized result is the required single `Polygon` |
| Inverse-geodesic tolerance | `0.00000001` m |
| Maximum inverse-distance residual | `0.000000003725290298461914` m |

The GeoJSON file is canonical UTF-8 JSON: keys are lexicographically sorted,
separators are `,` and `:`, and it has no insignificant whitespace. Its
SHA-256 is computed over those exact serialized bytes. The embedded `bbox` was
derived only from the serialized coordinate positions.

Generation used `Geodesic.WGS84.Direct` for each integer azimuth and
`Geodesic.WGS84.Inverse` for the independent distance validation. Before
writing the artifact, the generator verified the fixed center and radius; 360
unique vertices; finite and normalized coordinate ranges; no adjacent duplicate
non-closure vertices; exact ring closure; increasing declared azimuth order;
the inverse-distance tolerance; and the absence of a normalized-longitude jump
greater than 180 degrees. All checks passed.

## Source Records and Verification Status

The following source records were supplied and approved by the Manager as
provenance records for the summit center. They are not live-URL verification
results from this assignment.

| Provider label | Supplied official source URL | Supplied identifier/query | Verification status |
| --- | --- | --- | --- |
| Chinese Ministry of Natural Resources / Tianditu | `https://www.tianditu.gov.cn` | Standard place-name search: `珠穆朗玛峰` | User-approved source record; live URL and result not verified in this assignment |
| NGA Geographic Names Server | `https://geonames.nga.mil/` | NGA Feature ID `-1021295` | User-approved source record; live URL and feature record not verified in this assignment |

No external URL was accessed, no provider response was retrieved, and no claim
of live source, coordinate, license, access, or service verification is made by
this document.

## Exclusions

The following are expressly excluded unless the Everest Manager records a new
approval in this document:

- Data acquisition outside the default 100 km radius, except where the approved
  2,000 km expansion is necessary and documented for the specific workflow.
- Any AOI larger than the approved 2,000 km geodesic radius.
- Global datasets when an AOI-limited dataset or subset is sufficient.
- Inferred, estimated, or third-party route, camp, or named-feature geometry.
- Any polygon or bounding-box geometry other than the separately versioned,
  validated expanded-AOI artifact recorded in this document.
- Treating the 2,000 km expansion as the default operational AOI.
- Downloading, querying, subsetting, or otherwise acquiring data under this
  documentation-only assignment.

## Change Control

Only the Everest Manager may approve a change to the center, CRS, coordinate
convention, radius, scope, or geometry constraints. The GIS/3D owner may
prepare a proposed change and validation evidence, but it is not operational
until Manager approval is recorded here.

Every approved change must create a new `aoi_version`, retain the prior version
for audit, state its approval date and rationale, identify affected acquisition
workflows, and distinguish whether it changes the default AOI or adds a limited
expansion. Data records and retrieval jobs must retain the `aoi_id` and
`aoi_version` used for each acquisition.

## Assignment Verification

- The approved WGS 84 / `EPSG:4326` summit center is recorded as latitude
  `27.98806`, longitude `86.92528`.
- Prose uses latitude/longitude order; GeoJSON uses `[longitude, latitude]`.
- The supplied DMS center, source URLs, provider labels, and NGA Feature ID are
  recorded without claiming live verification.
- The default 100 km AOI and Manager-approved 2,000 km expansion are explicitly
  distinct.
- The canonical expanded-AOI `Polygon` and its serialized-coordinate bbox are
  recorded above. No route, camp, or other named-feature geometry is introduced.
- The 2,000 km expansion now has a fixed WGS 84 geodesic derivation and
  validation contract and a generated, validated canonical GeoJSON artifact.
