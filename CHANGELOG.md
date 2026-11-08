# Changelog

All notable changes to this project will be documented in this file.

## v0.2.0 - 2026-11-07

Adds `sigma-workbook-field-notes`.

### Added
- **`sigma-workbook-field-notes`** - Field-tested rules for building and editing Sigma workbooks from code, collected over about 30 builds on staging and AWS, GCP and Azure production orgs. Covers house defaults (read the live spec before editing, drill-down columns on every element, a tabbed Data page, hidden form headers), the gotchas that break builds most often, and references for spec shapes, formulas and sources, data apps, plugins, and API/QA.

## v0.1.0 - 2026-11-07

First release of the `sigma-pixel-perfect-report` skill.

### Added
- **`sigma-pixel-perfect-report`** - Build multi-page, print-quality reports with `POST /v2/reports/spec`: absolute layout, measured palettes, dot leaders, and ruled ledger totals. Output is a PDF.
- **`sigma-pixel-perfect-report`** - Design selection from a gallery of 456 annual reports (1937–2024), from the user's own PDF or brand spec, or chosen by the agent.
- **`sigma-pixel-perfect-report`** - `reference/measuring.md` and `reference/renderer-constraints.md` for measuring a source design and working within the report renderer's limits, updated with findings from client builds through November 2026: KPI anchors, integer font sizes, bound-table font size, column widths and row heights, chart colour order, page-width overflow, and the 7 MiB spec cap.
- **`sigma-pixel-perfect-report`** - `reference/live-data.md`: source kinds, one-row "facts" sources read with `{{ formula }}` text, right-aligning live numbers, live text bars, the as-of-week pattern, and per-recipient controls.
- **`sigma-pixel-perfect-report`** - `reference/delivery.md`: PDF export, one PDF per recipient with export `parameters`, 16:9 slide reports and PowerPoint packaging.
- **`sigma-pixel-perfect-report`** - Scripts for the Sigma API, warehouse queries, rasterizing, template derivation, and the `reportkit.py` spec builder, plus `motorola-1967` and `cummins-1989` templates and a scaffold. Org settings come from a per-org env file, and the token cache is per env file.
