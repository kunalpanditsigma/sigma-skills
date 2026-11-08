# Plugins

## SDK and bindings

- The SDK 1.3.x UMD build exposes `window.SigmaPlugin.client` (not
  `window.sigmaComputing`) and needs React UMD loaded first.
- Bind columns with the object form
  `{"kind": "column", "columnId": id, "source": "source"}`. Bare column ids have
  left plugins on "waiting for data". Add a name-based fallback via
  `subscribeToElementColumns`.
- Bind data from `config.get()` immediately rather than waiting for
  `config.subscribe`.
- A plugin can take several element sources (e.g. `source` and `quality`).
- Feed a plugin from a small hidden child table holding exactly the columns it
  needs; compute lat/lon with `Switch()` formula columns.
- `GET /v2/plugins` may not list a just-created plugin; keep the `pluginId` from
  the POST response.

## Rendering and CSS

- Scope plugin CSS to the plugin root. A global `svg {position: absolute;
  inset: 0}` once made a sparkline cover the whole iframe and swallow every
  click.
- SVG text font and stroke set in CSS override presentation attributes, so
  zoom-compensated sizes must use `.style()`, not `.attr()`.
- Animate with the `requestAnimationFrame` timestamp (start t0 on the first
  frame). Mixing `performance.now()` with the rAF clock drove progress negative
  and blanked the canvas.
- Draw heavy static layers once to an offscreen canvas; redrawing ~12k marks
  per frame made the page PNG export hang. Infinite CSS animations hang
  exports and screenshots too.
- d3 draw-in transitions freeze at frame 0 in headless renders; draw
  statically.
- Tile basemaps (CARTO) now need API keys; draw basemaps from us-atlas /
  world-atlas TopoJSON instead.

## Hosting

- Netlify: `netlify deploy --prod --dir <dir> --site <site id>`; the site name
  alone fails. The CLI may live outside PATH (`~/.npm-global/bin`).
- Pin CDN libraries to exact versions (d3 7.9.0, topojson-client 3.1.0,
  Leaflet 1.9.4 have all worked).

## Testing

- The headless export delivers plugin config and columns but NEVER element data,
  and an element screenshot of a plugin returns "Not a visualization". Verify
  visuals by injecting exported rows into a local copy of the plugin
  (`window.__load(rows)`), and test clicks with `elementFromPoint`.
- Some plugins do render in workbook PNG exports, others never complete; check
  in a real browser before calling it done.
- Add a URL-hash deep link (`#site=Name`) so headless screenshots can open a
  specific state.
