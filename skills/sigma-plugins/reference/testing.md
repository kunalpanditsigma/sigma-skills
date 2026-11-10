# Testing plugins

## What Sigma's API can show you

- The headless workbook export delivers plugin CONFIG and column metadata but
  never element data, so a plugin in an API-rendered PNG shows its empty
  state (or nothing). An element screenshot of a plugin returns "Not a
  visualization".
- Some plugins appear in page PNG exports and some never finish rendering;
  either way, an export can't prove the data flows.
- So plugin data must be checked in a real browser: open the workbook, or an
  embed portal page that loads it, and look.

## Local harness (do this before every deploy)

1. Export the feed table's rows as JSON (`POST /v2/workbooks/{id}/export` with
   the feed element, poll the download). Real rows catch nulls, long labels
   and odd values that sample data doesn't.
2. `python3 mktest.py site/index.html rows.json` writes `test/index.html`, the
   plugin page plus a script that calls `window.__load(rows)`.
3. `bash shot.sh out.png 1100 700` and again at about 700px wide: plugins live
   in grid cells that change width with the page.
4. Click test: `#click=<index>` dispatches a click at the row's position and sets
   `document.title` to `HIT:true` only if the element under that point really is
   the row. That catches overlays that swallow clicks (the scoped-CSS bug).
   Read it with Chrome `--dump-dom`.
5. Deep-link hooks (`#tab=`, `#site=`) let you screenshot every state.

`--virtual-time-budget` is fine for a local file. For a live Sigma embed it
hangs; use a real-time wait instead, and load the embed through its portal page
(a signed embed URL loaded top-level renders blank).

## Checklist before calling it done

- [ ] Renders at ~700px and ~1100px with real rows; no clipped labels.
- [ ] Empty state reads sensibly ("Bind a source element", "No rows").
- [ ] Every button, tab and mark responds (click test passes).
- [ ] No entrance animation, no infinite animation.
- [ ] Opened once in a real browser with data flowing; say so if you couldn't.
