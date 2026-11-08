# Spec shape (live API, Oct–Nov 2026)

## Document

```json
{"name": "...", "folderId": "<uuid, required>",
 "document": {"kind": "workbook", "schemaVersion": 1,
   "pages": [{"id": "pov", "name": "Overview", "visibility": "..."}],
   "elements": [...],
   "layout": "<Page ...> ... </Page>",
   "settings": {"theme": {"name": "Light", "overrides": {...}}}}}
```

- Elements are top-level in `document.elements`, not per page.
- Layout tags: `<Container>` / `<Element>` (not `GridContainer` /
  `LayoutElement`); `<TabbedContainer>` / `<Tab>` work, including inside an
  overlay page. Elements inside a `<Tab>` keep their ids.
- Grid layout uses `gridColumn` / `gridRow`. Page `gridTemplateColumns` is
  normalised to 24 server-side; design on 24 columns.
- `POST` returns YAML unless you send `Accept: application/json` (same for GET).
- Errors name the element (`document.elements[N]: Invalid kind`) but not the
  key. Bisect by dropping keys from element N.
- A ~3 MB spec POSTs fine.

## Charts

- `xAxis: {"columnId": id, "sort": {"by": id, "direction": "descending"}}`
- `yAxis: {"columnIds": [id, ...]}`; combo: `[{"columnId": id, "type": "line"}]`
  (`"bar"` / `"line"`, not `"column"`). `seriesLineAreaStyle` is rejected; line
  dash is global, not per series.
- `orientation: "horizontal"` for horizontal bars (diverging negatives work).
- `stacking`: `"none" | "stacked" | "normalized"`; default is stacked, so set
  `"none"` for grouped bars. A category-coloured single series with `"none"`
  leaves gaps; use `"stacked"`. `stacking` has been seen dropped on round trip.
- Colour: `{"by": "category", "column": id, "scheme": [...]}` or
  `{"by": "single", "value": hex}`. `{"by": "series"}` is invalid. Category
  colours are assigned in SORTED order of the categories present, so build the
  scheme from the values actually shown, alphabetically. A constant colour
  column shows up as "Series" in underlying data.
- Axis range: `"scale": {"type": "linear", "domain": {"min": .., "max": ..}}`
  (plain `min`/`max` are dropped); non-zero baseline:
  `yAxis.format.scale: {"type": "linear", "zero": false}`.
- `kpi-chart` value is `{"columnId": id}`, but `donut-chart` / `pie-chart`
  `value` and `color` use `{"id": id}`.
- `waterfall-chart` works (auto End bar; order via a `Min(order)` column). A big
  base bar hides small deltas; show deltas only.
- Line charts draw null months as 0; null the value, filter the rows, or use
  bars.
- `scatter-chart` works. Chart filter kind `"range"` is rejected.
- Vertical bars rotate even short labels; prefer horizontal.

## KPIs

- `kpi-chart` `layout` key is rejected on workbooks; `description` is rejected
  (no KPI tooltips via spec); text-align keys are dropped.
- Give a KPI about 5 grid rows or the delta badge clips.
- Format `",.0f"` can render `2.682` (period separator); use `",d"` or no format.
- The comparison column's name becomes the "vs …" label on the delta.

## Text

- Markdown headings `#`–`###` only (`####` rejected); no `<br>`; inline HTML only
  `<u> <sub> <sup> <span> <a>`. Bold is `**…**`, not `<b>`.
- `<span style>` allows only `color`, `background-color`, `font-size`,
  `font-family`. A blank line inside a `<span>` is rejected (unclosed span):
  one span per paragraph.
- A single `\n` doesn't break lines; use `\n\n`.
- Adjacent `**…**` spans can render a literal `****`; keep one bold span per
  line. `**LABEL  **` (trailing spaces inside) round-trips as escaped `\*\*`.
- `**` inside a `{{formula}}` string prints literally.
- A literal `{{` in a body (showing SQL, say) gives a masked 500; escape as
  `&#123;` / `&#125;`.
- `verticalAlign: "center"` (not `"middle"`).
- Markdown tables don't render.
- Text formulas can read hidden-page tables, and text is the only place
  cross-connection references work. A formula referencing an unset control
  shows "Select control value".

## Containers, panels, navigation

- Container `style.padding` must be `"none"` or omitted; `"none"` plus
  `borderColor` / `borderWidth` is rejected.
- Container background image: `{"source": {"kind": "url", "url": ...}, "style": ...}`;
  data URIs work for images.
- Formula-driven colours are rejected everywhere (control background, button
  fill, container background).
- `tabbed-container` `tabBar` key is rejected.
- Settings navigation: `{"pageHeader": ..., "pageSidebar": "enabled", "primary": "sidebar"}`;
  sidebar panel width `small|medium|large` (medium is the default and is omitted
  from GET, not dropped). Navigation `optionStyle.style` accepts only `"pill"`.
- Panels don't appear in page PNG exports. Embeds show the sidebar panel, so
  remove it for a portal that has its own navigation.

## Themes

`settings.theme.overrides`:
- `colors: {text, highlight (accent), surface, darkMode: "shown" | "hidden"}`
- `colorOverrides`: per-token hex (`backgroundCanvas`, `elementBackground`,
  `primary`, `success`, `warning`, `danger`, `surface`, `text`, `inputBorder`,
  `border`)
- `categoricalScheme: [hex, ...]`, `sequentialScheme`, `borderRadius:
  "square" | "round" | "pill"`, `hasCards`, `pageWidth`, `fonts`
- For a dark canvas set `darkMode: "shown"` plus canvas and element colours, or
  axis labels render dark on dark.
- Web fonts like Inter, Roboto, Roboto Condensed are accepted.

## Controls

- Single-select list default: `"value": "FY26"`. `"values": [...]` is silently
  dropped.
- Control `source` must be a table, not a chart. Controls only filter elements
  on the same page.
- Number and slider controls are rejected; `number-range` works.
- A segmented control shows at most 7 options in PNG renders.
- Control styling: only `style.backgroundColor` / `borderColor` survive;
  per-option colours, selected/accent colours and `includeNulls` are dropped.
  Emoji in option labels do render (useful for 🟢/🟡/🔴 status choices).
- `set-control-value` from a NUMBER column into a TEXT control fails at click
  time ("Invalid column type"), and compile checks don't catch it. Add a hidden
  `Text()` twin column.
- When a control is deleted (often in the UI), grep every formula for
  `[controlId]`; dangling references cascade errors across the workbook.

## Tables and pivots

- Grouped tables reject a top-level `sort`; sort goes inside
  `groupings[i].sort`. Top-level `sort: [{columnId, direction}]` works on
  ungrouped tables.
- Columns left out of `order` are appended, not hidden. Use `hidden: true`.
- A non-grouped extra column in a grouped table expands detail rows; put such
  filters in a child element.
- Pivots: `rowsBy` / `columnsBy` are `[{columnId}]`; no key turns off grand
  totals; numeric conditional formats can fail type checks, and `between` is
  rejected, so use condition `"formula"`. Pivot subtotals sum stock metrics;
  use `SumIf(x, [Month] = Max([Month]))`.
- Conditional format `IsNotNull` only shades filled cells. For an always-on tint
  use condition `"formula"` with an always-true formula.
- Table `on-select` trigger is plain `"on-select"`.
- `visibleAsSource` is rejected on workbooks.
