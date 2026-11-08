"""Derive a design system from a source cover or scan, by measuring it.

Sampling beats eyeballing: this reports the paper/field colours (modal colour of
each region), the ink colours (mean of the darkest slice of each ink mask), and
the ink bounding box as page fractions. Those numbers go straight into a
template's palette and grid constants.

    python3 derive_template.py <name> --cover path/to/cover.jpg
    python3 derive_template.py <name> --pdf path/to/report.pdf --page 4

Writes <name>/palette.json and prints a ready-to-paste constants block.
"""
import argparse
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import png


def to_png(src, page=1):
    """Rasterize one page of a PDF, or convert an image, to a readable PNG."""
    src = pathlib.Path(src)
    out = src.parent / ("_derive_%s_p%d.png" % (src.stem, page))
    if src.suffix.lower() == ".pdf":
        subprocess.run(["osascript", "-l", "JavaScript", str(HERE / "raster.js"),
                        str(src), str(src.parent), "2.0", str(page), str(page)],
                       check=True, capture_output=True)
        made = src.parent / ("p%02d.png" % page)
        made.rename(out)
    else:
        subprocess.run(["sips", "-s", "format", "png", str(src), "--out", str(out)],
                       check=True, capture_output=True)
    return out


def inset(w, h, frac=0.06):
    """Region excluding the outer margin, where scan edges and vignetting live."""
    return (int(w * frac), int(h * frac), int(w * (1 - frac)), int(h * (1 - frac)))


def modal(w, h, ch, pix, region, step=3, quant=12):
    counts = {}
    x0, y0, x1, y1 = region
    for y in range(max(0, y0), min(y1, h), step):
        for x in range(max(0, x0), min(x1, w), step):
            r, g, b = png.px(w, ch, pix, x, y)
            q = (r // quant * quant, g // quant * quant, b // quant * quant)
            counts[q] = counts.get(q, 0) + 1
    return max(counts.items(), key=lambda kv: kv[1])[0] if counts else (0, 0, 0)


def lum(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def ink_mean(w, h, ch, pix, region, field, frac=0.35, step=2, light=False,
             min_delta=45):
    """The perceived ink colour of a region.

    Two-stage on purpose. First keep only pixels that are actually ink — far
    enough from the field — because on a sparse text page the great majority of
    pixels are blank stock, and "the darkest 18% of the page" is still mostly
    paper (that mistake returned #BFBFB8 for ink that is really #1A1B14).
    Then average the darkest (or, on dark stock, brightest) slice of that subset:
    the single most extreme pixel reads far too strong.
    """
    fl = lum(field)
    vals = []
    x0, y0, x1, y1 = region
    for y in range(max(0, y0), min(y1, h), step):
        for x in range(max(0, x0), min(x1, w), step):
            r, g, b = png.px(w, ch, pix, x, y)
            l = 0.299 * r + 0.587 * g + 0.114 * b
            if (l - fl if light else fl - l) < min_delta:
                continue
            vals.append((l, r, g, b))
    if not vals:
        return field
    vals.sort(reverse=light)
    sel = vals[:max(1, int(len(vals) * frac))]
    n = len(sel)
    return tuple(round(sum(v[i] for v in sel) / n) for i in (1, 2, 3))


def accents(w, h, ch, pix, field, step=3, quant=24, top=6):
    """Saturated colours that differ from the field — candidate accent inks."""
    fr, fg, fb = field
    counts = {}
    for y in range(0, h, step):
        for x in range(0, w, step):
            r, g, b = png.px(w, ch, pix, x, y)
            if abs(r - fr) + abs(g - fg) + abs(b - fb) < 90:
                continue
            mx, mn = max(r, g, b), min(r, g, b)
            if mx - mn < 40:                    # not colourful enough to be an accent
                continue
            q = (r // quant * quant, g // quant * quant, b // quant * quant)
            counts[q] = counts.get(q, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: -kv[1])[:top]
    return [(png.hexs(c), n) for c, n in ranked]


def ink_bbox(w, h, ch, pix, field, step=1, margin=0.02):
    """Bounding box of the ink, as page fractions — gives the content margins.

    Polarity follows the field: dark ink on pale stock, light ink on dark stock.
    Returns None when the result is degenerate (a photographic or full-bleed
    cover, where ink covers the whole sheet and the box means nothing).
    """
    dark_field = lum(field) < 110
    thresh = (lum(field) + 255) / 2.0 if dark_field else lum(field) * 0.62
    minx, miny, maxx, maxy = w, h, -1, -1
    hits = 0
    for y in range(0, h, step):
        for x in range(0, w, step):
            l = lum(png.px(w, ch, pix, x, y))
            if (l > thresh) if dark_field else (l < thresh):
                hits += 1
                minx, miny = min(minx, x), min(miny, y)
                maxx, maxy = max(maxx, x), max(maxy, y)
    if maxx < 0 or not hits:
        return None
    box = {"x0": minx / w, "x1": maxx / w, "y0": miny / h, "y1": maxy / h}
    spans_all = ((box["x1"] - box["x0"]) > 1 - 2 * margin
                 and (box["y1"] - box["y0"]) > 1 - 2 * margin)
    return None if spans_all else box


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("name")
    ap.add_argument("--cover")
    ap.add_argument("--pdf")
    ap.add_argument("--page", type=int, default=1)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    if not (a.cover or a.pdf):
        raise SystemExit("give --cover IMAGE or --pdf FILE")

    src = to_png(a.cover or a.pdf, a.page)
    w, h, ch, pix = png.read(str(src))
    print("source %s  %dx%d" % (src.name, w, h))

    core = inset(w, h)                 # ignore scan edges when sampling stock
    fieldc = modal(w, h, ch, pix, core)
    dark_field = lum(fieldc) < 110
    borderc = modal(w, h, ch, pix, (0, 0, w, 40))
    inkc = ink_mean(w, h, ch, pix, core, fieldc, light=dark_field)
    acc = accents(w, h, ch, pix, fieldc)
    bbox = ink_bbox(w, h, ch, pix, fieldc, step=2)

    pal = {
        "field": png.hexs(fieldc),
        "field_is_dark": dark_field,
        "top_border": png.hexs(borderc),
        "ink": png.hexs(inkc),
        "accents": [c for c, _ in acc],
        "ink_bbox_fractions": bbox,
    }
    out = pathlib.Path(a.out or a.name)
    out.mkdir(parents=True, exist_ok=True)
    (out / "palette.json").write_text(json.dumps(pal, indent=1))

    print("\npalette")
    print("  field       %s%s" % (pal["field"], "  (dark stock)" if dark_field else ""))
    print("  ink         %s  (%s end of the range)"
          % (pal["ink"], "bright" if dark_field else "dark"))
    print("  accents     %s" % (", ".join(pal["accents"]) or "(none)"))
    if bbox:
        print("\ncontent box as page fractions")
        print("  x %.4f - %.4f      y %.4f - %.4f"
              % (bbox["x0"], bbox["x1"], bbox["y0"], bbox["y1"]))
        print("\npaste into your template (816x1056 page):")
        print("  LEFT  = %d" % round(bbox["x0"] * 816))
        print("  RIGHT = %d" % round(bbox["x1"] * 816))
    else:
        print("\ncontent box: NOT USABLE from this image — the ink covers the whole")
        print("  sheet, i.e. a photographic or full-bleed cover. Take the content")
        print("  box off an interior text page (--pdf ... --page N), or keep the")
        print("  scaffold's LEFT/RIGHT and set the margins by eye against a render.")
    print("\nwrote %s" % (out / "palette.json"))
    print("Next: copy templates/_scaffold/build.py, drop these values in, then")
    print("      python3 build.py dump && python3 build.py create")


if __name__ == "__main__":
    main()
