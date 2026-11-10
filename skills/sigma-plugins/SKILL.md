---
name: sigma-plugins
description: >-
  Design, build, host, register and wire custom Sigma plugins (bespoke
  visuals inside a workbook: maps, Sankeys, percentile bars, heat maps,
  quadrants, canvas scenes) with the @sigmacomputing/plugin SDK. Use when
  the user wants a custom or bespoke visual, a "plugin", an interactive map,
  or a chart Sigma doesn't have natively, or when an existing plugin shows
  "waiting for data", ignores clicks, renders blank in exports, or needs
  redeploying.
---

# Sigma plugins

A Sigma plugin is a web page you host. Sigma loads it in an iframe inside a
workbook, and the SDK hands it the rows of a workbook element. This recipe
comes from 12 plugins built between September and November 2026;
`reference/catalogue.md` is the menu of what's been built.

Use with `sigma-workbook-field-notes` (workbook spec rules) and `sigma-workbooks`
(the API).

## Workflow

1. **Offer 3–4 design options first**, each one line: what it shows, the main
   interaction, why it fits this client's domain. Clients pick, and they
   reject the generic option surprisingly often (one swapped a Sankey for a map
   after seeing it). Domain-specific scenes beat chart lookalikes.
2. **Build one self-contained `index.html`** from `templates/plugin/index.html`:
   React UMD, then the SDK UMD, then pinned libraries; all CSS scoped to the
   root element; no build step.
3. **Feed it a hidden child table** holding exactly the columns it needs, named
   to match the plugin's `LABELS` (the name fallback depends on it). Compute
   anything geometric (lat/lon via `Switch()`, sort orders, colour classes) in
   the table, not in the plugin.
4. **Test locally with real rows** before deploying: export the feed table,
   build a test page with `templates/plugin/mktest.py`, screenshot it at
   several widths with `shot.sh`, and check clicks with the `#click=` hook.
5. **Deploy and register** (`reference/wiring.md`): Netlify, then
   `POST /v2/plugins` once per org. Keep the returned `pluginId` in a file.
6. **Bind it in the spec** with object-form column bindings, put it in a card
   container, PUT, and open the workbook in a real browser to confirm data
   arrives. The API export can't show you plugin data.
7. **Redeploys are instant**: Sigma loads the URL live, so a fix is a Netlify
   deploy, not a workbook change, unless bindings change.

## Rules that keep plugins working

1. **`window.SigmaPlugin.client`**, not `window.sigmaComputing`. Load React UMD
   before the SDK.
2. **Bind with the object form**:
   `{"kind": "column", "columnId": id, "source": "source"}`. Bare ids have left
   plugins stuck on "waiting for data". Also resolve columns by NAME through
   `subscribeToElementColumns` as a fallback (the template does this).
3. **Read `config.get()` at start-up**, then subscribe. Don't wait for the first
   `config.subscribe` callback.
4. **Scope all CSS to the plugin root.** A global `svg {position: absolute;
   inset: 0}` let a small sparkline cover the iframe and swallow every click.
5. **Draw statically.** No entrance animations: rAF-deferred and d3
   transitions freeze at frame 0 in headless renders, so exports show empty
   charts. No infinite CSS animations (they hang exports and screenshots).
6. **Cache heavy layers** on an offscreen canvas and redraw only when dirty;
   redrawing ~12k marks per frame hung the page export.
7. **Use the rAF timestamp** for any animation you do run (start t0 on the
   first frame); mixing it with `performance.now()` went negative and blanked
   the canvas.
8. **In SVG, set zoom-dependent sizes with `.style()`**, because CSS beats
   presentation attributes.
9. **Pin every CDN version** and draw basemaps from TopoJSON (us-atlas,
   world-atlas). Tile services now want API keys.
10. **Expose `window.__load(rows)`** and a URL-hash deep link (`#site=Name`,
    `#tab=X`) so headless tests can reach every state.

## Reference

- `reference/wiring.md`: hosting, registration, spec binding, layout,
  feed tables, multiple sources, redeploying.
- `reference/testing.md`: local test harness, click testing, what the API
  export can and can't show, browser checks.
- `reference/catalogue.md`: the 12 plugins built so far, as patterns to reuse.
- Template: `templates/plugin/` (`index.html`, `mktest.py`, `shot.sh`,
  `sample.json`).
