"""Helvetica advance widths, for laying out text the renderer won't align for me.

The report renderer ignores an element-level `align`, and a <span style> can't
carry text-align — so right-aligned figures are positioned by computing their
rendered width and setting the element's x to `right_edge - width`. The
calibration render confirmed the renderer uses real Helvetica metrics (its
measured period advance, 3.057px at 11px, is exactly 278/1000 em).

Widths are Adobe AFM units per 1000 em. Digits, comma, period, parens and the
dollar sign have the SAME advance in Helvetica and Helvetica-Bold, so figures
right-align identically whatever their weight; Oblique matches Regular.
"""

_REGULAR = {
    " ": 278, "!": 278, '"': 355, "#": 556, "$": 556, "%": 889, "&": 667,
    "'": 222, "(": 333, ")": 333, "*": 389, "+": 584, ",": 278, "-": 333,
    ".": 278, "/": 278,
    "0": 556, "1": 556, "2": 556, "3": 556, "4": 556, "5": 556, "6": 556,
    "7": 556, "8": 556, "9": 556,
    ":": 278, ";": 278, "<": 584, "=": 584, ">": 584, "?": 556, "@": 1015,
    "A": 667, "B": 667, "C": 722, "D": 722, "E": 667, "F": 611, "G": 778,
    "H": 722, "I": 278, "J": 500, "K": 667, "L": 556, "M": 833, "N": 722,
    "O": 778, "P": 667, "Q": 778, "R": 722, "S": 667, "T": 611, "U": 722,
    "V": 667, "W": 944, "X": 667, "Y": 667, "Z": 611,
    "[": 278, "\\": 278, "]": 278, "^": 469, "_": 556, "`": 222,
    "a": 556, "b": 556, "c": 500, "d": 556, "e": 556, "f": 278, "g": 556,
    "h": 556, "i": 222, "j": 222, "k": 500, "l": 222, "m": 833, "n": 556,
    "o": 556, "p": 556, "q": 556, "r": 333, "s": 500, "t": 278, "u": 556,
    "v": 500, "w": 722, "x": 500, "y": 500, "z": 500,
    "{": 334, "|": 260, "}": 334, "~": 584,
    "—": 1000, "–": 556, "’": 222, "‘": 222,
    "¢": 556, "¾": 556, "⅝": 556, "¼": 556, "½": 556,
    "·": 278, " ": 278,
}

_BOLD = dict(_REGULAR)
_BOLD.update({
    "A": 722, "B": 722, "C": 722, "D": 722, "E": 667, "F": 611, "G": 778,
    "H": 722, "I": 278, "J": 556, "K": 722, "L": 611, "M": 833, "N": 722,
    "O": 778, "P": 667, "Q": 778, "R": 722, "S": 667, "T": 611, "U": 722,
    "V": 667, "W": 944, "X": 667, "Y": 667, "Z": 611,
    "a": 556, "b": 611, "c": 556, "d": 611, "e": 556, "f": 333, "g": 611,
    "h": 611, "i": 278, "j": 278, "k": 556, "l": 278, "m": 889, "n": 611,
    "o": 611, "p": 611, "q": 611, "r": 389, "s": 556, "t": 333, "u": 611,
    "v": 556, "w": 778, "x": 556, "y": 556, "z": 500,
    "'": 278, "&": 722, ":": 333, ";": 333, "!": 333, "?": 611,
    " ": 278, "-": 333, ".": 278, ",": 278, "(": 333, ")": 333, "$": 556,
})

DEFAULT = 556


def width(s, size, bold=False):
    """Advance width of `s` at `size` px."""
    table = _BOLD if bold else _REGULAR
    return sum(table.get(c, DEFAULT) for c in s) * size / 1000.0


def dot_width(size):
    return _REGULAR["."] * size / 1000.0


def wrap_lines(s, size, col_w, bold=False):
    """Greedy word-wrap line count for a paragraph in a column `col_w` px wide."""
    words = s.split()
    if not words:
        return 1
    lines, cur = 1, 0.0
    space = width(" ", size, bold)
    for w in words:
        ww = width(w, size, bold)
        if cur <= 0:
            cur = ww
        elif cur + space + ww <= col_w:
            cur += space + ww
        else:
            lines += 1
            cur = ww
    return lines
