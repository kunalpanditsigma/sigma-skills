"""reportkit — build pixel-faithful Sigma reports from code.

Wraps `POST /v2/reports/spec` in primitives that survive the renderer's real
constraints (see reference/renderer-constraints.md). The important ones, because
they shape this whole API:

  * an element-level `align` is SILENTLY IGNORED, and <span style> can't carry
    text-align — so `rt()` / `ct()` position text by computing its Helvetica
    advance width and setting x accordingly. This is exact, not approximate: the
    renderer uses true Helvetica metrics.
  * line pitch inside an element is a FIXED 22.4px at any font size, so anything
    that must sit on a specific grid gets one element per row, and prose heights
    are predicted by word-wrapping against the same metrics.
  * a text element with an empty/whitespace body renders an error card, so colour
    fields are stretched 2x2 PNGs generated in-memory.
  * `<Element x/y>` must be non-negative, and any box extending past pageHeight
    silently spills onto an EXTRA page — call `report.overflow()` before pushing.

Typical use:

    r = Report("Acme — Annual Report 1968", canvas="#F0F0E8")
    p = r.page("cover", "Cover")
    p.field("#A88430")
    p.rt("ACME", 240, 527, size=15, color="#FFFFFF", bold=True)
    print(r.overflow())          # [] before you push
    r.create()
"""
import base64
import json
import math
import os
import pathlib
import struct
import sys
import zlib

import helvetica as HV

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import sigmaapi as S

LINE_PITCH = 22.4      # the renderer's fixed line pitch, at ANY font size
PARA_GAP = 8.0         # extra space a markdown paragraph break adds
TEXT_DY = 9            # ink top sits ~9px below an element's y


# ------------------------------------------------------------------ helpers

def solid_datauri(hex_color, n=2):
    """An n x n solid PNG as a datauri — the only reliable colour rectangle."""
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    raw = bytearray()
    for _ in range(n):
        raw.append(0)
        raw += bytes([r, g, b]) * n
    comp = zlib.compress(bytes(raw), 9)

    def chunk(typ, body):
        return (struct.pack(">I", len(body)) + typ + body
                + struct.pack(">I", zlib.crc32(typ + body) & 0xFFFFFFFF))

    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", n, n, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", comp) + chunk(b"IEND", b""))
    return "data:image/png;base64," + base64.b64encode(png).decode()


def file_datauri(path):
    path = pathlib.Path(path)
    if path.suffix.lower() in (".txt",):          # a pre-baked datauri
        return path.read_text().strip()
    mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".svg": "image/svg+xml", ".gif": "image/gif"}[path.suffix.lower()]
    return "data:%s;base64,%s" % (mime, base64.b64encode(path.read_bytes()).decode())


def money(v, parens=True):
    """1234567 -> '1,234,567'; negatives in parentheses, as ledgers set them.

    A str passes through untouched, so a row can carry an already-formatted
    value (a percentage, a ratio, "n/a") through the same ledger machinery.
    """
    if isinstance(v, str):
        return v
    if isinstance(v, float):
        return "%.2f" % v
    if v < 0 and parens:
        return "(%s)" % "{:,}".format(-v)
    return "{:,}".format(v)


# -------------------------------------------------------------------- Page

class Page:
    """One report page. Coordinates are absolute page px, origin top-left."""

    def __init__(self, report, pid, name):
        self.r = report
        self.id = pid
        self.name = name

    # ---- raw element plumbing
    def _add(self, el, x, y, w, h, bleed=False):
        return self.r._add(self.id, el, x, y, w, h, bleed=bleed)

    def img(self, src, x, y, w, h, fit="contain", bleed=False):
        """`src` is a datauri, a file path, or an http URL.

        `fit` must be contain / cover / stretch / none / scale-down — "fill" is
        rejected by the validator, as is backgroundColor "transparent".

        `bleed=True` for a full-page background image (x=0, y=0, w=page_w,
        h=page_h) — same accounting `field()` gets, so `overflow()`'s
        page_h-4 tolerance doesn't false-positive on an intentional edge-to-edge
        image.
        """
        if not str(src).startswith(("data:", "http")):
            src = file_datauri(src)
        return self._add({"id": self.r._uid("i"), "kind": "image",
                          "source": {"kind": "url", "url": src},
                          "style": {"fit": fit, "padding": "none"}},
                         x, y, w, h, bleed=bleed)

    def field(self, hex_color):
        """Full-bleed colour field for this page."""
        return self._add({"id": self.r._uid("i"), "kind": "image",
                          "source": {"kind": "url", "url": solid_datauri(hex_color)},
                          "style": {"fit": "stretch", "padding": "none"}},
                         0, 0, self.r.page_w, self.r.page_h, bleed=True)

    def box(self, hex_color, x, y, w, h):
        """A solid rectangle (banner, tint block, vertical rule)."""
        return self._add({"id": self.r._uid("i"), "kind": "image",
                          "source": {"kind": "url", "url": solid_datauri(hex_color)},
                          "style": {"fit": "stretch", "padding": "none"}},
                         x, y, w, h)

    def rule(self, x, y, w, color=None, thickness=1):
        return self._add({"id": self.r._uid("r"), "kind": "divider",
                          "style": {"color": color or self.r.ink}},
                         x, y, w, thickness)

    def vrule(self, x, y, h, color=None, thickness=1):
        """A divider is horizontal only, so a vertical hairline is a thin box."""
        return self.box(color or self.r.rule_color, x, y, thickness, h)

    def raw_text(self, body, x, y, w, h):
        return self._add({"id": self.r._uid("t"), "kind": "text", "body": body},
                         x, y, w, h)

    # ---- styled text
    def span(self, body, size=None, color=None, family=None):
        return self.r.span(body, size, color, family)

    def st(self, s, x, y, size=None, color=None, bold=False, italic=False,
           h=None, w=None, family=None):
        """A single line whose glyphs start exactly at `x`."""
        size = size or self.r.body_size
        body = s
        if s.strip():
            body = "**%s**" % s if bold else ("*%s*" % s if italic else s)
        ww = w if w is not None else HV.width(s, size, bold) + 10
        return self.raw_text(self.span(body, size, color, family), x, y, ww,
                             h or (LINE_PITCH + 4))

    def rt(self, s, right, y, size=None, color=None, bold=False, italic=False,
           h=None, family=None):
        """Right-align: the last glyph lands on `right`."""
        size = size or self.r.body_size
        w = HV.width(s, size, bold)
        return self.st(s, right - w, y, size, color, bold, italic, h=h, w=w + 12,
                       family=family)

    def ct(self, s, centre, y, size=None, color=None, bold=False, italic=False,
           h=None, family=None):
        size = size or self.r.body_size
        w = HV.width(s, size, bold)
        return self.st(s, centre - w / 2.0, y, size, color, bold, italic, h=h,
                       w=w + 12, family=family)

    # ---- prose
    def prose_h(self, paras, size, col_w):
        if isinstance(paras, str):
            paras = [paras]
        n = sum(HV.wrap_lines(p, size, col_w) for p in paras)
        return n * LINE_PITCH + max(0, len(paras) - 1) * PARA_GAP + 8

    def prose(self, paras, x, y, w, size=None, color=None, family=None):
        """Lay out paragraphs and return the y just past the block.

        The height is PREDICTED from Helvetica word-wrapping — the renderer clips
        rather than growing an element, and an over-tall box pushes a new page.
        """
        size = size or self.r.note_size
        if isinstance(paras, str):
            paras = [paras]
        h = self.prose_h(paras, size, w)
        self.raw_text(self.span("\n\n".join(paras), size, color, family), x, y, w, h)
        return y + h

    # ---- composites
    def display_head(self, lines, subtitle=None, x=None, y=None, size=None,
                     pitch=None, color=None, sub_size=None):
        """A stacked display heading, optionally trailed by an italic subtitle."""
        x = self.r.left if x is None else x
        y = self.r.head_y if y is None else y
        size = size or self.r.head_size
        pitch = pitch or self.r.head_pitch
        color = color or self.r.highlight
        for i, line in enumerate(lines):
            self.st(line, x, y, size, color, bold=True, h=pitch + 10)
            if subtitle and i == len(lines) - 1:
                sx = x + HV.width(line, size, True) + 16
                self.st(subtitle, sx, y + 9, sub_size or self.r.body_size,
                        self.r.ink, italic=True, h=22)
            y += pitch
        return y

    def column_head(self, y, label, columns, color=None, rule=True):
        """A section label plus right-hand column headings, over a hairline.

        `columns` is [(text, right_edge), ...]; each heading is centred over its
        column a little left of the figures' right edge, as ledgers set them.
        """
        color = color or self.r.highlight
        if label:
            self.st(label, self.r.left, y, self.r.body_size, color, bold=True, h=22)
        for txt, right in columns:
            self.ct(txt, right - self.r.numcol_w / 2.0 - 6, y,
                    self.r.body_size, color, h=22)
        if rule:
            self.rule(self.r.left, y + 22, self.r.right - self.r.left)
        return y + 26

    def leader(self, label, x, dot_end, size, bold=False, gap=5.0):
        """label + the dot run that stops `gap` px short of `dot_end`.

        An over-long run wraps as a single word and vanishes entirely, so the
        count is computed rather than padded generously.
        """
        used = x + HV.width(label + " ", size, bold)
        n = int(math.floor((dot_end - gap - used) / HV.dot_width(size)))
        return label + " " + "." * n if n >= 2 else label

    def statement(self, block, y0, geom=None, size=None, pitch=None,
                  head_gap=6.0, leaders=True, currency=True):
        """A ledger: labels with dot leaders, right-aligned figures, ruled totals.

        `block` rows are `(indent, label, *values, kind)` where kind is one of
            ""            plain line
            "head"        bold section caps, no figures
            "head-fig"    bold caps WITH figures
            "sub"         sub-heading, no figures
            "total"       italic caps total, hairline above
            "total-plain" roman total, hairline above
            "subtotal"    unlabelled carry-forward, hairline above
            "grand"       bold grand total, hairline above + double rule below

        Returns the y after the last row.
        """
        geom = geom or self.r.geom()
        size = size or self.r.body_size
        pitch = pitch or self.r.row_pitch
        rights = geom["rights"]
        ncw = geom["numcol_w"]

        # A column's currency marks all align just left of that column's WIDEST
        # figure. Hanging them off a fixed column edge instead drops the second
        # column's mark on top of the first column's figure.
        stops = []
        for ci in range(len(rights)):
            widths = [HV.width(money(row[2 + ci]), size)
                      for row in block if row[2 + ci] is not None]
            stops.append(rights[ci] - (max(widths) if widths else 0) - 14)

        y = y0
        prev, seen = None, False
        for row in block:
            indent, label = row[0], row[1]
            vals, kind = list(row[2:-1]), row[-1]
            if kind == "head" and prev is not None:
                y += head_gap
            lx = geom["label_x"] + indent * geom["indent"]
            has = any(v is not None for v in vals)
            bold = kind in ("head", "head-fig", "grand")
            ital = kind == "total"

            if kind in ("total", "total-plain", "subtotal", "grand"):
                for right in rights:
                    self.rule(right - ncw, y - 3, ncw)

            if label:
                body = (self.leader(label, lx, geom["dot_end"], size, bold)
                        if (has and leaders) else label)
                self.st(body, lx, y, size, self.r.ink, bold, ital,
                        h=pitch + 2, w=geom["dot_end"] - lx + 14)

            if has:
                mark = currency and ((not seen) or kind == "grand")
                seen = True
                for ci, v in enumerate(vals):
                    if v is None:
                        continue
                    self.rt(money(v), rights[ci], y, size, self.r.ink, bold, ital,
                            h=pitch + 2)
                    if mark:
                        self.st("$", stops[ci], y, size, self.r.ink, bold, ital,
                                h=pitch + 2)

            if kind == "grand":
                for right in rights:
                    self.rule(right - ncw, y + pitch - 3, ncw)
                    self.rule(right - ncw, y + pitch, ncw)
            y += pitch
            prev = kind
        return y

    def matrix(self, row_labels, col_labels, values, x, y, label_w, right,
               size=8, row_h=46, fmt=None, hairlines=True, currency_col0=True,
               currency_rows=None):
        """A wide year-by-metric grid, with hairlines between columns.

        `values[r][c]` may be numbers or pre-formatted strings.

        `currency_rows` selects which rows carry the leading currency mark, by
        index. Without it every row gets one, which is wrong the moment a grid
        mixes money with percentages or unit counts.
        """
        ncols = len(col_labels)
        grid_x = x + label_w
        col_w = (right - grid_x) / float(ncols)
        for i, cl in enumerate(col_labels):
            self.ct(str(cl), grid_x + (i + 0.5) * col_w, y, size, self.r.ink,
                    bold=True, h=18)
        y += 20
        self.rule(x, y, right - x)
        top = y + 6
        for r, label in enumerate(row_labels):
            ry = top + r * row_h
            nlines = HV.wrap_lines(label, size, label_w - 8, bold=True)
            self.raw_text(self.span("**%s**" % label, size, self.r.ink), x, ry,
                          label_w - 6, nlines * LINE_PITCH + 4)
            # figures sit against the optical centre of a label that wraps
            fy = ry + (nlines - 1) * LINE_PITCH / 2.0
            for c in range(ncols):
                v = values[r][c]
                s = v if isinstance(v, str) else (fmt(v) if fmt else money(v))
                self.rt(s, grid_x + (c + 1) * col_w - 8, fy, size, self.r.ink, h=18)
                mark = currency_col0 and (currency_rows is None
                                          or r in set(currency_rows))
                if c == 0 and mark:
                    self.st("$", grid_x + 2, fy, size, self.r.ink, h=18)
        bottom = top + len(row_labels) * row_h
        if hairlines:
            for i in range(1, ncols):
                self.vrule(grid_x + i * col_w - 4, top - 6, bottom - top + 2)
        return bottom

    # ---- live warehouse data
    def table(self, source, columns, x, y, w, h, order=None, groupings=None,
              preset="presentation", spacing="small", bg=None, border=None,
              summary="hidden", sort=None, radius=None):
        """A table bound to a source element — figures resolve at RENDER time.

        `columns` is [(id, formula, display_name, format_or_None), ...].

        Worth knowing before you reach for this: a bound table gives you live
        data but not ledger typography. You cannot hide its header row
        (`tableComponents.columnHeaders` is rejected), and there is no per-row
        bold/italic, so dot leaders and italic-caps totals are out. Use it for
        data grids; use `statement()` for typeset ledgers.

        `bg`, when given, also pins `tableStyle.textStyles.header/cell`
        `backgroundColor` to that colour. This is NOT cosmetic-only: a bound
        table's actual header/cell fill in the interactive report editor
        defaults unpredictably per element (confirmed by fetching a live spec
        after opening two otherwise-identically-styled tables in the editor —
        one came back `#fcfcfc`, the other `#f5f3ef`, neither set by the
        authoring code). The editor appears to resolve "inherited from
        container" into an explicit value on open/auto-save, inconsistently.
        Leaving `textStyles` unset means two tables on the same page can drift
        to different fills depending on editor history. The PDF export path
        ignores this key either way (always renders white there), so this
        only affects the interactive viewer — but pin it, since "unset" is not
        the same as "consistent."
        """
        cols = []
        for c in columns:
            cid, formula, cname = c[0], c[1], c[2]
            fmt = c[3] if len(c) > 3 else None
            col = {"id": cid, "formula": formula, "name": cname}
            if fmt:
                col["format"] = fmt
            cols.append(col)
        table_style = {"preset": preset, "cellSpacing": spacing}
        if bg:
            table_style["textStyles"] = {"header": {"backgroundColor": bg},
                                         "cell": {"backgroundColor": bg}}
        el = {"id": self.r._uid("tb"), "kind": "table",
              "source": {"elementId": source, "kind": "table"},
              "columns": cols,
              "order": order or [c["id"] for c in cols],
              "name": {"visibility": "hidden"},
              "tableComponents": {"summaryBar": summary},
              "tableStyle": table_style}
        if groupings:
            el["groupings"] = groupings
        if sort:
            # (columnId, "ascending"|"descending") pairs
            el["sort"] = [{"columnId": c, "direction": d} for c, d in sort]
        style = {}
        if bg:
            style["backgroundColor"] = bg
        if radius:
            # "square" kills the card-like rounded corners; "none" is rejected
            style["borderRadius"] = radius
        if border:
            style["borderColor"] = border
            style["borderWidth"] = 1
        else:
            # padding "none" and border fields are mutually exclusive
            style["padding"] = "none"
        el["style"] = style
        return self._add(el, x, y, w, h)

    def text_table(self, columns, rows, x, y, size=None, pitch=None,
                   header_size=None, header_color=None, rule_color=None,
                   header_rule=True, top_rule=False, close_rule=True, zebra=None,
                   header_gap=6.0):
        """A typeset table: text elements on the page, in the report's own face.

        Use this when the table must match the page AND when it's going into a
        PDF export. A BOUND table's text always uses Sigma's UI font, no
        exceptions. Its cell/header fill CAN be pinned via
        `table(..., bg=...)` (see that method's docstring) -- but only the
        interactive report editor honours it; the PDF export path renders a
        bound table's fill as white regardless of `tableStyle.textStyles`. So
        for a print/PDF report, a bound table still can't be made to match a
        tinted page in the artifact that matters -- use `text_table()` there.
        Here the "cell background" is simply the page, because nothing is drawn
        behind the text.

        The trade is that figures are fixed when the spec is built (feed it
        `warehouse.query()`) rather than re-queried on export.

        `columns` is [(label, width, align)], align "left", "right" or
        "center". `rows` is a list of lists of already-formatted strings.
        `top_rule` (opt-in, default False so existing callers are unaffected)
        adds a hairline directly ABOVE the header row, to match a closed,
        ruled-top-and-bottom ledger look.
        Returns the y just past the table.
        """
        size = size or self.r.body_size
        pitch = pitch or self.r.row_pitch
        hsize = header_size or size
        rc = rule_color or self.r.rule_color
        hcol = header_color or self.r.ink

        edges, cx = [], x
        for label, w, align in columns:
            edges.append((cx, w, align))
            cx += w
        total = cx - x

        if top_rule:
            self.rule(x, y - 8, total, rc)

        for (label, w, align), (ex, _, _) in zip(columns, edges):
            if align == "right":
                self.rt(label, ex + w, y, hsize, hcol, bold=True, h=pitch + 2)
            elif align == "center":
                self.ct(label, ex + w / 2.0, y, hsize, hcol, bold=True, h=pitch + 2)
            else:
                self.st(label, ex, y, hsize, hcol, bold=True, h=pitch + 2)
        yy = y + pitch + header_gap
        if header_rule:
            self.rule(x, yy - 4, total, rc)

        for i, row in enumerate(rows):
            if zebra and i % 2 == 1:
                self.box(zebra, x, yy - 2, total, pitch)
            for value, (ex, w, align) in zip(row, edges):
                s = value if isinstance(value, str) else money(value)
                if align == "right":
                    self.rt(s, ex + w, yy, size, self.r.ink, h=pitch + 2)
                elif align == "center":
                    self.ct(s, ex + w / 2.0, yy, size, self.r.ink, h=pitch + 2)
                else:
                    self.st(s, ex, yy, size, self.r.ink, h=pitch + 2, w=w + 10)
            yy += pitch
        if close_rule:
            self.rule(x, yy + 2, total, rc)
            yy += 10
        return yy

    # measured off a render: a presentation-preset table draws a ~26px header
    # and ~24px rows at cellSpacing "small"
    TABLE_HEADER_H = 26
    TABLE_ROW_H = 24

    def table_h(self, nrows, header=True):
        """Expected rendered height of a bound table with `nrows` rows.

        Sizing a plate to this keeps the closing hairline against the last row;
        guessing leaves a band of dead space inside the frame.
        """
        return (self.TABLE_HEADER_H if header else 0) + nrows * self.TABLE_ROW_H + 6

    def data_plate(self, caption, source, columns, x, y, w, h, note=None,
                   sort=None, caption_size=11, rule_color=None, bg=None,
                   spacing="small"):
        """A bound table dressed as typography rather than as a widget.

        A bound table's text always uses Sigma's UI font, no exceptions. Its
        row/header fill is pinned to `bg` (defaulting to the report's own
        canvas colour) via `table()`'s `textStyles` handling -- this actually
        works in the interactive editor, but the PDF export path still always
        renders a bound table's fill as white regardless. So to make a LIVE
        table sit in a PRINTED page instead of floating on it:

          * put it on a near-white stock, so the PDF's white row fill disappears
          * `borderRadius: "square"` with no border, so there is no card edge
          * draw the report's OWN hairlines above and below, and set the caption
            in the report's own face — the frame is typeset even though the
            table's interior isn't, in print
          * the `bg` pin still matters for anyone viewing the live report in
            the interactive editor rather than the PDF, so two data_plate()s on
            the same page don't drift to different fills there (see `table()`)

        Returns the y just past the plate.
        """
        rc = rule_color or self.r.rule_color
        yy = y
        if caption:
            self.st(caption, x, yy, caption_size, self.r.highlight, bold=True, h=26)
            if note:
                self.st(note, x + HV.width(caption, caption_size, True) + 14,
                        yy + 3, 9, self.r.ink, italic=True, h=22)
            yy += 26
        self.rule(x, yy, w, rc)
        yy += 3
        self.table(source, columns, x, yy, w, h, sort=sort, spacing=spacing,
                   bg=bg or self.r.canvas, radius="square")
        yy += h + 1
        self.rule(x, yy, w, rc)
        return yy + 10

    def kpi(self, source, formula, name, x, y, w, h, fmt=None, size=27,
            color=None, anchor="center", bg=None):
        """A single live figure bound to a source element.

        `anchor` is "center" or "right" only: "start"/"end" fail verify as
        'Invalid kind: kpi-chart', and `horizontalAlign` verifies but is dropped.
        Right-align a live figure in a ledger row with anchor="right".
        """
        col = {"id": self.r._uid("k"), "formula": formula, "name": name}
        if fmt:
            col["format"] = fmt
        layout = {"anchor": anchor}
        el = {"id": self.r._uid("kp"), "kind": "kpi-chart",
              "source": {"elementId": source, "kind": "table"},
              "columns": [col],
              "value": {"columnId": col["id"], "color": color or self.r.ink,
                        "fontSize": size},
              "name": {"visibility": "hidden"},
              "style": {"backgroundColor": bg or self.r.canvas, "padding": "none"},
              "layout": layout}
        return self._add(el, x, y, w, h)

    def pageno(self, n, right=False, y=None, size=9):
        y = self.r.pageno_y if y is None else y
        if right:
            return self.rt(str(n), self.r.right, y, size, self.r.ink, h=18)
        return self.st(str(n), 40, y, size, self.r.ink, h=18)


# ------------------------------------------------------------------ Report

class Report:
    """A whole report document. Page size defaults to US Letter at 96dpi."""

    def __init__(self, name, folder_id=None, page_w=816, page_h=1056,
                 canvas="#FFFFFF", ink="#1A1B14", highlight="#333333",
                 family="Helvetica", left=85, right=774, numcol_w=110,
                 row_pitch=23.0, body_size=11, note_size=9, head_size=21,
                 head_pitch=22, head_y=49, pageno_y=1028, rule_color=None,
                 categorical=None):
        self.name = name
        self.folder_id = folder_id or S.FOLDER_ID
        self.page_w, self.page_h = page_w, page_h
        self.canvas, self.ink, self.highlight = canvas, ink, highlight
        self.family = family
        self.left, self.right, self.numcol_w = left, right, numcol_w
        self.row_pitch = row_pitch
        self.body_size, self.note_size = body_size, note_size
        self.head_size, self.head_pitch, self.head_y = head_size, head_pitch, head_y
        self.pageno_y = pageno_y
        self.rule_color = rule_color or ink
        self.categorical = categorical
        self.elements, self.rows, self.pages = [], {}, []
        self._bleed_ids = set()
        self._n = 0

    # ---- plumbing
    def _uid(self, prefix):
        self._n += 1
        return "%s%d" % (prefix, self._n)

    def _add(self, pid, el, x, y, w, h, bleed=False):
        if x < 0 or y < 0:
            raise ValueError("layout requires non-negative x/y (got %s,%s for %s)"
                             % (x, y, el["id"]))
        self.elements.append(el)
        self.rows[pid].append((el["id"], round(x), round(y), round(w), round(h)))
        if bleed:
            self._bleed_ids.add(el["id"])
        return el["id"]

    def page(self, pid, name=None):
        self.pages.append({"id": pid, "name": name or pid})
        self.rows[pid] = []
        return Page(self, pid, name or pid)

    def hidden_page(self, pid, name=None):
        self.pages.append({"id": pid, "name": name or pid, "visibility": "hidden"})
        self.rows[pid] = []
        return Page(self, pid, name or pid)

    def sql_source(self, eid, name, sql, columns, connection_id=None, page=None):
        """Register a warehouse-backed source element.

        Every element must appear in the layout, so sources live on a hidden
        `pdata` page. `columns` is [(id, sql_column_name, display_name), ...] and
        each formula reads `[Custom SQL/<sql_column_name>]`.

        NOTE: `/spec/verify` does NOT resolve SQL — a bad connection or a typo in
        a column name only surfaces on create, or as an "Invalid Query" string
        rendered inside the table. Always render and look.
        """
        if page is None:
            if not hasattr(self, "_pdata"):
                self._pdata = self.hidden_page("pdata", "Data")
            page = self._pdata
        cols = [{"id": cid, "formula": "[Custom SQL/%s]" % src, "name": disp}
                for cid, src, disp in columns]
        el = {"id": eid, "kind": "table", "name": name,
              "source": {"kind": "sql", "statement": sql,
                         "connectionId": S.require(
                             "SIGMA_CONNECTION_ID", connection_id or S.CONNECTION_ID)},
              "columns": cols}
        # Tile sources inside the page: stacking them would run off the bottom,
        # and an out-of-bounds box adds a blank page even on a hidden page.
        n = len(self.rows[page.id])
        bw, bh, per_row = 396, 248, 2
        x = 8 + (n % per_row) * (bw + 8)
        y = 8 + (n // per_row) * (bh + 8)
        page._add(el, x, y, bw, bh)
        return eid

    def dm_source(self, eid, name, data_model_id, dm_element_id, dm_table_name,
                  columns, page=None):
        """Register a data-model-backed source element (kind: "data-model").

        Same idea as `sql_source()`, for orgs/connections where the underlying
        warehouse tables aren't directly queryable via raw SQL from this
        environment but an already-published Sigma data model over them is
        (confirmed pattern: `source: {dataModelId, elementId, kind:
        "data-model"}`). `dm_element_id` is the data model's OWN elementId for
        the target table (from `GET /v2/dataModels/{id}/elements`); `dm_table_name`
        is that table's display name, used as the bracket prefix in each
        column's formula: `[<dm_table_name>/<field display name>]`. `columns` is
        [(id, field_display_name, output_name), ...]. Downstream elements bound
        to this source (`table()`, `kpi()`, or a hand-built `pivot-table`) then
        reference the OUTPUT names via `[<name>/<output_name>]`.
        """
        if page is None:
            if not hasattr(self, "_pdata"):
                self._pdata = self.hidden_page("pdata", "Data")
            page = self._pdata
        cols = [{"id": cid, "formula": "[%s/%s]" % (dm_table_name, field), "name": disp}
                for cid, field, disp in columns]
        el = {"id": eid, "kind": "table", "name": name,
              "source": {"kind": "data-model", "dataModelId": data_model_id,
                         "elementId": dm_element_id},
              "columns": cols}
        n = len(self.rows[page.id])
        bw, bh, per_row = 396, 248, 2
        x = 8 + (n % per_row) * (bw + 8)
        y = 8 + (n // per_row) * (bh + 8)
        page._add(el, x, y, bw, bh)
        return eid

    def span(self, body, size=None, color=None, family=None):
        """Styled body, wrapping EACH LINE separately.

        A <span> may not straddle two markdown blocks — the validator rejects it
        as an unclosed tag — so multi-line bodies get one span per line, with
        hard-break spaces and blank lines left outside the tags. Only color,
        background-color, font-size and font-family are permitted in the style.
        """
        size = size or self.body_size
        color = color or self.ink
        fam = family or self.family
        f = "font-family: %s; " % fam if fam else ""

        def one(s):
            return ('<span style="%sfont-size: %spx; color: %s">%s</span>'
                    % (f, size, color, s))

        lines = body.split("\n")
        if len(lines) == 1:
            return one(body)
        out = []
        for line in lines:
            stripped = line.rstrip()
            out.append("" if not stripped
                       else one(stripped) + line[len(stripped):])
        return "\n".join(out)

    def geom(self, ncols=2, label_x=None, indent=14):
        """Column geometry for `statement()`: n right edges butted together."""
        label_x = self.left if label_x is None else label_x
        rights = [self.right - (ncols - 1 - i) * self.numcol_w
                  for i in range(ncols)]
        return {"label_x": label_x, "indent": indent, "numcol_w": self.numcol_w,
                "rights": rights,
                "dot_end": rights[0] - self.numcol_w - 8}

    # ---- output
    def layout(self):
        out = ['<?xml version="1.0" encoding="utf-8"?>']
        for pg in self.pages:
            out.append('<Page id="%s">' % pg["id"])
            for eid, x, y, w, h in self.rows[pg["id"]]:
                out.append('  <Element elementId="%s" x="%s" y="%s" '
                           'width="%s" height="%s"/>' % (eid, x, y, w, h))
            out.append("</Page>")
        return "\n".join(out)

    def document(self):
        theme = {"colors": {"text": self.ink, "highlight": self.highlight,
                            "darkMode": "hidden"},
                 "colorOverrides": [{"name": "backgroundCanvas",
                                     "color": self.canvas}],
                 "space": {"unit": "small", "showElementPadding": "hidden"}}
        if self.categorical:
            theme["categoricalScheme"] = self.categorical
        return {"schemaVersion": 1, "kind": "report",
                "elements": self.elements, "pages": self.pages,
                "settings": {"theme": {"overrides": theme}},
                "config": {"margin": 0, "pageHeight": self.page_h,
                           "pageWidth": self.page_w},
                "layout": self.layout()}

    def spec(self):
        return {"name": self.name, "folderId": self.folder_id,
                "document": self.document()}

    def overflow(self):
        """Elements running past the trim — each would add a blank extra page."""
        bad = []
        for pg in self.pages:
            for eid, x, y, w, h in self.rows[pg["id"]]:
                if eid in self._bleed_ids:
                    continue
                if y + h > self.page_h - 4 or x + w > self.page_w:
                    bad.append((pg["id"], eid, x, y, w, h, y + h))
        return bad

    # ---- API
    def verify(self):
        S.call("POST", "/v2/reports/spec/verify", self.spec())
        return True

    def create(self):
        S.require("SIGMA_FOLDER_ID", self.folder_id)
        return S.create_report(self.spec()).get("reportId")

    def update(self, report_id):
        S.update_report(report_id, self.spec())
        return report_id

    def cli(self, argv=None, id_file="report_id.txt"):
        """Standard dump/verify/create/update entry point for a template."""
        argv = argv if argv is not None else sys.argv[1:]
        action = argv[0] if argv else "dump"
        idf = pathlib.Path(id_file)
        try:
            if action == "dump":
                print("pages: %d  elements: %d  spec bytes: %d"
                      % (len(self.pages), len(self.elements),
                         len(json.dumps(self.spec()))))
                bad = self.overflow()
                if bad:
                    print("\noverflowing elements (each spills an extra page):")
                    for pid, eid, x, y, w, h, bottom in bad:
                        print("  %-10s %-6s (%s,%s %sx%s) bottom=%s"
                              % (pid, eid, x, y, w, h, bottom))
                else:
                    print("no overflow — every element sits inside the trim")
                return
            if action == "verify":
                self.verify()
                print("verify OK — %d elements across %d pages"
                      % (len(self.elements), len(self.pages)))
            elif action == "create":
                rid = self.create()
                print("created report", rid)
                idf.write_text(rid or "")
            elif action == "update":
                rid = argv[1] if len(argv) > 1 else idf.read_text().strip()
                self.update(rid)
                print("updated", rid)
        except S.SigmaError as exc:
            msg = exc.body
            try:
                msg = json.loads(exc.body).get("message", msg)
            except ValueError:
                pass
            print("%s FAILED:\n%s" % (action, str(msg)[:2500]))
            sys.exit(1)
