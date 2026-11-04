"""Shared helpers: paths, Congress dates, downloads with cache and retry."""
import datetime as dt
import gzip
import io
import json
import os
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.environ.get("GP_CACHE", os.path.join(ROOT, "cache"))
CONFIG = os.path.join(ROOT, "config")
OUT = os.path.join(ROOT, "docs", "data")

FIRST_CONGRESS = 111
UA = "US_gender_policy-tracker/1.0 (+https://github.com/jongkonlee/US_gender_policy)"


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def congress_start(c):
    """Congress c runs from Jan 3 of its first year to Jan 3 two years later."""
    y = 1789 + 2 * (c - 1)
    return dt.date(y, 1, 3)


def congress_end(c):
    return congress_start(c + 1)


def congress_of(d):
    if isinstance(d, str):
        d = dt.date.fromisoformat(d[:10])
    c = (d.year - 1789) // 2 + 1
    if d < congress_start(c):
        c -= 1
    return c


def current_congress(today=None):
    return congress_of(today or dt.date.today())


def election_year(c):
    """General election that chose Congress c (e.g., 119 -> 2024)."""
    return congress_start(c).year - 1


def ensure_dir(p):
    os.makedirs(p, exist_ok=True)
    return p


def fetch(url, dest=None, max_age_hours=None, retries=4, timeout=120, binary=True):
    """Download url (to dest if given). Reuse dest if younger than max_age_hours."""
    if dest and os.path.exists(dest) and os.path.getsize(dest) > 0:
        if max_age_hours is None:
            return dest
        age = (time.time() - os.path.getmtime(dest)) / 3600
        if age < max_age_hours:
            return dest
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = r.read()
                if r.headers.get("Content-Encoding") == "gzip":
                    data = gzip.decompress(data)
            if dest:
                ensure_dir(os.path.dirname(dest))
                tmp = dest + ".part"
                with open(tmp, "wb") as f:
                    f.write(data)
                os.replace(tmp, dest)
                return dest
            return data if binary else data.decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (404, 410):
                raise
        except Exception as e:  # network hiccup
            last = e
        time.sleep(2 * (i + 1))
    raise RuntimeError(f"download failed: {url}: {last}")


def read_json(p, default=None):
    if not os.path.exists(p):
        return default
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def write_json(p, obj, compact=True):
    ensure_dir(os.path.dirname(p))
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        if compact:
            json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
        else:
            json.dump(obj, f, ensure_ascii=False, indent=1)
    os.replace(tmp, p)


def read_jsonl(p):
    with open(p, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


STATE_FIPS = {
    "01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA", "08": "CO", "09": "CT", "10": "DE",
    "11": "DC", "12": "FL", "13": "GA", "15": "HI", "16": "ID", "17": "IL", "18": "IN", "19": "IA",
    "20": "KS", "21": "KY", "22": "LA", "23": "ME", "24": "MD", "25": "MA", "26": "MI", "27": "MN",
    "28": "MS", "29": "MO", "30": "MT", "31": "NE", "32": "NV", "33": "NH", "34": "NJ", "35": "NM",
    "36": "NY", "37": "NC", "38": "ND", "39": "OH", "40": "OK", "41": "OR", "42": "PA", "44": "RI",
    "45": "SC", "46": "SD", "47": "TN", "48": "TX", "49": "UT", "50": "VT", "51": "VA", "53": "WA",
    "54": "WV", "55": "WI", "56": "WY", "60": "AS", "66": "GU", "69": "MP", "72": "PR", "78": "VI",
}
STATE_ABBR_FIPS = {v: k for k, v in STATE_FIPS.items()}
TERRITORIES = {"DC", "PR", "GU", "VI", "AS", "MP"}

# Census regions (used as a simple extra comparison)
REGION = {}
for s in "CT ME MA NH RI VT NJ NY PA".split():
    REGION[s] = "Northeast"
for s in "IL IN MI OH WI IA KS MN MO NE ND SD".split():
    REGION[s] = "Midwest"
for s in "DE DC FL GA MD NC SC VA WV AL KY MS TN AR LA OK TX".split():
    REGION[s] = "South"
for s in "AZ CO ID MT NV NM UT WY AK CA HI OR WA".split():
    REGION[s] = "West"


def die(msg):
    log("ERROR:", msg)
    sys.exit(1)
