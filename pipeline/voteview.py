"""Voteview roll calls, members and individual votes for one Congress and chamber."""
import csv
import io
import os

from common import CACHE, fetch, log

BASE = "https://voteview.com/static/data/out"


def _num(x):
    """Voteview sometimes writes integers as '200.0'."""
    if x is None or x == "":
        return None
    try:
        f = float(x)
    except ValueError:
        return None
    return int(f) if f.is_integer() else f


def _csv(kind, chamber, congress, refresh):
    name = f"{chamber}{congress}_{kind}.csv"
    dest = os.path.join(CACHE, "voteview", name)
    fetch(f"{BASE}/{kind}/{name}", dest, max_age_hours=20 if refresh else None, timeout=300)
    with open(dest, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load(chamber, congress, refresh=False):
    """Return (rollcalls, members, votes). chamber is 'H' or 'S'."""
    rc = _csv("rollcalls", chamber, congress, refresh)
    mem = _csv("members", chamber, congress, refresh)
    vt = _csv("votes", chamber, congress, refresh)
    rolls = []
    for r in rc:
        rolls.append(dict(
            roll=_num(r["rollnumber"]), clerk=_num(r.get("clerk_rollnumber")), date=r["date"], sess=_num(r["session"]),
            yea=_num(r["yea_count"]), nay=_num(r["nay_count"]), bill=(r.get("bill_number") or "").strip(),
            result=r.get("vote_result", ""), desc=r.get("vote_desc", ""), question=r.get("vote_question", ""),
            dtl=r.get("dtl_desc", ""), mid1=_num(r.get("nominate_mid_1")), mid2=_num(r.get("nominate_mid_2")),
            sp1=_num(r.get("nominate_spread_1")), sp2=_num(r.get("nominate_spread_2")),
        ))
    members = []
    for m in mem:
        if m.get("chamber") == "President":
            continue
        members.append(dict(
            icpsr=_num(m["icpsr"]), bioguide=m.get("bioguide_id", ""), state=m.get("state_abbrev", ""),
            district=_num(m.get("district_code")), party=_num(m.get("party_code")), name=m.get("bioname", ""),
            born=_num(m.get("born")), dw1=_num(m.get("nominate_dim1")), dw2=_num(m.get("nominate_dim2")),
            np1=_num(m.get("nokken_poole_dim1")), occupancy=_num(m.get("occupancy")),
        ))
    votes = {}
    for v in vt:
        votes.setdefault(_num(v["rollnumber"]), {})[_num(v["icpsr"])] = _num(v["cast_code"])
    log(f"voteview {chamber}{congress}: {len(rolls)} roll calls, {len(members)} members")
    return rolls, members, votes


# cast_code: 1-3 yea, 4-6 nay, 7-9 not voting / present, 0 not a member
def cast_simple(code):
    if code in (1, 2, 3):
        return 1
    if code in (4, 5, 6):
        return 2
    if code in (7, 8, 9):
        return 3
    return 0


PARTY = {100: "D", 200: "R", 328: "I", 329: "I", 370: "I", 380: "I"}


def party_letter(code):
    return PARTY.get(code, "I" if code else "")
