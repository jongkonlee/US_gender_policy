"""District and state characteristics for each Congress.

- Rural share: decennial census urban/rural population, re-tabulated to each set of district lines.
- Demographics: ACS 1-year detailed tables (race/ethnicity, bachelor's degree, median household income).
- Partisan lean: Cook PVI formula (since 2022) recomputed from presidential results by district
  (The Downballot) and by state (FEC official results).
"""
import csv
import io
import json
import os
import re
import urllib.parse

from common import CACHE, STATE_ABBR_FIPS, STATE_FIPS, ensure_dir, fetch, log

CENSUS = "https://api.census.gov/data"

# Congress -> (dataset, total, urban, rural); 2010 SF1 "congressional district" = 111th Congress lines.
RURAL_CD = {
    111: ("2010/dec/sf1", "P002001", "P002002", "P002005"),
    112: ("2010/dec/sf1", "P002001", "P002002", "P002005"),
    113: ("2010/dec/cd113", "P002001", "P002002", "P002005"),
    114: ("2010/dec/cd113", "P002001", "P002002", "P002005"),
    115: ("2010/dec/cd115", "P002001", "P002002", "P002005"),
    116: ("2010/dec/cd116", "P002001", "P002002", "P002005"),
    117: ("2010/dec/cd116", "P002001", "P002002", "P002005"),  # NC lines changed for 2020: flagged
    118: ("2020/dec/cd118", "P2_001N", "P2_002N", "P2_003N"),
    119: ("2020/dec/cd119", "P2_001N", "P2_002N", "P2_003N"),
    120: ("2020/dec/cd119", "P2_001N", "P2_002N", "P2_003N"),  # states redrawn for 2026: flagged
}
RURAL_STATE = {2010: ("2010/dec/sf1", "P002001", "P002002", "P002005"),
               2020: ("2020/dec/dhc", "P2_001N", "P2_002N", "P2_003N")}
# district lines that do not match the census file for that Congress
LINES_MISMATCH = {117: {"NC"}}

ACS_YEAR = {111: 2009, 112: 2011, 113: 2013, 114: 2015, 115: 2017, 116: 2019, 117: 2021, 118: 2023, 119: 2024, 120: 2024}

# The Downballot presidential results by congressional district (Google Sheets IDs)
DKE = {
    "2006": "1l7W130tPRF6dQ4JoqlQJSJexnEg4rZct-7kwDXqgoLE",  # 2008 results, 2006-2010 lines
    "2012": "1xn6nCNM97oFDZ4M-HQgoUT3X4paOiSDsRMSuxbaOBdg",  # 2008, 2012 results, 2012-2014 lines
    "2016": "1VfkHtzBTP5gf4jAu8tcVQgsBJ1IDvXEHjuMqYlOgYbA",  # 2008-2016 results, 2016 lines
    "2018": "1zLNAuRqPauss00HDz4XbTH2HqsCzMe0pR8QmD1K8jk8",  # 2008-2016 results, 2018 lines
    "2020": "1XbUXnI9OyfAuhP5P3vWtMuGc5UJlrhXbzZo3AwMuHtk",  # 2008-2020 results, 2020 lines
    "2022": "1CKngqOp8fzU22JOlypoxNsxL6KSAH920Whc-rd7ebuM",  # 2020 results, 2022 lines
    "2024": "1ng1i_Dm_RMDnEvauH44pgE6JCUsapcuu8F2pCfeLWFo",  # 2020, 2024 results, 2024 lines
    "2026": "1eZfaFI-c-PFOoKx1-zZA2MP0_dxRq_LVK0re3BOQqy0",  # 2024 results, 2026 lines
}
LINES = {111: "2006", 112: "2006", 113: "2012", 114: "2012", 115: "2016", 116: "2018", 117: "2020",
         118: "2022", 119: "2024", 120: "2026"}

# FEC official national totals (D, R), candidate totals incl. fusion lines
NATIONAL = {
    2004: (59028444, 62040610), 2008: (69498516, 59948323), 2012: (65915795, 60933504),
    2016: (65853514, 62984828), 2020: (81283501, 74223975), 2024: (75017613, 77302580),
}
FEC_STATE_FILES = {
    2004: "https://www.fec.gov/documents/1628/2004pres.xls",
    2008: "https://www.fec.gov/documents/1661/2008pres.xls",
    2012: "https://www.fec.gov/documents/1684/2012pres.xls",
    2016: "https://www.fec.gov/documents/1890/federalelections2016.xlsx",
    2020: "https://www.fec.gov/documents/4228/federalelections2020.xlsx",
    2024: "https://www.fec.gov/documents/5645/2024presgeresults.xlsx",
}
CAND = {2008: ("obama", "mccain"), 2012: ("obama", "romney"), 2016: ("clinton", "trump"),
        2020: ("biden", "trump"), 2024: ("harris", "trump"), 2004: ("kerry", "bush")}

STATE_NAMES = {
    "ALABAMA": "AL", "ALASKA": "AK", "ARIZONA": "AZ", "ARKANSAS": "AR", "CALIFORNIA": "CA", "COLORADO": "CO",
    "CONNECTICUT": "CT", "DELAWARE": "DE", "DISTRICT OF COLUMBIA": "DC", "FLORIDA": "FL", "GEORGIA": "GA",
    "HAWAII": "HI", "IDAHO": "ID", "ILLINOIS": "IL", "INDIANA": "IN", "IOWA": "IA", "KANSAS": "KS",
    "KENTUCKY": "KY", "LOUISIANA": "LA", "MAINE": "ME", "MARYLAND": "MD", "MASSACHUSETTS": "MA",
    "MICHIGAN": "MI", "MINNESOTA": "MN", "MISSISSIPPI": "MS", "MISSOURI": "MO", "MONTANA": "MT",
    "NEBRASKA": "NE", "NEVADA": "NV", "NEW HAMPSHIRE": "NH", "NEW JERSEY": "NJ", "NEW MEXICO": "NM",
    "NEW YORK": "NY", "NORTH CAROLINA": "NC", "NORTH DAKOTA": "ND", "OHIO": "OH", "OKLAHOMA": "OK",
    "OREGON": "OR", "PENNSYLVANIA": "PA", "RHODE ISLAND": "RI", "SOUTH CAROLINA": "SC", "SOUTH DAKOTA": "SD",
    "TENNESSEE": "TN", "TEXAS": "TX", "UTAH": "UT", "VERMONT": "VT", "VIRGINIA": "VA", "WASHINGTON": "WA",
    "WEST VIRGINIA": "WV", "WISCONSIN": "WI", "WYOMING": "WY",
}
STATES51 = set(STATE_NAMES.values())


def census_get(dataset, get, geo_for, geo_in=None):
    q = {"get": ",".join(get), "for": geo_for}
    if geo_in:
        q["in"] = geo_in
    key = os.environ.get("CENSUS_API_KEY")
    if key:
        q["key"] = key
    url = f"{CENSUS}/{dataset}?" + urllib.parse.urlencode(q, safe=":*,")
    tag = re.sub(r"[^A-Za-z0-9]+", "_", dataset + "_" + geo_for + "_" + get[1])[:120]
    dest = os.path.join(CACHE, "census", tag + ".json")
    fetch(url, dest)
    with open(dest, encoding="utf-8") as f:
        rows = json.load(f)
    head = rows[0]
    return [dict(zip(head, r)) for r in rows[1:]]


def _cd_key(state_fips, cd):
    st = STATE_FIPS.get(state_fips)
    if not st:
        return None
    if cd in ("00", "98", "ZZ") or not cd.isdigit():
        return (st, 0)
    return (st, int(cd))


def normalize_keys(d):
    """At-large states: any district number -> 0."""
    per = {}
    for (st, n) in d:
        per.setdefault(st, set()).add(n)
    return {(st, 0 if len(per[st]) == 1 else n): v for (st, n), v in d.items()}


def rural_districts(congress):
    ds, tot, urb, rur = RURAL_CD[congress]
    rows = census_get(ds, ["NAME", tot, urb, rur], "congressional district:*", "state:*")
    out = {}
    for r in rows:
        k = _cd_key(r["state"], r["congressional district"])
        if not k or k[1] == 0 and r["congressional district"] == "ZZ":
            continue
        t = float(r[tot] or 0)
        if t > 0:
            out[k] = round(100 * float(r[rur] or 0) / t, 2)
    return normalize_keys(out)


def rural_states(congress):
    ds, tot, urb, rur = RURAL_STATE[2020 if congress >= 118 else 2010]
    rows = census_get(ds, ["NAME", tot, urb, rur], "state:*")
    out = {}
    for r in rows:
        st = STATE_FIPS.get(r["state"])
        t = float(r[tot] or 0)
        if st and t > 0:
            out[st] = round(100 * float(r[rur] or 0) / t, 2)
    return out


ACS_VARS = ["B01003_001E", "B03002_001E", "B03002_003E", "B03002_004E", "B03002_006E", "B03002_012E", "B19013_001E"]
EDU_NEW = ["B15003_001E", "B15003_022E", "B15003_023E", "B15003_024E", "B15003_025E"]
EDU_OLD = ["B15002_001E", "B15002_015E", "B15002_016E", "B15002_017E", "B15002_018E",
           "B15002_032E", "B15002_033E", "B15002_034E", "B15002_035E"]


def _acs_row(r, year):
    def f(k):
        try:
            v = float(r.get(k))
        except (TypeError, ValueError):
            return None
        return None if v < 0 else v  # ACS uses negative codes for missing
    tot = f("B03002_001E")
    out = dict(pop=f("B01003_001E"))
    if tot:
        out.update(white_nh=round(100 * f("B03002_003E") / tot, 1), black_nh=round(100 * f("B03002_004E") / tot, 1),
                   asian_nh=round(100 * f("B03002_006E") / tot, 1), hisp=round(100 * f("B03002_012E") / tot, 1))
    inc = f("B19013_001E")
    out["med_income"] = int(inc) if inc else None
    if year >= 2012:
        base = f("B15003_001E")
        ba = sum(f(k) or 0 for k in EDU_NEW[1:])
    else:
        base = f("B15002_001E")
        ba = sum(f(k) or 0 for k in EDU_OLD[1:])
    out["ba_plus"] = round(100 * ba / base, 1) if base else None
    out["acs_year"] = year
    return out


def acs(congress, level):
    year = ACS_YEAR[congress]
    get = ["NAME"] + ACS_VARS + (EDU_NEW if year >= 2012 else EDU_OLD)
    if level == "cd":
        rows = census_get(f"{year}/acs/acs1", get, "congressional district:*", "state:*")
        out = {}
        for r in rows:
            k = _cd_key(r["state"], r["congressional district"])
            if k:
                out[k] = _acs_row(r, year)
        return normalize_keys(out)
    rows = census_get(f"{year}/acs/acs1", get, "state:*")
    return {STATE_FIPS[r["state"]]: _acs_row(r, year) for r in rows if r["state"] in STATE_FIPS}


# ---------- presidential results ----------

def _rows_from_workbook(path):
    """Yield (sheet_name, rows) for every sheet in an xls/xlsx file."""
    if path.endswith(".xls"):
        import xlrd
        wb = xlrd.open_workbook(path)
        for sh in wb.sheets():
            yield sh.name, [sh.row_values(i) for i in range(sh.nrows)]
    else:
        import openpyxl
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        for ws in wb.worksheets:
            yield ws.title, [list(r) for r in ws.iter_rows(values_only=True)]


def _num(x):
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x).strip().replace(",", "").replace("%", "")
    try:
        return float(s)
    except ValueError:
        return None


def state_results(year):
    """{state: (D votes, R votes)} from the FEC official results, found by matching national totals."""
    url = FEC_STATE_FILES[year]
    dest = os.path.join(CACHE, "fec", os.path.basename(url))
    fetch(url, dest)
    nd, nr = NATIONAL[year]
    for name, rows in _rows_from_workbook(dest):
        srows = {}
        for r in rows:
            cells = [c for c in r if c not in (None, "")]
            if not cells:
                continue
            first = str(cells[0]).strip().upper().rstrip("*").strip()
            st = first if first in STATES51 else STATE_NAMES.get(first)
            if st and st not in srows:
                srows[st] = r
        if len(srows) < 51:
            continue
        width = max(len(r) for r in srows.values())
        sums = []
        for j in range(width):
            s = 0.0
            ok = True
            for r in srows.values():
                v = _num(r[j]) if j < len(r) else None
                if v is None:
                    ok = False
                    break
                s += v
            sums.append(s if ok else None)
        dcol = [j for j, s in enumerate(sums) if s is not None and abs(s - nd) <= max(5, nd * 0.0005)]
        rcol = [j for j, s in enumerate(sums) if s is not None and abs(s - nr) <= max(5, nr * 0.0005)]
        if dcol and rcol:
            out = {st: (_num(r[dcol[0]]), _num(r[rcol[0]])) for st, r in srows.items()}
            log(f"FEC {year}: sheet '{name}', D col {dcol[0]}, R col {rcol[0]}")
            return out
    raise RuntimeError(f"FEC {year}: no sheet with state totals matching the national totals")


DIST_RE = re.compile(r"^([A-Z]{2})[- ]?(AL|\d{1,2})$")


def district_results(lines):
    """{(state, district): {year: two-party D share (0-100)}} from The Downballot workbook."""
    sid = DKE[lines]
    dest = os.path.join(CACHE, "dke", f"dke_{lines}.xlsx")
    fetch(f"https://docs.google.com/spreadsheets/d/{sid}/export?format=xlsx", dest)
    best = None
    for name, rows in _rows_from_workbook(dest):
        parsed = _parse_dke_sheet(rows)
        if parsed and (best is None or parsed[1] > best[1]):
            best = (parsed[0], parsed[1], name)
    if not best:
        raise RuntimeError(f"Downballot {lines}: no usable sheet")
    log(f"Downballot {lines}: sheet '{best[2]}', {len(best[0])} districts, score {best[1]}")
    return normalize_keys(best[0])


D_NAMES = {"obama", "clinton", "biden", "harris", "kerry"}
R_NAMES = {"mccain", "romney", "trump", "bush"}
PAIR_YEAR = {("obama", "mccain"): 2008, ("obama", "romney"): 2012, ("clinton", "trump"): 2016,
             ("biden", "trump"): 2020, ("harris", "trump"): 2024, ("kerry", "bush"): 2004}


def _parse_dke_sheet(rows):
    hdr = None
    for i, r in enumerate(rows[:15]):
        if any(str(c).strip().lower() == "district" for c in r if c is not None):
            hdr = i
            break
    if hdr is None:
        return None
    # candidate names: in the header row or the next one
    cand_row = None
    for i in (hdr, hdr + 1):
        if i < len(rows) and any(str(c).strip().lower() in D_NAMES for c in rows[i] if c is not None):
            cand_row = i
            break
    if cand_row is None:
        return None
    names = [str(c).strip().lower() if c is not None else "" for c in rows[cand_row]]
    pairs = []
    for j, n in enumerate(names):
        if n in D_NAMES:
            for k in range(j + 1, min(j + 3, len(names))):
                if names[k] in R_NAMES:
                    y = PAIR_YEAR.get((n, names[k]))
                    if y:
                        pairs.append((y, j, k))
                    break
    if not pairs:
        return None
    dcol = [str(c).strip().lower() if c is not None else "" for c in rows[hdr]].index("district")
    out = {}
    raw_votes = False
    for r in rows[cand_row + 1:]:
        if dcol >= len(r) or r[dcol] is None:
            continue
        m = DIST_RE.match(str(r[dcol]).strip().upper())
        if not m:
            continue
        st, d = m.group(1), m.group(2)
        key = (st, 0 if d == "AL" else int(d))
        vals = {}
        for y, j, k in pairs:
            dv, rv = _num(r[j]) if j < len(r) else None, _num(r[k]) if k < len(r) else None
            if dv is None or rv is None or dv + rv <= 0:
                continue
            if dv > 100 or rv > 100:
                raw_votes = True
            vals[y] = 100 * dv / (dv + rv)
        if vals:
            out[key] = vals
    score = len(out) * 10 + (5 if raw_votes else 0)
    return out, score


def lean(shares, years):
    """Cook PVI formula (2022-): 0.75*(latest - nation) + 0.25*(previous - nation). Positive = Democratic."""
    def nat(y):
        d, r = NATIONAL[y]
        return 100 * d / (d + r)
    have = [y for y in years if y in shares]
    if not have:
        return None, []
    if len(have) >= 2:
        y1, y0 = have[0], have[1]
        v = 0.75 * (shares[y1] - nat(y1)) + 0.25 * (shares[y0] - nat(y0))
        return round(v, 2), [y1, y0]
    y = have[0]
    return round(shares[y] - nat(y), 2), [y]


PVI_YEARS = {111: [2008, 2004], 112: [2008, 2004], 113: [2012, 2008], 114: [2012, 2008], 115: [2016, 2012],
             116: [2016, 2012], 117: [2020, 2016], 118: [2020, 2016], 119: [2024, 2020], 120: [2024, 2020]}


def pvi_districts(congress, dke_cache):
    lines = LINES[congress]
    if lines not in dke_cache:
        dke_cache[lines] = district_results(lines)
    res = dke_cache[lines]
    years = PVI_YEARS[congress]
    if congress == 120:  # 2020 results only on 2024 lines: reuse where a state's lines did not change
        if "2024" not in dke_cache:
            dke_cache["2024"] = district_results("2024")
        old = dke_cache["2024"]
        same = _unchanged_states(res, old, 2024)
        res = {k: dict(v, **({2020: old[k][2020]} if k[0] in same and k in old and 2020 in old[k] else {}))
               for k, v in res.items()}
    out = {}
    for k, shares in res.items():
        v, used = lean(shares, years)
        if v is not None:
            out[k] = dict(pvi=v, pvi_years=used)
    return out


def _unchanged_states(new, old, year):
    by = {}
    for (st, d), v in new.items():
        by.setdefault(st, []).append(((st, d), v))
    same = set()
    for st, items in by.items():
        if all(k in old and year in old[k] and year in v and abs(old[k][year] - v[year]) < 0.05 for k, v in items):
            same.add(st)
    return same


def pvi_states(congress, fec_cache):
    years = PVI_YEARS[congress]
    shares = {}
    for y in years:
        if y not in fec_cache:
            fec_cache[y] = state_results(y)
        for st, (d, r) in fec_cache[y].items():
            if d and r:
                shares.setdefault(st, {})[y] = 100 * d / (d + r)
    out = {}
    for st, s in shares.items():
        v, used = lean(s, years)
        out[st] = dict(pvi=v, pvi_years=used)
    return out


def build(congress, caches):
    """Return dict with 'cd' {(st,d): attrs} and 'state' {st: attrs} plus notes."""
    notes = []
    cd, stt = {}, {}

    def merge(target, src, label):
        for k, v in src.items():
            target.setdefault(k, {}).update(v if isinstance(v, dict) else {label: v})

    for label, fn, target in (("rural", lambda: rural_districts(congress), cd),
                              ("rural", lambda: rural_states(congress), stt)):
        try:
            merge(target, fn(), label)
        except Exception as e:
            notes.append(f"rural {congress}: {e}")
            log("WARN", notes[-1])
    for level, target in (("cd", cd), ("state", stt)):
        try:
            merge(target, acs(congress, level), "acs")
        except Exception as e:
            notes.append(f"acs {congress} {level}: {e}")
            log("WARN", notes[-1])
    try:
        merge(cd, pvi_districts(congress, caches.setdefault("dke", {})), "pvi")
    except Exception as e:
        notes.append(f"pvi districts {congress}: {e}")
        log("WARN", notes[-1])
    try:
        merge(stt, pvi_states(congress, caches.setdefault("fec", {})), "pvi")
    except Exception as e:
        notes.append(f"pvi states {congress}: {e}")
        log("WARN", notes[-1])
    for st in LINES_MISMATCH.get(congress, ()):
        for k in list(cd):
            if k[0] == st:
                cd[k]["lines_note"] = "census_lines_differ"
    return dict(cd=cd, state=stt, notes=notes)
