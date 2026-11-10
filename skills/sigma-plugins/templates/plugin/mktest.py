"""Build test/index.html: the plugin page plus sample rows injected through window.__load.

    python3 mktest.py site/index.html sample.json        # sample.json = [{"label":..,"group":..,"value":..}, ...]

Get real rows by exporting the feed table to CSV/JSON through the API, so the test
matches what the workbook sends. Then screenshot with shot.sh, at several widths.

URL-hash hooks for headless checks:
  #tab=<name>      click a tab
  #click=<index>   click row <index>; document.title becomes HIT:true if the
                   element under the click point is that row (catches overlays
                   that swallow clicks)
"""
import json
import pathlib
import sys

HOOK = """<script>window.__SAMPLE = %s;</script>
<script>
setTimeout(function () {
  __load(window.__SAMPLE);
  var h = decodeURIComponent(location.hash.slice(1));
  if (h.indexOf("tab=") === 0) { var b = document.querySelector('[data-tab="' + h.slice(4) + '"]'); b && b.click(); }
  if (h.indexOf("click=") === 0) setTimeout(function () {
    var r = document.querySelector('.row[data-i="' + h.slice(6) + '"]'), bb = r.getBoundingClientRect();
    var el = document.elementFromPoint(bb.left + 40, bb.top + bb.height / 2);
    document.title = "HIT:" + (!!el && el.closest(".row") === r);
    el && el.dispatchEvent(new MouseEvent("click", {bubbles: true}));
  }, 900);
}, 50);
</script>
</body>"""


def main():
    page, sample = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    out = pathlib.Path("test")
    out.mkdir(exist_ok=True)
    html = page.read_text().replace("</body>", HOOK % sample.read_text().strip(), 1)
    (out / "index.html").write_text(html)
    print("wrote", out / "index.html", "rows:", len(json.loads(sample.read_text())))


if __name__ == "__main__":
    main()
