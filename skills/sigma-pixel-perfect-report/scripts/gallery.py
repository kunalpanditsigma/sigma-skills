"""Browse and pick templates from the annual-reports-gallery registry.

    python3 gallery.py list --top 20
    python3 gallery.py list --designer "Paul Rand"
    python3 gallery.py list --company IBM
    python3 gallery.py list --decade 1960
    python3 gallery.py suggest "quarterly financials, conservative, navy"
    python3 gallery.py show general-dynamics-1977-ccfac5
    python3 gallery.py fetch general-dynamics-1977-ccfac5 --out ./src
"""
import argparse
import json
import pathlib
import re
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
REGISTRY = HERE.parent / "templates" / "gallery.json"


def load():
    return json.loads(REGISTRY.read_text())


def entries():
    return load()["entries"]


def find(slug):
    for e in entries():
        if e["slug"] == slug:
            return e
    # allow a loose match on company+year
    for e in entries():
        if slug.lower() in (e["slug"] or "").lower():
            return e
    raise SystemExit("no gallery entry matching %r" % slug)


def fmt(e, rank=None):
    bits = "%-44s %s" % ((e.get("company") or "")[:44], e.get("year") or "----")
    if e.get("designer"):
        bits += "  · %s" % e["designer"]
    head = "  " if rank is None else "%3d." % rank
    return "%s %s   [elo %s]  %s" % (head, bits, e.get("elo"), e["slug"])


def cmd_list(a):
    rows = entries()
    if a.designer:
        rows = [e for e in rows
                if a.designer.lower() in (e.get("designer") or "").lower()]
    if a.company:
        rows = [e for e in rows
                if a.company.lower() in (e.get("company") or "").lower()]
    if a.decade:
        rows = [e for e in rows
                if e.get("year") and a.decade <= e["year"] < a.decade + 10]
    if a.year:
        rows = [e for e in rows if e.get("year") == a.year]
    rows = rows[:a.top]
    print("%d entries (registry has %d)\n" % (len(rows), len(entries())))
    for i, e in enumerate(rows, 1):
        print(fmt(e, i))


# Loose keyword -> tone mapping, used only to shortlist candidates for the user
# to confirm. Deliberately simple: the point is a sensible default, not magic.
TONES = {
    "modernist": ("Paul Rand", "Chermayeff & Geismar Associates", "George Tscherny"),
    "corporate": ("IBM", "Xerox", "Westinghouse", "General Dynamics"),
    "industrial": ("General Dynamics", "Boeing", "Litton", "Cummins"),
    "conservative": ("Bond Stores", "American Stores", "Chase"),
    "bold": ("Paul Rand", "Saul Bass"),
}


def cmd_suggest(a):
    q = a.query.lower()
    rows = entries()
    scored = []
    for e in rows:
        s = (e.get("elo") or 1400) / 100.0
        hay = " ".join(str(e.get(k) or "") for k in
                       ("company", "designer", "title", "year")).lower()
        for word in re.findall(r"[a-z]{4,}", q):
            if word in hay:
                s += 6
        for tone, names in TONES.items():
            if tone in q and any(n.lower() in hay for n in names):
                s += 5
        m = re.search(r"(19|20)\d{2}", q)
        if m and e.get("year"):
            s += max(0, 5 - abs(int(m.group()) - e["year"]) / 4.0)
        # `.get(k, 0)` is wrong here: `year` exists but can be null
        if "modern" in q and (e.get("year") or 0) >= 1990:
            s += 3
        if any(w in q for w in ("vintage", "midcentury", "mid-century", "retro")) \
                and 1950 <= (e.get("year") or 0) <= 1975:
            s += 4
        scored.append((s, e))
    scored.sort(key=lambda t: -t[0])
    print("best matches for %r:\n" % a.query)
    for i, (s, e) in enumerate(scored[:a.top], 1):
        print(fmt(e, i))


def cmd_show(a):
    e = find(a.slug)
    print(json.dumps(e, indent=1))


def cmd_fetch(a):
    e = find(a.slug)
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    url = e["cover_url"]
    dest = out / ("%s%s" % (e["slug"], pathlib.Path(url).suffix or ".jpg"))
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    dest.write_bytes(urllib.request.urlopen(req, timeout=60).read())
    print("cover  ->", dest, dest.stat().st_size, "bytes")
    if e.get("source_url"):
        print("this entry also has a full PDF:", e["source_url"])
    print("\nnext: python3 derive_template.py %s --cover %s" % (e["slug"], dest))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("list")
    p.add_argument("--top", type=int, default=25)
    p.add_argument("--designer")
    p.add_argument("--company")
    p.add_argument("--decade", type=int)
    p.add_argument("--year", type=int)
    p.set_defaults(fn=cmd_list)

    p = sub.add_parser("suggest")
    p.add_argument("query")
    p.add_argument("--top", type=int, default=8)
    p.set_defaults(fn=cmd_suggest)

    p = sub.add_parser("show")
    p.add_argument("slug")
    p.set_defaults(fn=cmd_show)

    p = sub.add_parser("fetch")
    p.add_argument("slug")
    p.add_argument("--out", default="./src")
    p.set_defaults(fn=cmd_fetch)

    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
