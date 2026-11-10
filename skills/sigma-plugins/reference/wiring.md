# Wiring: host, register, bind

## Host

Any static HTTPS host works; Netlify has been the default.

```bash
netlify sites:create --name <client>-<plugin>          # once; keep the site id in a file
netlify deploy --prod --dir site --site <site id>      # every deploy; the name alone fails
```

- The CLI may be installed outside PATH (`~/.npm-global/bin/netlify`).
- Keep a deploy copy of just the files the plugin needs (`index.html`, any
  TopoJSON) in its own folder; don't deploy test pages or sample data.
- A local `python3 -m http.server` URL also registers, for quick iteration on
  your own machine only.

## Register (once per org)

```
POST /v2/plugins
{"name": "Care Map", "description": "...", "url": "https://<site>.netlify.app/", "type": "element"}
→ {"pluginId": "..."}
```

`sigmaapi.register_plugin(name, url, description)` in the
`sigma-pixel-perfect-report` scripts does this. Save the `pluginId` to a file
next to the build; `GET /v2/plugins` may not list a just-created plugin. A 401 or
403 means the API user can't register plugins; an org admin must.

## Bind in the workbook spec

```json
{"id": "ov-map", "kind": "plugin", "pluginId": "<pluginId>",
 "config": {
   "source": {"kind": "element", "elementId": "fmap"},
   "label": {"kind": "column", "columnId": "<feed column id>", "source": "source"},
   "value": {"kind": "column", "columnId": "<feed column id>", "source": "source"}}}
```

- Config keys match the plugin's `configureEditorPanel` names.
- Several sources: declare more element entries in the editor panel (for
  example `source` and `selected`) and bind each column with its own
  `"source": "<name>"`. Useful for a detail row (selected team, chosen site)
  alongside the main data.
- Place it inside a card container like any other element:
  `<Container elementId="ov-mapbox" ...><Element elementId="ov-map" gridColumn="1 / 25" gridRow="1 / 25"/></Container>`.
  Give maps and scenes 24+ grid rows.
- Plugins are exempt from the drill-down pass-through rule; they bind what they
  need.

## The feed table

- A hidden child of the element the page's controls already filter, so
  filters reach the plugin for free.
- Columns named exactly like the plugin's labels; precompute geometry and
  classes (`Switch()` lat/lon per site, rank, colour bucket, sort order).
- Keep it narrow and pre-aggregated where possible; send raw rows only when the
  plugin aggregates interactively (click to expand clinics, say).
- Put it on the hidden Data page's plugin tab.

## Changing a plugin later

- Visual or logic fixes: redeploy; the workbook picks it up on reload.
- New or renamed bindings: update `configureEditorPanel`, redeploy, then PUT
  the spec with the new config keys (read the live spec first).
- Keep the plugin source in the build folder (`plugin/index.html`) and the
  deploy copy separate.
