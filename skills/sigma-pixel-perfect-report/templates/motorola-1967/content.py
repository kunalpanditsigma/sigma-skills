"""Motorola, Inc. 1967 Annual Report — every string and figure, plus the
measured geometry of the original.

Figures and prose are transcribed from the scanned report; the palette and the
x/y grid are *measured* off the scans (see the sampling notes on each constant)
rather than eyeballed, which is what lets the generated PDF sit on top of the
original.

Nothing in here talks to the API — `build_motorola.py` consumes it.
"""

# --------------------------------------------------------------- palette
# Sampled from the scans: mean of the darkest 30% of each ink mask, and the
# modal colour of each paper field.
GOLD_COVER = "#A88430"    # cover stock
GOLD = "#B09030"          # letter pages 2-3
NAVY = "#20202A"          # inside front cover
CREAM = "#F0F0E8"         # financial pages
CREAM_ALT = "#E8E8E0"     # contents page (a shade darker)
MAROON = "#5E2313"        # display headings + section rules
INK = "#1A1B14"           # body text on cream
INK_GOLD = "#1F1E12"      # body text on gold
WHITE = "#FFFFFF"
RULE = "#4A4A42"          # hairlines in the ten-year grid

# ---------------------------------------------------------------- geometry
# US Letter portrait at 96dpi, which is what the report spec's page config uses.
PAGE_W, PAGE_H = 816, 1056

# Content box, from the ink bounding box on the balance-sheet scan:
#   left edge   x 0.1042 of page width
#   right edge  x 0.9479
LEFT = 85
RIGHT = 774
CW = RIGHT - LEFT                 # 689

# The two year columns right-align at these measured fractions (0.8142, 0.9479).
COL_1967_R = 664
COL_1966_R = 774
NUMCOL_W = 110
LABEL_W = CW - 2 * NUMCOL_W       # 469

# Vertical rhythm, measured on the balance sheet:
#   display heading lines start at y 0.0462 / 0.0667 / 0.0871  -> pitch 21.5
#   section label row ("ASSETS  1967  1966") at 0.1221
#   rule beneath it at 0.1333, first data row at 0.1454
#   data row pitch 58/2490 of page height -> 24.6
HEAD_Y = 49
HEAD_PITCH = 22
HEAD_SIZE = 21
SECT_Y = 129
SECT_RULE_Y = 141
TABLE_Y = 152
PAGENO_Y = 1028

BODY_SIZE = 11
SMALL_SIZE = 10
NOTE_SIZE = 10

# ------------------------------------------------------------------ cover
COVER = {
    "wordmark": "MOTOROLA",
    "title": "ANNUAL REPORT 1967",
    # the collage sits centred, measured x 0.3140-0.6845, y 0.3195-0.6890
    "art_x": 0.3140, "art_y": 0.3195, "art_x2": 0.6845, "art_y2": 0.6890,
}

INSIDE_QUOTE = (
    "The role of business is to honorably serve the needs of society at a "
    "profit. The serving of these needs, and doing so honorably—both of "
    "which are required in our free enterprise system—directly relate to "
    "the humanistic goals of our society."
)
INSIDE_NOTE = (
    "The illustrations on the following pages relate just a few of Motorola's "
    "diverse products to some of their applications in humanistic situations."
)

# --------------------------------------------------------------- contents
CONTENTS_LEFT = [
    ("2", "Letter to Shareholders"),
    ("4", "Balance Sheet"),
    ("6", "Statement of Earnings"),
    ("7", "Source and Use of Funds"),
    ("7", "Ten Year Financial Summary"),
    ("8", "Communications Division"),
    ("10", "Semiconductor Products Division"),
    ("12", "Consumer Products Division"),
]
CONTENTS_RIGHT = [
    ("14", "Government Electronics Division"),
    ("16", "Automotive Products Division"),
    ("18", "Control Systems Division"),
    ("20", "Annual Meeting"),
    ("INSIDE BACK COVER", "Directors and Officers"),
]

# ----------------------------------------------------------------- letter
LETTER_HEADING = "TO OUR SHAREHOLDERS\nAND FRIENDS"

# Page 2 of the report sets the letter in two columns.
LETTER_P2_COL1 = [
    "For the first time in six years we must report a temporary setback in "
    "sales and earnings. Total sales were $629,975,344, off the record pace of "
    "1966 by 8%. Earnings of $18,816,147 or $3.08 per share were down 43% from "
    "the record $5.40 in 1966. However, during these six years sales and "
    "earnings have nonetheless about doubled.",
    "The fourth quarter represented the year's most favorable comparison of "
    "equivalent quarters. The gap in sales was narrowed to within 3% of the "
    "record fourth quarter last year. Earnings were down by 14%.",
    "Over-all the advantage of broad product diversification was manifested. "
    "The gains in 1967 sales in four of the six operating divisions offset much "
    "of the decline in the largest division, consumer products. One division "
    "reported sales volume virtually the same as 1966.",
    "The communications and semiconductor products divisions scored advances in "
    "earnings as well as in sales. Automotive products and gov-",
]
LETTER_P2_COL2 = [
    "ernment electronics divisions' earnings were down somewhat, the latter a "
    "result of losses in one broad category of products produced for use in "
    "Viet Nam by the Chicago Center of our government electronics division. The "
    "smaller control systems division increased its sales and improved its "
    "anticipated loss position. Each division's progress is discussed in detail "
    "on the succeeding pages of this report.",
    "The major adversities experienced were in the consumer products division. "
    "Color television sales fell short of industry forecasts with the "
    "consequent runoff of excess inventory at marked down prices. Adding to "
    "this problem, the mix of color and monochrome receivers bought by "
    "consumers proved contrary to forecasts.",
    "The lowered color television production rate reflected adversely on our "
    "picture tube plant operation in that it could not readjust quickly to "
    "produce profitably at the level of requirements in the finished goods",
]

# Page 3 runs three columns and closes with the signatures.
LETTER_P3_COL1 = [
    "facilities. Another aspect of the picture tube situation bearing on the "
    "differential in earnings was the reduction of some 65 cents per share "
    "attributable to payments from and to National Video Corporation under the "
    "agreement with that company.",
    "We have come firmly to grips with the problems in the consumer products "
    "division. A reorganization was effected during the year with changes in "
    "the operations and marketing segments. A new marketing concept was "
    "introduced during the fourth quarter in several test markets featuring the "
    "company's solid state color television line which is setting new standards "
    "of reliability for the industry. The results have been most promising.",
    "The domestic and foreign plant expansion program activated in 1966 has "
    "been almost completed. On a comparative cost basis, capital expenditures "
    "were $57 million in 1966 and $28 million in 1967. Substantial new "
    "facilities and ventures have come on stream or approach readi-",
]
LETTER_P3_COL2 = [
    "ness in Schaumburg and Pontiac, Illinois; Mesa, Arizona; Toronto, Canada; "
    "Yokohama, Japan; Seoul, Korea and Toulouse, France.",
    "A phase of the restructuring the past year, and continuing in 1968, "
    "involved a broadening of management talent throughout the corporation to "
    "cope with changing technologies, increasing product diversification, and "
    "widening international scope.",
    "An Executive Institute aimed at generalizing the capabilities of "
    "specialists was started in Vail, Arizona, and has graduated its fourth "
    "class of 14 men. Ten corporate officers were elected to positions of major "
    "responsibility during the year. Eight were promoted from within the "
    "company and two were drawn from outside. Greater emphasis in recruitment "
    "and evaluation procedures has been given to the early recognition and "
    "rapid advancement of deserving young talent.",
    "In 1968, assuming a favorable general economy, sales are expected to be up "
    "significantly and earnings should",
]
LETTER_P3_COL3 = [
    "increase in even greater proportion, becoming evident in the second, third "
    "and fourth quarters.",
    "Electronics is an industry of momentum and change. There are bound to be "
    "periods of adversity interrupting a company's growth pattern. These "
    "periods test the mettle. We want to commend our associates for the manner "
    "in which they have redoubled their efforts the past year-and-a-half, and "
    "to express appreciation for the confidence of our shareholders.",
    "For the Board of Directors,",
]
LETTER_DATE = "March 21, 1968"

# ---------------------------------------------------- financial statements
# Each row: (indent level, label, 1967, 1966, kind)
#   kind: "" plain | "head" section caps | "sub" sub-heading, no figures
#         "total" italic-caps total | "grand" double-ruled grand total
#         "note" a wrapped explanatory line carrying figures
BALANCE_ASSETS = [
    (0, "CURRENT ASSETS", None, None, "head"),
    (0, "Cash", 22132822, 21993844, ""),
    (0, "Short-term investments, at cost", 596230, 5763058, ""),
    (0, "Accounts receivable", None, None, "sub"),
    (1, "United States government", 17955600, 12537878, ""),
    (1, "Other", 110155708, 98954974, ""),
    (1, "Allowance for doubtful accounts", -2801000, -3013801, ""),
    (0, "Costs recoverable under United States government contracts, "
        "less progress billings", 13625424, 14204119, ""),
    (0, "Inventories, at the lower of cost (first-in, first-out) or market",
     103434437, 106106282, ""),
    (0, "Other current assets", 5525907, 5183301, ""),
    (0, "TOTAL CURRENT ASSETS", 270625128, 261729655, "total"),
    (0, "PLANT AND EQUIPMENT, at Cost", None, None, "head"),
    (0, "Land", 8299360, 7276817, ""),
    (0, "Buildings", 103341055, 91596202, ""),
    (0, "Machinery and equipment", 92291504, 82341169, ""),
    (0, "Accumulated depreciation", -66969132, -53994969, ""),
    (0, "NET PLANT AND EQUIPMENT", 136962787, 127219219, "total"),
    (0, "Sundry assets, net", 3194847, 3964084, ""),
    (0, "", 410782762, 392912958, "grand"),
]

BALANCE_LIABS = [
    (0, "CURRENT LIABILITIES", None, None, "head"),
    (0, "Notes payable", 52000000, 38500000, ""),
    (0, "Current maturities of long-term debt", 1164104, 1070880, ""),
    (0, "Accounts payable", 38788540, 40689380, ""),
    (0, "Accrued compensation", 8748066, 8044225, ""),
    (0, "Federal income taxes", 6305641, 8349597, ""),
    (0, "Other (including withheld) taxes", 5586580, 5672009, ""),
    (0, "Contribution to employees' profit sharing fund", 4956347, 11528890, ""),
    (0, "Product and service warranties", 5121682, 4057609, ""),
    (0, "Other", 16745941, 15658523, ""),
    (0, "TOTAL CURRENT LIABILITIES", 139416901, 133571113, "total"),
    (0, "LONG-TERM DEBT (note 1)", 65079480, 66743572, "head-fig"),
    (0, "SHAREHOLDERS' EQUITY", None, None, "head"),
    (0, "Capital stock, $3.00 par value (note 2)", None, None, "sub"),
    (1, "Authorized: 10,000,000 shares", None, None, "sub"),
    (2, "Outstanding: 1967, 6,122,483 shares; 1966, 6,104,263 shares",
     18367449, 18312789, ""),
    (0, "Additional paid-in capital (note 2)", 17712959, 16781521, ""),
    (0, "Retained earnings (note 1)", 170205973, 157503963, ""),
    (0, "TOTAL SHAREHOLDERS' EQUITY", 206286381, 192598273, "total"),
    (0, "", 410782762, 392912958, "grand"),
]

EARNINGS = [
    (0, "SALES AND OTHER REVENUES", 629975344, 682374719, "head-fig"),
    (0, "Manufacturing and other costs of sales", 460922148, 491417637, ""),
    (0, "Selling, service, and administrative expenses", 105132184, 100452633, ""),
    (0, "Depreciation of plant and equipment (note 5)", 17771882, 13859021, ""),
    (0, "Contribution to employees' profit sharing fund", 4956347, 11528890, ""),
    (0, "Interest and amortization of debenture expense", 6621636, 5103695, ""),
    (0, "TOTAL COSTS AND OTHER EXPENSES", 595404197, 622361876, "total"),
    (0, "Income before federal income taxes", 34571147, 60012843, ""),
    (0, "Federal income taxes, net of investment credit of $1,230,000 in 1967; "
        "$1,793,000 in 1966", 15755000, 27060000, ""),
    (0, "EARNINGS", None, None, "head"),
    (1, "(per share outstanding during the year: 1967, $3.08; 1966, $5.40) "
        "(notes 3 and 4)", 18816147, 32952843, ""),
    (0, "Retained earnings at beginning of year", 157503963, 130652207, ""),
    (0, "", 176320110, 163605050, "subtotal"),
    (0, "Less cash dividends declared—$1.00 per share", 6114137, 6101087, ""),
    (0, "Retained earnings at end of year (note 1)", 170205973, 157503963, "grand"),
]

FUNDS_SOURCE = [
    (0, "SOURCE OF FUNDS", None, None, "head"),
    (0, "Earnings", 18816147, 32952843, ""),
    (0, "Depreciation", 17771882, 13859021, ""),
    (0, "Increase (decrease) in long-term debt", -1664092, 28429120, ""),
    (0, "Proceeds from exercise of share options", 986098, 744235, ""),
    (0, "Decrease in sundry assets", 769237, 255382, ""),
    (0, "Total", 36679272, 76240601, "total-plain"),
]
FUNDS_USE = [
    (0, "USE OF FUNDS", None, None, "head"),
    (0, "Additions to plant and equipment, net", 27515450, 59995652, ""),
    (0, "Cash dividends", 6114137, 6101087, ""),
    (0, "Increase in working capital", 3049685, 10143862, ""),
    (0, "Total", 36679272, 76240601, "grand"),
]

TEN_YEAR_YEARS = [1958, 1959, 1960, 1961, 1962, 1963, 1964, 1965, 1966, 1967]
TEN_YEAR = [
    ("SALES AND OTHER REVENUES",
     [218909968, 293081127, 301049185, 298219845, 346881779, 377852809,
      419066694, 516973065, 682374719, 629975344], "money"),
    ("INCOME BEFORE INCOME TAXES",
     [15171013, 27756237, 26548813, 19900308, 26514514, 27126526,
      38926724, 57838678, 60012843, 34571147], "money"),
    ("EARNINGS",
     [7356213, 14171237, 12633813, 9517308, 13206514, 12926526,
      20666724, 31838678, 32952843, 18816147], "money"),
    ("EARNINGS PER SHARE*",
     [1.27, 2.39, 2.09, 1.57, 2.02, 2.14, 3.41, 5.23, 5.40, 3.08], "eps"),
    ("WORKING CAPITAL",
     [59585830, 63336998, 73790019, 95078616, 96804189, 92358852,
      107625939, 118014680, 128158542, 131208227], "money"),
    ("NET INVESTMENT IN PLANT AND EQUIPMENT",
     [27615287, 33436676, 44594599, 48427446, 54783818, 67283543,
      67836835, 81082588, 127219219, 136962787], "money"),
    ("SHAREHOLDERS' EQUITY",
     [71533020, 83338386, 97166850, 102655506, 111835713, 120735367,
      137533422, 165002282, 192598273, 206286381], "money"),
]
TEN_YEAR_FOOTNOTES = (
    "*&nbsp;*Earnings per share are based on shares outstanding during the "
    "respective years, adjusted for share distributions.*  \n"
    "*Earnings per share shown above for 1962 do not include 17¢ of "
    "nonrecurring capital gain from sale of finance subsidiary.*"
)

# ------------------------------------------------------------------ notes
NOTES_1_2 = [
    ("1", "Long-term debt at December 31 consisted of the following:"),
]
# The note-1 debt schedule is a small two-year table of its own.
NOTE1_ROWS = [
    ("4¾% debentures due April 1, 1986 (less $500,000 debentures held in "
     "treasury for sinking fund payment)", 29000000, 29500000, ""),
    ("Revolving credit notes", 30000000, 30000000, ""),
    ("Notes payable", None, None, "sub"),
    ("3¾%, due $500,000 annually to 1972", 2500000, 3000000, ""),
    ("4⅝%, due $500,000 annually to 1976", 4500000, 5000000, ""),
    ("Real estate mortgages", 243584, 314452, ""),
    ("", 66243584, 67814452, "subtotal"),
    ("Less current maturities, included in current liabilities", 1164104, 1070880, ""),
    ("Noncurrent portion of long-term debt", 65079480, 66743572, "grand"),
]

NOTE_1_PROSE = (
    "Under the terms of the revolving credit, the company has the option of "
    "converting the notes to a five year term loan on or prior to February 1, "
    "1969; no reduction is contemplated during 1968. The agreement contains "
    "provisions restricting, among other things, the payment of cash dividends "
    "which are not to exceed $10,000,000 plus earnings (as defined) after "
    "December 31, 1965. It also requires the company to maintain consolidated "
    "working capital of not less than $75,000,000. At December 31, 1967, "
    "$53,000,000 of retained earnings was available for dividend payments."
)
NOTE_2_PROSE = (
    "Under the Employee Share Option Plan, adopted in 1960, options were "
    "granted (through 1965) to key employees to purchase Motorola, Inc. shares. "
    "During 1967, options on 18,220 shares were exercised; the excess "
    "($931,438) of the option price over the par value of shares issued was "
    "credited to additional paid-in capital. At year end, 75,685 shares were "
    "under option, all being currently exercisable, at an aggregate option "
    "price of $4,577,529; if not exercised, these options expire at various "
    "dates through 1973."
)
NOTE_2B_PROSE = (
    "The Board of Directors, subject to the approval of the shareholders, "
    "authorized the granting of options to key employees to purchase 300,000 "
    "Motorola, Inc. shares at not less than market value on date of grant. "
    "Options may be granted during the period February 1, 1968 to May 9, 1973. "
    "Options granted in any year shall not exceed 100,000 shares which become "
    "exercisable one year from date of grant and expire at the end of five "
    "years."
)
NOTE_3_PROSE = (
    "An Executive Incentive Plan, effective in 1968 (subject to shareholders' "
    "approval), provides that certain of the companies may reserve up to 4% of "
    "their annual consolidated net earnings (as defined) for the payment of "
    "cash incentive awards. Such awards are payable generally in equal annual "
    "installments over a period of five years and are generally subject to the "
    "recipients' continued employment. If the plan had been in effect in 1967 "
    "and the maximum reserve provided, net earnings would have been reduced "
    "$412,000 (7¢ per share)."
)
NOTE_4_PROSE = (
    "The company has a right to share in National Video Corporation's profit "
    "from the sale of color television tubes for a three year period ending in "
    "November, 1968, but has no obligation to make further repayments. Earnings "
    "per share for 1967 include a negative adjustment (repayment) of 16¢ of "
    "such profit from the cooperative color tube development program compared "
    "to 49¢ earned in 1966."
)
NOTE_5_PROSE = (
    "Depreciation of plant and equipment is provided on the basis of the "
    "estimated useful lives generally by the declining-balance method for items "
    "acquired subsequent to December 31, 1953 and by the straight-line method "
    "for items acquired prior to that date."
)
NOTE_6_PROSE = (
    "The companies are obligated under repurchase and other agreements, "
    "principally in connection with the financing of sales of products to "
    "consumers, and are defendants in suits and claims, which it is believed "
    "will have no material effect on the business of the companies."
)

# ------------------------------------------------------- auditors' opinion
AUDITOR_FIRM = "PEAT, MARWICK, MITCHELL & CO.\nCERTIFIED PUBLIC ACCOUNTANTS,\nCHICAGO, ILLINOIS"
AUDITOR_TO = "The Board of Directors and Shareholders of Motorola, Inc.:"
AUDITOR_P1 = (
    "We have examined the consolidated balance sheet of Motorola, Inc. and "
    "subsidiaries as of December 31, 1967 and the related statement of earnings "
    "and retained earnings and the statement of source and use of funds for the "
    "year then ended. Our examination was made in accordance with generally "
    "accepted auditing standards, and accordingly included such tests of the "
    "accounting records and such other auditing procedures as we considered "
    "necessary in the circumstances. It was not practicable to confirm accounts "
    "receivable from United States government departments"
)
AUDITOR_P2 = (
    "or agencies by communication with them but we satisfied ourselves as to "
    "such accounts by means of other auditing procedures."
)
AUDITOR_P3 = (
    "In our opinion, the accompanying consolidated balance sheet and statement "
    "of consolidated earnings and retained earnings present fairly the "
    "financial position of Motorola, Inc. and subsidiaries at December 31, 1967 "
    "and the results of their operations for the year then ended, in conformity "
    "with generally accepted accounting principles applied on a basis "
    "consistent with that of the preceding year. Also, in our opinion, the "
    "accompanying statement of consolidated source and use of funds for the "
    "year ended December 31, 1967 presents fairly the information shown therein."
)
AUDITOR_SIGN = "PEAT, MARWICK, MITCHELL & CO.\nFebruary 27, 1968"

FOOTER_NOTE = (
    "Reproduced from the Motorola, Inc. 1967 Annual Report as a Sigma report "
    "specification — every page, rule and figure is declared in code and "
    "created with POST /v2/reports/spec."
)
