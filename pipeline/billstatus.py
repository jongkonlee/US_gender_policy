"""GovInfo BILLSTATUS: download per-Congress zips and boil each bill down to a compact record.

Handles both the current schema (<number>/<type>, version 3.x) and the older one
(<billNumber>/<billType>, <billSubjects>)."""
import json
import os
import re
import zipfile
import xml.etree.ElementTree as ET

from common import CACHE, ensure_dir, fetch, log

TYPES = ["hr", "s", "hjres", "sjres", "hconres", "sconres", "hres", "sres"]
BASE = "https://www.govinfo.gov/bulkdata"

ROLL_H = re.compile(r"Roll\s+[Nn]o\.?\s*(\d+)")
ROLL_S = re.compile(r"Record\s+Vote\s+(?:Number|No\.?)\s*:?\s*(\d+)", re.I)


def _t(el, path, default=""):
    if el is None:
        return default
    x = el.find(path)
    if x is None or x.text is None:
        return default
    return x.text.strip()


def _session(congress, date):
    start = 1789 + 2 * (congress - 1)
    try:
        y = int(date[:4])
    except Exception:
        return 0
    return 1 if y <= start else 2


def _votes_from_actions(actions_el, congress):
    """Recorded votes inside an <actions> block: list of dicts (chamber, roll, date, session, text)."""
    out = []
    if actions_el is None:
        return out
    for it in actions_el.iter("item"):
        text = _t(it, "text")
        date = _t(it, "actionDate")
        found = False
        rv = it.find("recordedVotes")
        if rv is not None:
            for v in rv.iter("recordedVote"):
                roll = _t(v, "rollNumber")
                if not roll.isdigit():
                    continue
                ch = _t(v, "chamber")[:1].upper() or "?"
                vdate = (_t(v, "date") or date)[:10]
                sess = _t(v, "sessionNumber")
                out.append(dict(ch=ch, roll=int(roll), date=vdate,
                                sess=int(sess) if sess.isdigit() else _session(congress, vdate), text=text))
                found = True
        if not found and text:
            src = _t(it, "sourceSystem/name")
            m = ROLL_H.search(text)
            if m and ("House" in src or "Roll no" in text):
                out.append(dict(ch="H", roll=int(m.group(1)), date=date[:10], sess=_session(congress, date), text=text))
            else:
                m = ROLL_S.search(text)
                if m:
                    out.append(dict(ch="S", roll=int(m.group(1)), date=date[:10], sess=_session(congress, date), text=text))
    # de-duplicate (same vote is often listed by both chamber systems)
    seen, uniq = set(), []
    for v in out:
        k = (v["ch"], v["roll"], v["sess"])
        if k in seen:
            continue
        seen.add(k)
        uniq.append(v)
    return uniq


def _person(it):
    return dict(b=_t(it, "bioguideId"), p=_t(it, "party"), s=_t(it, "state"), d=_t(it, "district"),
                n=_t(it, "fullName"))


def parse_bill(xml_bytes):
    root = ET.fromstring(xml_bytes)
    bill = root.find("bill")
    if bill is None:
        bill = root
    congress = int(_t(bill, "congress") or 0)
    btype = (_t(bill, "type") or _t(bill, "billType")).lower()
    number = _t(bill, "number") or _t(bill, "billNumber")
    rec = dict(
        id=f"{congress}-{btype}-{number}", c=congress, t=btype, n=int(number) if number.isdigit() else number,
        intro=_t(bill, "introducedDate")[:10], title=_t(bill, "title"),
    )
    titles = []
    for it in bill.findall("titles/item"):
        tt = _t(it, "title")
        if tt and tt not in titles:
            titles.append(tt)
    rec["titles"] = titles
    pa = _t(bill, "policyArea/name") or _t(bill, "subjects/policyArea/name") or _t(bill, "subjects/billSubjects/policyArea/name")
    rec["pa"] = pa
    subj = []
    ls = bill.find("subjects/legislativeSubjects")
    if ls is None:
        ls = bill.find("subjects/billSubjects/legislativeSubjects")
    if ls is not None:
        for it in ls.findall("item"):
            nm = _t(it, "name")
            if nm:
                subj.append(nm)
    rec["subj"] = subj
    sp = bill.find("sponsors/item")
    rec["sp"] = _person(sp) if sp is not None else None
    cs = []
    for it in bill.findall("cosponsors/item"):
        p = _person(it)
        cs.append([p["b"], _t(it, "sponsorshipDate")[:10], 1 if _t(it, "isOriginalCosponsor").lower() == "true" else 0,
                   _t(it, "sponsorshipWithdrawnDate")[:10], p["p"], p["s"], p["d"]])
    rec["cs"] = cs
    rec["votes"] = _votes_from_actions(bill.find("actions"), congress)
    amdts = []
    for a in bill.iter("amendment"):
        av = _votes_from_actions(a.find("actions"), congress)
        if not av:
            continue  # only amendments with recorded votes matter here
        asp = a.find("sponsors/item")
        amdts.append(dict(num=_t(a, "number"), type=_t(a, "type"), desc=_t(a, "description"), purp=_t(a, "purpose"),
                          sp=_t(asp, "bioguideId") if asp is not None else "", votes=av))
    rec["amdts"] = amdts
    rec["latest"] = [_t(bill, "latestAction/actionDate")[:10], _t(bill, "latestAction/text")]
    laws = [f"{_t(it, 'type')} {_t(it, 'number')}".strip() for it in bill.findall("laws/item")]
    rec["law"] = "; ".join(x for x in laws if x)
    rel = []
    for it in bill.findall("relatedBills/item"):
        rt = _t(it, "type").lower()
        rn = _t(it, "number")
        reason = _t(it, "relationshipDetails/item/type")
        if rt and rn:
            rel.append([f"{_t(it, 'congress') or congress}-{rt}-{rn}", reason])
    rec["rel"] = rel
    return rec


def listing(congress, btype):
    url = f"{BASE}/json/BILLSTATUS/{congress}/{btype}"
    raw = fetch(url, binary=False)
    return json.loads(raw)


def zip_url(congress, btype):
    try:
        js = listing(congress, btype)
        for f in js.get("files", []):
            link = f.get("link") or ""
            if link.endswith(".zip"):
                return link
    except Exception as e:  # listing format changed or blocked: fall back to the usual name
        log("listing failed", congress, btype, e)
    return f"{BASE}/BILLSTATUS/{congress}/{btype}/BILLSTATUS-{congress}-{btype}.zip"


def bills_path(congress):
    return os.path.join(CACHE, "bills", f"bills_{congress}.jsonl")


def build_congress(congress, refresh=False, keep_zip=False):
    """Download all bill types of a Congress and write one compact JSONL file."""
    out = bills_path(congress)
    if os.path.exists(out) and not refresh:
        log("bills cached", out)
        return out
    ensure_dir(os.path.dirname(out))
    tmp = out + ".tmp"
    n = 0
    with open(tmp, "w", encoding="utf-8") as fo:
        for bt in TYPES:
            url = zip_url(congress, bt)
            zp = os.path.join(CACHE, "zips", f"BILLSTATUS-{congress}-{bt}.zip")
            log("download", url)
            fetch(url, zp, max_age_hours=0 if refresh else None, timeout=600)
            with zipfile.ZipFile(zp) as z:
                for name in z.namelist():
                    if not name.endswith(".xml"):
                        continue
                    try:
                        rec = parse_bill(z.read(name))
                    except ET.ParseError as e:
                        log("bad xml", name, e)
                        continue
                    fo.write(json.dumps(rec, ensure_ascii=False, separators=(",", ":")) + "\n")
                    n += 1
            if not keep_zip:
                os.remove(zp)
    os.replace(tmp, out)
    log(f"bills {congress}: {n}")
    return out
