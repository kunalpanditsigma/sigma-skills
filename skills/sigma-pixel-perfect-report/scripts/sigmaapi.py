"""Sigma API helper for the pixel-perfect report toolkit.

Reads credentials and org settings from an env file (SIGMA_ENV_FILE, default
~/.sigma-portals/staging.env) and caches the bearer token in
/tmp/.tok_<env file stem> (55-minute TTL), so two orgs never share a token.

Env file keys (a process environment variable of the same name wins):
  SIGMA_CLIENT_ID / SIGMA_CLIENT_SECRET   required
  SIGMA_BASE_URL       API host for your cloud, e.g. https://aws-api.sigmacomputing.com
  SIGMA_FOLDER_ID      folder that receives created reports and temp workbooks
  SIGMA_CONNECTION_ID  warehouse connection for SQL sources and warehouse.query()

Spec bodies wrap everything except `name`/`folderId` in `document`; report
bodies do the same, with `document.kind: report`.
"""

import base64
import json
import os
import pathlib
import time
import urllib.error
import urllib.parse
import urllib.request

ENV_FILE = pathlib.Path(os.environ.get(
    "SIGMA_ENV_FILE",
    str(pathlib.Path.home() / ".sigma-portals" / "staging.env")))
# A cache keyed by the env file keeps a prod build from reusing a staging token
# (the old fixed /tmp/.tok_staging silently pointed prod builds at staging).
TOKEN_CACHE = pathlib.Path(os.environ.get(
    "SIGMA_TOKEN_CACHE", "/tmp/.tok_" + ENV_FILE.stem))
TOKEN_TTL = 55 * 60


def _setting(key, default=None):
    """Process environment first, then the env file, then `default`."""
    if os.environ.get(key):
        return os.environ[key]
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            k, _, v = line.strip().partition("=")
            if k.strip() == key and v.strip():
                return v.strip().strip('"').strip("'")
    return default


BASE = _setting("SIGMA_BASE_URL", "https://api.sigmacomputing.com").rstrip("/")
ORG_ID = _setting("SIGMA_ORG_ID")

# Created reports and the temp workbooks warehouse.query() uses land here.
FOLDER_ID = _setting("SIGMA_FOLDER_ID")

# Pick a connection whose warehouse credentials are live. `verify` does NOT
# resolve SQL, so a bad connection only surfaces on create.
CONNECTION_ID = _setting("SIGMA_CONNECTION_ID")

# Older build scripts import these names.
FOLDER_CLAUDE_BUILDER, CONN_SNOWFLAKE = FOLDER_ID, CONNECTION_ID


def require(name, value):
    """Fail early, naming the env key, instead of sending a null id to the API."""
    if not value:
        raise SigmaError(0, "set %s in the environment or in %s" % (name, ENV_FILE),
                         str(ENV_FILE))
    return value


class SigmaError(RuntimeError):
    """An API call returned a non-2xx status. `body` holds the decoded payload."""

    def __init__(self, status, body, url):
        self.status = status
        self.body = body
        self.url = url
        super().__init__("HTTP %s on %s\n%s" % (status, url, body))


def _read_env():
    if not ENV_FILE.exists():
        raise SigmaError(0, "missing %s" % ENV_FILE, str(ENV_FILE))
    env = {}
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def _fetch_token():
    env = _read_env()
    # staging.env prefixes these; other org env files use the plain names.
    cid = env.get("SIGMA_STAGING_CLIENT_ID") or env["SIGMA_CLIENT_ID"]
    csec = env.get("SIGMA_STAGING_CLIENT_SECRET") or env["SIGMA_CLIENT_SECRET"]
    cred = base64.b64encode(("%s:%s" % (cid, csec)).encode()).decode()
    req = urllib.request.Request(
        BASE + "/v2/auth/token",
        data=urllib.parse.urlencode({"grant_type": "client_credentials"}).encode(),
        headers={
            "Authorization": "Basic " + cred,
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=40) as resp:
        tok = json.load(resp)["access_token"]
    TOKEN_CACHE.write_text(tok)
    os.chmod(TOKEN_CACHE, 0o600)
    return tok


def token():
    """Cached bearer token, refreshed once the cache file ages past the TTL."""
    if TOKEN_CACHE.exists() and time.time() - TOKEN_CACHE.stat().st_mtime < TOKEN_TTL:
        cached = TOKEN_CACHE.read_text().strip()
        if cached:
            return cached
    return _fetch_token()


def call(method, path, body=None, accept="application/json", retry_auth=True):
    """Issue an API call. Returns parsed JSON, or raw text when not JSON."""
    url = BASE + path
    data = None
    headers = {"Authorization": "Bearer " + token(), "Accept": accept}
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            raw = resp.read().decode()
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode()
        # A cached token can expire mid-build; refresh once and replay.
        if exc.code == 401 and retry_auth:
            _fetch_token()
            return call(method, path, body, accept, retry_auth=False)
        try:
            raw = json.dumps(json.loads(raw), indent=2)
        except ValueError:
            pass
        raise SigmaError(exc.code, raw, url) from None
    if not raw:
        return None
    try:
        return json.loads(raw)
    except ValueError:
        return raw


# ---------------------------------------------------------------- workbooks


def verify_workbook(spec):
    return call("POST", "/v2/workbooks/spec/verify", spec)


def create_workbook(spec):
    return call("POST", "/v2/workbooks/spec", spec)


def update_workbook(workbook_id, spec):
    return call("PUT", "/v2/workbooks/%s/spec" % workbook_id, spec)


def get_workbook(workbook_id):
    return call("GET", "/v2/workbooks/%s/spec" % workbook_id)


# ------------------------------------------------------------------ reports


def create_report(spec):
    return call("POST", "/v2/reports/spec", spec)


def update_report(report_id, spec):
    return call("PUT", "/v2/reports/%s/spec" % report_id, spec)


def get_report(report_id):
    return call("GET", "/v2/reports/%s/spec" % report_id)


# ------------------------------------------------------------------ plugins


def register_plugin(name, url, description=""):
    return call(
        "POST",
        "/v2/plugins",
        {"name": name, "url": url, "description": description, "type": "element"},
    )


def list_plugins():
    return call("GET", "/v2/plugins")


def describe(obj, limit=4000):
    """Pretty-print helper for poking at responses from the shell."""
    text = json.dumps(obj, indent=2) if not isinstance(obj, str) else obj
    return text[:limit]


if __name__ == "__main__":
    print("token ok, len", len(token()))
    print(describe(call("GET", "/v2/whoami")))
