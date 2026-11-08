"""Motorola, Inc. 1967 Annual Report — the reference template for reportkit.

Nine pages: cover, inside cover, contents, both shareholders'-letter pages, and
the four financial pages. Every colour and coordinate here was MEASURED off the
original scans (see content.py), which is what lets the output sit on top of the
original rather than merely evoke it.

Use this as the worked example when building any other template.

    python3 build.py dump | verify | create | update [reportId]
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "scripts"))
sys.path.insert(0, str(HERE))

import content as C
import helvetica as HV
from reportkit import LINE_PITCH, Report

ASSETS = HERE / "assets"


def asset(name):
    return (ASSETS / ("%s.datauri.txt" % name)).read_text().strip()


r = Report("Motorola, Inc. — Annual Report 1967",
           canvas=C.CREAM, ink=C.INK, highlight=C.MAROON,
           left=C.LEFT, right=C.RIGHT, numcol_w=C.NUMCOL_W,
           row_pitch=23.0, body_size=C.BODY_SIZE, note_size=9,
           head_size=C.HEAD_SIZE, head_pitch=C.HEAD_PITCH, head_y=C.HEAD_Y,
           pageno_y=C.PAGENO_Y, rule_color=C.RULE)

GEOM = r.geom(ncols=2)
YEARS = [("1967", C.COL_1967_R), ("1966", C.COL_1966_R)]
NOTE_L_X, NOTE_L_W = C.LEFT + 18, 300
NOTE_R_X, NOTE_R_W = 452, 322
NSIZE = 9

# ---------------------------------------------------------------- 1 cover
p = r.page("cover", "Cover")
p.field(C.GOLD_COVER)
p.img(asset("cover"), 256, 337, 303, 391)
p.rt(C.COVER["wordmark"], 240, 527, 15, C.WHITE, bold=True, h=26)
p.st(C.COVER["title"], 575, 527, 15, C.WHITE, bold=True, h=26)

# --------------------------------------------------------- 2 inside cover
p = r.page("inside", "Inside Cover")
p.field(C.NAVY)
p.prose(["*%s*" % C.INSIDE_QUOTE], 285, 520, 233, 11, C.WHITE)
p.prose([C.INSIDE_NOTE], 540, 520, 236, 11, C.WHITE)
p.img(asset("signature"), 293, 684, 219, 39)

# ------------------------------------------------------------- 3 contents
p = r.page("contents", "Contents")
p.field(C.CREAM_ALT)
p.st("CONTENTS", 50, 517, 17, C.MAROON, bold=True, h=30)
for i, (num, title) in enumerate(C.CONTENTS_LEFT):
    yy = 520 + i * 33.4
    p.rt(num, 320, yy, 11, h=22)
    p.st(title, 331, yy, 11, h=22)
for i, (num, title) in enumerate(C.CONTENTS_RIGHT):
    yy = 520 + i * 37.4
    if num.startswith("INSIDE"):
        # three stacked 7px lines still occupy three 22.4px line slots
        p.raw_text(r.span("INSIDE  \nBACK  \nCOVER", 7, C.INK), 528, yy - 6, 52, 74)
    else:
        p.rt(num, 569, yy, 11, h=22)
    p.st(title, 587, yy, 11, h=22)
p.img(asset("mlogo"), 630, 735, 62, 62)
p.pageno(1, right=True)

# --------------------------------------------------------------- 4 letter
p = r.page("letter2", "Letter to Shareholders")
p.field(C.GOLD)
for i, line in enumerate(C.LETTER_HEADING.split("\n")):
    p.rt(line, 266, 498 + i * 24, 13, C.WHITE, bold=True, h=26)
p.prose(C.LETTER_P2_COL1, 285, 250, 233, 11, C.INK_GOLD)
p.prose(C.LETTER_P2_COL2, 551, 250, 231, 11, C.INK_GOLD)
p.pageno(2)

# ---------------------------------------------------- 5 letter, continued
p = r.page("letter3", "Letter, continued")
p.field(C.GOLD)
p.prose(C.LETTER_P3_COL1, 33, 252, 239, 11, C.INK_GOLD)
p.prose(C.LETTER_P3_COL2, 289, 252, 239, 11, C.INK_GOLD)
ey = p.prose(C.LETTER_P3_COL3, 549, 252, 235, 11, C.INK_GOLD)
p.img(asset("sig_galvin"), 549, ey + 4, 236, 62)
p.img(asset("sig_wavering"), 549, ey + 74, 236, 66)
p.rt(C.LETTER_DATE, 784, 782, 11, C.INK_GOLD, h=22)
p.pageno(3, right=True)

# -------------------------------------------------------- 6 balance sheet
p = r.page("bs1", "Balance Sheet")
p.display_head(["CONSOLIDATED", "BALANCE", "SHEET"],
               subtitle="as of December 31    Motorola, Inc. and Subsidiaries")
p.column_head(C.SECT_Y, "ASSETS", YEARS)
p.statement(C.BALANCE_ASSETS, C.TABLE_Y, GEOM)

ny = 600
p.st("NOTES TO FINANCIAL STATEMENTS", C.LEFT, ny, 11, bold=True, h=22)
p.rule(C.LEFT, ny + 22, C.CW)
ny += 32

n1y = p.prose(["**1**  Long-term debt at December 31 consisted of the following:"],
              NOTE_L_X, ny, NOTE_L_W, NSIZE)
N1_C67, N1_C66, N1_W = NOTE_L_X + 218, NOTE_L_X + 290, 68
p.ct("1967", N1_C67 - 34, n1y, NSIZE, h=20)
p.ct("1966", N1_C66 - 34, n1y, NSIZE, h=20)
p.rule(N1_C67 - N1_W, n1y + 18, 158)
n1y += 24
for label, v67, v66, kind in C.NOTE1_ROWS:
    lines = HV.wrap_lines(label, NSIZE, 148) if label else 1
    h = lines * LINE_PITCH
    if kind in ("subtotal", "grand"):
        for right in (N1_C67, N1_C66):
            p.rule(right - N1_W, n1y - 2, N1_W)
    if label:
        p.raw_text(r.span(label, NSIZE, C.INK), NOTE_L_X, n1y, 150, h + 4)
    for val, right in ((v67, N1_C67), (v66, N1_C66)):
        if val is not None:
            p.rt("{:,}".format(val), right, n1y, NSIZE,
                 bold=(kind == "grand"), h=20)
    if kind == "grand":
        for right in (N1_C67, N1_C66):
            p.rule(right - N1_W, n1y + 18, N1_W)
            p.rule(right - N1_W, n1y + 21, N1_W)
    n1y += h

r1 = p.prose([C.NOTE_1_PROSE], NOTE_R_X, ny, NOTE_R_W, NSIZE)
p.prose(["**2**  " + C.NOTE_2_PROSE], NOTE_R_X, r1 + 6, NOTE_R_W, NSIZE)
p.pageno(4)

# --------------------------------------------- 7 balance sheet, continued
p = r.page("bs2", "Balance Sheet, continued")
p.column_head(C.SECT_Y, "LIABILITIES AND SHAREHOLDERS' EQUITY", YEARS)
p.statement(C.BALANCE_LIABS, C.TABLE_Y, GEOM)

ny = 646
p.rule(60, ny, C.RIGHT - 60)
ny += 12
l1 = p.prose([C.NOTE_2B_PROSE], NOTE_L_X, ny, NOTE_L_W, NSIZE)
p.prose(["**3**  " + C.NOTE_3_PROSE], NOTE_L_X, l1 + 6, NOTE_L_W, NSIZE)
r1 = p.prose(["**4**  " + C.NOTE_4_PROSE], NOTE_R_X, ny, NOTE_R_W, NSIZE)
r2 = p.prose(["**5**  " + C.NOTE_5_PROSE], NOTE_R_X, r1 + 6, NOTE_R_W, NSIZE)
p.prose(["**6**  " + C.NOTE_6_PROSE], NOTE_R_X, r2 + 6, NOTE_R_W, NSIZE)
p.pageno(5, right=True)

# ------------------------------------------------ 8 statement of earnings
p = r.page("earnings", "Statement of Earnings")
p.display_head(["STATEMENT OF CONSOLIDATED", "EARNINGS AND RETAINED", "EARNINGS"],
               subtitle="Motorola, Inc. and Subsidiaries")
p.column_head(C.SECT_Y, "YEARS ENDED DECEMBER 31", YEARS)
y = p.statement(C.EARNINGS, C.TABLE_Y, GEOM)
p.st("See accompanying notes to financial statements.", C.LEFT, y + 4, 10,
     italic=True, h=22)

ay = 690
p.rule(C.LEFT, ay, C.CW)
ay += 10
p.raw_text(r.span("**%s**" % C.AUDITOR_FIRM.replace("\n", "**  \n**"), NSIZE, C.INK),
           C.LEFT, ay, 300, 3 * LINE_PITCH + 6)
a1 = ay + 3 * LINE_PITCH + 8
a2 = p.prose(["*%s*" % C.AUDITOR_TO], C.LEFT, a1, 300, NSIZE)
p.prose([C.AUDITOR_P1], C.LEFT, a2, 300, NSIZE)
r1 = p.prose([C.AUDITOR_P2], NOTE_R_X, ay, NOTE_R_W, NSIZE)
r2 = p.prose([C.AUDITOR_P3], NOTE_R_X, r1 + 4, NOTE_R_W, NSIZE)
for i, line in enumerate(C.AUDITOR_SIGN.split("\n")):
    p.rt(line, C.RIGHT, r2 + 4 + i * LINE_PITCH, NSIZE, bold=True, h=20)
p.pageno(6)

# ---------------------------------------------- 9 source & use + ten year
p = r.page("funds", "Source and Use of Funds")
p.display_head(["STATEMENT OF CONSOLIDATED", "SOURCE AND USE", "OF FUNDS"],
               subtitle="Motorola, Inc. and Subsidiaries")
p.column_head(C.SECT_Y, "YEARS ENDED DECEMBER 31", YEARS)
y = p.statement(C.FUNDS_SOURCE, C.TABLE_Y, GEOM)
y = p.statement(C.FUNDS_USE, y + 16, GEOM)

ty = 470
for i, line in enumerate(["TEN YEAR", "FINANCIAL", "SUMMARY"]):
    p.st(line, C.LEFT + 25, ty + i * C.HEAD_PITCH, C.HEAD_SIZE, C.MAROON,
         bold=True, h=C.HEAD_PITCH + 10)
ty += 3 * C.HEAD_PITCH + 18

bottom = p.matrix(
    row_labels=[m for m, _, _ in C.TEN_YEAR],
    col_labels=C.TEN_YEAR_YEARS,
    values=[[("%.2f" % v) if k == "eps" else "{:,}".format(v) for v in vals]
            for _, vals, k in C.TEN_YEAR],
    x=40, y=ty, label_w=120, right=C.RIGHT, size=8, row_h=46)
p.prose([C.TEN_YEAR_FOOTNOTES], 40, bottom + 4, C.RIGHT - 40, 9)
p.pageno(7, right=True)


if __name__ == "__main__":
    r.cli(id_file=str(HERE / "report_id.txt"))
