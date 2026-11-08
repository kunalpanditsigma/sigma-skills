"""<Company> <Year> — pixel-perfect Sigma report.

Copy this file, replace the measured constants with values from
`derive_template.py`, then iterate: dump -> verify -> create -> rasterize -> look.

    python3 build.py dump | verify | create | update [reportId]
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "scripts"))

from reportkit import Report

# ---- palette: from derive_template.py, not from taste
FIELD = "#FFFFFF"     # cover / feature page stock
PAPER = "#F5F5F0"     # body page stock
INK = "#1A1A1A"       # body text
DISPLAY = "#7A2214"   # display headings + section rules

# ---- grid: content box fractions x 816/1056
LEFT, RIGHT = 85, 774
NUMCOL_W = 110
ROW_PITCH = 23.0      # measured top-to-top over a LONG run of body rows

r = Report("<Company> — Annual Report <Year>",
           canvas=PAPER, ink=INK, highlight=DISPLAY,
           left=LEFT, right=RIGHT, numcol_w=NUMCOL_W, row_pitch=ROW_PITCH)

GEOM = r.geom(ncols=2)
COLS = [("<Year>", RIGHT - NUMCOL_W), ("<Year-1>", RIGHT)]

# ---- cover
p = r.page("cover", "Cover")
p.field(FIELD)
p.rt("<COMPANY>", 240, 527, 15, "#FFFFFF", bold=True, h=26)
p.st("ANNUAL REPORT <YEAR>", 575, 527, 15, "#FFFFFF", bold=True, h=26)
# p.img("assets/cover.jpg", 256, 337, 303, 391)

# ---- a financial page
p = r.page("balance", "Balance Sheet")
p.display_head(["CONSOLIDATED", "BALANCE", "SHEET"],
               subtitle="as of December 31    <Company> and Subsidiaries")
p.column_head(129, "ASSETS", COLS)

# (indent, label, value_current, value_prior, kind)
#   kind: "" | head | head-fig | sub | total | total-plain | subtotal | grand
ASSETS = [
    (0, "CURRENT ASSETS", None, None, "head"),
    (0, "Cash", 22132822, 21993844, ""),
    (0, "Accounts receivable", None, None, "sub"),
    (1, "Trade", 110155708, 98954974, ""),
    (0, "Inventories", 103434437, 106106282, ""),
    (0, "TOTAL CURRENT ASSETS", 235722967, 227055100, "total"),
    (0, "", 410782762, 392912958, "grand"),
]
y = p.statement(ASSETS, 152, GEOM)
p.pageno(1)

# ---- a wide grid page
p = r.page("tenyear", "Ten Year Summary")
YEARS = list(range(1958, 1968))
ROWS = ["SALES", "EARNINGS"]
VALS = [[218909968 + i * 1000 for i in range(10)],
        [7356213 + i * 1000 for i in range(10)]]
bottom = p.matrix(ROWS, YEARS, VALS, x=40, y=200, label_w=120, right=RIGHT,
                  size=8, row_h=46)
p.pageno(2, right=True)


if __name__ == "__main__":
    r.cli(id_file=str(HERE / "report_id.txt"))
