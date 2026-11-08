# Measuring a source so the output lands on top of it

Fidelity comes from measurement, not from taste. Everything below was used to
build the Motorola 1967 template; `scripts/derive_template.py` automates the
first two sections.

## 0. Get the source as PNGs

```bash
osascript -l JavaScript scripts/raster.js source.pdf ./src_pages 1.6
```

`scripts/png.py` reads 8- and 16-bit PNGs with no third-party libraries (there's
no PIL here). Note the rasterizer's Retina doubling — derive scale from
`png_width / page_points`, never from the requested factor.

## 1. Colours

**Paper / field colour** = the *modal* quantised colour of the region. Scanned
stock is textured, so a single pixel is unreliable and the mean is muddy.

**Ink colour** = the mean of the **darkest 10–30%** of pixels in a mask, not the
single darkest pixel. On the Motorola scan the darkest maroon pixel read
`#4F1D0E` while the perceived ink was `#5E2313`; the extreme pixel would have
made every heading too dark.

Separate ink masks by hue before averaging, or the maroon headings and the black
body text merge into one muddy brown:

```python
if r - g > 22 and r - b > 30:   maroon.append(px)     # warm display ink
elif lum < 120 and abs(r-g) <= 22: dark.append(px)    # neutral body ink
```

Sampled example (Motorola 1967): cover stock `#A88430`, letter stock `#B09030`,
inside cover `#20202A`, financial paper `#F0F0E8`, contents paper `#E8E8E0`,
display ink `#5E2313`, body ink `#1A1B14`.

## 2. Geometry, as page fractions

Work in fractions of page width/height, then multiply by 816×1056. Source scans
rarely match Letter's aspect exactly, so fractions travel better than absolutes.

- **Content box** — bounding box of all ink. Motorola: x `0.1042`–`0.9479`
  → `LEFT = 85`, `RIGHT = 774`.
- **Column right edges** — restrict the ink scan to the table body and to
  `x > (some cutoff)`, then find column bands with a gap threshold. Motorola's
  year columns right-aligned at `0.8142` and `0.9479` → 664 and 774.
  Beware: dot leaders connect labels to figures, so a naive column scan over the
  whole row merges everything into one band.
- **Row pitch** — group ink rows into bands, then take the mean top-to-top delta
  **over a long run** of body rows. Short runs and section breaks skew it: an
  early estimate of 24.6px became 23.0px when measured across ten rows.
- **Display type size** — cap-height band ÷ ~0.7. A 35px cap band on a 2490px-tall
  scan → `35/2490 × 1056 = 14.8px` cap → ~21px font.
- **Rules** — rows where >60% of the content width is inked.

## 3. Type metrics

`scripts/helvetica.py` holds Adobe AFM advance widths. Validate against a render
before trusting a new family: build a calibration page with one string per
element at known y, rasterize, and compare measured ink extents to the table.
Advance should exceed ink extent by a small positive side bearing (Motorola check:
mean +1.16px over 67 labels, max +3.07 — a good fit).

Dot leaders then become arithmetic:

```
n = floor((dot_end - gap - x - width(label + " ")) / dot_advance)
```

## 4. Artwork out of a scan

Crop by fraction, then **alpha-key** the mark so it composites over any field
instead of carrying a visible rectangle of its original background:

```python
png.key_ink(src, out, ink=(0xFF,0xFF,0xFF), mode="light", lo=70, hi=165)  # white on dark
png.key_ink(src, out, ink=(0x1A,0x1B,0x14), mode="dark",  lo=95, hi=205)  # black on paper
```

`mode="light"` keeps bright pixels (a white signature on a near-black page);
`mode="dark"` keeps dark pixels (a logo on cream). Keep genuinely textured art
(a full-bleed collage) as RGB/JPEG and match the page field to the crop's own
field colour so the seam disappears.

Locating art: contrast against the modal field colour works for hard-edged panels,
but on textured stock a low threshold catches grain. Raise the threshold, restrict
to a region, or crop generously and tighten after looking at it.

## 5. Iterate against the render

Export, rasterize, and put your page beside the source. Cheap programmatic checks
beat squinting:

- corner/edge pixel colours to confirm a field really reaches the trim
- ink row bands to confirm row pitch and first-baseline offset
- ink extents per element to confirm alignment

Expect two or three passes. Real first-pass defects from the Motorola build:
figures flush left (element `align` ignored), the subtitle colliding with the
last heading word, notes overflowing into two extra pages, and the second
column's `$` landing on the first column's figure.
