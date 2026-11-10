# Catalogue: plugins built so far

Twelve plugins built between September and November 2026, described by
pattern rather than client. Reuse the approach and interaction, not the
branding. Every one is a single `index.html` on React UMD + the SDK.

| Pattern | What it shows | Interaction | Libraries |
|---|---|---|---|
| Choropleth + donut map | Regions shaded by a toggle metric; a donut per site with a slice per sub-unit | Wheel/pinch zoom, click a site to fly in and explode into sub-unit rings, breadcrumb back, list↔map hover sync | d3 7.9.0, topojson-client 3.1.0, world-atlas / us-atlas |
| National → local drill map | A donut per organisation nationally; click zooms to its clinics | Pills switch the metric (mix, average, threshold rate); side panel; auto-zoom when only one org is visible | d3, topojson-client, us-atlas |
| Market health map | Markets as shaded areas with a side panel and sparkline | Mode buttons (several metrics), click for detail | d3, topojson-client |
| Care / capacity map | Real county groups shaded by a toggle; city bubbles coloured by status | Toggle metric, hover detail | Leaflet 1.9.4, topojson-client, us-atlas, world-atlas |
| Simple location map | Sites as markers with availability | Hover, click for detail | inline SVG |
| Dumbbell comparison | Each entity's metric then vs now | Pills switch metric, click to expand children, hover tooltip, a mix strip per row | plain DOM/SVG |
| Percentile bars | Stat-by-stat percentile rank vs peers, colour from weak to elite | Section tabs, hover definitions, click a stat for a league distribution strip with dodged dots | plain DOM/SVG |
| Zone heat map | A 5×5 grid (strike zone style) shaded by a chosen metric | Metric pills, per-cell hover | inline SVG |
| Sankey journey | Flow between stages | Hover ribbons | d3, d3-sankey 0.12.3 |
| Risk quadrant | Accounts on two axes (health vs expansion), sized by value | Hover, quadrant labels | canvas |
| Aerial farm scene | Fields sized by spend; crop rows fill month by month; silo = output | Play button and month slider, hover tips, click for a detail card | canvas (static layer cached offscreen) |
| Galaxy of people | Spiral arms = segments, radius = propensity, size = giving, twinkle = visits | Search with top-8 dropdown and keyboard nav, fly-to, detail card, `#q=` deep link | canvas |

## What made these land

- **Domain metaphor over chart type.** A farm for an ag-marketing client, a
  galaxy for a science museum, a strike zone for a baseball team. Clients
  remember those.
- **One clear interaction**, such as click to drill, plus hover detail. Not a
  dozen controls.
- **Calm palette**: the brand colour softened, light background, thin borders,
  matching the workbook around it.
- **Real geography** from TopoJSON, never a tile service.
- **Useful empty and single-entity states**, for example auto-zooming when RLS
  leaves one organisation.

Before building, offer three or four options like these, each in one line, and
let the client pick.
