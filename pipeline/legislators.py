"""congress-legislators (github.com/unitedstates/congress-legislators): name, gender, birthday, terms."""
import datetime as dt
import os

import yaml

from common import CACHE, congress_end, congress_start, fetch, log

RAW = "https://raw.githubusercontent.com/unitedstates/congress-legislators/main/"
FILES = ["legislators-current.yaml", "legislators-historical.yaml"]


def load(refresh=False):
    people = {}
    for f in FILES:
        dest = os.path.join(CACHE, "legislators", f)
        fetch(RAW + f, dest, max_age_hours=20 if refresh else None)
        with open(dest, encoding="utf-8") as fh:
            data = yaml.load(fh, Loader=getattr(yaml, "CSafeLoader", yaml.SafeLoader))
        for p in data:
            b = p["id"].get("bioguide")
            if b:
                people[b] = p
    log(f"legislators: {len(people)} people")
    return people


def _d(s):
    return dt.date.fromisoformat(s)


def served_congresses(p, chamber):
    """Set of Congress numbers in which the person served in chamber ('H'/'S')."""
    typ = "rep" if chamber == "H" else "sen"
    out = set()
    for t in p.get("terms", []):
        if t["type"] != typ:
            continue
        s, e = _d(t["start"]), _d(t["end"])
        c = (s.year - 1789) // 2 + 1
        if s < congress_start(c):
            c -= 1
        while congress_start(c) < e:
            a, b = congress_start(c), congress_end(c)
            if (min(e, b) - max(s, a)).days > 0:
                out.add(c)
            c += 1
    return out


def profile(p, congress, chamber):
    """Person attributes as of the start of a Congress."""
    bio = p.get("bio", {})
    name = p.get("name", {})
    start = congress_start(congress)
    age = None
    if bio.get("birthday"):
        b = _d(bio["birthday"])
        age = start.year - b.year - ((start.month, start.day) < (b.month, b.day))
    served_h = served_congresses(p, "H")
    served_s = served_congresses(p, "S")
    # number of Congresses served in this chamber up to and including this one
    n_ch = len([c for c in (served_h if chamber == "H" else served_s) if c <= congress])
    # Senate terms started up to this Congress
    sen_terms = len([t for t in p.get("terms", []) if t["type"] == "sen" and _d(t["start"]) < congress_end(congress)])
    first = min([_d(t["start"]) for t in p.get("terms", [])] or [start])
    years = max(0.0, round((start - first).days / 365.25, 1))
    return dict(
        name=name.get("official_full") or f"{name.get('first', '')} {name.get('last', '')}".strip(),
        last=name.get("last", ""), first=name.get("first", ""),
        gender=bio.get("gender", ""), birthday=bio.get("birthday", ""), age=age,
        n_congress_chamber=n_ch, sen_terms=sen_terms if chamber == "S" else None,
        years_in_congress=years, prior_house=1 if (chamber == "S" and any(c < congress for c in served_h)) else 0,
        icpsr_cl=p["id"].get("icpsr"),
    )
