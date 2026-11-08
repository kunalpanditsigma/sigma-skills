# API endpoints and QA

## Endpoints worth knowing

| Need | Call |
|---|---|
| Create | `POST /v2/workbooks/spec` (top-level `folderId` required) |
| Update | `PUT /v2/workbooks/{id}/spec` |
| Read back | `GET /v2/workbooks/{id}/spec` with `Accept: application/json` |
| Compile one element, no warehouse read | `GET /v2/workbooks/{id}/elements/{eid}/query` |
| Export element CSV / page PNG | `POST /v2/workbooks/{id}/export {elementId or pageId, format}` → poll `GET /v2/query/{queryId}/download` (204 or empty until ready) |
| Test control-driven tables | add `"parameters": {"<controlId>": value}` to the export body |
| Copy | `POST /v2/workbooks/{id}/copy {name, destinationFolderId}` |
| Delete | `DELETE /v2/files/{id}` (`/v2/workbooks/{id}` 404s) |
| Who am I | `GET /v2/whoami` |
| Catalog without reading data | `GET /v2/connections/paths?connectionId=`; `POST /v2/connection/{id}/lookup {path}` → inodeId; `GET /v2/connections/tables/{inodeId}/columns?pageSize=1000` |
| Paging | columns endpoints page with `pageToken`, not `page` |
| Data model spec | `GET` / `PUT /v2/dataModels/{id}/spec`; PUT body `{name, folderId, schemaVersion, pages}`; untouched elements stay byte-identical |
| API connectors | `POST /v2/api-connectors`; path params are `:vin`, not `{vin}`; PATCH to edit |

There is no CSV-upload API; uploads happen in the UI.

## QA without spending warehouse time

1. Compile-check every element with the element query endpoint. Errors appear
   as `'...'::text` literals or an `error` field.
2. Export a handful of key elements to CSV and compare totals with SQL.
3. Render each page to PNG and look at it. Only the DEFAULT tab of a tabbed
   container renders; to preview other tabs, post a throwaway copy with each
   tab as its own page.
4. Write-back, plugins with data, and agent writes need a real browser; say so.

A user who wants no warehouse reads during exploration: use the catalog
endpoints above and compile checks only, and ask before any export.

## Round-trip drift

- After UI use, a GET differs from what you PUT by normalisation: lower-case
  hex, `**` moved inside spans, chart columns reordered with colour first,
  default stacking dropped, auto-named passthrough columns. Everything else is a
  possible user edit.
- An open editor tab (workbook or data model) can save over an API update.
  Ask the user to refresh or close it before you PUT, and GET-check afterwards.
- If a data model element is recreated, republish the workbook to re-link it.

## Embedding

- Edit / Explore tools only appear for a WORKBOOK-level embed URL with
  `:menu_position=top`. Open on a page with `:nodeId=<pageId>`; page-level
  `/page/<id>` URLs hide the tools.
- Gate editing per persona with the JWT `account_type` (a view-only built-in
  type for clients, a creator type for internal users) rather than changing
  grants.
- A signed embed URL loaded top-level in headless Chrome renders blank; load it
  through the portal page instead, with a real-time wait (virtual time budgets
  hang).
- Pinning a tenant through a control (`&Control=<value>` on the signed URL) is
  cosmetic; the control stays editable. Use user-attribute RLS for real
  isolation.
- Team grants and sharing changes may be blocked by an approval prompt; ask the
  user to approve or run them.

## Credentials

- Keep one env file per org and point your helper at it.
- Pasted client secrets are often truncated (seen several times at 62 of 128
  characters). If auth fails, compare the secret's length with the original.
