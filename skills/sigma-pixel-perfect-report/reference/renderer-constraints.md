# Sigma report renderer — what it actually accepts

Established empirically from 2026-08-17 (reproducing the Motorola 1967 annual
report) through 2026-11 (a few dozen client reports on staging and on AWS, GCP
and Azure production orgs). Every item below cost at least one round trip; the
error messages are quoted so you can recognise them.

**Read this first: `verify` proves very little.** The validator is lenient toward
unknown keys, several invalid values only fail on create, and some keys verify
and are then silently dropped. Only a render tells the truth, and the in-app
editor and the PDF export are two different renders that can disagree.

## Text elements

**Inline HTML is whitelisted.**
> `<b> is not in the allowed inline-HTML set (allowed: <u>, <sub>, <sup>, <span>, <a>)`

No `<b>`, `<i>`, `<pre>`, `<div>`, `<br>`, `<table>`. Weight and slant come from
markdown `**bold**` / `*italic*` / `***both***`, and all three render distinctly.
Avoid literal asterisks inside bold text: `**` next to `***` garbles.

**`<span style>` has a four-property whitelist.**
> `<span style> only allows color, background-color, font-size, and font-family, got "font-weight"`

So no `font-weight`, no `letter-spacing`, no `text-align`, no `line-height`.

**`font-size` must be an integer number of px, at most 96.** `7.5px` passes
`verify` and is then rejected on create.

**`font-family` must be one name.**
> `font-family must start with a letter and contain only letters, numbers, spaces, underscores, or dashes, got "Georgia, serif"`

No fallback lists, no quotes. Families that actually resolve: **Helvetica, Arial,
Verdana, Georgia, Times New Roman, Courier New**. Futura, Univers, Tahoma and web
fonts (Asap, Montserrat, Roboto…) silently fall back, so pick the closest of the
six. Georgia stands in well for a brand serif, Courier New for a brand mono.

**A `<span>` may not straddle two markdown blocks.**
> `body: unclosed inline HTML tag <span>`

A multi-line or multi-paragraph body must wrap each LINE in its own span.
`reportkit.Report.span()` handles this.

**An element-level `align` is silently ignored.** Unknown top-level element keys
are accepted and dropped, so this fails quietly rather than erroring; the symptom
is numbers sitting flush left in their boxes. Right-align by computing width:
`x = right_edge - advance_width`. This is exact: the renderer uses true Helvetica
metrics (measured period advance at 11px = 3.0571px vs the AFM's 3.0580, a 0.03%
match). Digits, comma, period, parens and `$` share the same advance in Regular
and Bold, so figures align identically at any weight.

- `rt()`/`ct()` measure with the Helvetica width table. **Georgia runs wider**:
  when centring Georgia, scale the computed width by about 1.12 for bold, 1.05
  for italic and 1.01 for letter-spaced caps, and pass an explicit `w` so the
  box doesn't clip.
- Glyphs missing from the Helvetica table (`→`, for one) are misplaced by
  `rt()`. Keep them out of right-aligned cells.
- Courier New renders `§` like `$`; draw `§` in Helvetica.

**Line pitch is a fixed 22.4px at every font size** (10, 11 and 12px all measured
22.4). It's governed by `theme.space.unit`, not by `font-size`. Consequences:
- rows needing a specific grid pitch get one element each; for tight prose, one
  `st()` per wrapped line at your own lead beats `prose()`'s fixed pitch
- block heights must be predicted, because the renderer CLIPS an overfull element
  rather than growing it

**A single line of text needs ~24–26px of element height, whatever the font
size.** Because line pitch is a fixed 22.4px, an `h=16` box clips a 9px label just
as badly as a 20px one. Symptom: caps look sheared ("UNITS SOLD" renders as
"UNITS SOI D"). Underscores and descenders need `h>=26`.

**The same undersizing also bleeds INTO THE NEXT ELEMENT, not just clips its
own box.** A pass that shrunk vertical offsets to match a smaller font (rule at
`y+19` after a 12px heading, next row at `y+36` after a 9px label) rendered with
the rule cutting through the descenders above it and each bar row's label
overlapping the previous row's bar. Give every single-line text element
`h=LINE_PITCH` (or `LINE_PITCH+4`) and space siblings at least one full
`LINE_PITCH` apart regardless of font size; use `heading()`'s offsets (rule at
`+26`, next element at `+38`) as the template for any stacked-text composite.

**Bold/italic markers must not wrap an empty string**: `"**" + "" + "**"` is
`****`, which markdown renders as a literal `**` on the page.

**An empty or whitespace-only body renders an error card** ("We've encountered an
error / Sentry Id …"), even with `backgroundColor` set. Use a stretched solid PNG
for colour rectangles.

**Not supported, emitted literally:** fenced code blocks (```), markdown tables.
A monospace span using `&nbsp;` *does* preserve runs of spaces, which is the only
route to preformatted columns.

**A long unbroken dot-leader run wraps as a single word and disappears entirely**
(it moves to line 2, which the element height clips). Compute the dot count from
measured widths so it never wraps.

**Dynamic text works.** `{{ formula }}` in a text body is evaluated at open and at
export, keeps the span's font, size and colour, and can read a source:
`{{Max([Src/COL])}}`, `{{DateFormat(Today(), "%d-%b-%Y")}}`. `=Today()`,
`{=…}`, `${…}` and `[=…]` all pass verify and render literally. See
`reference/live-data.md` for building whole live pages this way. A malformed
formula (for example a missing `& "`) makes verify return a bare HTTP 500 rather
than a validation error; bisect by dropping one element at a time.

## Image elements

- `style.fit` ∈ `contain | cover | stretch | none | scale-down`. **`fill` is
  rejected** (`Invalid kind: "image"`). Use `stretch` for colour fields, `contain`
  for artwork.
- `style.backgroundColor` must be a hex; `"transparent"` is rejected.
- `style.borderRadius: "square"` is accepted on image and box elements.
- `style.padding: "none"` conflicts with borders:
  > `padding is 'none' but border fields (borderWidth / borderColor) are set — border fields require default padding`
- `source` is `{"kind": "url", "url": <datauri or http url>}`. Datauris work well.
- **The whole spec is capped at 7 MiB decompressed.** Photographs must be JPEG
  (quality ~84 gives 70–500 KB each); PNG photos blow through the cap. Size each
  image to the area it actually covers rather than the full page, so it isn't
  upscaled and blurred.

## Layout

- `<Element x y width height>`: **x and y must be non-negative integers**
  (`layout[0].elements[0].x: must be a non-negative integer`), so artwork cannot
  bleed off the trim.
- Coordinates are absolute page px. `config.margin` is NOT an inset; set it to 0
  and position everything explicitly.
- Document order is z-order: the first element is furthest back, so page fields
  go first. An opaque KPI covers anything drawn before it, so draw labels after.
- **Any element extending past `pageHeight` silently spills onto an extra blank
  page.** Check every box's bottom before pushing; `reportkit` exposes
  `report.overflow()` and `build.py dump` prints it.
- **Any element whose `x + width` exceeds `pageWidth` silently WIDENS the page in
  the PDF**, so the whole page renders shrunk on a grey ground. Size text and bar
  boxes to their content. `overflow()` checks this too.
- Page size is free: 816×1056 (US Letter portrait), 1056×816 (landscape) and
  1280×720 (16:9 slides) all work. See `reference/delivery.md` for slides.
- `panels` (`type: header|footer`) are optional; omit them when page furniture
  varies per page.

## KPI elements

- `layout.anchor` accepts only `"center"` and `"right"`. `"start"`/`"end"` fail
  verify as `Invalid kind: kpi-chart`. Use `"right"` to right-align a live figure
  inside a typeset ledger row.
- `layout.horizontalAlign` verifies and is dropped; the value is always centred
  in its box otherwise.
- On at least one GCP production org the whole `layout` key was rejected; if a
  KPI fails verify there, remove `layout`.
- `style.backgroundColor` is honoured in both renders, and `"transparent"` works,
  so two KPIs can overlay (red/green variants with complementary `If()`s).
- Format with d3 strings: `{"kind":"number","formatString":"$.3s"}` renders
  `$86.8M`; `"(,.0f"` gives parenthesised negatives.
- A KPI card under ~5 rows tall can render the value with a stray decimal
  ("1.480"); keep KPI boxes at least ~5 text rows high.
- `SumIf` with no matching rows shows "null". Wrap aggregates in `Coalesce(…, 0)`.

## Charts

A native `bar-chart` renders inside a `kind: "report"` document, bound live to a
source. The element shape is the workbook chart's (`kind`, `source`, `columns`,
`xAxis`, `yAxis`), placed with absolute `x/y/width/height`.

- The top-level `sort` array that orders a `table()` is a no-op on a chart. Order
  categories with `xAxis.sort: {"by": <value-column-id>, "direction": ...}`.
- **A single-series bar chart with an `xAxis.sort` can mispair labels and bars
  in the PDF.** Use two series, or sort by an explicit order column.
- `color: {"by": "category", "scheme": [...]}` works, but colours are assigned in
  the SORTED order of the categories actually present. Build the scheme from the
  values shown, in alphabetical order. One colour: `{"by": "single", "value": hex}`.
- A chart can't use the same column for the x axis and colour; duplicate the
  column.
- `name: {"visibility": "hidden"}` removes the auto title; a hidden legend key is
  accepted.
- Axis `min`/`max` and label-hiding keys are ignored on report charts. For a
  fixed scale, add a stacked "track" series (stacking draws the LAST series from
  0) and cover repeated tick labels with a page-coloured box.
- A category-coloured single series with `stacking: "none"` leaves a gap per
  category; use `"stacked"`.
- Vertical bars rotate even short labels; horizontal bars read better and give
  diverging negatives.
- Workbook layout XML (used by `warehouse.py`) requires `gridColumn`/`gridRow`;
  only REPORT layouts take absolute x/y.

## Tables: what you can and cannot style

**Works (confirmed by spec round trip and PDF render):**
- `tableStyle.textStyles.header.fontSize` / `textStyles.cell.fontSize`: integer
  px; 9 gives ~20px rows.
- per-column `style.width`. Without widths Sigma splits columns evenly and
  truncates long ones.
- `tableComponents: {"summaryBar": "hidden"}` hides the summary bar. Shrinking
  the box instead clips rows.
- `tableStyle.preset` (`presentation` | `spreadsheet`), `tableStyle.cellSpacing`
  (`small|medium|large`; `none` rejected), `style.borderRadius` (`round|square`),
  `style.borderColor`/`borderWidth`, `style.backgroundColor` (container only),
  per-column `format`, an element-level `sort`.

**Verifies but is a NO-OP:** `tableStyle.rowBanding` / `banding` / `borders` /
`headerStyle` / `fontSize` (top-level) / `density`; `tableComponents.header` /
`headers` / `rowNumbers` / `pagination` / `footer` / `totals`;
`style.fontFamily` / `color` / `fontSize`.

**The table face is always Sigma's UI font**; only the size can change.

**Cell/header fill differs between the two renders.**
`tableStyle.textStyles.header.backgroundColor` and `textStyles.cell.
backgroundColor` work in the interactive editor, and if left unset the editor
resolves "inherited from container" into an explicit per-element value on
open/auto-save, inconsistently (two identically built tables came back
`#fcfcfc` and `#f5f3ef`). The PDF export ignores them and renders bound-table
fill as white. `table()`/`data_plate()` pin `textStyles` to `bg` automatically
so the in-app view stays consistent; don't call `table()` with `bg` unset.

For a PRINTED report on tinted stock, choose:

1. **`Page.text_table()`**: typeset the table from build-time or `{{ }}` live
   figures. Cells and header are the page; the type is the report's own face;
   leaders, per-row weights and ruled totals all become possible.
2. **`Page.data_plate()`**: keep it bound, put it on a near-white sheet so the
   white fill disappears, square the corners, frame it with your own hairlines.

**Row heights and clipping.** An undersized table silently CLIPS its extra rows,
with no scrollbar or warning. Measured rendered heights:

| Text size / spacing | Header | Row | Box height for n rows |
|---|---|---|---|
| 9px, small (landscape/letter) | ~28 | ~20.4 | `28 + n*20.4` |
| 10px | ~30 | ~21 | |
| 11px | ~30 | ~22 | |
| default (portrait 816×1056) | ~30 | ~25 | `30 + n*25` |

`Page.table_h()` assumes 24px rows, which is right for the default size but
leaves a clipped last row at 9px. Size from the table above, and if the data is
longer than the page show a top-N and state the remainder. An EMPTY bound table
shows a large "No data" box and collapses its column widths.

**Ordering.** A bound table does not inherit its source SQL's `ORDER BY`; set
`sort` on the element. `order` does not hide columns; to sort by a value you
don't want shown, sort a grouping by a calc column that's in `calculations` but
not in `order`. In a descending sort a null ranks ABOVE every number, so wrap
ranking calcs in `Coalesce(…, 0)`. An element-level `sort` on a calc column is
rejected (`Sort column not in level`); sort inside the grouping instead.

## Validator behaviour

The reports validator collapses element problems to `Invalid kind: "<kind>"`
without naming the field, so bisect by removing one key at a time. Unknown keys
at element or column level are accepted and ignored; unknown keys INSIDE a known
object (e.g. `tableComponents`) invalidate the whole element. A malformed text
formula returns a bare HTTP 500 instead. Create and update occasionally fail with
a transient `upstream connect error`; retry once before debugging.

## Entitlement

Reports-as-code (`/v2/reports/spec`) worked on every org tried from October 2026:
staging, several AWS production orgs, a GCP production org and an Azure
production org. An org without it returns an **empty 404** on
`/v2/reports/spec` and `/v2/reports/spec/verify` while `/v2/workbooks/spec/verify`
returns a normal 400. Probe both to distinguish "not entitled" from "bad
request".

## Rasterizing the exported PDF on macOS

There is no `pdftoppm`, `gs`, `mutool` or pyobjc on a stock Mac.
`scripts/raster.js` drives PDFKit through JXA instead (`rasterize.py` calls it).

- JXA selectors are camelCase concatenations (`representationUsingTypeProperties`,
  **not** the PyObjC `representationUsingType_properties_`).
- `PDFPage.thumbnailOfSize_forBox_` is not bridged; render via
  `NSImage.initWithData(page.dataRepresentation)`.
- **`NSImage.TIFFRepresentation` captures at the display's backing scale**, so a
  requested 1.0 yields a 2x PNG on a Retina machine. Always derive the true ratio
  as `png_width / page_width` rather than trusting the requested scale.
