---
name: sigma-pixel-perfect-report
description: Build a pixel-perfect, print-quality Sigma report (PDF) from code via POST /v2/reports/spec, styled after a chosen annual-report design. Use when the user asks for a "pixel perfect report", a print/PDF report, an annual-report-style document, a statement or shareholder letter, or wants to reproduce the look of an existing report or a design from the annual reports gallery. Also use when iterating on an existing report built this way.
---

# Pixel-perfect Sigma reports

Builds multi-page, print-quality reports with `POST /v2/reports/spec`: absolute
layout, measured palettes, real dot leaders, ruled ledger totals. Output is a PDF.

**Reports-as-code may be entitlement-gated.** It has worked on every org tried
since October 2026 (staging plus AWS, GCP and Azure production orgs), but an org
without it returns an empty 404 on `/v2/reports/spec` while
`/v2/workbooks/spec/verify` answers normally. Probe before promising anything,
and say so plainly if the target org lacks it.

---

## Step 1 — ALWAYS ask which design to use

Before building anything, ask the user how they want the design chosen. Use
`AskUserQuestion` with these three options (this question is the entry point to
the skill — do not skip it and do not guess):

1. **Pick from the gallery** — 456 real annual reports (1937–2024) from
   <https://annual-reports-gallery.vercel.app/>, including 64 Paul Rand covers
   and 54 by Chermayeff & Geismar. Offer a shortlist rather than 456 rows: run
   `gallery.py list --top 12` for the highest-rated, or
   `gallery.py suggest "<their brief>"`, then let them choose.
2. **Use their own** — they supply a PDF, scan, screenshot or brand spec. Measure
   it (Step 3) instead of using a gallery entry.
3. **You choose for them** — pick a fitting template yourself, say which one you
   picked and why in one sentence, then proceed without further back-and-forth.

If the user has *already* named a source (attached a PDF, named a company/year,
or said "like the Motorola one"), skip the question and use it — the question is
for when the design is genuinely unspecified.

**What a gallery template gives you:** each gallery entry is a COVER image, not a
full PDF. So it supplies a *design system* — palette, type feel, cover
composition — which you apply to a full report page set. Be explicit about this
with the user; don't imply you're reproducing 40 interior pages you can't see. (A
handful of entries carry a `source_url` full PDF; those can be reproduced deeply.)

---

## Step 2 — Set up

```bash
cd <build dir>                       # e.g. builds/<company>-<year>/
export SIGMA_ENV_FILE=~/.sigma-portals/<org>.env     # default: ~/.sigma-portals/staging.env
python3 <skill>/scripts/sigmaapi.py  # prints token + whoami; fails loudly if creds are wrong
```

The env file holds one org's settings (a process environment variable of the
same name wins):

```
SIGMA_BASE_URL=https://aws-api.sigmacomputing.com   # your cloud's API host
SIGMA_CLIENT_ID=...
SIGMA_CLIENT_SECRET=...
SIGMA_FOLDER_ID=...        # where reports and temp query workbooks are created
SIGMA_CONNECTION_ID=...    # warehouse connection for SQL sources
```

Use one env file per org. The token is cached for 55 minutes in
`/tmp/.tok_<env file stem>`, so switching `SIGMA_ENV_FILE` never reuses another
org's token. Pasted client secrets are often truncated; if auth fails, check the
secret's length against the original.

## Step 3 — Measure the source, never eyeball it

This is the step that produces fidelity. Sample the real colours and geometry:

```bash
python3 <skill>/scripts/gallery.py fetch <slug> --out ./src      # gallery pick
python3 <skill>/scripts/derive_template.py <name> --cover ./src/<slug>.jpg
python3 <skill>/scripts/derive_template.py <name> --pdf ./src/theirs.pdf --page 4
```

You get the paper/field colour (modal colour of the region), the ink colours
(mean of the darkest slice of each ink mask — NOT the single darkest pixel, which
reads far too dark), candidate accent inks, and the content bounding box as page
fractions, converted to a `LEFT`/`RIGHT` for an 816×1056 page.

Read `reference/measuring.md` for the fuller method: row pitch from ink bands,
column right-edges, display-heading cap heights, and cropping/alpha-keying
artwork (logos, signatures) out of a scan.

## Step 4 — Build with reportkit

Copy `templates/_scaffold/build.py` and fill it in, or copy the closest existing
template. `scripts/reportkit.py` provides the primitives:

| Call | Purpose |
|---|---|
| `Report(...)` | document + palette + grid constants |
| `page.field(hex)` | full-bleed colour field |
| `page.st / rt / ct` | one line of text, left / right / centre aligned **by computed width** |
| `page.prose(paras, x, y, w)` | wrapped body copy; returns the y after the block |
| `page.statement(rows, y, geom)` | ledger: dot leaders, right-aligned figures, ruled totals, `$` marks |
| `page.matrix(...)` | wide year-by-metric grid with column hairlines |
| `page.display_head(lines, subtitle)` | stacked display heading |
| `page.column_head(y, label, cols)` | section label + column headings over a rule |
| `page.table / kpi` | live elements bound to a source (re-query on export); `kpi(anchor=)` is `"center"` or `"right"` only |
| `page.text_table(cols, rows, x, y)` | a TYPESET table — cells are the page colour, in your face |
| `page.data_plate(...)` | a live table framed as typography, on near-white stock |
| `page.table_h(nrows)` | expected table height; size plates with it or rows get clipped |
| `report.sql_source / dm_source` | live sources (custom SQL, data-model element) on the hidden data page |
| `warehouse.query(sql, cols)` | run SQL at BUILD time so figures can be typeset |
| `page.rule / vrule / box / img` | hairlines, blocks, artwork |
| `report.overflow()` | **run before pushing** — see below |

`statement()` row kinds: `""`, `head`, `head-fig`, `sub`, `total`,
`total-plain`, `subtotal`, `grand`.

## Step 5 — Dump, verify, create, render, compare

```bash
python3 build.py dump      # element/page count + OVERFLOW CHECK, no API call
python3 build.py verify    # server-side validation
python3 build.py create    # writes report_id.txt
python3 build.py update    # re-push after edits
python3 <skill>/scripts/rasterize.py $(cat report_id.txt) shots/v1 1.0
```

Then **look at the render** next to the source and iterate. Two or three passes is
normal; the first pass always has collisions. Always view the pages — do not
declare a report finished off a successful `create`.

`dump`'s overflow check is not optional: any element whose box extends past
`pageHeight` silently spills onto an extra blank page, so a 9-page report quietly
becomes 11, and any element wider than the page shrinks the whole page in the
PDF. Fix overflow before rendering.

`verify` misses things that `create` rejects (non-integer font sizes, bad SQL),
so treat a clean `create` plus a render as the real test.

## Step 6 — Make it live, and deliver it

Read `reference/live-data.md` before binding figures: source kinds, one-row
"facts" sources read with `{{ formula }}` text, right-aligning live numbers, the
as-of-week pattern, and per-recipient controls. Read `reference/delivery.md` for
PDF export, one PDF per recipient (the schedules API drops burst settings; export
with `parameters` instead), 16:9 slide reports and PowerPoint packaging.

---

## Renderer constraints that will bite you

Full list with evidence in `reference/renderer-constraints.md`. The ones that
break a build immediately:

1. **`align` on an element is silently ignored**, and `<span style>` can't carry
   `text-align`. Right-align by computing Helvetica advance widths — `rt()` does
   this, and it's exact because the renderer uses true Helvetica metrics.
2. **`<span style>` permits only** `color`, `background-color`, `font-size`,
   `font-family`. Weight and slant come from markdown `**`/`*`. `font-family`
   must be a single name; only Helvetica, Arial, Verdana, Georgia, Times New
   Roman and Courier New actually resolve.
3. **Line pitch is a fixed 22.4px at any font size.** Anything that must sit on a
   specific grid needs one element per row. Prose block heights must be predicted
   (`prose()` does it) because the renderer clips instead of growing.
4. **An empty or whitespace-only text body renders an error card.** Use
   `field()`/`box()` for colour rectangles.
5. **A long dot-leader run wraps as one word and vanishes.** Compute the count
   (`page.leader()`).
6. **Text `font-size` must be an integer px (max 96).** `7.5px` passes verify
   and fails create.
7. **KPI `layout.anchor` is `center` or `right` only**; `start` errors as
   `Invalid kind: kpi-chart` and `horizontalAlign` is dropped.
8. **Bound tables clip silently.** Size them from the row-height table in the
   reference; an empty one shows a big "No data" box.
9. **The spec is capped at 7 MiB decompressed.** Embed photos as JPEG, not PNG.

Also: `<Element x/y>` must be non-negative (no true bleed), image `fit` is
`contain|cover|stretch|none|scale-down` (**not** `fill`), and document order is
z-order.

---

## Templates

`templates/gallery.json` — the 456-entry registry (company, year, designer, elo,
public cover URL). Refresh with `scripts/build_gallery_registry.py`.

`templates/motorola-1967/` — **the worked reference.** Nine pages, fully measured,
9 of 9 pages verified against the original scans. Read its `build.py` when
building anything new; read its `content.py` to see how measured constants and
copy are kept separate from layout.

`templates/_scaffold/` — minimal starting point.

Keep content (copy, figures, palette) in `content.py` and layout in `build.py`, so
re-skinning is a palette edit rather than a rewrite.

## Honest limits — state these rather than faking them

- **No justified text** (no `text-align`), so columns are ragged-right where an
  original is justified.
- **Note-sized type looks loose**, because line pitch is fixed regardless of size.
- **Photographic/illustrated pages can't be generated** — reproduce the
  typographic pages and say which ones you left out.
- Figures can be static, resolved at build time via `warehouse.query()`, or bound
  live. Ask which the user wants if it matters, and don't imply a static build is
  live.
- **A live table's face is always Sigma's UI font.** Its size
  (`tableStyle.textStyles.header/cell.fontSize`) and column widths
  (`style.width`) can be set, but in the PDF its fill is always white. If it must
  sit on tinted stock in the report's own face, use `text_table()` with
  build-time or `{{ }}` live figures. KPI elements honour `style.backgroundColor`
  in both renders, so headline figures can stay live and still match.
- **No native burst through the API.** Export once per recipient with
  `parameters` (see `reference/delivery.md`).
- **PowerPoint output is images.** A 16:9 report packaged as `.pptx` has one
  picture per slide, not editable text.
