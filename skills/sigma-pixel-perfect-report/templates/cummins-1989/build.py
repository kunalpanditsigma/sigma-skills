"""Big Buys — Annual Report 2025, in the Cummins 1989 (Paul Rand) design system.

Demonstrates BOTH data paths in one document:

  * build-time figures  — `warehouse.query()` runs SQL now and returns rows, so
    the ledger and the five-year grid can be TYPESET (dot leaders, ruled totals,
    italic-caps totals). Fixed at build time.
  * render-time figures — `sql_source()` + `table()`/`kpi()` bind elements to the
    warehouse, so they re-query on every export. Live, but a bound table has no
    per-row styling, hence no leaders.

Page 6 states which figures are which, so the document doesn't overclaim.

Design system measured off the Cummins 1989 cover: grey stock, and the four line
colours of Rand's exploded-engine drawing recovered by hue-clustering the cover.

    python3 build.py dump | verify | create | update [reportId]
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "scripts"))

import helvetica as HV
from reportkit import LINE_PITCH, Report, money
from warehouse import num, query

TABLE = "SE_DEMO_DB.BIG_BUYS.BIG_BUYS_POS"
FY, PRIOR = 2025, 2024

# ---------------------------------------------------------------- palette
# Measured from the cover: modal stock colour, and the darkest third of each
# hue cluster (the line core rather than its antialiasing).
STOCK = "#E6E6E3"        # cover: matched to the artwork's rendered background so
                         # the cropped panel does not read as a lighter rectangle
PAPER = "#F5F5F2"        # interior sheet. Near-white on purpose: a bound table's
                         # row fill is ALWAYS white and cannot be themed, so the
                         # stock meets the tables rather than fighting them
INK = "#2B2A2E"
BLUE = "#283F79"         # display headings
RED = "#621625"
OCHRE = "#7F5930"
GREEN = "#26412B"
RULE = "#9A9A98"
CATEGORICAL = [BLUE, RED, OCHRE, GREEN, "#5D7762", "#907860"]

MONEY0 = {"kind": "number", "formatString": "$,.0f", "currencySymbol": "$"}
MONEY2 = {"kind": "number", "formatString": "$,.2f", "currencySymbol": "$"}
NUM0 = {"kind": "number", "formatString": ",.0f"}
PCT1 = {"kind": "number", "formatString": ".1%"}

# ------------------------------------------------------- build-time figures
YEARLY_SQL = """SELECT
  YEAR(DATE)                                   AS FY,
  SUM(QUANTITY * PRICE)                        AS REVENUE,
  SUM(QUANTITY * COST)                         AS COGS,
  SUM(QUANTITY)                                AS UNITS,
  COUNT(DISTINCT ORDER_NUMBER)                 AS ORDERS,
  COUNT(DISTINCT STORE_KEY)                    AS STORES,
  COUNT(DISTINCT CUST_KEY)                     AS CUSTOMERS
FROM %s
GROUP BY 1
ORDER BY 1""" % TABLE

TOP_N = 12

TAIL_SQL = """WITH f AS (
  SELECT PRODUCT_FAMILY AS P, SUM(QUANTITY * PRICE) AS REV
  FROM %s WHERE YEAR(DATE) = %d GROUP BY 1
), r AS (SELECT P, REV, ROW_NUMBER() OVER (ORDER BY REV DESC) AS RN FROM f)
SELECT COUNT(*) AS N, COALESCE(SUM(REV), 0) AS REV FROM r WHERE RN > %d
""" % (TABLE, FY, TOP_N)

FAMILY_SQL = """SELECT
  PRODUCT_FAMILY                                              AS FAMILY,
  SUM(QUANTITY * PRICE)                                       AS REVENUE,
  SUM(QUANTITY)                                               AS UNITS,
  (SUM(QUANTITY * PRICE) - SUM(QUANTITY * COST))
      / NULLIF(SUM(QUANTITY * PRICE), 0)                      AS MARGIN
FROM %s WHERE YEAR(DATE) = %d
GROUP BY 1
QUALIFY ROW_NUMBER() OVER (ORDER BY SUM(QUANTITY * PRICE) DESC) <= 12
ORDER BY 2 DESC""" % (TABLE, FY)

REGION_SQL = """SELECT
  STORE_REGION                                                AS REGION,
  SUM(QUANTITY * PRICE)                                       AS REVENUE,
  COUNT(DISTINCT STORE_KEY)                                   AS STORES,
  SUM(QUANTITY * PRICE) / NULLIF(COUNT(DISTINCT STORE_KEY), 0) AS PER_STORE
FROM %s WHERE YEAR(DATE) = %d
GROUP BY 1 ORDER BY 2 DESC""" % (TABLE, FY)

COUNT_SQL = """SELECT
  COUNT(DISTINCT PRODUCT_FAMILY) AS FAMILIES,
  COUNT(DISTINCT STORE_REGION)   AS REGIONS
FROM %s WHERE YEAR(DATE) = %d""" % (TABLE, FY)

print("querying the warehouse for build-time figures ...")
YEARS = query(YEARLY_SQL, ["FY", "REVENUE", "COGS", "UNITS", "ORDERS",
                           "STORES", "CUSTOMERS"])
BY_FY = {int(num(r, "FY")): r for r in YEARS}
print("  got %d fiscal years: %s" % (len(YEARS), sorted(BY_FY)))
_c = query(COUNT_SQL, ["FAMILIES", "REGIONS"])[0]
N_FAMILIES, N_REGIONS = int(num(_c, "FAMILIES")), int(num(_c, "REGIONS"))
print("  %d product families, %d store regions" % (N_FAMILIES, N_REGIONS))
_t = query(TAIL_SQL, ["N", "REV"])[0]
N_TAIL, REV_TAIL = int(num(_t, "N")), num(_t, "REV")
print("  showing top %d families; tail = %d families, $%s"
      % (TOP_N, N_TAIL, "{:,.0f}".format(REV_TAIL)))
def m(fy, key):
    return num(BY_FY.get(fy, {}), key)


def gross(fy):
    return m(fy, "REVENUE") - m(fy, "COGS")


def margin(fy):
    rev = m(fy, "REVENUE")
    return (gross(fy) / rev) if rev else 0.0


def aov(fy):
    o = m(fy, "ORDERS")
    return (m(fy, "REVENUE") / o) if o else 0.0


def i(v):
    return int(round(v))


# (indent, label, FY, prior, kind) — every figure below is warehouse-derived
LEDGER = [
    (0, "REVENUE", None, None, "head"),
    (0, "Net sales", i(m(FY, "REVENUE")), i(m(PRIOR, "REVENUE")), ""),
    (0, "Cost of sales", i(m(FY, "COGS")), i(m(PRIOR, "COGS")), ""),
    (0, "GROSS PROFIT", i(gross(FY)), i(gross(PRIOR)), "total"),
    (0, "Gross margin", "%.1f%%" % (margin(FY) * 100),
     "%.1f%%" % (margin(PRIOR) * 100), ""),
    (0, "TRADING VOLUME", None, None, "head"),
    (0, "Units sold", i(m(FY, "UNITS")), i(m(PRIOR, "UNITS")), ""),
    (0, "Orders", i(m(FY, "ORDERS")), i(m(PRIOR, "ORDERS")), ""),
    (0, "Average order value", "$" + "{:,.2f}".format(aov(FY)),
     "$" + "{:,.2f}".format(aov(PRIOR)), ""),
    (0, "NETWORK", None, None, "head"),
    (0, "Stores trading", i(m(FY, "STORES")), i(m(PRIOR, "STORES")), ""),
    (0, "Customers served", i(m(FY, "CUSTOMERS")), i(m(PRIOR, "CUSTOMERS")), ""),
    (0, "Net sales per store", i(m(FY, "REVENUE") / max(1, m(FY, "STORES"))),
     i(m(PRIOR, "REVENUE") / max(1, m(PRIOR, "STORES"))), "total-plain"),
]

# ------------------------------------------------------------------ report
r = Report("Big Buys — Annual Report %d (Cummins 1989 design)" % FY,
           canvas=PAPER, ink=INK, highlight=BLUE, rule_color=RULE,
           left=85, right=774, numcol_w=115, row_pitch=23.0,
           body_size=11, note_size=9, head_size=15, head_pitch=19,
           head_y=64, categorical=CATEGORICAL)

GEOM = r.geom(ncols=2)
COLS = [(str(FY), 659), (str(PRIOR), 774)]

# ---- live sources: every table on pages 2 and 4 re-queries on export
live_years = r.sql_source("src-years", "Years", YEARLY_SQL, [
    ("y0", "FY", "FY"), ("y1", "REVENUE", "Revenue"), ("y2", "COGS", "COGS"),
    ("y3", "UNITS", "Units"), ("y4", "ORDERS", "Orders"),
    ("y5", "STORES", "Stores"), ("y6", "CUSTOMERS", "Customers"),
])

live_family = r.sql_source("src-family", "Family", FAMILY_SQL, [
    ("f0", "FAMILY", "Family"), ("f1", "REVENUE", "Revenue"),
    ("f2", "UNITS", "Units"), ("f3", "MARGIN", "Margin"),
])

live_region = r.sql_source("src-region", "Region", REGION_SQL, [
    ("g0", "REGION", "Region"), ("g1", "REVENUE", "Revenue"),
    ("g2", "STORES", "Stores"), ("g3", "PER_STORE", "Per store"),
])

# scoped to the reporting year -- a Sum() over `src-years` totals ALL years
live_fy = r.sql_source("src-fy", "ThisYear", """SELECT
  SUM(QUANTITY * PRICE)                        AS REVENUE,
  SUM(QUANTITY * PRICE) - SUM(QUANTITY * COST) AS GROSS,
  COUNT(DISTINCT ORDER_NUMBER)                 AS ORDERS,
  SUM(QUANTITY)                                AS UNITS
FROM %s WHERE YEAR(DATE) = %d""" % (TABLE, FY), [
    ("n0", "REVENUE", "Revenue"), ("n1", "GROSS", "Gross"),
    ("n2", "ORDERS", "Orders"), ("n3", "UNITS", "Units"),
])




def heading(p, text, y, sub=None):
    """Rand-ish section head: small bold caps in blue over a hairline."""
    p.st(text, 85, y, 15, BLUE, bold=True, h=24)
    if sub:
        p.st(sub, 85 + HV.width(text, 15, True) + 14, y + 5, 10, INK,
             italic=True, h=20)
    p.rule(85, y + 26, 689, RULE)
    return y + 38


# =============================================================== 1 cover
p = r.page("cover", "Cover")
p.field(STOCK)
p.img(HERE / "assets" / "wireframe.datauri.txt", 150, 190, 640, 680)
p.st("BIG BUYS", 85, 92, 19, INK, bold=True, h=30)
p.rule(85, 126, 200, INK)
p.st("Annual Report %d" % FY, 85, 136, 12, INK, h=22)
p.st("Retail Point of Sale · %d stores" % i(m(FY, "STORES")), 85, 158, 9, INK,
     italic=True, h=20)

# ====================================================== 2 financial highlights
p = r.page("highlights", "Financial Highlights")
y = heading(p, "FINANCIAL HIGHLIGHTS", 64,
            sub="figures below re-query on export")
py = p.prose(
    ["Big Buys traded through %d stores in fiscal %d, serving %s customers "
     "across %s orders. Net sales of %s produced a gross margin of %.1f%%."
     % (i(m(FY, "STORES")), FY, "{:,}".format(i(m(FY, "CUSTOMERS"))),
        "{:,}".format(i(m(FY, "ORDERS"))),
        "$" + "{:,}".format(i(m(FY, "REVENUE"))), margin(FY) * 100),
     "The four accent colours used throughout this report are the line colours "
     "of the exploded-engine drawing on the cover of the Cummins 1989 annual "
     "report, designed by Paul Rand — recovered by clustering the cover scan "
     "by hue."],
    85, y, 689, 11)

ky = py + 16
p.rule(85, ky - 12, 689, RULE)
for label, formula, fmt, colour in (
        ("Net sales", "Sum([ThisYear/Revenue])", MONEY0, BLUE),
        ("Gross profit", "Sum([ThisYear/Gross])", MONEY0, GREEN),
        ("Orders", "Sum([ThisYear/Orders])", NUM0, OCHRE),
        ("Units sold", "Sum([ThisYear/Units])", NUM0, RED)):
    x = 85 + len([1]) * 0  # placeholder to keep the loop readable
    idx = ["Net sales", "Gross profit", "Orders", "Units sold"].index(label)
    x = 85 + idx * 174
    p.st(label.upper(), x, ky, 9, INK, bold=True, h=26)
    p.kpi(live_fy, formula, label, x, ky + 24, 168, 44, fmt=fmt, size=21,
          color=colour, bg=PAPER)
    if idx:                       # hairline between each figure, not a card each
        p.vrule(x - 18, ky + 2, 66, RULE)
ky += 78
p.rule(85, ky, 689, RULE)
ky += 18

p.data_plate("FIVE YEAR TREND", live_years, [
    ("t0", "[Years/FY]", "Fiscal year"),
    ("t1", "[Years/Revenue]", "Net sales", MONEY0),
    ("t2", "[Years/COGS]", "Cost of sales", MONEY0),
    ("t3", "[Years/Units]", "Units", NUM0),
    ("t4", "[Years/Orders]", "Orders", NUM0),
    ("t5", "[Years/Customers]", "Customers", NUM0),
], 85, ky, 689, p.table_h(len(YEARS)),
    note="live — re-queries on every export",
    sort=[("t0", "ascending")], bg=PAPER)
p.pageno(2)

# ========================================================= 3 trading results
p = r.page("results", "Statement of Trading Results")
y = heading(p, "STATEMENT OF TRADING RESULTS",
            64, sub="years ended December 31 · Big Buys")
p.column_head(y, "", COLS, color=BLUE)
y = p.statement(LEDGER, y + 32, GEOM)
p.prose(["*Every figure on this page was read from the warehouse when the "
         "specification was built, then typeset — which is what allows the dot "
         "leaders, ruled totals and italic-caps subtotals. The bound tables "
         "elsewhere re-query on export but cannot carry per-row styling.*"],
        85, y + 10, 689, 9)
p.pageno(3)

# ============================================================== 4 live detail
p = r.page("detail", "Trading Detail")
y = heading(p, "TRADING DETAIL", 64, sub="live · %d" % FY)

y = p.data_plate("BY PRODUCT FAMILY", live_family, [
    ("a0", "[Family/Family]", "Product family"),
    ("a1", "[Family/Revenue]", "Net sales", MONEY0),
    ("a2", "[Family/Units]", "Units", NUM0),
    ("a3", "[Family/Margin]", "Margin", PCT1),
], 85, y, 689, p.table_h(TOP_N), sort=[("a1", "descending")], bg=PAPER,
    note="live · %d largest of %d" % (TOP_N, N_FAMILIES))

p.st("The %d largest product families are shown. The remaining %d account for "
     "$%s, or %.1f%% of net sales."
     % (TOP_N, N_TAIL, "{:,.0f}".format(REV_TAIL),
        100.0 * REV_TAIL / max(1.0, m(FY, "REVENUE"))),
     85, y + 6, 9, INK, italic=True, h=24)
y += 26

p.data_plate("BY STORE REGION", live_region, [
    ("b0", "[Region/Region]", "Region"),
    ("b1", "[Region/Revenue]", "Net sales", MONEY0),
    ("b2", "[Region/Stores]", "Stores", NUM0),
    ("b3", "[Region/Per store]", "Net sales per store", MONEY0),
], 85, y + 16, 689, p.table_h(N_REGIONS), sort=[("b1", "descending")], bg=PAPER,
    note="live · all regions")
p.pageno(4)

# ========================================================== 5 five year summary
p = r.page("fiveyear", "Five Year Summary")
y = heading(p, "FIVE YEAR SUMMARY", 64, sub="typeset from build-time figures")
fys = sorted(BY_FY)
bottom = p.matrix(
    row_labels=["NET SALES", "COST OF SALES", "GROSS PROFIT", "GROSS MARGIN",
                "UNITS SOLD", "ORDERS", "CUSTOMERS"],
    col_labels=fys,
    values=[
        [i(m(f, "REVENUE")) for f in fys],
        [i(m(f, "COGS")) for f in fys],
        [i(gross(f)) for f in fys],
        ["%.1f%%" % (margin(f) * 100) for f in fys],
        [i(m(f, "UNITS")) for f in fys],
        [i(m(f, "ORDERS")) for f in fys],
        [i(m(f, "CUSTOMERS")) for f in fys],
    ],
    x=85, y=y + 6, label_w=150, right=774, size=9, row_h=44,
    currency_rows=[0, 1, 2])      # money rows only, not % or counts
p.prose(["*Fiscal %d is a partial trading year in the source data.*" % max(fys)],
        85, bottom + 6, 689, 9)
p.pageno(5)

# ================================================================== 6 method
p = r.page("method", "Basis of Preparation")
y = heading(p, "BASIS OF PREPARATION", 64)
p.prose([
    "**Design.** The palette and cover artwork are taken from the Cummins 1989 "
    "annual report (Paul Rand), one of 456 designs in the gallery registry that "
    "ships with this skill. Stock colour and the four line colours were measured "
    "off the cover scan rather than chosen by eye; the drawing itself is cropped "
    "from that scan.",
    "**Source.** All figures derive from %s on the Snowflake connection. "
    "Net sales are QUANTITY x PRICE and cost of sales QUANTITY x COST; gross "
    "profit and margin are computed from those. No figure is invented." % TABLE,
    "**Two data paths, deliberately mixed.** The statement of trading results and "
    "the five year summary were resolved by querying the warehouse while this "
    "specification was generated, then typeset as text — that is what permits dot "
    "leaders, ruled totals and italic-caps subtotals. The highlights KPIs and the "
    "trading detail tables are bound elements: they re-query the warehouse on "
    "every export, so those figures are live at the moment of export.",
    "**Why the live tables look different.** A bound table\'s cell and header fill "
    "is always white and its text always uses Sigma\'s interface font; neither can "
    "be overridden. The interior sheet is therefore a near-white stock, chosen so "
    "the white fill disappears into the page, and each table is framed with the "
    "report\'s own hairlines and caption rather than left as a floating card.",
    "**Limits.** The renderer offers no justified text, and line pitch is fixed "
    "regardless of font size, so small type is more loosely leaded than a 1989 "
    "original. This document is a demonstration of report generation, not a "
    "financial statement of any real company.",
], 85, y, 689, 10)
p.pageno(6)


if __name__ == "__main__":
    r.cli(id_file=str(HERE / "report_id.txt"))
