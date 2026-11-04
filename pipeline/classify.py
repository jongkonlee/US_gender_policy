"""Women's policy classification (automatic, rule based).

Every bill and every roll-call vote gets:
  include  -> True when it is a women's policy item
  scope    -> 'core' or 'broad' (child care, paid leave, WIC, human trafficking; hidden by default)
  commem   -> True for commemorative resolutions (hidden by default)
  topics   -> list of sub-topic codes, first = main topic
  dir      -> +1 / -1 / 0 (direction of the measure; 0 = not coded / contested)
  basis    -> short list explaining which rule fired
"""
import re

TOPICS = [
    # code, group, Korean label, label for +1, label for -1
    ("repro_abortion", "reproduction", "임신중지", "접근 확대", "접근 제한"),
    ("repro_contraception", "reproduction", "피임·가족계획", "지원 확대", "지원 축소"),
    ("repro_ivf", "reproduction", "난임·체외수정", "보호·지원 확대", "제한"),
    ("health_maternal", "health", "산모·출산 건강", "지원 확대", "지원 축소"),
    ("health_women", "health", "여성 질병·연구", "지원 확대", "지원 축소"),
    ("violence_dv", "violence", "가정폭력·여성폭력방지법", "보호 강화", "보호 축소"),
    ("violence_sexual", "violence", "성폭력·성희롱", "보호 강화", "보호 축소"),
    ("econ_pay", "economy", "동일임금·고용 차별", "보호 강화", "보호 축소"),
    ("econ_pregnant_workers", "economy", "임신 노동자·수유", "보호 강화", "보호 축소"),
    ("econ_business", "economy", "여성 창업", "지원 확대", "지원 축소"),
    ("rights_era", "rights", "남녀평등 헌법 수정안", "비준 추진", "반대"),
    ("rights_education_sports", "rights", "교육·운동경기", "지원 확대", "지원 축소"),
    ("rights_military_veterans", "rights", "여성 군인·참전군인", "지원 확대", "지원 축소"),
    ("rights_international", "rights", "국제 여성", "지원 확대", "지원 축소"),
    ("rights_other", "rights", "기타 성평등", "지원 확대", "지원 축소"),
    ("broad_care", "broad", "돌봄·가족(넓은 범위)", "지원 확대", "지원 축소"),
    ("broad_trafficking", "broad", "인신매매(넓은 범위)", "대응 강화", "대응 약화"),
]
GROUPS = [("reproduction", "임신"), ("health", "모성·여성 건강"), ("violence", "여성 폭력"),
          ("economy", "일·경제"), ("rights", "성평등·권리"), ("broad", "넓은 범위")]
PRIORITY = ["repro_abortion", "repro_contraception", "repro_ivf", "violence_dv", "violence_sexual",
            "econ_pregnant_workers", "econ_pay", "econ_business", "rights_era", "rights_military_veterans",
            "rights_education_sports", "rights_international", "health_maternal", "health_women",
            "broad_care", "broad_trafficking", "rights_other"]


def _c(*pats):
    return re.compile("|".join(f"(?:{p})" for p in pats), re.I)


# Strong phrases: enough on their own (checked on the raw text)
STRONG = {
    "repro_abortion": _c(r"\babortion", r"\bunborn\b", r"\bpro-?life\b", r"\bborn[- ]alive\b", r"\bfetal (pain|heartbeat|personhood)",
                         r"pain[- ]capable", r"\bheartbeat (act|bill|protection)", r"\bRoe v\.? Wade\b", r"\bHyde (amendment|protections)",
                         r"Planned Parenthood", r"Mexico City policy", r"global gag", r"\bUNFPA\b", r"United Nations Population Fund",
                         r"partial[- ]birth", r"dismemberment", r"life at conception", r"sanctity of (human )?life", r"\bright to life\b",
                         r"reproductive (freedom|rights|health ?care access|choice|autonomy|health services access)",
                         r"Women'?s Health Protection Act", r"(crisis|resource|support|help) pregnancy center|pregnancy (resource|help|support|care) centers?",
                         r"mifepristone", r"chemical abortion", r"abortion pills?", r"\bpersonhood\b", r"\bpro-?choice\b",
                         r"\bDobbs\b", r"reproductive health ?care"),
    "repro_contraception": _c(r"contracepti", r"birth control", r"family planning", r"\bTitle X\b"),
    "repro_ivf": _c(r"\bIVF\b", r"in vitro fertili", r"\binfertil", r"fertility (treatment|preservation|care|services|coverage)",
                    r"assisted reproductive", r"\bembryos?\b"),
    "violence_dv": _c(r"domestic violence", r"dating violence", r"family violence", r"intimate partner", r"violence against (\w+ )?(women|females?|girls)",
                      r"\bVAWA\b", r"\bstalking\b", r"\bbattered\b", r"gender[- ]based violence", r"\bfemicide"),
    "violence_sexual": _c(r"sexual (assault|violence|harassment|misconduct)", r"\brape\b", r"\brapes\b", r"rape kits?",
                          r"sexual assault (kits?|evidence)", r"military sexual trauma", r"\bmetoo\b", r"#metoo"),
    "econ_pay": _c(r"equal pay", r"paycheck fairness", r"pay equity", r"wage (gap|discrimination)", r"Lilly Ledbetter",
                   r"gender pay gap", r"\bsex discrimination\b", r"discrimination (on the basis|because) of sex",
                   r"gender discrimination", r"Women'?s Bureau"),
    "econ_pregnant_workers": _c(r"pregnant workers?", r"pregnancy discrimination", r"nursing mothers", r"\bPUMP for Nursing",
                                r"(lactation|breastfeeding|breast-feeding).{0,50}(work|employ|accommodat|space|room|federal (building|facilit)|airport|travel)",
                                r"(work|employ).{0,30}(lactation|breastfeeding)"),
    "econ_business": _c(r"women'?s business", r"women[- ]owned", r"women entrepreneurs?", r"women in business", r"\bWOSB\b",
                        r"women'?s (small )?business"),
    "rights_era": _c(r"equal rights amendment", r"ratification of the equal rights", r"\bERA\b.{0,40}(ratif|deadline|amendment)"),
    "rights_military_veterans": _c(r"women veterans?", r"\bservicewomen\b", r"women (in|serving in|in the) (the )?(armed forces|military|combat)",
                                   r"female (service ?members?|veterans?|soldiers?|troops)", r"Women Airforce Service Pilots",
                                   r"\bWASPs?\b", r"Women'?s Army Corps", r"women'?s military"),
    "health_maternal": _c(r"\bmaternal\b", r"\bmaternity\b", r"\bprenatal\b", r"post[- ]?partum", r"\bobstetric", r"\bmidwi",
                          r"\bdoulas?\b", r"\bchildbirth", r"\bbirthing\b", r"\bperinatal\b", r"\bmomnibus\b", r"\bstillbirth",
                          r"preeclampsia", r"pregnancy[- ]related (death|mortality|deaths)", r"\bpregnant (women|people|individuals|patients|mothers)\b.{0,40}(health|care|coverage|medicaid)",
                          r"(health|care|coverage|medicaid).{0,40}\bpregnant (women|people|individuals)"),
    "health_women": _c(r"\bwomen'?s health\b", r"breast cancer", r"cervical cancer", r"ovarian cancer", r"uterine (cancer|fibroid)",
                       r"endometriosis", r"menopaus", r"menstrua", r"period products", r"feminine hygiene", r"mammogra",
                       r"\bPCOS\b", r"polycystic ovar", r"gynecolog", r"women.{0,20}(heart|cardiovascular) (health|disease)",
                       r"women in (clinical )?research", r"breast (density|implants?|reconstruction)", r"\bDES daughters"),
    "rights_education_sports": _c(r"\bTitle IX\b", r"women'?s sports", r"girls'? sports", r"women and girls in sports",
                                  r"(women|girls|female|females)\b.{0,25}\b(sports?|athlet\w*|olympic|teams?)\b",
                                  r"\b(sports?|athletics)\b.{0,25}\b(women|girls|females?)\b", r"fair play for women",
                                  r"female athletes?", r"girls'? education", r"women'?s (educational )?equity", r"women'?s colleges?",
                                  r"(women|girls) in (STEM|science|technology|engineering|mathematics|math|computing|aviation)"),
    "rights_international": _c(r"global women", r"women'?s global", r"women,? peace,? and security", r"international violence against women",
                               r"\bchild marriage", r"female genital (mutilation|cutting)", r"\bFGM\b", r"Ambassador[- ]at[- ]Large for Global Women",
                               r"(afghan|iranian|ukrainian|uyghur|yazidi|rohingya|haitian|sudanese|congolese) (women|girls)",
                               r"women (and girls )?(in|of) (afghanistan|iran|ukraine|sudan|haiti|congo|gaza|syria|iraq|yemen)"),
    "broad_care": _c(r"child ?care", r"child (and|&) (elder|dependent) care", r"dependent care", r"paid (family |sick |parental )?leave",
                     r"family (and medical )?leave", r"parental leave", r"\bFMLA\b", r"\bFAMILY Act\b", r"\bWIC\b",
                     r"Women,? Infants,? and Children", r"early (care|childhood) and education"),
    "broad_trafficking": _c(r"(human|sex|sexual|labor|labour|child|children|minors?|people|persons?|women|girls) traffick",
                            r"trafficking (victims?|survivors?|in persons|of (women|girls|children|persons|people|minors))",
                            r"traffick(ed|ing) (women|girls|children|persons|people|minors)", r"anti-?trafficking",
                            r"Trafficking Victims Protection", r"victims of trafficking", r"trafficking survivors?"),
}
# Weak single words: count only after noise phrases are removed
WEAK = _c(r"\bwomen'?s?\b", r"\bwoman'?s?\b", r"\bgirls?\b", r"\bfemales?\b", r"\bmothers?\b", r"\bpregnan", r"\bsuffrag",
          r"\b(19th|nineteenth) amendment", r"\bgender equ", r"\bwidows?\b(?=.{0,20}(women|benefit))")
NOISE = [
    re.compile(p, re.I) for p in (
        r"(minorit(y|ies)|disadvantaged|veterans?|minority-owned|small)[- ,]*(and|or)[- ]women(-owned)?",
        r"women(-owned)?[- ,]*(and|or)[- ]minorit(y|ies)(-owned)?",
        r"gold star (mothers?|wives|families)", r"mothers? against drunk driving", r"\bmother lode\b",
        r"women,? infants,? and children", r"\bWIC\b",
        r"(women|girls) (basketball|soccer|softball|volleyball|hockey|lacrosse|golf|tennis|gymnastics|rowing|swimming)",
        r"\b(men|boys|fathers|sons|husbands?|brothers) (and|&) (women|girls|mothers|daughters|wives|sisters)\b",
        r"\b(women|girls|mothers|daughters|wives|sisters) (and|&) (men|boys|fathers|sons|husbands?|brothers)\b",
        r"fathers,? mothers", r"mothers,? fathers", r"servicemen and servicewomen", r"\bboys and girls clubs?\b",
        r"\bmen'?s (and|&) women'?s\b", r"\bwomen'?s (and|&) men'?s\b", r"service ?(men|members) (and|&) women",
    )]
ENV_AREAS = {"Environmental Protection", "Energy", "Agriculture and Food", "Public Lands and Natural Resources",
             "Water Resources Development", "Transportation and Public Works", "Animals"}
ENV_NOISE = re.compile(r"pregnant (women|people|individuals|sows|animals)|women and children|children and pregnant|\bpregnan\w*", re.I)
LGBT = re.compile(r"gender identity|sexual orientation|\bLGBT|transgender|\bqueer\b", re.I)
SPORTS_COMMEM = re.compile(r"\b(team|championships?|champions|NCAA|basketball|soccer|softball|volleyball|hockey|lacrosse|golf|tennis|"
                           r"gymnastics|track and field|rowing|swimming|World Cup|Olympi|Paralympi|athletic program|national title)\b", re.I)
COMMEM = re.compile(r"^(a |an )?(resolution |concurrent resolution )?(recogniz|honou?r|commemorat|celebrat|designat|"
                    r"supporting the (designation|goals and ideals)|expressing support for the (designation|goals)|congratulat|"
                    r"remember|in memory|mourn|observ|acknowledg|marking|calling for the observance)", re.I)
AWARE = re.compile(r"(awareness|history) (month|week|day)|anniversary|international women'?s day|equal pay day|women'?s equality day", re.I)
RULE = re.compile(r"^providing for (the )?consideration", re.I)

# Women's policy subjects (CRS legislative subject terms); mixed terms need a women word in the title
SUBJ_TOPIC = [  # (pattern, topic, specific?)
    (re.compile(r"^abortion$", re.I), "repro_abortion", True),
    (re.compile(r"family planning|birth control|contracepti", re.I), "repro_contraception", True),
    (re.compile(r"infertil|assisted reproductive", re.I), "repro_ivf", True),
    (re.compile(r"maternal|pregnan", re.I), "health_maternal", True),
    (re.compile(r"^women'?s health$", re.I), "health_women", True),
    (re.compile(r"^women'?s employment$", re.I), "econ_pay", True),
    (re.compile(r"^women in business$", re.I), "econ_business", True),
    (re.compile(r"^crimes against women$", re.I), "violence_dv", True),
    (re.compile(r"^women'?s rights$", re.I), "rights_other", False),
    (re.compile(r"women", re.I), "rights_other", False),
]
DUTY = re.compile(r"\bdut(y|ies)\b|\btariff|harmonized tariff", re.I)
SUBJ_BROAD = [(re.compile(r"^human trafficking$", re.I), "broad_trafficking"),
              (re.compile(r"^child care", re.I), "broad_care")]

INTL_AREA = {"International Affairs"}
MIL_AREA = {"Armed Forces and National Security"}

# ---------- direction ----------
AB_MINUS = _c(r"no (taxpayer|federal|government) funding for abortion", r"prohibit.{0,60}abortion", r"abortion.{0,40}prohibit",
              r"protect(ing|ion of)? (the )?(unborn|pain[- ]capable|life|children from abortion)", r"born[- ]alive", r"pain[- ]capable",
              r"heartbeat", r"life at conception", r"sanctity of (human )?life", r"right to life", r"partial[- ]birth", r"dismemberment",
              r"defund.{0,40}planned parenthood", r"planned parenthood.{0,40}(defund|terminat|prohibit|eliminat)",
              r"abortion provider prohibition", r"conscience", r"(codify|permanent).{0,20}Hyde", r"Hyde.{0,20}(codif|permanent)",
              r"chemical abortion", r"abortion(-| )?inducing drugs?", r"mifepristone.{0,40}(restrict|safety|prohibit|ban)",
              r"(reinstat|codif|restor).{0,40}Mexico City", r"Mexico City.{0,40}(reinstat|codif)", r"\bpersonhood\b",
              r"\bprotecting life\b", r"\bpro-?life\b", r"ban on abortion|abortion ban", r"unborn child")
AB_PLUS = _c(r"Women'?s Health Protection Act", r"(right|access) to (an )?abortion", r"abortion (access|rights|justice|care|coverage)",
             r"reproductive (freedom|rights|choice|health ?care access|autonomy|health services access)", r"repeal.{0,40}Hyde",
             r"\bEACH (Woman )?Act\b", r"Equal Access to Abortion Coverage", r"Global HER", r"(repeal|rescind|end).{0,40}(global gag|Mexico City)",
             r"Freedom to Travel", r"protect(ing)? (abortion )?(clinics|providers|patients)", r"codify Roe|restor(e|ing) Roe|Roe.{0,10}(codif|restor)",
             r"Reproductive Health Care (Accessibility|Rights)", r"Stop Anti-Abortion Disinformation", r"\bpro-?choice\b",
             r"oppos.{0,30}(abortion ban|Dobbs)", r"condemn.{0,40}Dobbs")
CONTRA_PLUS = _c(r"right to contraception", r"access to (birth control|contraception|contraceptives)", r"contraceptive (access|equity|coverage)",
                 r"affordab.{0,30}contracepti", r"Title X (Family Planning )?(funding|program)")
IVF_PLUS = _c(r"right to (IVF|in vitro)", r"access to (IVF|fertility|in vitro)", r"IVF (protection|access)", r"protect.{0,30}(IVF|in vitro)",
              r"fertility (coverage|treatment|preservation)")
POS = re.compile(r"reauthoriz|improv|expand|strengthen|protect|support|prevent|establish|increase|ensur|promot|enhanc|access|fairness|"
                 r"equity|equal|empower|invest|provid|award|combat|address|reduc|end(ing)? (violence|discrimination|the backlog)|eliminat|"
                 r"justice|safety|safe|help|assist|honou?r|recogni", re.I)
NEG = re.compile(r"\brepeal|prohibit|restrict|\blimit|terminat|rescind|disapprov|nullif|withhold|defund|\bban\b|block", re.I)
CONTESTED = _c(r"sports", r"athlet", r"biological sex", r"\bTitle IX\b.{0,60}(rule|regulation)")


def topic_info():
    return [dict(code=c, group=g, label=l, plus=p, minus=m) for c, g, l, p, m in TOPICS]


def _clean(text, pa):
    t = text
    for rx in NOISE:
        t = rx.sub(" ", t)
    if pa in ENV_AREAS:
        t = ENV_NOISE.sub(" ", t)
    return t


def text_topics(text, pa=""):
    """Topics matched in a piece of text (title, amendment purpose, vote description).
    Returns (strong, weak, basis): strong = specific phrases, weak = generic words like 'women'."""
    strong, weak, basis = [], [], []
    raw = text or ""
    clean = _clean(raw, pa)
    for code in PRIORITY:
        rx = STRONG.get(code)
        if not rx:
            continue
        m = rx.search(clean if code != "broad_care" else raw)
        if m:
            strong.append(code)
            basis.append(f"제목 낱말: {m.group(0)}")
    if not strong:
        m = WEAK.search(clean)
        if m:
            w = m.group(0).lower()
            if w.startswith(("mother", "pregnan")):
                strong.append("health_maternal")  # pregnancy / motherhood words are specific enough
            else:
                weak.append("rights_other")
            basis.append(f"제목 낱말: {m.group(0)}")
    if LGBT.search(raw) and not WEAK.search(clean) and not any(
            STRONG[c].search(raw) for c in ("repro_abortion", "violence_dv", "violence_sexual", "econ_pregnant_workers")):
        return [], [], ["성소수자 관련(제외)"]
    found = strong + weak
    if found and pa in INTL_AREA and "rights_international" not in found:
        strong.append("rights_international")
    if found and pa in MIL_AREA and "rights_military_veterans" not in found and re.search(r"women|female|servicewomen", raw, re.I):
        strong.append("rights_military_veterans")
    return strong, weak, basis


INVERT = re.compile(r"\b(to strike|striking|strike the|repeal|remove|eliminat\w+ the|nullif\w+|reverse)\b", re.I)
RESCIND = re.compile(r"strike the rescission|restor\w* (funding|funds)|prevent.{0,30}cuts", re.I)
NO_DIR_AREAS = {"Immigration"}


def direction(topics, text, commem=False, pa=""):
    if not topics or commem:
        return 0
    t = topics[0]
    s = text or ""
    inv = bool(INVERT.search(s))
    if t == "repro_abortion":
        minus, plus = AB_MINUS.search(s), AB_PLUS.search(s)
        if minus and not plus:
            return 1 if inv else -1
        if plus and not minus:
            return -1 if inv else 1
        return 0
    if t in ("repro_contraception", "repro_ivf"):
        if RESCIND.search(s):
            return 1
        if re.search(r"(prohibit|terminat|eliminat|defund|withhold|rescind|rescission).{0,60}(Title X|family planning|contracepti)", s, re.I):
            return 1 if re.search(r"strike|striking", s, re.I) else -1
        if (CONTRA_PLUS if t == "repro_contraception" else IVF_PLUS).search(s):
            return 1
        if t == "repro_ivf" and re.search(r"personhood|life at conception", s, re.I):
            return -1
        return 0
    if pa in NO_DIR_AREAS:
        return 0
    if t == "rights_education_sports" and CONTESTED.search(s):
        return 0
    if t == "rights_era":
        return -1 if re.search(r"rescind|oppos|withdraw", s, re.I) else 1
    if RESCIND.search(s):
        return 1
    if NEG.search(s) and not POS.search(s):
        return -1
    if POS.search(s) and not NEG.search(s):
        return 1
    return 0


def _order(strong, subj, weak):
    out = []
    for group in (sorted(strong, key=PRIORITY.index), sorted(subj, key=PRIORITY.index), sorted(weak, key=PRIORITY.index)):
        for t in group:
            if t not in out:
                out.append(t)
    core = [t for t in out if not t.startswith("broad")]
    broad = [t for t in out if t.startswith("broad")]
    return core + broad


def own_titles(b):
    """Titles of the bill itself: leave out short titles of divisions ('for portions of this bill'),
    so that an omnibus or defense bill is not counted because one of its parts is about women."""
    out = []
    for t in b.get("titles", []):
        if isinstance(t, (list, tuple)):
            ty, tt = (t[0] or ""), t[1]
            if "portion" in ty.lower():
                continue
        else:
            tt = t
        if tt and tt not in out:
            out.append(tt)
    return out


def classify_bill(b):
    """Return classification dict for a bill record (from billstatus.parse_bill)."""
    pa = b.get("pa") or ""
    titles = [b.get("title") or ""] + [t for t in own_titles(b) if t != b.get("title")]
    text = " | ".join(titles)
    main_title = b.get("title") or (titles[0] if titles else "")
    is_res = b["t"] in ("hres", "sres", "hconres", "sconres")
    if b["t"] == "hres" and RULE.search(main_title):
        return dict(include=False, rule=True)
    strong, weak, basis = text_topics(text, pa)
    subj = b.get("subj") or []
    s_topics, n_specific, n_women = [], 0, 0
    for s in subj:
        for rx, code, specific in SUBJ_TOPIC:
            if rx.search(s):
                n_women += 1
                n_specific += 1 if specific else 0
                if code not in s_topics:
                    s_topics.append(code)
                break
    n_subj = len(subj)
    subj_ok = (n_specific >= 1 and n_subj <= 10) or (n_women >= 2 and n_subj <= 25)
    if not subj_ok:
        s_topics = []
    else:
        basis.append("주제어: " + ", ".join(x for x in subj if any(p[0].search(x) for p in SUBJ_TOPIC))[:120])
    if not strong and not s_topics and weak and DUTY.search(text):
        return dict(include=False, excluded="tariff")
    topics = _order(strong, s_topics, weak)
    if not topics:
        return dict(include=False)
    commem = bool(is_res and (COMMEM.search(main_title) or AWARE.search(main_title)))
    if commem and SPORTS_COMMEM.search(main_title) and not re.search(r"title ix|women'?s sports day|girls in sports day", main_title, re.I):
        return dict(include=False, excluded="sports")
    core = [t for t in topics if not t.startswith("broad")]
    scope = "core" if core else "broad"
    d = direction(topics, text, commem, pa)
    return dict(include=True, scope=scope, commem=commem, topics=topics, dir=d, basis=basis[:4])


def classify_text(text, pa=""):
    """For amendments and vote descriptions: topics + direction, or None."""
    if not text:
        return None
    strong, weak, basis = text_topics(text, pa)
    topics = _order(strong, [], weak)
    if not topics:
        return None
    core = [t for t in topics if not t.startswith("broad")]
    return dict(topics=topics, scope="core" if core else "broad", dir=direction(topics, text, False, pa), basis=basis[:3])


# ---------- votes ----------
Q_PLUS = re.compile(r"passage|pass\b|agree|adopt|cloture|motion to proceed|override|objections of the president|concur|"
                    r"conference report|on the (bill|joint resolution|resolution|concurrent resolution|nomination|amendment)\b|"
                    r"discharge|waive|suspend", re.I)
Q_MINUS = re.compile(r"\btable\b|postpone", re.I)
Q_ZERO = re.compile(r"recommit|commit\b|reconsider|point of order|instruct|adjourn|quorum|previous question|appeal|"
                    r"question of consideration|division", re.I)


def motion_polarity(question, detail=""):
    q = question or ""
    if re.fullmatch(r"\s*on the motion\s*", q, re.I):
        d = detail or ""
        if re.search(r"waive", d, re.I):
            return 1
        if re.search(r"table", d, re.I):
            return -1
        return 0
    if Q_MINUS.search(q):
        return -1
    if Q_ZERO.search(q):
        return 0
    if Q_PLUS.search(q):
        return 1
    return 0


def vote_type(question, on_amendment, is_rule, is_nom):
    q = (question or "").lower()
    if is_nom:
        return "nomination"
    if is_rule or "previous question" in q:
        return "procedural"
    if "veto" in q or "objections of the president" in q:
        return "veto"
    if on_amendment or "amendment" in q:
        if "table" in q or "point of order" in q or "waive" in q:
            return "amendment_procedural"
        return "amendment"
    if any(k in q for k in ("passage", "pass", "agree", "adopt", "conference report", "concur", "on the bill",
                            "on the joint resolution", "on the resolution", "on the concurrent resolution")):
        return "passage"
    return "procedural"
