---
name: sigma-workbook-field-notes
description: >-
  Field-tested rules, house defaults and API gotchas for building or editing
  Sigma workbooks, data apps and plugins from code (POST/PUT
  /v2/workbooks/spec). Use alongside sigma-workbooks whenever you create or
  change a workbook spec: dashboards, branded demos, input tables and
  write-back apps, forms, modals and drawers, agents, plugins, embeds,
  data-model sources, Rollup/Lookup formulas, or when a spec verifies but
  renders wrong, a PUT is rejected with "Invalid kind", or a build is slow.
---

# Sigma workbook field notes

Lessons from about 30 workbook builds on staging and on AWS, GCP and Azure
production orgs (June–November 2026). Each item cost at least one failed round
trip. This skill does not replace `sigma-workbooks`; it covers what that skill
gets wrong, leaves out, or can't know about how the API behaves today.

**Trust order:** a render or GET-back beats this file, and this file beats older
references. The spec API changes often; when something here fails, probe it,
then fix this file.

## House defaults (apply without being asked)

1. **Read the live spec before changing an existing workbook.** People edit in
   the UI between turns. `GET /v2/workbooks/{id}/spec` with
   `Accept: application/json`, diff it against your local spec, and patch the
   live spec rather than re-PUTting generator output. Only hex case, re-wrapped
   `**`, auto-named passthrough columns, `order` and verbatim defaults are safe
   to call normalisation. Name every other difference back to the user as a
   possible edit (for example `nullValues: "hidden"` on a control), and port
   their edits into the generator.
2. **Every element gets all of its source's columns** so drill-down and "View
   underlying data" show every field:
   - charts, KPIs, sparklines, pivots: an unnamed pass-through column
     `{"id": ..., "formula": "[Source/Col]"}` per visible source column
     (skip aggregate columns when the source is grouped);
   - tables: every source field they don't show, added with `hidden: true`.
     Hidden base-level columns on a grouped table do not expand its rows.
   Plugins are exempt.
3. **The hidden Data page is one tabbed container**: a title text, then a
   `tabbed-container` spanning the page with one tab per **category** (what the
   tables feed, e.g. "Pipeline", "Forecast", "Funnel"), several tables stacked
   per tab in pipeline order (raw sources → write-back input tables → modelled
   children → grouped tables → worklists), each under a one-line note (what it
   is, grain, what reads it), and a last "Selection state" tab holding the
   hidden selection and drawer controls. Not one tab per table.
   **Every tabbed container (Data page, drawers, in-page tabs) stretches its
   tabs across the container**: `"tabBar": {"alignment": "justify"}`.
4. **Forms hide their own header**:
   `"header": {"title": {"visibility": "hidden"}, "description": {"visibility": "hidden"}}`.
   Put any heading in a text element above the form.
5. **Controls hide nulls**: `"nullValues": "hidden"` on every list control
   (workbooks and reports), so pickers have no "null" option. Text controls
   drop the key; that's fine.
6. **Calm, light design**: white or pale canvas, white cards with thin borders,
   the brand primary desaturated for large fills (exact brand hex only for the
   logo and small accents), horizontal bars instead of rotated labels. No
   full-width dark gradient bands or electric primaries.
7. **Ship a working version first**, then optimise. Don't run long probe loops
   before the user sees something.
8. **Say plainly what kind of change you made**: formula-only, new custom SQL,
   or data-model change. Users ask.
9. **Agents never name internals** (data-model names, schemas, table names) in
   replies; plain business terms only.

## Workflow

1. Keep a generator (`build.py`) that assembles the spec; keep IDs stable.
2. `POST /v2/workbooks/spec/verify` (cheap, but lenient).
3. PUT, then **compile-check every element without running it**:
   `GET /v2/workbooks/{id}/elements/{elementId}/query` returns the compiled SQL;
   errors show up as `'...'::text` literals or a top-level `error`. Zero
   warehouse cost.
4. **GET the spec back after any PUT that removes elements.** A PUT that
   returned `success: true` has been seen not to apply.
5. Render pages (PNG export) and look at them before saying it's done.

## The gotchas that break builds most often

1. **A table's `name` is its formula reference.** Renaming a referenced table
   breaks every `[Name/Col]` (`Dependency not found`). Keep names stable.
2. **A `/` in a column or element name breaks references** (`Unknown column`,
   `Dependency not found`, or a flat series). Use "per", not "/".
3. **Control order matters**: an input-table formula referencing a control fails
   at query time unless the control comes earlier in `document.elements`.
   Sort controls first.
4. **A control can't filter a table its own value list depends on**
   (`Circular dependency`). Source list controls from separate small tables.
5. **Nested `if-else` actions are rejected** (masked as `Invalid kind: button`),
   and `elseIf` is silently dropped. Chain single-branch if-else steps with
   mutually exclusive conditions.
6. **`insert-rows` values: use plain `Sum()`**. `SumIf(...)` evaluates to NULL
   and `Lookup(value, <number literal>, ...)` raises "expected type: text got
   number". Precompute helper columns and `Sum()` them.
7. **Agent and published-view writes need "Editable in published version"** set
   on the input table in the UI; no spec key does it.
8. **Cross-connection references fail** (Lookup, Rollup, KPI, table columns),
   except in text elements. Keep input tables on a write-enabled connection
   and don't join them across connections.
9. **One rejected key can cascade** into spurious `Dependency not found` errors
   elsewhere. Fix the first error, then re-verify.
10. **Very large specs time out**: about 450 controls or 250 text elements on a
    page made verify/PUT exceed the gateway timeout (and the save did not
    apply). Split pages or workbooks; native forms are cheap.

## Reference

- `reference/spec-shape.md`: document shape, layout tags, charts, KPIs, text,
  containers, navigation, themes, controls; keys that verify and are dropped.
- `reference/formulas-and-sources.md`: sources (SQL, warehouse table, data
  model), references, Rollup/Lookup, functions that don't exist, SQL dialect
  traps, performance, row-level security.
- `reference/data-apps.md`: input tables, actions, forms, modals and drawers,
  agents and agent tools, email, write-back read by a report.
- `reference/api-and-qa.md`: endpoints worth knowing, embedding, QA without
  warehouse reads, round-trip drift.

Plugins have their own skill: `sigma-plugins` (workflow, template, test
harness, catalogue).
