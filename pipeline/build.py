"""Build the tracker's data files (docs/data/*.json).

  python pipeline/build.py                 # current Congress (and previous one in January-March)
  python pipeline/build.py --congress 118 119
  python pipeline/build.py --all           # 111th to current
"""
import argparse
import collections
import csv
import datetime as dt
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import billstatus  # noqa: E402
import classify as C  # noqa: E402
import districts  # noqa: E402
import legislators  # noqa: E402
import voteview  # noqa: E402
from common import (CONFIG, FIRST_CONGRESS, OUT, REGION, ROOT, TERRITORIES, congress_end, congress_start,  # noqa: E402
                    current_congress, log, read_json, read_jsonl, write_json)

DIST_DIR = os.path.join(ROOT, "data", "districts")
TYPE_LABEL = {"hr": "H.R.", "s": "S.", "hres": "H.Res.", "sres": "S.Res.", "hjres": "H.J.Res.", "sjres": "S.J.Res.",
              "hconres": "H.Con.Res.", "sconres": "S.Con.Res."}
TYPE_URL = {"hr": "house-bill", "s": "senate-bill", "hres": "house-resolution", "sres": "senate-resolution",
            "hjres": "house-joint-resolution", "sjres": "senate-joint-resolution",
            "hconres": "house-concurrent-resolution", "sconres": "senate-concurrent-resolution"}
VV_BILL = re.compile(r"^(HCONRES|SCONRES|HJRES|SJRES|HRES|SRES|HR|S)(\d+)$")
RULE_BILLS = re.compile(r"\((H\.\s?R\.|S\.|H\.\s?J\.\s?Res\.|S\.\s?J\.\s?Res\.|H\.\s?Res\.|S\.\s?Res\.|H\.\s?Con\.\s?Res\.|S\.\s?Con\.\s?Res\.)\s?(\d+)\)", re.I)
RULE_TYPE = {"h.r.": "hr", "s.": "s", "h.j.res.": "hjres", "s.j.res.": "sjres", "h.res.": "hres", "s.res.": "sres",
             "h.con.res.": "hconres", "s.con.res.": "sconres"}


def ordinal(n):
    return f"{n}{'th' if 11 <= n % 100 <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def bill_url(c, t, n):
    return f"https://www.congress.gov/bill/{ordinal(c)}-congress/{TYPE_URL[t]}/{n}"


def load_csv(name):
    p = os.path.join(CONFIG, name)
    if not os.path.exists(p):
        return []
    with open(p, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def config_maps():
    race = {}
    for r in load_csv("race.csv"):
        codes = "".join(c for c, k in (("B", "black"), ("H", "hispanic"), ("A", "asian_pi"), ("N", "native_american"))
                        if str(r.get(k, "0")).strip() == "1")
        race[r["bioguide"]] = dict(codes=codes, note=r.get("note", ""), conf=r.get("confidence", ""))
    religion = {}
    for r in load_csv("religion.csv"):
        religion[(r["bioguide"], int(r["congress"]))] = r.get("religion_group") or r.get("religion_detail", "")
    caucus = collections.defaultdict(set)
    for r in load_csv("caucus_members.csv"):
        try:
            caucus[(r["bioguide"], int(r["congress"]))].add(r["caucus"])
        except (KeyError, ValueError):
            pass
    caucus_complete = set()
    for r in load_csv("caucus_availability.csv"):
        if r.get("list_available") == "yes":
            try:
                caucus_complete.add((r["caucus"], int(r["congress"])))
            except ValueError:
                pass
    factions = collections.defaultdict(set)
    for r in load_csv("factions.csv"):
        try:
            factions[(r["bioguide"], int(r["congress"]))].add(r["faction"])
        except (KeyError, ValueError):
            pass
    return dict(race=race, religion=religion, caucus=caucus, caucus_complete=caucus_complete, factions=factions)


def district_attrs(congress, refresh=False):
    """District/state characteristics, cached in data/districts/{congress}.json (rarely change)."""
    p = os.path.join(DIST_DIR, f"{congress}.json")
    cached = read_json(p)
    if cached and not refresh and not cached.get("transient"):
        return cached
    caches = {}
    res = districts.build(congress, caches)
    out = dict(congress=congress, built=dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
               cd={f"{k[0]}-{k[1]}": v for k, v in res["cd"].items()}, state=res["state"], notes=res["notes"],
               transient=res["transient"])
    # keep values from an older run when a source failed this time
    if cached:
        for lvl in ("cd", "state"):
            for k, v in cached.get(lvl, {}).items():
                cur = out[lvl].setdefault(k, {})
                for kk, vv in v.items():
                    cur.setdefault(kk, vv)
    write_json(p, out, compact=False)
    return out


def term_in_congress(p, congress, chamber):
    typ = "rep" if chamber == "H" else "sen"
    a, b = congress_start(congress), congress_end(congress)
    terms = []
    for t in p.get("terms", []):
        if t["type"] != typ:
            continue
        s, e = dt.date.fromisoformat(t["start"]), dt.date.fromisoformat(t["end"])
        if s < b and e > a and (min(e, b) - max(s, a)).days > 0:
            terms.append(t)
    return terms


def party_code(name):
    n = (name or "").lower()
    if n.startswith("democrat"):
        return "D"
    if n.startswith("republican"):
        return "R"
    return "I"


def build_roster(congress, chamber, people, vmembers, cfg, dist):
    vv_by_bg = {m["bioguide"]: m for m in vmembers if m.get("bioguide")}
    roster = []
    for b, p in people.items():
        terms = term_in_congress(p, congress, chamber)
        if not terms:
            continue
        last = terms[-1]
        prof = legislators.profile(p, congress, chamber)
        party = party_code(last.get("party"))
        caucus = party_code(last.get("caucus")) if last.get("caucus") else party
        if party == "I" and caucus == "I":
            caucus = {"Sanders": "D", "King": "D", "Sinema": "D", "Lieberman": "D"}.get(prof["last"], "I")
        st = last["state"]
        d = int(last.get("district", 0) or 0) if chamber == "H" else None
        start = max(dt.date.fromisoformat(terms[0]["start"]), congress_start(congress))
        end = min(dt.date.fromisoformat(last["end"]), congress_end(congress))
        vm = vv_by_bg.get(b, {})
        race = cfg["race"].get(b, {})
        m = dict(b=b, n=prof["name"], last=prof["last"], p=party, pc=caucus, st=st, g=prof["gender"], age=prof["age"],
                 nc=prof["n_congress_chamber"], yrs=prof["years_in_congress"], race=race.get("codes", ""),
                 reg=REGION.get(st, ""), dl=1 if st in TERRITORIES else 0,
                 fr=str(start), to=str(end), icpsr=vm.get("icpsr") or prof.get("icpsr_cl"),
                 dw1=vm.get("dw1"), dw2=vm.get("dw2"))
        if chamber == "H":
            m["d"] = d
            if prof.get("prior_house") is not None:
                pass
        else:
            m["st_terms"] = prof.get("sen_terms")
            m["ph"] = prof.get("prior_house")
        rel = cfg["religion"].get((b, congress))
        if rel:
            m["rel"] = rel
        cau = sorted(cfg["caucus"].get((b, congress), set()))
        if cau:
            m["cau"] = cau
        fac = sorted(cfg["factions"].get((b, congress), set()))
        if fac:
            m["fac"] = fac
        # district (House) or state (Senate) characteristics
        if chamber == "H":
            a = dist["cd"].get(f"{st}-{d}") or {}
            if not a and d == 0 or (a and "rural" not in a and d == 0):
                a = dict(dist["state"].get(st, {}), **a)
        else:
            a = dist["state"].get(st, {})
        for k_out, k_in in (("rural", "rural"), ("pvi", "pvi"), ("white", "white_nh"), ("black", "black_nh"),
                            ("hisp", "hisp"), ("asian", "asian_nh"), ("ba", "ba_plus"), ("inc", "med_income")):
            if a.get(k_in) is not None:
                m[k_out] = a[k_in]
        if a.get("lines_note"):
            m["ln"] = 1
        roster.append(m)
    roster.sort(key=lambda m: (m["st"], m.get("d") or 0, m["fr"], m["last"]))
    return roster


def bill_label(t, n):
    return f"{TYPE_LABEL.get(t, t.upper())} {n}"


def link_rolls(bills):
    """(chamber, session, roll) -> (bill_id, amendment dict or None, action text)"""
    m = {}
    for b in bills.values():
        for v in b.get("votes", []):
            m.setdefault((v["ch"], v["sess"], v["roll"]), (b["id"], None, v["text"]))
        for a in b.get("amdts", []):
            for v in a.get("votes", []):
                m[(v["ch"], v["sess"], v["roll"])] = (b["id"], a, v["text"])
    return m


def rule_targets(title, congress):
    out = []
    for kind, num in RULE_BILLS.findall(title or ""):
        t = RULE_TYPE.get(re.sub(r"\s", "", kind.lower()))
        if t:
            out.append(f"{congress}-{t}-{num}")
    return out


def build_congress(congress, people, cfg, refresh_bills, refresh_votes, refresh_dist):
    log(f"=== Congress {congress} ===")
    path = billstatus.build_congress(congress, refresh=refresh_bills)
    bills = {b["id"]: b for b in read_jsonl(path)}
    log(f"bills loaded: {len(bills)}")
    cls = {}
    for bid, b in bills.items():
        cls[bid] = C.classify_bill(b)
    women = {bid for bid, c in cls.items() if c.get("include")}
    log(f"women's policy bills: {len(women)} (core {sum(1 for x in women if cls[x]['scope'] == 'core')})")
    dist = district_attrs(congress, refresh=refresh_dist)
    roll_map = link_rolls(bills)
    rosters, votes_out = {}, {}
    bill_votes = collections.defaultdict(list)
    for ch in ("H", "S"):
        try:
            rolls, vmem, vcast = voteview.load(ch, congress, refresh=refresh_votes)
        except Exception as e:
            log("WARN voteview", ch, congress, e)
            rolls, vmem, vcast = [], [], {}
        roster = build_roster(congress, ch, people, vmem, cfg, dist)
        rosters[ch] = roster
        idx_icpsr = {m["icpsr"]: i for i, m in enumerate(roster) if m.get("icpsr")}
        out = []
        for r in rolls:
            clerk = r["clerk"] or r["roll"]
            link = roll_map.get((ch, r["sess"], clerk))
            bid, amdt, act = (link if link else (None, None, ""))
            if not bid:
                mm = VV_BILL.match(r["bill"] or "")
                if mm:
                    bid = f"{congress}-{mm.group(1).lower()}-{int(mm.group(2))}"
            is_nom = (r["bill"] or "").startswith("PN")
            question = r["question"] or act
            info, basis, is_rule = None, [], False
            if amdt:
                info = C.classify_text(" ".join([amdt.get("purp", ""), amdt.get("desc", "")]),
                                       bills.get(bid, {}).get("pa", ""))
                if info:
                    basis = ["수정안 내용"] + info["basis"]
            if not info and bid in women:
                c = cls[bid]
                info = dict(topics=c["topics"], scope=c["scope"], dir=c["dir"] if not amdt else 0, commem=c["commem"])
                basis = ["법안"] + c["basis"][:2]
            if not info and bid and cls.get(bid, {}).get("rule"):
                targets = [t for t in rule_targets(bills[bid].get("title", ""), congress) if t in women]
                if targets:
                    c = cls[targets[0]]
                    info = dict(topics=c["topics"], scope=c["scope"], dir=c["dir"], commem=c["commem"])
                    basis = ["의사규칙: " + ", ".join(bill_label(*t.split("-")[1:]) for t in targets)]
                    is_rule = True
            if not info and (is_nom or not bid):
                info = C.classify_text(" ".join([r["desc"], r["dtl"]]))
                if info:
                    basis = ["표결 설명"] + info["basis"]
            if not info:
                continue
            pol = C.motion_polarity(question)
            ydir = (info.get("dir") or 0) * pol
            if is_rule:
                ydir = 0
            cast = ["0"] * len(roster)
            for icpsr, code in vcast.get(r["roll"], {}).items():
                i = idx_icpsr.get(icpsr)
                if i is not None:
                    cast[i] = str(voteview.cast_simple(code))
            year = r["date"][:4]
            vid = f"{ch}{congress}-{year}-{clerk}"
            rec = dict(id=vid, roll=r["roll"], clerk=clerk, date=r["date"], q=question, res=r["result"],
                       yea=r["yea"], nay=r["nay"], bill=bid or "", bl=bill_label(*bid.split("-")[1:]) if bid else (r["bill"] or ""),
                       desc=(r["desc"] or "")[:300], topics=info["topics"], scope=info.get("scope", "core"),
                       commem=bool(info.get("commem")), dir=ydir, mdir=info.get("dir") or 0,
                       vt=C.vote_type(question, bool(amdt), is_rule, is_nom), basis=basis[:3], cast="".join(cast))
            if amdt:
                rec["amdt"] = dict(num=amdt.get("num"), type=amdt.get("type"), sp=amdt.get("sp"),
                                   text=(amdt.get("purp") or amdt.get("desc") or "")[:400])
            if r.get("mid1") is not None:
                rec["mid"] = [r["mid1"], r["mid2"], r["sp1"], r["sp2"]]
            out.append(rec)
            if bid:
                bill_votes[bid].append(vid)
        votes_out[ch] = out
        log(f"{ch}{congress}: {len(out)} women's policy votes, roster {len(roster)}")
    # bills
    idx = {ch: {m["b"]: i for i, m in enumerate(rosters[ch])} for ch in rosters}
    bills_out = []
    for bid in sorted(women, key=lambda x: (bills[x]["t"], bills[x]["n"] if isinstance(bills[x]["n"], int) else 0)):
        b, c = bills[bid], cls[bid]
        ch = "S" if b["t"].startswith("s") else "H"
        ix = idx.get(ch, {})
        sp = b.get("sp") or {}
        cs = []
        for row in b.get("cs", []):
            bg, date, orig, wd = row[0], row[1], row[2], row[3]
            cs.append([ix.get(bg, bg), date, orig, 1 if wd else 0])
        short = [t for t in b.get("titles", []) if t != b.get("title")]
        rec = dict(id=bid, t=b["t"], n=b["n"], bl=bill_label(b["t"], b["n"]), title=b.get("title", ""),
                   alt=short[:3], intro=b.get("intro", ""), pa=b.get("pa", ""), topics=c["topics"], scope=c["scope"],
                   commem=c["commem"], dir=c["dir"], basis=c["basis"], sp=ix.get(sp.get("b"), sp.get("b")),
                   cs=cs, latest=b.get("latest"), law=b.get("law", ""), votes=bill_votes.get(bid, []),
                   url=bill_url(congress, b["t"], b["n"]),
                   rel=[r for r in b.get("rel", []) if r[0] in women][:6], subj=b.get("subj", [])[:12])
        bills_out.append(rec)
    data = dict(congress=congress, generated=dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
                members=rosters, bills=bills_out, votes=votes_out, notes=dist.get("notes", []))
    write_json(os.path.join(OUT, f"c{congress}.json"), data)
    return dict(c=congress, bills=len(bills_out), votes={ch: len(v) for ch, v in votes_out.items()},
                members={ch: len(r) for ch, r in rosters.items()}, generated=data["generated"])


def abortion_timeline():
    return load_csv("abortion_law_timeline.csv")


def write_index(summaries):
    p = os.path.join(OUT, "index.json")
    idx = read_json(p, {}) or {}
    have = {s["c"]: s for s in idx.get("congresses", [])}
    for s in summaries:
        have[s["c"]] = s
    idx.update(
        generated=dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
        current=current_congress(),
        congresses=[have[c] for c in sorted(have)],
        topics=C.topic_info(), groups=[dict(code=g, label=l) for g, l in C.GROUPS],
        abortion_law=abortion_timeline(),
        caucus_lists=sorted({f"{c}|{n}" for c, n in config_maps()["caucus_complete"]}),
    )
    write_json(p, idx, compact=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--congress", nargs="*", type=int)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--refresh-districts", action="store_true")
    ap.add_argument("--keep-cache", action="store_true", help="reuse downloaded bill files")
    args = ap.parse_args()
    cur = current_congress()
    if args.all:
        targets = list(range(FIRST_CONGRESS, cur + 1))
    elif args.congress:
        targets = args.congress
    else:
        targets = [cur]
        today = dt.date.today()
        if today < congress_start(cur) + dt.timedelta(days=90):
            targets.insert(0, cur - 1)  # the previous Congress keeps getting late bill updates
    people = legislators.load(refresh=True)
    cfg = config_maps()
    summaries = []
    for c in targets:
        is_live = c >= cur - 1
        summaries.append(build_congress(c, people, cfg, refresh_bills=is_live and not args.keep_cache,
                                        refresh_votes=is_live, refresh_dist=args.refresh_districts))
    write_index(summaries)
    log("done", summaries)


if __name__ == "__main__":
    main()
