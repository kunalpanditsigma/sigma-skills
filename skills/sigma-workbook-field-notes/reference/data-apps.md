# Data apps: input tables, actions, forms, agents

## Input tables

- Need a write-enabled connection. If the data connection is read-only, put
  input tables on a write-enabled one, and don't Lookup or Rollup across the
  two connections.
- Column type `"date"` is rejected; use `"datetime"`. Unknown column keys are
  accepted silently. A number column's `format` is dropped on round trip.
- On some connections (seen on Redshift) input tables created by PUT need
  UPPERCASE column ids; lowercase-hyphen ids got no storage columns
  ("Column ... does not exist"). Re-create under a new element id. On
  Databricks, use underscore ids: they become the physical column names.
- **"Editable in published version" is a UI-only setting** and is required for
  agent writes and published-view entry ("Manual commit is not enabled for this
  input table"). `inputMode: "edit"` doesn't set it.
- Linked input tables over a SQL table work (keys + override + `Coalesce`);
  their row order isn't preserved. A list control filter on an input table
  works.
- A union source is rejected; merge live and imported rows with a Rollup.
- Rows survive PUTs. Moving an input table to another connection is rejected;
  it needs a new element id.
- Workbook copy (`POST /v2/workbooks/{id}/copy`): the copy's input tables share
  storage at first and fork to new tables on its first PUT, history carried.
- Don't query input-table storage (`SIGDS_<uuid>`) directly; it has id-named
  columns plus a write-ahead log.

## Reading write-back from elsewhere

Reports can't source a workbook element. To read input-table rows in a report
or another tool, use the input table's warehouse view or audit log
(`input_table_audit_log_<uuid>`): `DATA_CHANGE` rows are full snapshots; the
latest `ROW_VERSION` per ID with null `TOMBSTONE_VERSION` is the current row.

## Actions

- `update-rows`: `{"tableElementId", "whichRows": {"type": "formula",
  "formula": "[Row ID] = [SelRow]"}, "values": {...}}`; works from buttons and
  agent tools.
- `insert-rows` uses `tableElementId`. Values: plain `Sum()` and
  `Lookup(..., const, ...)` evaluate; `SumIf` gives NULL; a number literal
  Lookup key raises a type error. Use hidden helper columns and `Sum()`.
- If-else: no nesting, no `elseIf`. Chain single-branch steps.
- `clear-control` scope: `{"type": "control", "controlId"}` or
  `{"type": "workbook"}`; `{"type": "page", "page"}` loses the page key.
- `open-url` needs `"openTarget": "_blank"` and a plain string URL (formula URLs
  rejected). Agent tools can only navigate within the same workbook.
- Export effect: formats `excel` / `png` (page or element) and
  `{"type": "external-report", "documentId"}` for a report PDF.
- Email effect: `{"kind": "effect", "effect": "export", "channel": "email",
  "recipients": {"type": "dynamic", "value": {"type": "control", "control": "EscTo"}}`
  (or `{"type": "static", "values": [...]}`), `"subject"` / `"messageBody"`
  strings with `{{formula}}`, `"includeLink": true, "linkTo": {"type": "workbook"}}`.
  No SharePoint, OneDrive or webhook channels.
- `successToast` works. Control `actions` with trigger `on-change` work.
- Table `on-select` → `set-control-value` / `set-form-values` /
  `open-overlay` is the drawer pattern: selection controls on the Data page's
  "Selection state" tab, drawer reads them.
- Write-back buttons can't be click-tested headlessly. Say so, and ask the
  user to click through once.

## Forms

- Native forms are single-column: `layout.columns` and per-field `width` verify
  and are dropped. No heading or section field types. Always hide the header
  (see SKILL.md).
- Dropdown option `label` is dropped (values only). A dropdown can source a
  table: `"source": {"kind": "source", "source": {"kind": "table",
  "elementId"}, "columnId"}`.
- Form-field values are usable only in actions hosted by the same form; no
  cross-form submit button.
- On-submit supports `set-control-value` from a form field, `insert-rows`,
  export/email, `reset-form`, `close-overlay`.
- `fieldLabels.width` 0.25 works; 0.3 is rejected.
- Forms are cheap: three 150-field forms verified in 2 s, where ~450 separate
  controls timed out.

## Modals and drawers

- Overlay pages hold modals and drawers; a tabbed container works inside one.
- A guard modal ("pick a row first") is an if-else step before the real action.
- Agent `set-control-value` can't reach a control inside a PANEL ("control could
  not be found"); keep agent-targeted controls on a page.

## Agents

- `greeting` must be an object: `{"mode": "static", "message": ...}`.
- Tools: `{"toolId", "kind": "action", "steps": [{"kind": "effect", "effect":
  ..., "values": {"col": {"type": "agent-input", "inputName"}}}]}`. A tool can
  `set-control-value` then `update-rows` on that control.
- Hidden table columns are invisible to agents; give the agent an unhidden
  source.
- Write tools need the input table "Editable in published version" (UI).
- Headless run: `POST /v2/workbooks/{id}/agents/{agentId}` with
  `{"messages": [{"role", "content"}]}`.
- Instructions: require a readback and explicit confirmation before any write;
  never name internal tables or models.
- `automatedActions` triggers: only `"schedule"`.
