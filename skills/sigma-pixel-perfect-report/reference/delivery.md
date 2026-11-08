# Delivery: export, burst, slides, housekeeping

## Exporting a PDF

`POST /v2/reports/{id}/export` with `{"format": {"type": "pdf", "layout":
"portrait"}}` returns a query id; download from `/v2/query/{queryId}/download`.
The download returns an empty body until the file is ready, so poll.
`scripts/rasterize.py` does the export, download and PNG conversion
(`rasterize.export_pdf()` on its own for just the PDF). Reports export to PDF only; there is no
PowerPoint or Excel export.

Large live reports (hundreds of elements) take a minute or more to export.

## One PDF per recipient (burst)

`POST /v2/reports/{id}/schedules` silently DROPS `exportDestination:
email-burst`, `dynamicExportSettings`, `dynamicRecipientSettings` and
`workbookSettings.controlValues`. Native burst can't be set for a report through
the API.

What works: export with control values as `parameters`.

```json
POST /v2/reports/{id}/export
{"format": {"type": "pdf", "layout": "portrait"}, "parameters": {"<controlId>": "Acme Health"}}
```

In Python: `rasterize.export_pdf(report_id, dest, parameters={"Client": name})`.

Loop that over the recipient list (keep it on a hidden page as an unfiltered
source) and write `out/<recipient>/<report>.pdf`. The control id must match the
report's control id exactly. A scheduled burst can then be set up in the Sigma
UI if the client wants Sigma to send it.

## Slides (16:9) and PowerPoint

Set `page_w=1280, page_h=720` in `Report(...)`. The PDF comes out at 960×540pt,
which maps 1:1 onto a widescreen PowerPoint slide (13.333×7.5in).

To hand over a `.pptx`: export the PDF, rasterize each page at 3× (3840px wide)
with `scripts/raster.js`, and place each PNG full-bleed on a blank slide with
`python-pptx`. State plainly that the slides are images, not editable text.

## Page sizes

| Use | Size |
|---|---|
| US Letter portrait | 816×1056 |
| US Letter landscape | 1056×816 |
| 16:9 slide | 1280×720 |

## Housekeeping

- The report's URL is `.url` on `GET /v2/reports/{id}`.
- Delete a report with `DELETE /v2/files/{id}`; `DELETE /v2/reports/{id}` 404s.
- `GET /v2/reports/{id}/schedules` exists; schedules can be read and created,
  minus the burst fields above.
- If someone has the report open in the editor, a save there can overwrite an
  API update. After any update that removes elements, GET the spec back and
  check.
- Keep each client's credentials in its own env file and point
  `SIGMA_ENV_FILE` at it. The token cache is per env file, so two orgs never
  share a token.

## Design notes from client reviews

These came from repeated client feedback; treat them as defaults, not rules.

- Clients consistently prefer calm, editorial pages: one accent colour,
  typeset headlines, a few large figures, one chart per page. Busy stat strips,
  photo collages and literal illustrations were rejected more often than not.
- Abstract cover art built from a brand motif (generated with PIL, then embedded
  as a JPEG) lands better than a giant logo. Keep the art clear of headline text,
  or fade it under each text block.
- A closing page with a short line and the logo beats a page of takeaways.
- Sample brand colours from the client's site CSS. If the site blocks plain
  `curl`, try the `www.` host. Soften saturated brand colours for large fills.
