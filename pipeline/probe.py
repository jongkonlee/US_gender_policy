"""Connectivity and format check for every data source. Writes a report to probe/report.json."""
import json
import os
import sys
import time
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import billstatus  # noqa: E402
import districts  # noqa: E402
import legislators  # noqa: E402
import voteview  # noqa: E402
from common import ROOT, ensure_dir  # noqa: E402

OUT = ensure_dir(os.path.join(ROOT, "probe"))
report = {}


def step(name, fn):
    t = time.time()
    try:
        res = fn()
        report[name] = dict(ok=True, sec=round(time.time() - t, 1), result=res)
    except Exception as e:
        report[name] = dict(ok=False, sec=round(time.time() - t, 1), error=repr(e), tb=traceback.format_exc()[-1500:])
    print(name, json.dumps(report[name], ensure_ascii=False, default=str)[:1500], flush=True)


def vv():
    rolls, mem, votes = voteview.load("H", 119)
    return dict(rolls=len(rolls), members=len(mem), votes=sum(len(v) for v in votes.values()),
                sample_roll=rolls[-1], sample_member=mem[0])


def bs_listing():
    js = billstatus.listing(119, "hjres")
    files = js.get("files", [])
    return dict(keys=list(js.keys()), n=len(files), first=files[:2], zips=[f for f in files if str(f.get("link", "")).endswith(".zip")][:2])


def bs_zip():
    p = billstatus.build_congress(119, refresh=True) if os.environ.get("PROBE_FULL") else None
    if p:
        return p
    # small type only
    import zipfile
    from common import CACHE, fetch
    url = billstatus.zip_url(119, "hjres")
    zp = os.path.join(CACHE, "zips", "probe-119-hjres.zip")
    fetch(url, zp)
    recs = []
    with zipfile.ZipFile(zp) as z:
        for name in z.namelist():
            if name.endswith(".xml"):
                recs.append(billstatus.parse_bill(z.read(name)))
    voted = [r for r in recs if r["votes"]]
    with open(os.path.join(OUT, "bs_sample.json"), "w", encoding="utf-8") as f:
        json.dump(recs[:3] + voted[:3], f, ensure_ascii=False, indent=1)
    return dict(url=url, size=os.path.getsize(zp), bills=len(recs), with_votes=len(voted),
                with_cosponsors=sum(1 for r in recs if r["cs"]), with_subjects=sum(1 for r in recs if r["subj"]),
                sample=voted[0] if voted else recs[0])


def bs_one():
    from common import fetch
    xml = fetch("https://www.govinfo.gov/bulkdata/BILLSTATUS/118/hr/BILLSTATUS-118hr7.xml")
    with open(os.path.join(OUT, "BILLSTATUS-118hr7.xml"), "wb") as f:
        f.write(xml)
    r = billstatus.parse_bill(xml)
    r["cs"] = r["cs"][:3]
    return r


def leg():
    p = legislators.load()
    return dict(n=len(p))


def rural(c):
    d = districts.rural_districts(c)
    return dict(n=len(d), sample=dict(list((f"{k[0]}-{k[1]}", v) for k, v in d.items())[:5]))


def rural_st(c):
    d = districts.rural_states(c)
    return dict(n=len(d), sample=dict(list(d.items())[:5]))


def acs(c, level):
    d = districts.acs(c, level)
    return dict(n=len(d), sample={f"{k}": v for k, v in list(d.items())[:3]})


def dke(lines):
    d = districts.district_results(lines)
    return dict(n=len(d), sample={f"{k[0]}-{k[1]}": v for k, v in list(d.items())[:6]})


def fec(y):
    d = districts.state_results(y)
    return dict(n=len(d), sample=dict(list(d.items())[:5]))


def dke_sheets(lines):
    from common import CACHE
    dest = os.path.join(CACHE, "dke", f"dke_{lines}.xlsx")
    out = {}
    for name, rows in districts._rows_from_workbook(dest):
        out[name] = [[str(c) for c in r[:12]] for r in rows[:6]]
    return out


if __name__ == "__main__":
    step("voteview_H119", vv)
    step("billstatus_listing", bs_listing)
    step("billstatus_zip_hjres", bs_zip)
    step("billstatus_118hr7", bs_one)
    step("legislators", leg)
    for c in (111, 113, 115, 116, 118, 119):
        step(f"rural_cd_{c}", lambda c=c: rural(c))
    step("rural_state_111", lambda: rural_st(111))
    step("rural_state_119", lambda: rural_st(119))
    for c in (111, 113, 119):
        step(f"acs_cd_{c}", lambda c=c: acs(c, "cd"))
    step("acs_state_119", lambda: acs(119, "state"))
    for lines in ("2006", "2012", "2022", "2024", "2026"):
        step(f"downballot_{lines}", lambda lines=lines: dke(lines))
        step(f"downballot_sheets_{lines}", lambda lines=lines: dke_sheets(lines))
    for y in (2004, 2008, 2016, 2024):
        step(f"fec_{y}", lambda y=y: fec(y))
    with open(os.path.join(OUT, "report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1, default=str)
    print("done", sum(1 for v in report.values() if v["ok"]), "/", len(report))
