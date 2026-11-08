"""Minimal PNG reader/writer (8-bit RGB/RGBA, non-interlaced) — no PIL on this box.

Used to sample the 1967 report's ink colours and to crop its artwork.
"""
import struct
import zlib


def read(path):
    """-> (width, height, channels, bytearray pixels)"""
    data = open(path, "rb").read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "not a png"
    pos, idat, w, h, ch = 8, [], None, None, None
    depth = ctype = None
    while pos < len(data):
        ln, typ = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + ln]
        if typ == b"IHDR":
            w, h, depth, ctype = struct.unpack(">IIBB", body[:10])
            assert depth in (8, 16), "only 8/16-bit supported, got %s" % depth
            ch = {0: 1, 2: 3, 4: 2, 6: 4}[ctype]
        elif typ == b"IDAT":
            idat.append(body)
        elif typ == b"IEND":
            break
        pos += 12 + ln
    raw = zlib.decompress(b"".join(idat))
    bpp = ch * (depth // 8)          # filter offset is in BYTES per pixel
    stride = w * bpp
    out = bytearray(h * stride)
    prev = bytearray(stride)
    p = 0
    for y in range(h):
        f = raw[p]
        p += 1
        line = bytearray(raw[p:p + stride])
        p += stride
        if f == 1:
            for i in range(bpp, stride):
                line[i] = (line[i] + line[i - bpp]) & 0xFF
        elif f == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif f == 3:
            for i in range(stride):
                a = line[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 0xFF
        elif f == 4:
            for i in range(stride):
                a = line[i - bpp] if i >= bpp else 0
                c = prev[i - bpp] if i >= bpp else 0
                b = prev[i]
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 0xFF
        out[y * stride:(y + 1) * stride] = line
        prev = line
    if depth == 16:                  # keep the high byte of each sample
        out = out[0::2]
    return w, h, ch, out


def write_rgb(path, w, h, pix):
    """pix = bytearray of w*h*3."""
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw += pix[y * w * 3:(y + 1) * w * 3]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(typ, body):
        return (struct.pack(">I", len(body)) + typ + body
                + struct.pack(">I", zlib.crc32(typ + body) & 0xFFFFFFFF))

    with open(path, "wb") as fh:
        fh.write(b"\x89PNG\r\n\x1a\n")
        fh.write(chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)))
        fh.write(chunk(b"IDAT", comp))
        fh.write(chunk(b"IEND", b""))


def write_rgba(path, w, h, pix):
    """pix = bytearray of w*h*4."""
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw += pix[y * w * 4:(y + 1) * w * 4]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(typ, body):
        return (struct.pack(">I", len(body)) + typ + body
                + struct.pack(">I", zlib.crc32(typ + body) & 0xFFFFFFFF))

    with open(path, "wb") as fh:
        fh.write(b"\x89PNG\r\n\x1a\n")
        fh.write(chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)))
        fh.write(chunk(b"IDAT", comp))
        fh.write(chunk(b"IEND", b""))


def key_ink(src, out, ink, mode, lo, hi):
    """Flatten a scanned mark to one ink colour + an alpha ramp.

    mode "dark": dark pixels become opaque ink (a black mark on paper).
    mode "light": bright pixels become opaque ink (white mark on a dark field).
    lo/hi bracket the luminance ramp that maps to alpha 0..255.
    """
    w, h, ch, pix = read(src)
    buf = bytearray(w * h * 4)
    ir, ig, ib = ink
    for y in range(h):
        for x in range(w):
            r, g, b = px(w, ch, pix, x, y)
            lum = 0.299 * r + 0.587 * g + 0.114 * b
            t = (hi - lum) / (hi - lo) if mode == "dark" else (lum - lo) / (hi - lo)
            a = max(0.0, min(1.0, t))
            j = (y * w + x) * 4
            buf[j], buf[j + 1], buf[j + 2], buf[j + 3] = ir, ig, ib, int(round(a * 255))
    write_rgba(out, w, h, buf)
    return w, h


def px(w, ch, pix, x, y):
    i = (y * w + x) * ch
    if ch >= 3:
        return pix[i], pix[i + 1], pix[i + 2]
    v = pix[i]
    return v, v, v


def crop_rgb(path, x0, y0, cw, chh, out):
    w, h, ch, pix = read(path)
    x0, y0 = max(0, x0), max(0, y0)
    cw, chh = min(cw, w - x0), min(chh, h - y0)
    buf = bytearray(cw * chh * 3)
    for y in range(chh):
        for x in range(cw):
            r, g, b = px(w, ch, pix, x0 + x, y0 + y)
            j = (y * cw + x) * 3
            buf[j], buf[j + 1], buf[j + 2] = r, g, b
    write_rgb(out, cw, chh, buf)
    return cw, chh


def hexs(t):
    return "#%02X%02X%02X" % t


def sample(path, x0, y0, rw, rh, top=6):
    """Dominant quantised colours in a rect, plus the reddest dark ink."""
    w, h, ch, pix = read(path)
    counts, darkest, best = {}, None, 1e9
    for y in range(y0, min(y0 + rh, h)):
        for x in range(x0, min(x0 + rw, w)):
            r, g, b = px(w, ch, pix, x, y)
            q = (r // 8 * 8, g // 8 * 8, b // 8 * 8)
            counts[q] = counts.get(q, 0) + 1
            lum = 0.299 * r + 0.587 * g + 0.114 * b
            if lum < 150 and r > g + 12:
                s = lum - (r - g)
                if s < best:
                    best, darkest = s, (r, g, b)
    ranked = sorted(counts.items(), key=lambda kv: -kv[1])[:top]
    lines = ["  %s n=%d" % (hexs(c), n) for c, n in ranked]
    if darkest:
        lines.append("  reddest-dark: %s" % hexs(darkest))
    return "\n".join(lines)
