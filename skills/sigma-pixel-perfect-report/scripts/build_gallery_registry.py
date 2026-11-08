"""Rebuild templates/gallery.json from the annual-reports-gallery site.

The gallery (https://annual-reports-gallery.vercel.app/) reads a Supabase
`entries` table server-side and exposes no anon key, but Next.js serialises the
whole result set into the streamed RSC payload — so the catalogue is recoverable
from the HTML of the /grade page. Cover images themselves live in a PUBLIC
storage bucket and can be fetched directly.

Run this only to refresh the registry; normal use reads the committed JSON.

    python3 build_gallery_registry.py
"""
import json
import pathlib
import re
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE.parent / "templates" / "gallery.json"

PAGE = "https://annual-reports-gallery.vercel.app/grade"
COVERS = "https://xaannolrmzdccxgionbj.supabase.co/storage/v1/object/public/covers/"

KEEP = ("slug", "company", "year", "designer", "title", "source", "elo",
        "matches", "storage_path", "generated_path", "width", "height",
        "source_url")


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")


def recover(html):
    # quotes arrive backslash-escaped inside JS string literals
    text = html.replace('\\"', '"').replace("\\\\", "\\")
    out, seen = [], set()
    for m in re.finditer(r'\{"id":\d+,"slug":"', text):
        start, depth, i, n = m.start(), 0, m.start(), len(text)
        while i < n:
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    i += 1
                    break
            i += 1
        try:
            rec = json.loads(text[start:i])
        except ValueError:
            continue
        if "company" not in rec or rec.get("slug") in seen:
            continue
        seen.add(rec["slug"])
        out.append({k: rec.get(k) for k in KEEP})
    return out


def main():
    entries = recover(fetch(PAGE))
    if not entries:
        raise SystemExit("recovered no entries — the gallery's markup may have changed")
    for e in entries:
        # the restored/generated render is the better source when present
        path = e.get("generated_path") or e.get("storage_path")
        e["cover_url"] = COVERS + path if path else None
    entries.sort(key=lambda e: (-(e.get("elo") or 0), e.get("company") or ""))
    doc = {
        "source": PAGE,
        "covers_base": COVERS,
        "note": ("Each entry is a COVER image, not a full PDF (except the few with "
                 "source_url). A gallery template therefore supplies a design "
                 "system — palette, type feel, cover composition — which the "
                 "builder applies to a full report page set."),
        "count": len(entries),
        "entries": entries,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=1))
    print("wrote %s with %d entries" % (OUT, len(entries)))
    named = [e for e in entries if e.get("designer")]
    print("%d have a named designer" % len(named))


if __name__ == "__main__":
    main()
