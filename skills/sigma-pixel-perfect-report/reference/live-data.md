# Live data in a report

A figure on a report page can come from three places. Ask the user which they
want; never imply a static build is live.

| Route | How | Survives a data refresh | Keeps the report's typography |
|---|---|---|---|
| Static | `warehouse.query()` at build time, typeset with `st()`/`rt()` | No (rebuild) | Yes |
| Native elements | bound `table`, `kpi-chart`, `bar-chart` | Yes | Partly (table face is Sigma's UI font) |
| Live text | `{{ formula }}` in a text body, reading a one-row source | Yes | Yes |

Clients usually ask for "every number live" once they see the first draft, so
prefer the two live routes from the start. Some clients reject live text because
it doesn't look "connected to data tables" in the editor; if they want to click
into each figure, use native elements.

## Sources

Every element must sit in the layout, so sources live on a hidden page (`pdata`)
in small tiles. A few dozen sources fit if each tile is small; full-size tiles
run off the hidden page and add a blank page.

| Kind | Shape | Formula prefix |
|---|---|---|
| Custom SQL | `{"kind":"sql","statement",...,"connectionId"}` | `[Custom SQL/COL]` in the source; `[<element name>/COL]` elsewhere |
| Warehouse table | `{"kind":"warehouse-table",...}` | table name, friendly column names: `[fct_orders/Order Date]` |
| Data model | `{"kind":"data-model","dataModelId","elementId"}` (`r.dm_source()`) | `[<DM element name>/<Column>]` |

- There is no workbook-element source: a report cannot read a workbook's input
  table directly. For write-back data, read the warehouse view or audit log
  behind the input table.
- A source id and a page id must differ (page `brk` + source `brk` →
  `Duplicate id`).
- Renaming an element breaks every `[Name/Col]` reference to it
  (`Dependency not found`). Keep referenced names stable.
- A `/` in a column name breaks references (`Unknown column` or a flat series).
  Rename the column.
- Custom SQL needs unique output column names; duplicates make exports fail with
  a bare 500.
- Wrap sums in `Coalesce(…, 0)`: nulls render as the word "null".
- `Sum([Src/Col])` aggregates the WHOLE source. A figure for one period needs a
  period-scoped source or a `SumIf`.
- An aggregate (`Max`, `MinIf`) in an UNGROUPED table column evaluates per row.
  For a global value, use a one-row grouped element (group by a constant "all")
  and `Lookup([CAL/As Of], "all", [CAL/K])`.
- `Round(x, If(...))` is an invalid query; the digits argument must be constant.
- Report `DateFormat` doesn't support `%-d` / `%-m`.
- Reserved words bite as SQL aliases: `NEW` and `RANGE` in BigQuery, `ON` in
  Snowflake.

## Live text: one-row "facts" sources

The most flexible live route: compute every figure, label and even headline
sentence in SQL as ONE row of pre-formatted strings, then reference them from
text bodies.

```
**{{Max([Facts/ARR_FMT])}}** ARR, up {{Max([Facts/ARR_GROWTH_FMT])}} on last year
```

The text keeps its font, size, weight and span colour. Build the sentences in SQL
(rank pivots with `MAX(IFF(RN=i, …))`) so a per-client report personalises
itself. Cache a sample row at build time (`build.py pull`) to predict wraps.

### Right-aligning a live number

`rt()` can't measure a value it doesn't know, so pad it in SQL to a fixed width
and place the box at `right − slot_width`:

- **Figure space U+2007** has exactly the width of a digit, and **punctuation
  space U+2008** the width of a comma or period. Left-pad to a fixed digit count
  (include decimal digits in the count).
- Alternatively pad with `CHR(160)`: in Helvetica a no-break space is 0.278em, a
  digit = 2 nbsp, `,`/`.` = 1, `-` = 1, `%` = 3. Then
  `x = right − units × 0.278 × size − suffix_width`.
- Parenthesised negatives: lead positives with a figure space where negatives
  have `(`.
- Month labels: one `CASE` per month name, padded to a common Helvetica width.

### Live bars in text

- `REPEAT('█', n)` in SQL: each block is 0.708em. Don't use the eighth-blocks;
  they fall back to another font. For a leftward bar, emit page-coloured blocks
  first.
- Or a span with `background-color` over `REPEAT(CHR(160), n)` and no
  `font-family`: 0.2em per character, a fixed ~20px tall at any size, bar top at
  element y + 5. The value can follow inline.
- Conditional colour: overlay two text bars with complementary `If()`s.

## Native elements

- Grouped tables: a non-grouped extra column (a filter flag, say) expands detail
  rows. Put such filters in a child element.
- Element filters: `{"kind":"list","columnId","values":[...]}` (including
  `[True]` on a boolean calc) and
  `{"kind":"top-n","rankingFunction":"rank","mode":"top-n","rowCount":N}` both
  work on list and grouped calc columns.
- `PercentOfTotal()` works in a grouping calc.
- Data-model elements can fan out: a header amount joined to lines repeats per
  line. Check a total against SQL; fall back to a custom-SQL source at the right
  grain.

## As-of week pattern

For a weekly report whose window should follow the data rather than the
calendar:

1. A grouped element `ASOF` (group by constant "all"): `Max` of the activity date
   up to `Now()`.
2. On each source: `Wk = Floor(DateDiff(day, [date], Lookup([ASOF/As Of], "all",
   [ASOF/K])) / 7)`.
3. Filter each source to `Wk` 0–11:
   `{"kind":"number-range","includeNulls":"never","min":0,"max":11}`.

A load-date column ("As of Date") is usually per row, not a constant; don't use
it as the anchor.

## Controls and per-recipient reports

A hidden report control (for example `Client`) filtering every source lets one
report serve many recipients. Leave it empty to mean "latest" or "all" by
computing a default in SQL (`IS_DEFAULT` via `row_number`). A control whose
value list and filter formula use the same table is a `Circular dependency`;
give the value list its own keys source. Text that references an unset control
renders "Select control value". To render one PDF per value, see
`reference/delivery.md`.

## Row-level security

Sources wrapped in a `{{#raw}}` user-attribute clause work in reports exactly as
in workbooks. A text formula that reads `CurrentUserAttributeText(...)` with no
table reference can render "null"; derive the label from the RLS'd source
instead.
