# Formulas and sources

## Sources

| Kind | Shape | References |
|---|---|---|
| Custom SQL | `{"kind": "sql", "statement", "connectionId"}` | `[Custom SQL/COL]` inside; `[<element name>/COL]` elsewhere |
| Warehouse table | `{"kind": "warehouse-table", ...}` | snake_case becomes Title Case: `id_user` → `[sf_user/Id User]` |
| Data model | `{"kind": "data-model", "dataModelId", "elementId"}` | `[<DM element name>/<Column>]` |
| Child | `{"kind": "table", "elementId"}` | parent's name |

- Fetch a data model's elements with `GET /v2/dataModels/{id}/spec`. A workbook
  table may share its DM element's name.
- Custom SQL columns must be listed explicitly; output names must be unique.
- After replacing a chart's columns, bare `[Col]` resolves only to the chart's
  own columns; qualify as `[Source/Col]`. A column named X with formula `[X]`
  references itself.
- KPI formulas should be qualified `[Source/Col]`.
- Every column `id` must be unique within an element (watch truncation
  collisions).
- Data-model elements can fan out (a header amount repeated per line). Check a
  total against SQL.

## Rollup and Lookup

- `Rollup(Sum([Child/x]), [Key], [Child/Key])` works across tables, including
  over input tables. Wrap in `Coalesce(…, 0)`.
- A constant key (`"All" = 1`) gives a grand total. For a one-row table, group
  on a constant key and read at that grouping; a `RowNumber() = 1` filter
  compiles to a window over the whole base table and is slow.
- A global "as of" value: one-row grouped element (`Max(date)`), then
  `Lookup([ASOF/As Of], "all", [ASOF/K])`. An aggregate in an UNGROUPED column
  evaluates per row.
- Latest row per key: `Rollup(Max(date))` plus a two-key Lookup on a composite
  `"id|date"` key.
- `Lookup` keys must be the same type; `Text()` numbers before concatenating.
- A filter on a child table also restricts a Rollup from that child into its
  parent. Filter the chart instead.
- A Lookup into another custom-SQL table inlines that SQL into the query, so
  big lookups can blow Snowflake's 1 MB statement limit. Bake the joined field
  into the SQL.
- A Lookup into a FILTERED table built on an input table was very slow (70 s);
  a Lookup straight into the input table on a composite-key column took ~7 s.
- On RLS-wrapped (`{{#raw}}`) SQL sources, Rollup from a child to other sources
  has returned null for every row; compute those scorecards in SQL.

## Functions: what exists

- Missing or broken: `Length()`, `Null()`, `Or()` (use the `or` operator),
  `NumberFormat(x, ",.0f")` ("Argument 2 invalid"), `Text(x, fmt)` (one
  argument only), `Date(y, m, d)` (wrong; use `MakeDate`).
- `DateFormat` doesn't support `%-d`, `%-m`, `%-I` (prints them literally); build
  with `Text(Day())` / `Mod(Hour(), 12)`. Column FORMAT strings do support them.
- `Text(float)` prints long decimals and `Text(Round(x))` prints `73.000`; use
  `Text(Int(x))`.
- `Rank()` is ascending by default: `Rank([x], "desc")`.
- In a descending sort a null ranks above every number; `Coalesce` the rank
  input.
- `Round(x, If(...))` is invalid; the digits must be constant.
- `&` treats null as `""`.
- Work fine: `PercentileCont`, `Median`, `AvgIf`, `SumIf`, `CountIf`, `MaxIf`,
  `Log`, `Exp`, `PercentOfTotal`, `GrandTotal(<aggregate>)`, `Switch`.
- `SumIf` with no matches shows "null" on a KPI; wrap in `Coalesce`.
- Compound returns: `Exp(Sum(Ln(1 + r))) - 1`.
- Controls are not visible inside input-table formulas (`Unknown column`); put
  control-driven math in a normal table.

## SQL dialect traps

- Snowflake: `VALUES` caps at 16,384 rows (use `UNION ALL` chunks); statements
  cap at 1 MB; `AVG(...) FILTER (WHERE ...)` is rejected; `GET(array, idx)`
  returns NULL for a FLOAT index (cast `::INT`); `ON` as an alias is reserved.
- BigQuery: `NEW` and `RANGE` are reserved aliases.
- Databricks: `element_at(array(...), NULL)` surfaces as "Received invalid UTF-8
  data from your warehouse"; guard with `CASE WHEN idx IS NULL`.
- Some service accounts can't read every schema; compile checks don't catch
  missing grants. Stick to schemas existing sources already read.
- Cortex `CallText` fails on some connections ("unknown model"), and Claude
  models fail there; `CORTEX.COMPLETE` in SQL and Sigma agents work. Have a
  rule-based `{{ }}` narrative ready as a fallback.

## Performance

- Generator SQL that uses `CURRENT_DATE` is never cached (~27 s per query). For
  demos, bake to static data with offsets from `CURRENT_DATE`, each derived table
  a child of the baked base.
- A `VALUES` list of ~170k literals cost ~12 s of COMPILE per query. Pack rows
  into ~50 long string literals (records `;`, fields `,`) and unpack with
  `LATERAL SPLIT_TO_TABLE` + `SPLIT_PART` casts (Databricks:
  `explode(split())`). Encode categoricals as int codes decoded with
  `GET(ARRAY_CONSTRUCT(...))`.
- Iterative ML in SQL times out the 120 s resolve on save. Train offline and
  score in SQL (logistic regression = one expression, random forest = a
  leaf-bounds table join, k-means = nearest centroid).
- Redshift: multiple `COUNT(DISTINCT)` is the expensive part; group once, then
  count.
- Control-driven "in scope" filters are pruned from SQL when controls are at
  defaults.
- Materialisation schedules can be listed via API but only created in the UI.

## Row-level security

- Wrap each SQL source:
  `SELECT * FROM (<sql>) WHERE '{{#raw system::CurrentUserAttributeText::attr}}' = 'ALL' OR COL = '{{#raw system::CurrentUserAttributeText::attr}}'`.
  Give the attribute a default of `ALL` so editors see everything. RLS in SQL
  keeps drill-down working (a filter-column approach broke it).
- `CurrentUserAttributeText(...)` in a text formula with no table reference can
  render "null"; derive labels from the RLS'd source instead.
- Agent answers respect RLS in embeds.
- User attribute API: `POST /v2/user-attributes {name, description,
  defaultValue: {type: "string", val}}`; assign with
  `POST /v2/user-attributes/{id}/users {assignments: [{userId, value}]}`.
