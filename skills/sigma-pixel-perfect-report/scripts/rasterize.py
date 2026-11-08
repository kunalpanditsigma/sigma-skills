"""Export a Sigma report to PDF and rasterize every page to PNG + JPEG.

Replaces the older shot_report.py, whose `swift` rasterizer no longer compiles on
current macOS Command Line Tools (6.1.2 against a 26.2 SDK). This drives PDFKit
through JXA instead, which needs no toolchain.

Caveat worth knowing: NSImage.TIFFRepresentation captures at the display's
backing scale, so a "1.0" request on a Retina machine yields a 2x PNG. Always
derive the real ratio as `png_width / report_page_width`.

    python3 rasterize.py <reportId> <outDir> [scale]
"""
import pathlib
import subprocess
import sys
import time
import urllib.error
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import sigmaapi as S


def export_pdf(report_id, dest, layout="portrait", parameters=None):
    """`parameters` maps report control ids to values, e.g. {"Client": "Acme"};
    looping over values is how to burst one PDF per recipient."""
    body = {"format": {"type": "pdf", "layout": layout}}
    if parameters:
        body["parameters"] = parameters
    q = S.call("POST", "/v2/reports/%s/export" % report_id, body)
    qid = q.get("queryId") or q.get("exportId")
    print("export queued:", qid)
    for _ in range(120):
        req = urllib.request.Request(
            S.BASE + "/v2/query/%s/download" % qid,
            headers={"Authorization": "Bearer " + S.token(), "Accept": "*/*"})
        try:
            data = urllib.request.urlopen(req, timeout=120).read()
        except urllib.error.HTTPError as exc:
            if exc.code in (404, 409, 425, 500, 502, 503, 504):
                time.sleep(3)
                continue
            raise
        if data:                      # zero bytes means "not ready yet"
            dest.write_bytes(data)
            return len(data)
        time.sleep(3)
    raise SystemExit("export never became ready")


def rasterize(pdf, out, scale="1.0"):
    r = subprocess.run(["osascript", "-l", "JavaScript", str(HERE / "raster.js"),
                        str(pdf), str(out), str(scale)],
                       capture_output=True, text=True)
    print(r.stdout.strip() or r.stderr.strip())
    for p in sorted(out.glob("p*.png")):
        subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "80",
                        "-Z", "1300", str(p), "--out", str(p.with_suffix(".jpg"))],
                       capture_output=True)


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    report_id, out = sys.argv[1], pathlib.Path(sys.argv[2])
    scale = sys.argv[3] if len(sys.argv) > 3 else "1.0"
    out.mkdir(parents=True, exist_ok=True)
    pdf = out / "report.pdf"
    print("pdf bytes:", export_pdf(report_id, pdf))
    rasterize(pdf, out, scale)
    print("pages:", [p.name for p in sorted(out.glob("p*.jpg"))])


if __name__ == "__main__":
    main()
