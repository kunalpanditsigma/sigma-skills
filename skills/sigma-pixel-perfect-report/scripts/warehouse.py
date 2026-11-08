"""Run SQL against a Sigma connection at BUILD time and get rows back.

Reports export as PDF only, and there is no generic "run this SQL" REST endpoint,
so this creates a throwaway WORKBOOK holding the query, exports its element as
CSV, parses it, and deletes the workbook.

Why bother: typeset ledger typography (dot leaders, italic-caps totals, per-row
rules) needs the figures as text at build time — a bound table renders live but
has no per-row styling. This closes that gap, so a report can look typeset AND
carry real warehouse numbers.

    from warehouse import query
    rows = query("SELECT 1 AS N, 'x' AS L", ["N", "L"])
    # -> [{"N": "1", "L": "x"}]
"""
import csv
import io
import pathlib
import sys
import time
import urllib.error
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import sigmaapi as S


def _download(query_id, timeout=240):
    deadline = time.time() + timeout
    while time.time() < deadline:
        req = urllib.request.Request(
            S.BASE + "/v2/query/%s/download" % query_id,
            headers={"Authorization": "Bearer " + S.token(), "Accept": "*/*"})
        try:
            data = urllib.request.urlopen(req, timeout=120).read()
        except urllib.error.HTTPError as exc:
            if exc.code in (404, 409, 425, 500, 502, 503, 504):
                time.sleep(2)
                continue
            raise
        if data:
            return data.decode("utf-8", "replace")
        time.sleep(2)
    raise SystemExit("query %s never became ready" % query_id)


def _delete(wid):
    """Bin the throwaway workbook.

    It must go through /v2/files/{id}: DELETE /v2/workbooks/{id} 404s. Getting
    this wrong is how 51 "TEMP warehouse query" workbooks accumulated in one
    afternoon — the 404 was swallowed by a bare except, so every build silently
    left one behind. Failures are reported now rather than hidden.
    """
    try:
        S.call("DELETE", "/v2/files/%s" % wid)
        return True
    except S.SigmaError as exc:
        print("WARNING: could not delete temp workbook %s (HTTP %s). "
              "Delete it by hand or these will pile up." % (wid, exc.status))
        return False


def query(sql, columns, connection_id=None, folder_id=None, keep=False):
    """Execute `sql` and return a list of dicts keyed by `columns`.

    `columns` are the SQL output column names, in the order you want them.
    """
    conn = S.require("SIGMA_CONNECTION_ID", connection_id or S.CONNECTION_ID)
    folder = S.require("SIGMA_FOLDER_ID", folder_id or S.FOLDER_ID)
    cols = [{"id": "c%d" % i, "formula": "[Custom SQL/%s]" % name, "name": name}
            for i, name in enumerate(columns)]
    spec = {
        "name": "TEMP warehouse query (safe to delete)",
        "folderId": folder,
        "document": {
            "schemaVersion": 1, "kind": "workbook",
            "elements": [{
                "id": "q", "kind": "table", "name": "Q",
                "source": {"kind": "sql", "statement": sql, "connectionId": conn},
                "columns": cols,
                "order": [c["id"] for c in cols],
            }],
            "pages": [{"id": "p1", "name": "P"}],
            # workbooks lay out on a 24-column grid (reports use absolute x/y),
            # and gridColumn/gridRow are required attributes here
            "layout": ('<?xml version="1.0" encoding="utf-8"?>'
                       '<Page id="p1"><Element elementId="q" '
                       'gridColumn="1 / 25" gridRow="1 / 13"/></Page>'),
        },
    }
    wb = S.create_workbook(spec)
    wid = wb.get("workbookId") or wb.get("id")
    try:
        r = S.call("POST", "/v2/workbooks/%s/export" % wid,
                   {"elementId": "q", "format": {"type": "csv"}})
        raw = _download(r.get("queryId") or r.get("exportId"))
        rows = list(csv.DictReader(io.StringIO(raw)))
        return rows
    finally:
        if not keep:
            _delete(wid)


def num(row, key, default=0.0):
    """CSV comes back as strings; coerce a cell to float, tolerating $ and commas."""
    v = (row.get(key) or "").replace(",", "").replace("$", "").strip()
    if not v:
        return default
    try:
        return float(v)
    except ValueError:
        return default


if __name__ == "__main__":
    sql = sys.argv[1] if len(sys.argv) > 1 else "SELECT 1 AS N, 'hello' AS L"
    cols = sys.argv[2].split(",") if len(sys.argv) > 2 else ["N", "L"]
    for r in query(sql, cols)[:20]:
        print(r)
