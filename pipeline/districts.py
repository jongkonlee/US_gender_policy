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

WWW2 = "https://www2.census.gov"
UR2020 = WWW2 + "/geo/docs/maps-data/data/rel2020/cd-sld/CD{n}_UR_POPAREA.txt"
UR2010 = WWW2 + "/geo/relfiles/{folder}/{fips}/ur_cd_delim_{fips}.txt"
UR_STATE_2010 = WWW2 + "/geo/docs/reference/ua/PctUrbanRural_State.txt"
UR_STATE_2020 = WWW2 + "/geo/docs/reference/ua/State_Urban_Rural_Pop_2020_2010.xlsx"
ZCTA_CD111 = WWW2 + "/geo/docs/maps-data/data/rel/zcta_cd111_rel_10.txt"
UA_ZCTA_2010 = WWW2 + "/geo/docs/reference/ua/ua_zcta_rel_10.txt"
ACS_TABLE = WWW2 + "/programs-surveys/acs/summary_file/{y}/table-based-SF/data/1YRData/acsdt1y{y}-{t}.dat"

# district lines that do not match the census file used for that Congress
LINES_MISMATCH = {117: {"NC"}}
# Congress -> ACS 1-year vintage tabulated on (nearly) the same district lines
ACS_YEAR = {111: 2009, 112: 2011, 113: 2013, 114: 2015, 115: 2017, 116: 2019, 117: 2021, 118: 2023, 119: 2024, 120: 2024}
US_POP = {2010: 308745538, 2020: 331449281}
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
    "D.C.": "DC", "D. C.": "DC", "DIST. OF COL.": "DC", "DIST. OF COLUMBIA": "DC", "DISTRICT OF COL.": "DC",
    "WASHINGTON DC": "DC", "WASHINGTON, D.C.": "DC",
}
STATES51 = set(STATE_NAMES.values())


def _text(url, tag):
    dest = os.path.join(CACHE, "census", tag)
    fetch(url, dest, timeout=300)
    with open(dest, encoding="utf-8-sig", errors="replace") as f:
        return f.read()


def _csv_rows(txt, delim=","):
    return list(csv.reader(io.StringIO(txt), delimiter=delim))


def _cd_key(state_fips, cd):
    st = STATE_FIPS.get(state_fips)
    if not st:
        return None
    cd = str(cd).strip()
    if cd in ("00", "98", "ZZ", "AL") or not cd.isdigit():
        return (st, 0)
    return (st, int(cd))


def normalize_keys(d):
    """At-large states: any district number -> 0."""
    per = {}
    for (st, n) in d:
        per.setdefault(st, set()).add(n)
    return {(st, 0 if len(per[st]) == 1 else n): v for (st, n), v in d.items()}


_UR_FAILS = []


def _ur2010_state_file(folder, fips):
    url = UR2010.format(folder=folder, fips=fips)
    try:
        txt = _text(url, f"ur_{folder}_{fips}.txt")
    except Exception as e:
        if folder == "cdsld13" or "404" not in str(e):
            _UR_FAILS.append(f"{folder}/{fips}: {e}")
            if len(_UR_FAILS) <= 3:
                log("WARN urban/rural file", url, e)
        return None  # this state has no file for these lines (lines unchanged)
    out = {}
    rows = _csv_rows(txt)
    if not rows or "TotalPop" not in ",".join(rows[0]):
        return None
    h = rows[0]
    i_st, i_cd, i_t, i_r = h.index("State"), h.index("CongressionalDistrict"), h.index("TotalPop"), h.index("RuralPop")
    for r in rows[1:]:
        if len(r) <= i_r or not r[i_t].strip().isdigit():
            continue
        k = _cd_key(r[i_st].zfill(2), r[i_cd])
        t = float(r[i_t])
        if k and t > 0:
            out[k] = dict(rural=round(100 * float(r[i_r]) / t, 2), pop10=int(t))
    return out


def rural_districts(congress):
    """{(st, d): {'rural': pct}} for the district lines of a Congress."""
    if congress >= 118:
        n = 118 if congress == 118 else 119
        rows = _csv_rows(_text(UR2020.format(n=n), f"CD{n}_UR_POPAREA.txt"))
        out = {}
        for r in rows[1:]:
            if len(r) < 6 or not r[1].strip().isdigit():
                continue
            geoid = r[0].strip()
            k = _cd_key(geoid[:2], geoid[2:4])
            t = float(r[1])
            if k and t > 0:
                out[k] = dict(rural=round(100 * float(r[4]) / t, 2), ur_src=f"2020 Census, {n}th CD")
        return normalize_keys(out)
    if congress >= 113:
        out = {}
        folders = ["cdsld13"] + (["cdsld16"] if congress >= 115 else []) + (["cdsld18"] if congress >= 116 else [])
        for folder in folders:
            for fips in sorted(STATE_FIPS):
                if fips in ("60", "66", "69", "78"):
                    continue
                res = _ur2010_state_file(folder, fips)
                if not res:
                    continue
                st = STATE_FIPS[fips]
                for k in [k for k in out if k[0] == st]:
                    del out[k]  # newer lines replace older ones for this state
                for k, v in res.items():
                    v["ur_src"] = f"2010 Census, {folder}"
                    out[k] = v
        if len(out) < 400:
            raise RuntimeError(f"urban/rural 2010 files: only {len(out)} districts ({'; '.join(_UR_FAILS[:3])})")
        return normalize_keys(out)
    return rural_districts_zcta111()


def rural_districts_zcta111():
    """111th-112th lines: no official district file, so estimate from ZCTA pieces (2010 Census):
    rural population of each ZCTA (total minus urban-area parts) allocated to districts by population."""
    zurban, zpop = {}, {}
    rows = _csv_rows(_text(UA_ZCTA_2010, "ua_zcta_rel_10.txt"))
    h = rows[0]
    iz, ip, izp, iua = h.index("ZCTA5"), h.index("POPPT"), h.index("ZPOP"), h.index("UA")
    for r in rows[1:]:
        if len(r) <= izp or r[iz] == "99999" or r[iua] == "99999":  # 99999 = not in an urban area
            continue
        zurban[r[iz]] = zurban.get(r[iz], 0) + float(r[ip] or 0)
        zpop[r[iz]] = float(r[izp] or 0)
    rows = _csv_rows(_text(ZCTA_CD111, "zcta_cd111_rel_10.txt"))
    h = rows[0]
    iz, ist, icd, ip = h.index("ZCTA5"), h.index("STATE"), h.index("CD"), h.index("POPPT")
    tot, rur = {}, {}
    for r in rows[1:]:
        if len(r) <= ip:
            continue
        k = _cd_key(r[ist].zfill(2), r[icd])
        if not k:
            continue
        p = float(r[ip] or 0)
        z = r[iz]
        share_rural = 1.0
        if zpop.get(z):
            share_rural = max(0.0, 1 - zurban.get(z, 0) / zpop[z])
        tot[k] = tot.get(k, 0) + p
        rur[k] = rur.get(k, 0) + p * share_rural
    out = {k: dict(rural=round(100 * rur[k] / tot[k], 2), ur_src="2010 Census, ZCTA estimate")
           for k in tot if tot[k] > 0}
    return normalize_keys(out)


def rural_states(congress):
    year = 2020 if congress >= 118 else 2010
    if year == 2010:
        rows = _csv_rows(_text(UR_STATE_2010, "PctUrbanRural_State.txt"))
        h = [x.strip().upper() for x in rows[0]]
        i_st, i_t, i_r = h.index("STATE"), h.index("POP_ST"), h.index("POP_RURAL")
        out = {}
        for r in rows[1:]:
            if len(r) > i_r and r[i_st].strip().zfill(2) in STATE_FIPS:
                t = float(r[i_t])
                out[STATE_FIPS[r[i_st].strip().zfill(2)]] = dict(rural=round(100 * float(r[i_r]) / t, 2), ur_src="2010 Census")
        return out
    dest = os.path.join(CACHE, "census", "State_Urban_Rural_Pop_2020_2010.xlsx")
    fetch(UR_STATE_2020, dest)
    for name, rows in _rows_from_workbook(dest):
        res = _parse_state_ur(rows, "2020")
        if res:
            return res
    raise RuntimeError("state urban/rural 2020: layout not recognized")


def _parse_state_ur(rows, year):
    """Find the 2020 total and rural population columns by header text, check against the US total."""
    hdr_rows = rows[:8]
    width = max(len(r) for r in rows[:60]) if rows else 0
    labels = []
    for j in range(width):
        lab = " ".join(str(r[j]) for r in hdr_rows if j < len(r) and r[j] is not None).lower()
        labels.append(lab)
    srows = {}
    for r in rows:
        cells = [c for c in r if c not in (None, "")]
        if not cells:
            continue
        first = str(cells[0]).strip().upper()
        st = first if first in STATES51 else STATE_NAMES.get(first)
        if not st and len(cells) > 1:
            second = str(cells[1]).strip().upper()
            st = second if second in STATES51 else STATE_NAMES.get(second)
        if st and st not in srows:
            srows[st] = r
    if len(srows) < 51:
        return None

    def colsum(j):
        s = 0.0
        for r in srows.values():
            v = _num(r[j]) if j < len(r) else None
            if v is None:
                return None
            s += v
        return s
    tot_cols = [j for j in range(width) if year in labels[j] and colsum(j) and abs(colsum(j) - US_POP[int(year)]) / US_POP[int(year)] < 0.01]
    rur_cols = [j for j in range(width) if year in labels[j] and "rural" in labels[j] and "%" not in labels[j]
                and "pct" not in labels[j] and "percent" not in labels[j] and colsum(j) and 0.1 < colsum(j) / US_POP[int(year)] < 0.3]
    if not tot_cols or not rur_cols:
        return None
    jt, jr = tot_cols[0], rur_cols[0]
    log(f"state urban/rural {year}: total col {jt} '{labels[jt][:40]}', rural col {jr} '{labels[jr][:40]}'")
    return {st: dict(rural=round(100 * _num(r[jr]) / _num(r[jt]), 2), ur_src=f"{year} Census") for st, r in srows.items()}


ACS_TABLES = ["b01003", "b03002", "b19013"]


def _acs_table(year, table):
    url = ACS_TABLE.format(y=year, t=table)
    txt = _text(url, f"acsdt1y{year}-{table}.dat")
    rows = _csv_rows(txt, "|")
    h = rows[0]
    return h, rows[1:]


ACS_BASE = WWW2 + "/programs-surveys/acs/summary_file/{y}/data"
_ACS_SEQ_CACHE = {}


def _acs_needed(year):
    v = ["B01003_001", "B03002_001", "B03002_003", "B03002_004", "B03002_006", "B03002_012", "B19013_001"]
    if year >= 2012:
        v += ["B15003_001", "B15003_022", "B15003_023", "B15003_024", "B15003_025"]
    else:
        v += ["B15002_001"] + [f"B15002_{i:03d}" for i in (15, 16, 17, 18, 32, 33, 34, 35)]
    return v


def _first_row(data, name):
    if name.lower().endswith(".xls"):
        import xlrd
        sh = xlrd.open_workbook(file_contents=data).sheet_by_index(0)
        return sh.row_values(0) if sh.nrows else []
    import openpyxl
    wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True)
    for r in wb.worksheets[0].iter_rows(max_row=1, values_only=True):
        return list(r)
    return []


def acs_seq(year):
    """ACS 1-year estimates for 2009-2019 from the sequence-based Summary File (files per state).
    Returns {'cd': {(st, d): row}, 'state': {st: row}}."""
    if year in _ACS_SEQ_CACHE:
        return _ACS_SEQ_CACHE[year]
    import zipfile
    base = ACS_BASE.format(y=year)
    tz = os.path.join(CACHE, "acs", f"{year}_1yr_templates.zip")
    fetch(f"{base}/{year}_1yr_Summary_FileTemplates.zip", tz, timeout=300)
    need = set(_acs_needed(year))
    pos = {}
    with zipfile.ZipFile(tz) as z:
        for name in z.namelist():
            m = re.search(r"seq(?:uence)?[_ ]?(\d+)\.xlsx?$", os.path.basename(name), re.I)
            if not m:
                continue
            seq = int(m.group(1))
            for j, lab in enumerate(_first_row(z.read(name), name)):
                mm = re.match(r"^([BC]\d{5}[A-Z]?)_?e?(\d+)$", str(lab or "").strip())
                if mm:
                    key = f"{mm.group(1)}_{int(mm.group(2)):03d}"
                    if key in need:
                        pos[key] = (seq, j)
    missing = need - set(pos)
    if missing:
        raise RuntimeError(f"ACS {year}: variables not found in templates: {sorted(missing)[:5]}")
    html = fetch(f"{base}/1_year_seq_by_state/", binary=False)
    folders = sorted(set(re.findall(r'href="([A-Za-z]+)/"', html)))
    names = {k.replace(" ", "").lower(): v for k, v in STATE_NAMES.items()}
    names.update({"districtofcolumbia": "DC", "puertorico": "PR"})
    seqs = sorted({s for s, _ in pos.values()})
    cd, stt = {}, {}
    for folder in folders:
        st = folder.upper() if len(folder) == 2 else names.get(folder.lower())
        if not st or st == "US":
            continue
        stl = st.lower()
        try:
            gtxt = _text(f"{base}/1_year_seq_by_state/{folder}/g{year}1{stl}.csv", f"acs_g{year}1{stl}.csv")
        except Exception as e:
            log("ACS geo missing", year, st, e)
            continue
        want = {}
        for r in _csv_rows(gtxt):
            if len(r) < 5 or r[3] != "00" or r[2] not in ("500", "040"):
                continue
            geoid = next((c for c in r if re.match(r"^\d{3}[0-9A-Z]{2,4}US\d+$", c or "")), "")
            if r[2] == "500" and geoid:
                k = _cd_key(geoid[-4:-2], geoid[-2:])
                if k:
                    want[r[4]] = ("cd", k)
            elif r[2] == "040":
                want[r[4]] = ("state", st)
        vals = {lr: {} for lr in want}
        for seq in seqs:
            url = f"{base}/1_year_seq_by_state/{folder}/{year}1{stl}{seq:04d}000.zip"
            zp = os.path.join(CACHE, "acs", f"{year}1{stl}{seq:04d}000.zip")
            try:
                fetch(url, zp, timeout=300)
            except Exception as e:
                log("ACS seq missing", year, st, seq, e)
                continue
            with zipfile.ZipFile(zp) as z:
                ef = [n for n in z.namelist() if os.path.basename(n).lower().startswith("e")]
                if not ef:
                    continue
                txt = z.read(ef[0]).decode("latin-1")
            cols = [(k, j) for k, (s, j) in pos.items() if s == seq]
            for r in _csv_rows(txt):
                if len(r) > 5 and r[5] in vals:
                    for k, j in cols:
                        if j < len(r):
                            vals[r[5]][k.replace("_", "_") + "E"] = r[j]
        for lr, (lvl, key) in want.items():
            row = _acs_row(vals[lr], year)
            (cd if lvl == "cd" else stt)[key] = row
    log(f"ACS {year} (sequence files): {len(cd)} districts, {len(stt)} states")
    _ACS_SEQ_CACHE[year] = dict(cd=normalize_keys(cd), state=stt)
    return _ACS_SEQ_CACHE[year]


def acs(congress, level):
    """ACS 1-year estimates: table-based Summary File (2021 onward) or sequence files (2009-2019)."""
    year = ACS_YEAR[congress]
    if year < 2021:
        return acs_seq(year)["cd" if level == "cd" else "state"]
    vals = {}
    for t in ACS_TABLES + (["b15003"]):
        h, rows = _acs_table(year, t)
        gi = h.index("GEO_ID")
        for r in rows:
            g = r[gi]
            if level == "cd" and g.startswith("500"):
                key = _cd_key(g[-4:-2], g[-2:])
            elif level == "state" and g.startswith("0400000US"):
                key = STATE_FIPS.get(g[-2:])
            else:
                continue
            if not key:
                continue
            d = vals.setdefault(key, {})
            for j, col in enumerate(h):
                if "_E" in col and j < len(r):
                    d[col.replace("_E", "_").upper() + "E"] = r[j]
    out = {k: _acs_row(v, year) for k, v in vals.items()}
    return normalize_keys(out) if level == "cd" else out


def _acs_row(r, year):
    def f(k):
        try:
            v = float(r.get(k))
        except (TypeError, ValueError):
            return None
        return None if v < 0 else v  # negative = missing
    tot = f("B03002_001E")
    out = dict(pop=f("B01003_001E"))
    if tot:
        out.update(white_nh=round(100 * (f("B03002_003E") or 0) / tot, 1), black_nh=round(100 * (f("B03002_004E") or 0) / tot, 1),
                   asian_nh=round(100 * (f("B03002_006E") or 0) / tot, 1), hisp=round(100 * (f("B03002_012E") or 0) / tot, 1))
    inc = f("B19013_001E")
    out["med_income"] = int(inc) if inc else None
    if year >= 2012:
        base = f("B15003_001E")
        ba = sum(f(k) or 0 for k in ("B15003_022E", "B15003_023E", "B15003_024E", "B15003_025E"))
    else:
        base = f("B15002_001E")
        ba = sum(f(f"B15002_{i:03d}E") or 0 for i in (15, 16, 17, 18, 32, 33, 34, 35))
    out["ba_plus"] = round(100 * ba / base, 1) if base else None
    out["acs_year"] = year
    return out


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
    best, diag = None, []
    for name, rows in _rows_from_workbook(dest):
        srows = {}
        for r in rows:
            cells = [c for c in r if c not in (None, "")]
            if not cells:
                continue
            first = re.sub(r"\s+", " ", str(cells[0]).strip().upper().rstrip("*").strip())
            st = first if first in STATES51 else STATE_NAMES.get(first)
            if st and st not in srows:
                srows[st] = r
        diag.append(f"{name}:{len(srows)} states")
        if len(srows) < 50:
            continue
        width = max(len(r) for r in srows.values())
        sums = []
        for j in range(width):
            s, ok = 0.0, True
            for r in srows.values():
                v = _num(r[j]) if j < len(r) else None
                if v is None:
                    ok = False
                    break
                s += v
            sums.append(s if ok else None)
        for j, s in enumerate(sums):
            if s is None:
                continue
            for k, s2 in enumerate(sums):
                if s2 is None or k == j:
                    continue
                err = abs(s - nd) / nd + abs(s2 - nr) / nr
                if best is None or err < best[0]:
                    best = (err, name, j, k, srows)
    if best and best[0] < 0.01:
        err, name, j, k, srows = best
        log(f"FEC {year}: sheet '{name}', D col {j}, R col {k}, {len(srows)} states, total error {err:.5f}")
        return {st: (_num(r[j]), _num(r[k])) for st, r in srows.items()}
    for name, rows in _rows_from_workbook(dest):
        res = _fec_long(rows, year)
        if res:
            log(f"FEC {year}: long-format sheet '{name}'")
            return res
    raise RuntimeError(f"FEC {year}: no state table matching national totals ({'; '.join(diag)[:300]}; best {best[0] if best else None})")


def _fec_long(rows, year):
    """Long format: one row per candidate and party line in each state."""
    dname, rname = CAND[year]
    nd, nr = NATIONAL[year]
    hdr = None
    for i, r in enumerate(rows[:12]):
        cells = [str(c).strip().upper() if c is not None else "" for c in r]
        if any("LAST NAME" in c for c in cells) and any(c.startswith("GENERAL") for c in cells):
            hdr = (i, cells)
            break
    if not hdr:
        return None
    i0, cells = hdr
    def col(pred):
        for j, c in enumerate(cells):
            if pred(c):
                return j
        return None
    j_st = col(lambda c: c in ("STATE ABBREVIATION", "STATE ABBR", "STATE_ABBREVIATION")) or col(lambda c: c == "STATE")
    j_last = col(lambda c: c == "LAST NAME" or c.startswith("LAST NAME"))
    j_party = col(lambda c: c == "PARTY")
    j_val = col(lambda c: c in ("GENERAL RESULTS", "GENERAL VOTES") or c == "GENERAL")
    if None in (j_st, j_last, j_val):
        return None
    lines = {}
    for r in rows[i0 + 1:]:
        if len(r) <= max(j_st, j_last, j_val):
            continue
        st_raw = str(r[j_st] or "").strip().upper()
        st = st_raw if st_raw in STATES51 else STATE_NAMES.get(st_raw)
        last = str(r[j_last] or "").strip().lower()
        v = _num(r[j_val])
        if not st or v is None or last not in (dname, rname):
            continue
        party = str(r[j_party] or "").strip().lower() if j_party is not None and j_party < len(r) else ""
        lines.setdefault((st, last), []).append((party, v))
    def total(ls, mode):
        comb = [v for p, v in ls if "combined" in p]
        if mode == "combined" and comb:
            return max(comb)
        return sum(v for p, v in ls if "combined" not in p)
    for mode in ("combined", "sum"):
        out = {}
        for (st, last), ls in lines.items():
            d, r_ = out.get(st, (0.0, 0.0))
            t = total(ls, mode)
            out[st] = (d + t, r_) if last == dname else (d, r_ + t)
        sd, sr = sum(v[0] for v in out.values()), sum(v[1] for v in out.values())
        if len(out) >= 51 and abs(sd - nd) / nd < 0.002 and abs(sr - nr) / nr < 0.002:
            return out
    return None


DIST_RE = re.compile(r"^([A-Z]{2})[- ]?(AL|\d{1,2})$")


def district_results(lines):
    """{(state, district): {year: two-party D share (0-100)}} from The Downballot workbook."""
    sid = DKE[lines]
    dest = os.path.join(CACHE, "dke", f"dke_{lines}.xlsx")
    fetch(f"https://docs.google.com/spreadsheets/d/{sid}/export?format=xlsx", dest)
    sheets = []
    for name, rows in _rows_from_workbook(dest):
        parsed = _parse_dke_sheet(rows)
        if parsed and len(parsed[0]) >= 400:
            sheets.append((parsed[1], name, parsed[0]))
    if not sheets:
        raise RuntimeError(f"Downballot {lines}: no usable sheet")
    # vote-count sheets first (exact), then percentage sheets fill in missing years
    sheets.sort(key=lambda x: -x[0])
    out, used = {}, []
    for raw, name, res in sheets:
        used.append(f"{name}({'votes' if raw else 'pct'})")
        for k, v in res.items():
            cur = out.setdefault(k, {})
            for y, s in v.items():
                cur.setdefault(y, s)
    log(f"Downballot {lines}: {len(out)} districts from {', '.join(used)}")
    return normalize_keys(out)


D_NAMES = {"obama", "clinton", "biden", "harris", "kerry", "gore"}
R_NAMES = {"mccain", "romney", "trump", "bush"}
PAIR_YEAR = {("obama", "mccain"): 2008, ("obama", "romney"): 2012, ("clinton", "trump"): 2016,
             ("biden", "trump"): 2020, ("harris", "trump"): 2024, ("kerry", "bush"): 2004, ("gore", "bush"): 2000}


def _parse_dke_sheet(rows):
    hdr = None
    for i, r in enumerate(rows[:15]):
        if any(str(c).strip().lower() in ("district", "cd") for c in r if c is not None):
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
    hcells = [str(c).strip().lower() if c is not None else "" for c in rows[hdr]]
    dcol = hcells.index("district") if "district" in hcells else hcells.index("cd")
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
    return out, (1 if raw_votes else 0)


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
    transient = bool(notes)
    return dict(cd=cd, state=stt, notes=notes, transient=transient)
