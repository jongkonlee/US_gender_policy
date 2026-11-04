/* 미국 의회 여성정책 트래커 — front end (no dependencies) */
'use strict';

const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const fmt = (x, d = 1) => (x === null || x === undefined || isNaN(x)) ? '–' : Number(x).toFixed(d);
const pct = (x, d = 1) => (x === null || x === undefined || isNaN(x)) ? '–' : (100 * x).toFixed(d) + '%';

const S = { idx: null, cache: {}, D: null, c: null, ch: 'H', tab: 'summary', topic: 'all', cmp: 'gender', within: true,
  commem: false, broad: false, vtype: 'all', dir: 'all', q: '', page: 0, sort: null, open: null };

const PARTY = { D: '민주', R: '공화', I: '무소속' };
const RACE = { B: '흑인', H: '히스패닉', A: '아시아·태평양계', N: '원주민' };
const VT = { passage: '통과·채택', amendment: '수정안', amendment_procedural: '수정안 절차(보류 등)', procedural: '절차',
  veto: '거부권 재의결', nomination: '인준' };
const VT_FILTER = { final: ['passage', 'veto'], amend: ['amendment', 'amendment_procedural'], proc: ['procedural'], nom: ['nomination'] };
const PA = { 'Agriculture and Food': '농업·식품', 'Animals': '동물', 'Armed Forces and National Security': '국방·안보',
  'Arts, Culture, Religion': '문화·종교', 'Civil Rights and Liberties, Minority Issues': '시민권·소수자', 'Commerce': '상업',
  'Congress': '의회', 'Crime and Law Enforcement': '범죄·치안', 'Economics and Public Finance': '경제·재정', 'Education': '교육',
  'Emergency Management': '재난 관리', 'Energy': '에너지', 'Environmental Protection': '환경', 'Families': '가족',
  'Finance and Financial Sector': '금융', 'Foreign Trade and International Finance': '통상·국제금융',
  'Government Operations and Politics': '정부 운영·정치', 'Health': '보건', 'Housing and Community Development': '주거·지역개발',
  'Immigration': '이민', 'International Affairs': '외교', 'Labor and Employment': '노동·고용', 'Law': '법률',
  'Native Americans': '원주민', 'Private Legislation': '사적 법안', 'Public Lands and Natural Resources': '공유지·자연자원',
  'Science, Technology, Communications': '과학·기술·통신', 'Social Sciences and History': '사회과학·역사',
  'Social Welfare': '사회복지', 'Sports and Recreation': '체육·여가', 'Taxation': '조세',
  'Transportation and Public Works': '교통·공공사업', 'Water Resources Development': '수자원', 'Commemorations': '기념' };
const LAW = { roe: 'Roe 시기(2021-09 이전)', ban: '전면 금지', ban_6wk: '6주 전후 금지', limit_12_18: '12~18주 제한',
  limit_20_24: '20~24주·생존 가능 시점', no_limit: '제한 없음', na: '자료 없음' };
const H_TYPES = new Set(['hr', 'hres', 'hjres', 'hconres']);

let TOPIC = {};   // code -> {label, group, plus, minus}

/* ---------- comparison groups ---------- */
function tertileCut(arr) {
  const v = arr.filter(x => x !== null && x !== undefined).sort((a, b) => a - b);
  if (v.length < 6) return null;
  return [v[Math.floor(v.length / 3)], v[Math.floor(2 * v.length / 3)]];
}
function tert(x, cut, unit) {
  if (x === null || x === undefined || !cut) return '자료 없음';
  const u = unit || '';
  if (x < cut[0]) return `하위 1/3 (${fmt(cut[0], 0)}${u} 미만)`;
  if (x < cut[1]) return `중간 1/3`;
  return `상위 1/3 (${fmt(cut[1], 0)}${u} 이상)`;
}
function lawStatus(st, date) {
  if (!date || date < '2021-09-01') return 'roe';
  const rows = (S.idx.abortion_law || []).filter(r => r.state === st);
  for (const r of rows) {
    if (r.start_date <= date && (!r.end_date || date <= r.end_date)) return r.status in LAW ? r.status : 'na';
  }
  return 'na';
}
const CMP = {
  gender: { label: '성별', f: m => [m.g === 'F' ? '여성' : '남성'], order: ['여성', '남성'] },
  race: { needs: 'race', label: '인종(여러 집단이면 각각 셈)', f: m => { const o = [...(m.race || '')].map(c => RACE[c]).filter(Boolean); return o.length ? o : ['백인·기타']; },
    order: ['흑인', '히스패닉', '아시아·태평양계', '원주민', '백인·기타'] },
  rural: { label: '농촌 인구 비율(지역구·주)', f: m => [m.rural == null ? '자료 없음' : m.rural < 10 ? '도시형 (10% 미만)' : m.rural < 30 ? '중간 (10~30%)' : '농촌형 (30% 이상)'],
    order: ['도시형 (10% 미만)', '중간 (10~30%)', '농촌형 (30% 이상)', '자료 없음'] },
  pvi: { label: '당파 지수(Cook 방식 계산)', f: m => [m.pvi == null ? '자료 없음' : m.pvi >= 15 ? '민주 강세 (D+15 이상)' : m.pvi >= 5 ? '민주 우세 (D+5~15)' :
      m.pvi > -5 ? '경합 (±5 이내)' : m.pvi > -15 ? '공화 우세 (R+5~15)' : '공화 강세 (R+15 이상)'],
    order: ['민주 강세 (D+15 이상)', '민주 우세 (D+5~15)', '경합 (±5 이내)', '공화 우세 (R+5~15)', '공화 강세 (R+15 이상)', '자료 없음'] },
  age: { label: '나이(회기 시작 때)', f: m => [m.age == null ? '자료 없음' : m.age < 50 ? '50세 미만' : m.age < 65 ? '50~64세' : '65세 이상'],
    order: ['50세 미만', '50~64세', '65세 이상', '자료 없음'] },
  tenure: { label: '선수(이 원에서 몇 번째 회기)', f: m => {
      if (S.ch === 'H') return [m.nc <= 1 ? '초선' : m.nc <= 3 ? '2~3선' : '4선 이상'];
      return [m.nc <= 3 ? '첫 임기' : m.nc <= 6 ? '두 번째 임기' : '세 번째 임기 이상'];
    }, order: ['초선', '2~3선', '4선 이상', '첫 임기', '두 번째 임기', '세 번째 임기 이상'] },
  region: { label: '지역(인구조사국 4대 권역)', f: m => [({ Northeast: '북동부', Midwest: '중서부', South: '남부', West: '서부' })[m.reg] || '준주·기타'],
    order: ['북동부', '중서부', '남부', '서부', '준주·기타'] },
  dw: { label: 'DW-NOMINATE 1차원(이념 위치)', f: m => [m.dw1 == null ? '자료 없음' : m.dw1 <= -0.5 ? '−0.5 이하' : m.dw1 <= -0.2 ? '−0.5~−0.2' :
      m.dw1 < 0.2 ? '−0.2~0.2' : m.dw1 < 0.5 ? '0.2~0.5' : '0.5 이상'], order: ['−0.5 이하', '−0.5~−0.2', '−0.2~0.2', '0.2~0.5', '0.5 이상', '자료 없음'] },
  law: { label: '주 임신중지 법(표결·발의 날짜 기준)', f: (m, ctx) => [LAW[lawStatus(m.st, ctx && ctx.date)]], order: Object.values(LAW), needs: 'law' },
  white: { label: '지역구 비히스패닉 백인 비율', f: m => [tert(m.white, S.cuts.white, '%')], tert: 'white' },
  black: { label: '지역구 흑인 비율', f: m => [tert(m.black, S.cuts.black, '%')], tert: 'black' },
  hisp: { label: '지역구 히스패닉 비율', f: m => [tert(m.hisp, S.cuts.hisp, '%')], tert: 'hisp' },
  ba: { label: '지역구 대졸 비율(25세 이상)', f: m => [tert(m.ba, S.cuts.ba, '%')], tert: 'ba' },
  inc: { label: '지역구 가구 소득 중앙값', f: m => [tert(m.inc, S.cuts.inc, '달러')], tert: 'inc' },
  religion: { label: '종교', f: m => [m.rel || '자료 없음'], needs: 'rel' },
  caucus: { label: '여성정책 관련 코커스', f: m => (m.cau && m.cau.length) ? m.cau : ['해당 없음'], needs: 'cau' },
  faction: { label: '계파', f: m => (m.fac && m.fac.length) ? m.fac : ['해당 없음'], needs: 'fac' },
};

function groupsOf(m, ctx) { return CMP[S.cmp].f(m, ctx); }
function partyKey(m) { return S.within ? (m.pc || m.p) : 'ALL'; }
function orderGroups(keys) {
  const ord = CMP[S.cmp].order;
  return keys.sort((a, b) => {
    const ia = ord ? ord.indexOf(a) : -1, ib = ord ? ord.indexOf(b) : -1;
    if (ia !== -1 || ib !== -1) return (ia === -1 ? 99 : ia) - (ib === -1 ? 99 : ib);
    if (a.startsWith('하위')) return -1; if (b.startsWith('하위')) return 1;
    if (a === '자료 없음' || a === '해당 없음') return 1; if (b === '자료 없음' || b === '해당 없음') return -1;
    return a.localeCompare(b, 'ko');
  });
}

/* ---------- data ---------- */
async function getJSON(u) { const r = await fetch(u, { cache: 'no-cache' }); if (!r.ok) throw new Error(u + ' ' + r.status); return r.json(); }

async function loadCongress(c) {
  if (!S.cache[c]) {
    const d = await getJSON(`data/c${c}.json`);
    const P = S.people || {};
    for (const ch of ['H', 'S']) {
      (d.members[ch] || []).forEach((m, i) => {
        m.i = i; m.ch = ch;
        const p = P[m.b];
        if (p) {
          if (p.race !== undefined) m.race = p.race;
          if (p.race_note) m.race_note = p.race_note;
          if (p.rel && p.rel[c]) m.rel = p.rel[c];
          if (p.cau && p.cau[c]) m.cau = p.cau[c];
          if (p.fac && p.fac[c]) m.fac = p.fac[c];
        }
      });
    }
    d.billsBy = { H: [], S: [] };
    d.bills.forEach(b => { b.ch = H_TYPES.has(b.t) ? 'H' : 'S'; d.billsBy[b.ch].push(b); });
    d.voteIndex = {};
    for (const ch of ['H', 'S']) (d.votes[ch] || []).forEach(v => { v.ch = ch; d.voteIndex[v.id] = v; });
    d.billIndex = Object.fromEntries(d.bills.map(b => [b.id, b]));
    S.cache[c] = d;
  }
  S.D = S.cache[c];
  const R = roster();
  S.cuts = {};
  for (const k of ['white', 'black', 'hisp', 'ba', 'inc']) S.cuts[k] = tertileCut(R.map(m => m[k]));
}
const roster = () => (S.D.members[S.ch] || []);

function topicMatch(topics) {
  if (S.topic === 'all') return true;
  if (S.topic.startsWith('g:')) { const g = S.topic.slice(2); return topics.some(t => TOPIC[t] && TOPIC[t].group === g); }
  return topics.includes(S.topic);
}
function scopeOk(x) {
  if (x.commem && !S.commem) return false;
  if (x.scope === 'broad' && !S.broad && !(S.topic.startsWith('broad') || S.topic === 'g:broad')) return false;
  return true;
}
function normNum(s) { return String(s || '').toLowerCase().replace(/[\s.]/g, ''); }
const BILLNUM = /^(h\.?\s?r|s|h\.?\s?res|s\.?\s?res|h\.?\s?j\.?\s?res|s\.?\s?j\.?\s?res|h\.?\s?con\.?\s?res|s\.?\s?con\.?\s?res)\.?\s*\d+$/i;
function textHit(q, parts) { const n = normNum(q); const l = q.toLowerCase(); return parts.some(p => { const s = String(p || ''); return normNum(s) === n || s.toLowerCase().includes(l); }); }

function filteredBills() {
  const R = roster();
  return (S.D.billsBy[S.ch] || []).filter(b => {
    if (!scopeOk(b) || !topicMatch(b.topics)) return false;
    if (S.dir !== 'all' && String(b.dir) !== S.dir) return false;
    if (S.q) {
      if (BILLNUM.test(S.q.trim())) return normNum(b.bl) === normNum(S.q);
      if (/^\d+$/.test(S.q.trim())) return String(b.n) === S.q.trim();
      const sp = typeof b.sp === 'number' ? R[b.sp] : null;
      if (!textHit(S.q, [b.bl, b.title, ...(b.alt || []), sp && sp.n])) return false;
    }
    return true;
  });
}
function filteredVotes() {
  return (S.D.votes[S.ch] || []).filter(v => {
    if (!scopeOk(v) || !topicMatch(v.topics)) return false;
    if (S.vtype !== 'all' && !VT_FILTER[S.vtype].includes(v.vt)) return false;
    if (S.dir !== 'all' && String(v.mdir) !== S.dir) return false;
    if (S.q) {
      if (BILLNUM.test(S.q.trim())) return normNum(v.bl) === normNum(S.q);
      const b = S.D.billIndex[v.bill];
      if (!textHit(S.q, [v.bl, v.desc, v.q, b && b.title, v.amdt && v.amdt.text, v.id])) return false;
    }
    return true;
  });
}

/* ---------- per-member statistics ---------- */
function memberStats(bills, votes) {
  const R = roster();
  const st = R.map(() => ({ sp: 0, cs: 0, n: 0, plus: 0, yea: 0, cast: 0 }));
  for (const b of bills) {
    if (typeof b.sp === 'number' && st[b.sp]) st[b.sp].sp++;
    for (const c of b.cs) if (typeof c[0] === 'number' && !c[3] && st[c[0]]) st[c[0]].cs++;
  }
  for (const v of votes) {
    for (let i = 0; i < v.cast.length; i++) {
      const c = v.cast[i];
      if (c !== '1' && c !== '2') continue;
      st[i].cast++; if (c === '1') st[i].yea++;
      if (v.dir) { st[i].n++; if ((c === '1' && v.dir === 1) || (c === '2' && v.dir === -1)) st[i].plus++; }
    }
  }
  return st;
}

function groupTable(rows) {
  // rows: [{m, ...}] -> Map party -> Map group -> list
  const out = new Map();
  for (const r of rows) {
    const p = partyKey(r.m);
    if (!out.has(p)) out.set(p, new Map());
    for (const g of groupsOf(r.m, r.ctx)) {
      const gm = out.get(p);
      if (!gm.has(g)) gm.set(g, []);
      gm.get(g).push(r);
    }
  }
  return out;
}
const partyOrder = ps => ps.sort((a, b) => 'DRIALL'.indexOf(a) - 'DRIALL'.indexOf(b));
const pLabel = p => p === 'ALL' ? '전체' : `<span class="p${p}">${PARTY[p] || p}</span>`;

/* ---------- views ---------- */
function render() {
  if (!S.D) return;
  document.querySelectorAll('#tabs button').forEach(b => b.classList.toggle('on', b.dataset.tab === S.tab));
  document.querySelectorAll('#chamberSeg button').forEach(b => b.classList.toggle('on', b.dataset.ch === S.ch));
  const f = { summary: viewSummary, bills: viewBills, votes: viewVotes, members: viewMembers, download: viewDownload, about: viewAbout }[S.tab];
  $('#main').innerHTML = f();
  bindTables();
  writeHash();
}

function filterNote() {
  const parts = [`${S.D.congress}대 ${S.ch === 'H' ? '하원' : '상원'}`];
  parts.push(S.topic === 'all' ? '모든 세부 정책' : S.topic.startsWith('g:') ? (S.idx.groups.find(g => g.code === S.topic.slice(2)) || {}).label : (TOPIC[S.topic] || {}).label);
  if (!S.commem) parts.push('기념 결의안 제외'); if (!S.broad) parts.push('넓은 범위 제외');
  if (S.q) parts.push(`찾기: "${esc(S.q)}"`);
  return parts.join(' · ');
}

function bars(items, maxv, fmtv, color) {
  return items.map(it => {
    const w = maxv > 0 ? Math.max(0, Math.min(100, 100 * it.v / maxv)) : 0;
    return `<div class="bar"><div class="lab" title="${esc(it.lab)}">${esc(it.lab)} <span class="muted">(${it.n}명)</span></div>
      <div class="track"><div class="fill" style="width:${w}%;background:${it.color || color}"></div></div><div class="val">${fmtv(it.v)}</div></div>`;
  }).join('');
}
const PCOLOR = { D: 'var(--d)', R: 'var(--r)', I: 'var(--i)', ALL: 'var(--accent)' };

function viewSummary() {
  const B = filteredBills(), V = filteredVotes(), R = roster();
  const st = memberStats(B, V);
  const nCs = B.reduce((a, b) => a + b.cs.filter(c => !c[3]).length, 0);
  const dirV = V.filter(v => v.dir).length;
  let h = `<p class="muted">${filterNote()}</p>
  <div class="cards">
    <div class="card"><div class="k">여성정책 법안</div><div class="v">${B.length}</div></div>
    <div class="card"><div class="k">공동발의(건)</div><div class="v">${nCs.toLocaleString()}</div></div>
    <div class="card"><div class="k">호명투표</div><div class="v">${V.length}</div></div>
    <div class="card"><div class="k">방향이 정해진 표결</div><div class="v">${dirV}</div></div>
    <div class="card"><div class="k">의원</div><div class="v">${R.length}</div></div>
  </div>`;
  // comparison by group
  const rows = R.map((m, i) => ({ m, s: st[i] })).filter(r => !(S.ch === 'H' && r.m.dl && S.cmp === 'pvi'));
  const gt = groupTable(rows);
  let cos = '', dir = '';
  let maxc = 0;
  for (const gm of gt.values()) for (const list of gm.values()) { const a = avg(list.map(r => r.s.sp + r.s.cs)); if (a > maxc) maxc = a; }
  for (const p of partyOrder([...gt.keys()])) {
    const gm = gt.get(p);
    const keys = orderGroups([...gm.keys()]);
    cos += `<div class="pgroup">${pLabel(p)}</div>` + bars(keys.map(g => ({ lab: g, n: gm.get(g).length, v: avg(gm.get(g).map(r => r.s.sp + r.s.cs)), color: PCOLOR[p] })), maxc, x => fmt(x, 1) + '건');
    const dkeys = keys.filter(g => gm.get(g).some(r => r.s.n > 0));
    dir += `<div class="pgroup">${pLabel(p)}</div>` + bars(dkeys.map(g => { const l = gm.get(g).filter(r => r.s.n > 0); return { lab: g, n: l.length, v: avg(l.map(r => r.s.plus / r.s.n)), color: PCOLOR[p] }; }), 1, x => pct(x, 0));
  }
  h += `<h2>${esc(CMP[S.cmp].label)}별 비교${S.within ? ' (정당 안)' : ''}</h2>
  <div class="chart-block"><b>의원 1인당 여성정책 법안 발의·공동발의 수</b>${cos}
    <div class="cap">대표발의 + 공동발의(철회 제외). 막대 옆 괄호는 그 집단의 의원 수입니다.${S.cmp === 'race' ? ' 여러 인종 집단에 속하는 의원은 각 집단에 모두 셉니다.' : ''}</div></div>
  <div class="chart-block"><b>확대·보호 쪽 표 비율(의원 평균)</b>${dirV ? dir : '<p class="muted">방향이 정해진 표결이 없습니다.</p>'}
    <div class="cap">방향이 정해진 표결에서, 의원마다 '확대·보호' 쪽으로 던진 표의 비율을 구한 뒤 집단 평균을 냈습니다(불참 제외). 방향은 법안·수정안 내용으로 자동 판정했으며, 판정이 어려운 표결은 뺐습니다.</div></div>`;
  const sg = (() => { const set = new Set(); R.forEach(m => groupsOf(m, {}).forEach(x => set.add(x))); return orderGroups([...set].filter(x => x !== '자료 없음' && x !== '해당 없음')); })();
  if (S.plotGroup && !sg.includes(S.plotGroup)) S.plotGroup = '';
  h += `<h2>이념 위치와 여성정책 활동</h2><div class="chart-block"><div class="btns" style="align-items:center">
    <div class="seg"><button data-sumy="cs" class="${(S.sumY || 'cs') === 'cs' ? 'on' : ''}">발의·공동발의 수</button><button data-sumy="dir" class="${S.sumY === 'dir' ? 'on' : ''}">확대 쪽 표 비율</button></div>
    <label class="fld">강조 <select data-sumgroup><option value="">없음</option>${sg.map(x => `<option value="${esc(x)}" ${S.plotGroup === x ? 'selected' : ''}>${esc(x)}</option>`).join('')}</select></label></div>
    <div id="sumScatter">${summaryScatter(st)}</div>
    <div class="cap">점 하나가 의원 한 명입니다(가로: DW-NOMINATE 1차원). 점에 마우스를 올리면 이름이 보입니다. 같은 이념 위치에서 위아래로 벌어지는 정도가 이념만으로 설명되지 않는 차이입니다.</div></div>`;
  // topic summary
  const topics = new Map();
  const add = (t, k, x) => { if (!topics.has(t)) topics.set(t, { bills: 0, votes: 0, csD: 0, csR: 0, csI: 0, plus: { D: [0, 0], R: [0, 0] } }); const o = topics.get(t); if (k === 'b') { o.bills++; for (const c of x.cs) { const m = typeof c[0] === 'number' ? R[c[0]] : null; if (m && !c[3]) o['cs' + (m.pc === 'D' ? 'D' : m.pc === 'R' ? 'R' : 'I')]++; } } else { o.votes++; if (x.dir) for (let i = 0; i < x.cast.length; i++) { const c = x.cast[i]; const m = R[i]; if (!m || (c !== '1' && c !== '2')) continue; const p = m.pc === 'D' ? 'D' : m.pc === 'R' ? 'R' : null; if (!p) continue; o.plus[p][1]++; if ((c === '1' && x.dir === 1) || (c === '2' && x.dir === -1)) o.plus[p][0]++; } } };
  B.forEach(b => add(b.topics[0], 'b', b));
  V.forEach(v => add(v.topics[0], 'v', v));
  const order = (S.idx.topics || []).map(t => t.code);
  const trs = [...topics.entries()].sort((a, b) => order.indexOf(a[0]) - order.indexOf(b[0])).map(([t, o]) => {
    const tot = o.csD + o.csR + o.csI;
    return `<tr class="click" data-topic="${t}"><td>${esc((TOPIC[t] || {}).label || t)}</td><td class="num">${o.bills}</td><td class="num">${o.votes}</td>
      <td class="num">${tot ? pct(o.csD / tot, 0) : '–'}</td><td class="num">${tot ? pct(o.csR / tot, 0) : '–'}</td>
      <td class="num">${o.plus.D[1] ? pct(o.plus.D[0] / o.plus.D[1], 0) : '–'}</td><td class="num">${o.plus.R[1] ? pct(o.plus.R[0] / o.plus.R[1], 0) : '–'}</td></tr>`;
  }).join('');
  h += `<h2>세부 정책 요약</h2><div class="tbl-wrap"><table><thead><tr><th>세부 정책(주 분류)</th><th class="num">법안</th><th class="num">표결</th>
    <th class="num">공동발의 중 민주</th><th class="num">공동발의 중 공화</th><th class="num">민주 확대 쪽 표</th><th class="num">공화 확대 쪽 표</th></tr></thead>
    <tbody>${trs || '<tr><td colspan="7" class="muted">해당 자료가 없습니다.</td></tr>'}</tbody></table></div>
    <p class="note">줄을 누르면 그 세부 정책만 봅니다. '확대 쪽 표'는 방향이 정해진 표결에서 그 정당 의원들이 던진 찬반 표 가운데 확대·보호 쪽 표의 비율입니다.</p>`;
  if (S.D.notes && S.D.notes.length) h += `<p class="note">자료 메모: ${S.D.notes.map(esc).join(' / ')}</p>`;
  return h;
}
const avg = a => a.length ? a.reduce((x, y) => x + y, 0) / a.length : null;

function dirTag(topic, d) {
  const t = TOPIC[topic] || {};
  if (d === 1) return `<span class="tag plus">${esc(t.plus || '확대')}</span>`;
  if (d === -1) return `<span class="tag minus">${esc(t.minus || '제한')}</span>`;
  return `<span class="tag">방향 없음</span>`;
}
function topicTags(ts) { return ts.map(t => `<span class="tag">${esc((TOPIC[t] || {}).label || t)}</span>`).join(''); }
function memLabel(m) { if (!m) return ''; const d = m.ch === 'H' ? (m.d ? '-' + m.d : (m.dl ? '' : '-AL')) : ''; return `${esc(m.n)} <span class="p${m.pc}">(${m.p}-${m.st}${d})</span>`; }

const PAGE = 100;
function pager(n) {
  const pages = Math.ceil(n / PAGE); if (pages <= 1) return '';
  return `<div class="pager"><button class="btn" data-page="${S.page - 1}" ${S.page <= 0 ? 'disabled' : ''}>이전</button>
    <span>${S.page + 1} / ${pages}쪽 (${n}건)</span><button class="btn" data-page="${S.page + 1}" ${S.page >= pages - 1 ? 'disabled' : ''}>다음</button></div>`;
}
const TYPE_ORDER = ['hr', 'hjres', 'hconres', 'hres', 's', 'sjres', 'sconres', 'sres'];
function sortRows(rows, keyfns, def) {
  const so = S.sort || def;
  if (!so || !keyfns[so.k]) return rows;
  const f = keyfns[so.k], s = so.d;
  return rows.slice().sort((a, b) => { const x = f(a), y = f(b); return (x < y ? -1 : x > y ? 1 : 0) * s; });
}
function th(k, label, cls) { const on = S.sort && S.sort.k === k ? (S.sort.d > 0 ? ' ▲' : ' ▼') : ''; return `<th class="sortable ${cls || ''}" data-sort="${k}">${label}${on}</th>`; }

function viewBills() {
  const R = roster();
  let B = filteredBills();
  const keys = { num: b => TYPE_ORDER.indexOf(b.t) * 1e6 + (typeof b.n === 'number' ? b.n : 0), cs: b => b.cs.filter(c => !c[3]).length,
    intro: b => b.intro, votes: b => b.votes.length };
  B = sortRows(B, keys, S.sort || { k: 'num', d: 1 });
  const rows = B.slice(S.page * PAGE, (S.page + 1) * PAGE).map(b => {
    const sp = typeof b.sp === 'number' ? R[b.sp] : null;
    const cnt = { D: 0, R: 0, I: 0 }; b.cs.forEach(c => { if (c[3]) return; const m = typeof c[0] === 'number' ? R[c[0]] : null; if (m) cnt[m.pc === 'D' ? 'D' : m.pc === 'R' ? 'R' : 'I']++; });
    return `<tr class="click" data-open="bill:${b.id}"><td class="nowrap">${esc(b.bl)}</td><td>${esc(b.title)}${b.commem ? ' <span class="tag commem">기념</span>' : ''}${b.scope === 'broad' ? ' <span class="tag">넓은 범위</span>' : ''}</td>
      <td>${topicTags(b.topics.slice(0, 2))}</td><td>${dirTag(b.topics[0], b.dir)}</td><td>${sp ? memLabel(sp) : esc(b.sp || '')}</td>
      <td class="num"><span class="pD">${cnt.D}</span> / <span class="pR">${cnt.R}</span>${cnt.I ? ' / ' + cnt.I : ''}</td><td class="num">${b.votes.length || ''}</td><td class="num">${esc(b.intro)}</td></tr>`;
  }).join('');
  return `<p class="muted">${filterNote()} · ${B.length}건</p>${pager(B.length)}
  <div class="tbl-wrap"><table><thead><tr>${th('num', '번호')}<th>이름</th><th>세부 정책</th><th>방향</th><th>대표발의</th>${th('cs', '공동발의 민/공', 'num')}${th('votes', '표결', 'num')}${th('intro', '발의일', 'num')}</tr></thead>
  <tbody>${rows || '<tr><td colspan="8" class="muted">해당 법안이 없습니다.</td></tr>'}</tbody></table></div>${pager(B.length)}`;
}

function viewVotes() {
  let V = filteredVotes();
  const keys = { date: v => v.date + String(v.clerk).padStart(5, '0'), margin: v => (v.yea || 0) - (v.nay || 0) };
  V = sortRows(V, keys);
  const rows = V.slice(S.page * PAGE, (S.page + 1) * PAGE).map(v => `<tr class="click" data-open="vote:${v.id}"><td class="num">${esc(v.date)}</td><td class="num">${v.clerk}</td>
    <td>${esc(v.bl)}${v.amdt ? ` <span class="tag">수정안 ${esc(v.amdt.num || '')}</span>` : ''}</td><td>${esc(v.q)}<div class="muted">${esc((v.amdt && v.amdt.text) || v.desc || '').slice(0, 140)}</div></td>
    <td>${esc(v.res)}</td><td>${topicTags(v.topics.slice(0, 1))}<span class="tag">${VT[v.vt] || v.vt}</span></td>
    <td>${v.dir ? dirTag(v.topics[0], v.dir).replace('">', '">찬성=') : '<span class="tag">방향 없음</span>'}</td><td class="num">${v.yea}–${v.nay}</td></tr>`).join('');
  return `<p class="muted">${filterNote()} · ${V.length}건</p>${pager(V.length)}
  <div class="tbl-wrap"><table><thead><tr>${th('date', '날짜', 'num')}<th class="num">번호</th><th>법안</th><th>표결 내용</th><th>결과</th><th>분류</th><th>찬성의 뜻</th>${th('margin', '찬–반', 'num')}</tr></thead>
  <tbody>${rows || '<tr><td colspan="8" class="muted">해당 표결이 없습니다.</td></tr>'}</tbody></table></div>${pager(V.length)}`;
}

function viewMembers() {
  const R = roster(), B = filteredBills(), V = filteredVotes();
  const st = memberStats(B, V);
  let list = R.map((m, i) => ({ m, s: st[i] }));
  if (S.q) list = list.filter(r => textHit(S.q, [r.m.n, r.m.st, r.m.b]));
  const keys = { name: r => r.m.last, party: r => r.m.pc, state: r => r.m.st + String(r.m.d || 0).padStart(2, '0'), age: r => r.m.age ?? -1,
    nc: r => r.m.nc, rural: r => r.m.rural ?? -1, pvi: r => r.m.pvi ?? -99, dw: r => r.m.dw1 ?? -9, cs: r => r.s.sp + r.s.cs,
    plus: r => r.s.n ? r.s.plus / r.s.n : -1 };
  list = sortRows(list, keys);
  const rows = list.slice(S.page * PAGE, (S.page + 1) * PAGE).map(({ m, s }) => `<tr class="click" data-open="mem:${m.b}">
    <td>${esc(m.n)}</td><td class="p${m.pc}">${m.p}</td><td>${m.st}${S.ch === 'H' ? '-' + (m.d || (m.dl ? '대의원' : 'AL')) : ''}</td><td>${m.g === 'F' ? '여' : '남'}</td>
    <td>${[...(m.race || '')].map(c => RACE[c]).join(', ')}</td><td class="num">${m.age ?? ''}</td><td class="num">${m.nc}</td>
    <td class="num">${m.rural != null ? fmt(m.rural, 0) + '%' : ''}</td><td class="num">${pviLabel(m.pvi)}</td><td class="num">${fmt(m.dw1, 2)}</td>
    <td class="num">${s.sp + s.cs}</td><td class="num">${s.n ? pct(s.plus / s.n, 0) + ` <span class="muted">(${s.n})</span>` : ''}</td></tr>`).join('');
  return `<p class="muted">${filterNote()} · ${list.length}명. 공동발의와 표 비율은 위에서 고른 세부 정책·조건 기준입니다.</p>${pager(list.length)}
  <div class="tbl-wrap"><table><thead><tr>${th('name', '이름')}${th('party', '정당')}${th('state', '주·선거구')}<th>성별</th><th>인종</th>${th('age', '나이', 'num')}${th('nc', '선수', 'num')}
  ${th('rural', '농촌', 'num')}${th('pvi', '당파 지수', 'num')}${th('dw', 'DW1', 'num')}${th('cs', '발의·공동발의', 'num')}${th('plus', '확대 쪽 표', 'num')}</tr></thead><tbody>${rows}</tbody></table></div>${pager(list.length)}`;
}
function pviLabel(x) { if (x === null || x === undefined) return ''; const r = Math.round(x); return r === 0 ? 'EVEN' : (r > 0 ? 'D+' + r : 'R+' + (-r)); }

/* ---------- detail panels ---------- */
function groupBreakdownBill(b) {
  const R = roster();
  const cs = new Set(b.cs.filter(c => !c[3] && typeof c[0] === 'number').map(c => c[0]));
  if (typeof b.sp === 'number') cs.add(b.sp);
  const rows = R.filter(m => m.fr <= b.intro && b.intro <= m.to || cs.has(m.i)).map(m => ({ m, ctx: { date: b.intro }, y: cs.has(m.i) }));
  const gt = groupTable(rows);
  let h = `<div class="tbl-wrap"><table><thead><tr><th>정당</th><th>${esc(CMP[S.cmp].label)}</th><th class="num">의원</th><th class="num">발의·공동발의</th><th class="num">비율</th></tr></thead><tbody>`;
  for (const p of partyOrder([...gt.keys()])) for (const g of orderGroups([...gt.get(p).keys()])) {
    const l = gt.get(p).get(g), y = l.filter(r => r.y).length;
    h += `<tr><td>${pLabel(p)}</td><td>${esc(g)}</td><td class="num">${l.length}</td><td class="num">${y}</td><td class="num">${pct(y / l.length, 0)}</td></tr>`;
  }
  return h + '</tbody></table></div>';
}
function groupBreakdownVote(v) {
  const R = roster();
  const rows = R.map((m, i) => ({ m, c: v.cast[i], ctx: { date: v.date } })).filter(r => r.c && r.c !== '0');
  const gt = groupTable(rows);
  let h = `<div class="tbl-wrap"><table><thead><tr><th>정당</th><th>${esc(CMP[S.cmp].label)}</th><th class="num">찬성</th><th class="num">반대</th><th class="num">불참·출석</th><th class="num">찬성 비율</th></tr></thead><tbody>`;
  for (const p of partyOrder([...gt.keys()])) for (const g of orderGroups([...gt.get(p).keys()])) {
    const l = gt.get(p).get(g), y = l.filter(r => r.c === '1').length, n = l.filter(r => r.c === '2').length, nv = l.length - y - n;
    h += `<tr><td>${pLabel(p)}</td><td>${esc(g)}</td><td class="num">${y}</td><td class="num">${n}</td><td class="num">${nv}</td><td class="num">${y + n ? pct(y / (y + n), 0) : '–'}</td></tr>`;
  }
  return h + '</tbody></table></div>';
}

function billPanel(id) {
  const b = S.D.billIndex[id]; if (!b) return '<p>법안을 찾을 수 없습니다.</p>';
  const R = S.D.members[b.ch];
  const sp = typeof b.sp === 'number' ? R[b.sp] : null;
  const active = b.cs.filter(c => !c[3]);
  const csSet = new Set(active.filter(c => typeof c[0] === 'number').map(c => c[0]));
  let h = `<h2>${esc(b.bl)} ${esc(b.title)}</h2>
  <div>${topicTags(b.topics)} ${dirTag(b.topics[0], b.dir)} ${b.commem ? '<span class="tag commem">기념</span>' : ''}${b.scope === 'broad' ? '<span class="tag">넓은 범위</span>' : ''}</div>
  <div class="kv"><div>대표발의</div><div>${sp ? memLabel(sp) : esc(b.sp)}</div>
  <div>발의일</div><div>${esc(b.intro)}</div>
  <div>공동발의</div><div>${active.length}명 (처음부터 ${active.filter(c => c[2]).length}명${b.cs.length - active.length ? `, 철회 ${b.cs.length - active.length}명` : ''})</div>
  <div>최근 처리</div><div>${esc((b.latest || [])[0] || '')} ${esc((b.latest || [])[1] || '')}${b.law ? ` <b>${esc(b.law)}</b>` : ''}</div>
  <div>겹치는 영역</div><div>${esc(PA[b.pa] || b.pa || '–')} <span class="muted">(CRS 정책 분야)</span></div>
  <div>분류 근거</div><div class="muted">${(b.basis || []).map(esc).join(' · ')}</div>
  ${b.alt && b.alt.length ? `<div>다른 이름</div><div class="muted">${b.alt.map(esc).join('<br>')}</div>` : ''}
  <div>원문</div><div><a href="${b.url}" target="_blank" rel="noopener">congress.gov에서 보기</a></div></div>
  <h3>${esc(CMP[S.cmp].label)}별 발의·공동발의</h3>${groupBreakdownBill(b)}
  <p class="note">발의일에 재임 중이던 의원 기준입니다(대표발의자 포함, 철회 제외).</p>${billPlots(b)}`;
  if (b.votes.length) {
    h += `<h3>표결별 공동발의자의 찬반</h3>`;
    for (const vid of b.votes) {
      const v = S.D.voteIndex[vid]; if (!v) continue;
      const VR = S.D.members[v.ch];
      const sameChamber = v.ch === b.ch;
      let x = '';
      if (sameChamber) {
        const t = { yy: 0, yn: 0, yv: 0, ny: 0, nn: 0, nv: 0 }; const against = [];
        VR.forEach((m, i) => { const c = v.cast[i]; if (!c || c === '0') return; const isC = csSet.has(i) || b.sp === i; const k = (isC ? 'y' : 'n') + (c === '1' ? 'y' : c === '2' ? 'n' : 'v'); t[k]++; if (isC && c === '2') against.push(m); });
        x = `<div class="tbl-wrap"><table><thead><tr><th></th><th class="num">찬성</th><th class="num">반대</th><th class="num">불참</th></tr></thead><tbody>
          <tr><td>발의·공동발의한 의원</td><td class="num">${t.yy}</td><td class="num">${t.yn}</td><td class="num">${t.yv}</td></tr>
          <tr><td>그 밖의 의원</td><td class="num">${t.ny}</td><td class="num">${t.nn}</td><td class="num">${t.nv}</td></tr></tbody></table></div>
          ${against.length ? `<p class="note">공동발의하고 반대한 의원: ${against.map(memLabel).join(', ')}</p>` : ''}`;
      }
      h += `<details ${b.votes.length <= 3 ? 'open' : ''}><summary>${esc(v.date)} ${v.ch === 'H' ? '하원' : '상원'} ${v.clerk}번 · ${esc(v.q)} · ${esc(v.res)} (${v.yea}–${v.nay})</summary>
        <p><a href="#" data-open="vote:${v.id}">표결 자세히 보기</a></p>${x}</details>`;
    }
  }
  const csl = active.map(c => [typeof c[0] === 'number' ? R[c[0]] : null, c]).sort((a, b) => (a[1][1] || '').localeCompare(b[1][1] || ''));
  h += `<details><summary>공동발의자 명단 (${active.length}명)</summary><div class="tbl-wrap"><table><thead><tr><th>의원</th><th>날짜</th><th>처음부터</th><th>성별</th><th>인종</th><th class="num">농촌</th><th class="num">당파 지수</th></tr></thead><tbody>
    ${csl.map(([m, c]) => `<tr${m ? ` class="click" data-open="mem:${m.b}"` : ''}><td>${m ? memLabel(m) : esc(c[0])}</td><td>${esc(c[1])}</td><td>${c[2] ? '예' : ''}</td><td>${m ? (m.g === 'F' ? '여' : '남') : ''}</td><td>${m ? [...(m.race || '')].map(r => RACE[r]).join(', ') : ''}</td><td class="num">${m && m.rural != null ? fmt(m.rural, 0) + '%' : ''}</td><td class="num">${m ? pviLabel(m.pvi) : ''}</td></tr>`).join('')}</tbody></table></div></details>`;
  return h;
}

function votePanel(id) {
  const v = S.D.voteIndex[id]; if (!v) return '<p>표결을 찾을 수 없습니다.</p>';
  const b = S.D.billIndex[v.bill];
  const R = S.D.members[v.ch];
  const t = TOPIC[v.topics[0]] || {};
  let h = `<h2>${v.ch === 'H' ? '하원' : '상원'} ${esc(v.date)} ${v.clerk}번 표결</h2>
  <div>${topicTags(v.topics)} <span class="tag">${VT[v.vt] || v.vt}</span> ${v.commem ? '<span class="tag commem">기념</span>' : ''}</div>
  <div class="kv"><div>표결</div><div>${esc(v.q)} — <b>${esc(v.res)}</b> (${v.yea}–${v.nay})</div>
  <div>대상</div><div>${b ? `<a href="#" data-open="bill:${b.id}">${esc(b.bl)} ${esc(b.title)}</a>` : esc(v.bl)}</div>
  ${v.amdt ? `<div>수정안</div><div>${esc(v.amdt.num || '')} ${esc(v.amdt.text || '')}</div>` : ''}
  ${v.desc ? `<div>설명</div><div>${esc(v.desc)}</div>` : ''}
  <div>찬성의 뜻</div><div>${v.dir === 1 ? esc(t.plus || '확대') + ' 쪽' : v.dir === -1 ? esc(t.minus || '제한') + ' 쪽' : '방향 없음(자동 판정하지 않음)'}</div>
  <div>분류 근거</div><div class="muted">${(v.basis || []).map(esc).join(' · ')}</div></div>
  <h3>${esc(CMP[S.cmp].label)}별 찬반</h3>${groupBreakdownVote(v)}${plotBlock('vote', v.id)}`;
  const names = { '1': [], '2': [], '3': [] };
  R.forEach((m, i) => { const c = v.cast[i]; if (names[c]) names[c].push(m); });
  h += `<details><summary>의원별 표 보기</summary>${[['1', '찬성'], ['2', '반대'], ['3', '불참·출석']].map(([k, l]) => `<p><b>${l} (${names[k].length})</b>: ${names[k].map(memLabel).join(', ')}</p>`).join('')}</details>`;
  return h;
}

function memberPanel(bg) {
  const R = roster();
  const m = R.find(x => x.b === bg) || S.D.members[S.ch === 'H' ? 'S' : 'H'].find(x => x.b === bg);
  if (!m) return '<p>의원을 찾을 수 없습니다.</p>';
  const B = (S.D.billsBy[m.ch] || []).filter(b => scopeOk(b) && topicMatch(b.topics));
  const V = (S.D.votes[m.ch] || []).filter(v => scopeOk(v) && topicMatch(v.topics) && (S.vtype === 'all' || VT_FILTER[S.vtype].includes(v.vt)));
  const spon = B.filter(b => b.sp === m.i), cos = B.filter(b => b.cs.some(c => c[0] === m.i && !c[3]));
  let plus = 0, n = 0;
  const vrows = V.map(v => { const c = v.cast[m.i]; if (v.dir && (c === '1' || c === '2')) { n++; if ((c === '1' && v.dir === 1) || (c === '2' && v.dir === -1)) plus++; } return [v, c]; }).filter(x => x[1] && x[1] !== '0');
  const bl = list => list.map(b => `<li><a href="#" data-open="bill:${b.id}">${esc(b.bl)}</a> ${esc(b.title)} ${dirTag(b.topics[0], b.dir)}</li>`).join('');
  return `<h2>${memLabel(m)}</h2>
  <div class="kv"><div>성별·나이</div><div>${m.g === 'F' ? '여성' : '남성'}, ${m.age ?? '–'}세(회기 시작 때)</div>
  <div>인종</div><div>${[...(m.race || '')].map(c => RACE[c]).join(', ') || '백인·기타'}</div>
  <div>재임</div><div>${esc(m.fr)} ~ ${esc(m.to)} · 이 원에서 ${m.nc}번째 회기 · 의회 경력 ${fmt(m.yrs, 1)}년</div>
  <div>${m.ch === 'H' ? '지역구' : '주'}</div><div>농촌 인구 ${m.rural != null ? fmt(m.rural, 1) + '%' : '–'} · 당파 지수 ${pviLabel(m.pvi) || '–'}${m.ln ? ' <span class="muted">(선거구 경계가 인구조사 파일과 다름)</span>' : ''}<br>
    비히스패닉 백인 ${fmt(m.white, 1)}% · 흑인 ${fmt(m.black, 1)}% · 히스패닉 ${fmt(m.hisp, 1)}% · 대졸 ${fmt(m.ba, 1)}% · 가구 소득 중앙값 ${m.inc ? m.inc.toLocaleString() + '달러' : '–'}</div>
  <div>DW-NOMINATE</div><div>${fmt(m.dw1, 3)}, ${fmt(m.dw2, 3)}</div>
  ${m.rel ? `<div>종교</div><div>${esc(m.rel)}</div>` : ''}${m.cau ? `<div>코커스</div><div>${m.cau.map(esc).join(', ')}</div>` : ''}${m.fac ? `<div>계파</div><div>${m.fac.map(esc).join(', ')}</div>` : ''}
  <div>확대 쪽 표</div><div>${n ? `${pct(plus / n, 0)} (${plus}/${n})` : '방향이 정해진 표결 없음'}</div></div>
  <h3>대표발의 (${spon.length})</h3><ul>${bl(spon) || '<li class="muted">없음</li>'}</ul>
  <h3>공동발의 (${cos.length})</h3><details ${cos.length <= 15 ? 'open' : ''}><summary>목록</summary><ul>${bl(cos) || '<li class="muted">없음</li>'}</ul></details>
  <h3>표결 (${vrows.length})</h3><div class="tbl-wrap"><table><thead><tr><th>날짜</th><th>법안</th><th>표결</th><th>표</th><th>찬성의 뜻</th></tr></thead><tbody>
  ${vrows.map(([v, c]) => `<tr class="click" data-open="vote:${v.id}"><td>${esc(v.date)}</td><td>${esc(v.bl)}</td><td>${esc(v.q)}</td><td>${c === '1' ? '찬성' : c === '2' ? '반대' : '불참'}</td><td>${v.dir ? dirTag(v.topics[0], v.dir) : ''}</td></tr>`).join('')}</tbody></table></div>`;
}

function summaryScatter(st) {
  const R = roster();
  const ymode = S.sumY || 'cs';
  const pts = R.map((m, i) => ({ m, y: ymode === 'cs' ? st[i].sp + st[i].cs : (st[i].n ? st[i].plus / st[i].n : null) })).filter(p => p.m.dw1 != null && p.y != null);
  if (!pts.length) return '<p class="muted">그릴 자료가 없습니다.</p>';
  const W = 620, H = 400, L = 56, T = 16, R0 = 16, B = 64, pw = W - L - R0, ph = H - T - B;
  const niceStep = x => { const e = Math.pow(10, Math.floor(Math.log10(x))); const f = x / e; return (f <= 1 ? 1 : f <= 2 ? 2 : f <= 5 ? 5 : 10) * e; };
  const step = ymode === 'cs' ? Math.max(1, niceStep(Math.max(1, ...pts.map(p => p.y)) / 4)) : 0.25;
  const ymax = ymode === 'cs' ? step * Math.ceil(Math.max(1, ...pts.map(p => p.y)) / step) : 1;
  const nt = Math.round(ymax / step);
  const sx = x => L + (x + 1) / 2 * pw, sy = y => T + (1 - y / ymax) * ph;
  const grp = S.plotGroup, inG = m => grp && groupsOf(m, {}).includes(grp);
  let g = `<rect width="${W}" height="${H}" fill="#fff"/><rect x="${L}" y="${T}" width="${pw}" height="${ph}" fill="none" stroke="#bbb"/>`;
  for (const v of [-1, -0.5, 0, 0.5, 1]) g += `<line x1="${sx(v)}" y1="${T}" x2="${sx(v)}" y2="${T + ph}" stroke="#eee"/><text x="${sx(v)}" y="${T + ph + 15}" text-anchor="middle" font-size="10.5" fill="#555">${v}</text>`;
  for (let k = 0; k <= nt; k++) { const v = step * k; g += `<line x1="${L}" y1="${sy(v)}" x2="${L + pw}" y2="${sy(v)}" stroke="#eee"/><text x="${L - 6}" y="${sy(v) + 4}" text-anchor="end" font-size="10.5" fill="#555">${ymode === 'cs' ? Math.round(v) : Math.round(v * 100) + '%'}</text>`; }
  g += `<text x="${L + pw / 2}" y="${T + ph + 32}" text-anchor="middle" font-size="11.5" fill="#333">DW-NOMINATE 1차원 (진보 ← → 보수)</text>`;
  g += `<text transform="translate(14 ${T + ph / 2}) rotate(-90)" text-anchor="middle" font-size="11.5" fill="#333">${ymode === 'cs' ? '여성정책 법안 발의·공동발의 수' : '확대·보호 쪽 표 비율'}</text>`;
  pts.sort((a, b) => (inG(a.m) ? 1 : 0) - (inG(b.m) ? 1 : 0));
  for (const { m, y } of pts) {
    const em = !grp || inG(m), col = PC[m.pc] || PC.I;
    g += `<circle cx="${sx(m.dw1).toFixed(1)}" cy="${sy(y).toFixed(1)}" r="3.6" fill="${col}" fill-opacity="${em ? 0.8 : 0.18}" stroke="${em && grp ? '#111' : 'none'}" stroke-width="0.8"><title>${esc(m.n)} (${m.p}-${m.st}): ${ymode === 'cs' ? y + '건' : Math.round(y * 100) + '%'}</title></circle>`;
  }
  const ly = T + ph + 50; let lx = L;
  for (const [p, l] of [['D', '민주'], ['R', '공화']]) { g += `<circle cx="${lx + 5}" cy="${ly}" r="5" fill="${PC[p]}"/><text x="${lx + 14}" y="${ly + 4}" font-size="11" fill="#333">${l}</text>`; lx += 58; }
  if (grp) g += `<text x="${lx + 10}" y="${ly + 4}" font-size="11" fill="#333">진하게(테두리) = ${esc(CMP[S.cmp].label)}: ${esc(grp)}</text>`;
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" width="100%" style="max-width:${W}px;font-family:system-ui,'Apple SD Gothic Neo','Malgun Gothic','Noto Sans KR',sans-serif">${g}</svg>`;
}

/* ---------- DW-NOMINATE plot ---------- */
const PC = { D: '#2f6db5', R: '#c2413a', I: '#7b7b7b' };
function plotGroups(ch, date) {
  const set = new Set();
  (S.D.members[ch] || []).forEach(m => groupsOf(m, { date }).forEach(g => set.add(g)));
  return orderGroups([...set].filter(g => g !== '자료 없음' && g !== '해당 없음'));
}
function nomSVG(points, opt) {
  // points: [{m, k}] k = 'y' | 'n' | 'v' (vote) or 'c' | 'o' (cosponsor / not)
  const W = 620, H = 640, L = 60, T = opt.bw ? 70 : 24, R0 = 20, B = opt.bw ? 120 : 92;
  const pw = W - L - R0, ph = H - T - B;
  const sx = x => L + (x + 1) / 2 * pw, sy = y => T + (1 - (y + 1) / 2) * ph;
  const grp = opt.group, inG = m => grp && groupsOf(m, opt.ctx).includes(grp);
  let g = `<rect width="${W}" height="${H}" fill="#fff"/>`;
  if (opt.bw) g += `<text x="${W / 2}" y="26" text-anchor="middle" font-size="15" font-weight="700" fill="#111">${esc(opt.title)}</text><text x="${W / 2}" y="46" text-anchor="middle" font-size="11.5" fill="#444">${esc(opt.sub || '')}</text>`;
  g += `<rect x="${L}" y="${T}" width="${pw}" height="${ph}" fill="none" stroke="#bbb"/>`;
  for (const v of [-0.5, 0, 0.5]) {
    g += `<line x1="${sx(v)}" y1="${T}" x2="${sx(v)}" y2="${T + ph}" stroke="${v === 0 ? '#ccc' : '#eee'}"/><line x1="${L}" y1="${sy(v)}" x2="${L + pw}" y2="${sy(v)}" stroke="${v === 0 ? '#ccc' : '#eee'}"/>`;
  }
  for (const v of [-1, -0.5, 0, 0.5, 1]) {
    g += `<text x="${sx(v)}" y="${T + ph + 16}" text-anchor="middle" font-size="10.5" fill="#555">${v}</text><text x="${L - 8}" y="${sy(v) + 4}" text-anchor="end" font-size="10.5" fill="#555">${v}</text>`;
  }
  g += `<text x="${L + pw / 2}" y="${T + ph + 34}" text-anchor="middle" font-size="11.5" fill="#333">DW-NOMINATE 1차원 (진보 ← → 보수)</text>`;
  g += `<text transform="translate(16 ${T + ph / 2}) rotate(-90)" text-anchor="middle" font-size="11.5" fill="#333">DW-NOMINATE 2차원</text>`;
  // draw de-emphasized first, emphasized last
  const sorted = points.slice().sort((a, b) => (inG(a.m) ? 1 : 0) - (inG(b.m) ? 1 : 0));
  for (const { m, k } of sorted) {
    if (m.dw1 == null || m.dw2 == null) continue;
    const x = sx(m.dw1), y = sy(m.dw2), em = !grp || inG(m);
    let col = opt.bw ? (em ? '#000' : '#9a9a9a') : (PC[m.pc] || PC.I);
    const op = em ? 1 : (opt.bw ? 1 : 0.28), sw = opt.bw ? (em && grp ? 1.9 : 1.1) : 1.4;
    const r = 4.2;
    if (k === 'y' || k === 'c') {
      g += opt.bw ? `<circle cx="${x}" cy="${y}" r="${r}" fill="${k === 'c' ? col : 'none'}" stroke="${col}" stroke-width="${sw}" opacity="${op}"/>`
        : `<circle cx="${x}" cy="${y}" r="${r}" fill="${col}" fill-opacity="${0.85 * op}" stroke="${em && grp ? '#111' : col}" stroke-width="${em && grp ? 1 : 0.6}" opacity="${op}"/>`;
    } else if (k === 'n') {
      g += `<path d="M${x - r},${y - r}L${x + r},${y + r}M${x - r},${y + r}L${x + r},${y - r}" stroke="${col}" stroke-width="${sw + 0.3}" opacity="${op}"/>`;
    } else if (k === 'o') {
      g += `<circle cx="${x}" cy="${y}" r="${r - 0.6}" fill="none" stroke="${col}" stroke-width="0.9" opacity="${opt.bw ? op : 0.55 * op}"/>`;
    } else {
      g += `<circle cx="${x}" cy="${y}" r="1.6" fill="${col}" opacity="${0.6 * op}"/>`;
    }
  }
  // legend
  const ly = T + ph + 52;
  const items = opt.kind === 'vote' ? [['y', '찬성'], ['n', '반대'], ['v', '불참·출석']] : [['c', '발의·공동발의'], ['o', '하지 않음']];
  let lx = L;
  const sym = (k, x, y, col) => k === 'n' ? `<path d="M${x - 4},${y - 4}L${x + 4},${y + 4}M${x - 4},${y + 4}L${x + 4},${y - 4}" stroke="${col}" stroke-width="1.6"/>`
    : k === 'v' ? `<circle cx="${x}" cy="${y}" r="1.8" fill="${col}"/>` : `<circle cx="${x}" cy="${y}" r="4.2" fill="${(k === 'c' || (!opt.bw && k === 'y')) ? col : 'none'}" stroke="${col}" stroke-width="1.3"/>`;
  if (!opt.bw) {
    for (const [p, l] of [['D', '민주'], ['R', '공화']]) { g += `<circle cx="${lx + 5}" cy="${ly}" r="5" fill="${PC[p]}"/><text x="${lx + 14}" y="${ly + 4}" font-size="11" fill="#333">${l}</text>`; lx += 58; }
    lx += 10;
  }
  for (const [k, l] of items) { g += sym(k, lx + 5, ly, opt.bw ? '#000' : '#444') + `<text x="${lx + 15}" y="${ly + 4}" font-size="11" fill="#333">${l}</text>`; lx += 30 + l.length * 11; }
  if (grp) g += `<text x="${L}" y="${ly + 22}" font-size="11" fill="#333">${opt.bw ? '검은색·굵게' : '진하게(테두리)'} = ${esc(CMP[S.cmp].label)}: ${esc(grp)} · ${opt.bw ? '회색' : '흐리게'} = 그 밖의 의원</text>`;
  if (opt.bw) g += `<text x="${L}" y="${ly + 42}" font-size="10" fill="#666">자료: Voteview(DW-NOMINATE), ${opt.kind === 'vote' ? 'Voteview 호명투표' : 'GovInfo BILLSTATUS 공동발의'} · 미국 의회 여성정책 트래커</text>`;
  const miss = points.filter(p => p.m.dw1 == null).length;
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" width="100%" style="max-width:${W}px;font-family:system-ui,'Apple SD Gothic Neo','Malgun Gothic','Noto Sans KR',sans-serif">${g}</svg>` +
    (miss ? `<div class="muted" style="font-size:.8rem">DW-NOMINATE 값이 없는 의원 ${miss}명(대의원·새 의원 등)은 그림에서 빠졌습니다.</div>` : '');
}
function plotControls(ch, date) {
  const groups = plotGroups(ch, date);
  if (S.plotGroup && !groups.includes(S.plotGroup)) S.plotGroup = '';
  const opts = groups.map(gname => `<option value="${esc(gname)}" ${S.plotGroup === gname ? 'selected' : ''}>${esc(gname)}</option>`).join('');
  return `<div class="btns" style="align-items:center">
    <div class="seg"><button data-pmode="color" class="${S.plotMode !== 'bw' ? 'on' : ''}">컬러</button><button data-pmode="bw" class="${S.plotMode === 'bw' ? 'on' : ''}">흑백 O·X</button></div>
    <label class="fld">강조 <select data-pgroup><option value="">없음</option>${opts}</select></label></div>`;
}
let PLOT_SEQ = 0;
function plotBox(kind, id, heading) {
  const n = ++PLOT_SEQ;
  return `${heading ? `<h3>${heading}</h3>` : ''}<div class="plotbox" id="pb${n}" data-kind="${kind}" data-id="${esc(id)}"></div>
    <div class="btns"><button class="btn" data-psave="png" data-box="pb${n}">PNG 저장</button><button class="btn" data-psave="svg" data-box="pb${n}">SVG 저장</button></div>`;
}
function plotBlock(kind, id) {
  const it = kind === 'vote' ? S.D.voteIndex[id] : S.D.billIndex[id];
  return `<h3>DW-NOMINATE 그림</h3>${plotControls(it.ch, kind === 'vote' ? it.date : it.intro)}${plotBox(kind, id, '')}`;
}
function voteHeading(v) { return `표결: ${esc(v.date)} ${v.ch === 'H' ? '하원' : '상원'} ${v.clerk}번 · ${esc(v.q)} · ${esc(v.res)} (${v.yea}–${v.nay})${v.amdt ? ` · 수정안 ${esc(v.amdt.num || '')}` : ''}`; }
function billPlots(b) {
  let h = `<h2>공동발의자</h2>${plotControls(b.ch, b.intro)}${plotBox('bill', b.id, '')}`;
  const vs = b.votes.map(id => S.D.voteIndex[id]).filter(Boolean);
  if (vs.length) {
    h += `<h2>이 법안의 표결 (${vs.length}건)</h2>`;
    vs.forEach(v => { h += plotBox('vote', v.id, voteHeading(v) + ` <a href="#" data-open="vote:${v.id}" style="font-weight:400;font-size:.85rem">자세히</a>`); });
  }
  return h;
}
function renderPlot() {
  document.querySelectorAll('.plotbox').forEach(box => {
    const kind = box.dataset.kind, id = box.dataset.id;
    let points, opt;
    if (kind === 'vote') {
      const v = S.D.voteIndex[id]; const R = S.D.members[v.ch];
      points = R.map((m, i) => ({ m, k: v.cast[i] === '1' ? 'y' : v.cast[i] === '2' ? 'n' : v.cast[i] === '3' ? 'v' : null })).filter(p => p.k);
      opt = { kind, ctx: { date: v.date }, title: `${S.D.congress}대 ${v.ch === 'H' ? '하원' : '상원'} ${v.date} ${v.clerk}번: ${v.bl}`, sub: `${v.q} — ${v.res} (${v.yea}–${v.nay})` };
      box._name = id;
    } else {
      const b = S.D.billIndex[id]; const R = S.D.members[b.ch];
      const cs = new Set(b.cs.filter(c => !c[3] && typeof c[0] === 'number').map(c => c[0])); if (typeof b.sp === 'number') cs.add(b.sp);
      points = R.filter(m => (m.fr <= b.intro && b.intro <= m.to) || cs.has(m.i)).map(m => ({ m, k: cs.has(m.i) ? 'c' : 'o' }));
      opt = { kind, ctx: { date: b.intro }, title: `${S.D.congress}대 ${b.bl} 발의·공동발의`, sub: b.title.length > 80 ? b.title.slice(0, 78) + '…' : b.title };
      box._name = `${S.D.congress}_${b.bl.replace(/[^A-Za-z0-9]/g, '')}_cosponsors`;
    }
    opt.bw = S.plotMode === 'bw'; opt.group = S.plotGroup || '';
    box.innerHTML = nomSVG(points, opt);
    if (opt.bw) box._name += '_bw';
  });
}
function savePlot(fmt, boxId) {
  const box = document.getElementById(boxId); const svg = box && box.querySelector('svg'); if (!svg) return;
  const xml = new XMLSerializer().serializeToString(svg);
  const name = 'dwnominate_' + (box._name || 'plot');
  if (fmt === 'svg') { const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([xml], { type: 'image/svg+xml' })); a.download = name + '.svg'; a.click(); return; }
  const img = new Image(); const vb = svg.viewBox.baseVal; const k = 3;
  img.onload = () => { const c = document.createElement('canvas'); c.width = vb.width * k; c.height = vb.height * k; const x = c.getContext('2d'); x.fillStyle = '#fff'; x.fillRect(0, 0, c.width, c.height); x.drawImage(img, 0, 0, c.width, c.height);
    c.toBlob(bl => { const a = document.createElement('a'); a.href = URL.createObjectURL(bl); a.download = name + '.png'; a.click(); }); };
  img.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(xml);
}
function bindPlot(root) {
  root.querySelectorAll('[data-pmode]').forEach(b => b.addEventListener('click', () => { S.plotMode = b.dataset.pmode; root.querySelectorAll('[data-pmode]').forEach(x => x.classList.toggle('on', x.dataset.pmode === S.plotMode)); renderPlot(); }));
  root.querySelectorAll('[data-pgroup]').forEach(sel => sel.addEventListener('change', () => { S.plotGroup = sel.value; root.querySelectorAll('[data-pgroup]').forEach(x => { x.value = S.plotGroup; }); renderPlot(); }));
  root.querySelectorAll('[data-psave]').forEach(b => b.addEventListener('click', () => savePlot(b.dataset.psave, b.dataset.box)));
  renderPlot();
}

function openPanel(key) {
  S.open = key;
  const [kind, id] = [key.slice(0, key.indexOf(':')), key.slice(key.indexOf(':') + 1)];
  $('#panelBody').innerHTML = kind === 'bill' ? billPanel(id) : kind === 'vote' ? votePanel(id) : memberPanel(id);
  $('#panel').hidden = false;
  $('#panel .panel-in').scrollTop = 0;
  bindTables($('#panelBody'));
  bindPlot($('#panelBody'));
  writeHash();
}
function closePanel() { S.open = null; $('#panel').hidden = true; writeHash(); }

/* ---------- downloads ---------- */
function memberCols() {
  return [['congress', '회기', 'long'], ['chamber', '원(H/S)', 'str'], ['bioguide', 'Bioguide ID', 'str'], ['icpsr', 'ICPSR(Voteview)', 'long'],
    ['name', '이름', 'str'], ['party', '정당', 'str'], ['caucus_party', '함께하는 정당(무소속 포함)', 'str'], ['state', '주', 'str'], ['district', '선거구(0=전역·대의원)', 'long'],
    ['delegate', '대의원(1)', 'byte'], ['female', '여성(1)', 'byte'], ['black', '흑인(1)', 'byte'], ['hispanic', '히스패닉(1)', 'byte'], ['asian_pi', '아시아·태평양계(1)', 'byte'],
    ['native_am', '원주민(1)', 'byte'], ['age', '나이(회기 시작)', 'long'], ['n_congress', '이 원에서 몇 번째 회기', 'long'], ['years_cong', '의회 경력(년)', 'double'],
    ['region', '권역', 'str'], ['religion', '종교', 'str'], ['caucus', '코커스', 'str'], ['faction', '계파', 'str'], ['rural_pct', '농촌 인구 비율(%)', 'double'],
    ['pvi', '당파 지수(+민주, Cook 방식)', 'double'], ['white_nh', '비히스패닉 백인 비율(%)', 'double'], ['black_pct', '흑인 비율(%)', 'double'], ['hisp_pct', '히스패닉 비율(%)', 'double'],
    ['asian_pct', '아시아계 비율(%)', 'double'], ['ba_plus', '대졸 비율(%)', 'double'], ['med_income', '가구 소득 중앙값(달러)', 'long'], ['dw1', 'DW-NOMINATE 1차원', 'double'], ['dw2', 'DW-NOMINATE 2차원', 'double'],
    ['served_from', '재임 시작(이 회기 안)', 'date'], ['served_to', '재임 끝(이 회기 안)', 'date']];
}
function memberVals(m) {
  const r = m.race || '';
  return [S.D.congress, m.ch, m.b, m.icpsr, m.n, m.p, m.pc, m.st, m.ch === 'H' ? (m.d || 0) : null, m.dl, m.g === 'F' ? 1 : 0, +r.includes('B'), +r.includes('H'), +r.includes('A'),
    +r.includes('N'), m.age, m.nc, m.yrs, m.reg, m.rel || '', (m.cau || []).join('; '), (m.fac || []).join('; '), m.rural, m.pvi, m.white, m.black, m.hisp, m.asian, m.ba, m.inc,
    m.dw1, m.dw2, m.fr, m.to];
}
function datasets() {
  const R = roster(), B = filteredBills(), V = filteredVotes(), st = memberStats(B, V);
  const tl = t => (TOPIC[t] || {}).label || t;
  const dl = (t, d) => d === 1 ? (TOPIC[t] || {}).plus : d === -1 ? (TOPIC[t] || {}).minus : '방향 없음';
  const sname = x => typeof x === 'number' ? (R[x] || {}).n : x;
  return {
    bills: () => ({ cols: [['congress', '회기', 'long'], ['bill_id', '법안 ID', 'str'], ['bill', '법안 번호', 'str'], ['title', '법안 이름', 'str'], ['intro', '발의일', 'date'],
      ['topic', '세부 정책(주)', 'str'], ['topics', '세부 정책(모두)', 'str'], ['scope', '범위(core/broad)', 'str'], ['commem', '기념 결의안(1)', 'byte'], ['dir', '방향(+1 확대, -1 제한, 0 없음)', 'byte'],
      ['dir_label', '방향 이름', 'str'], ['policy_area', 'CRS 정책 분야', 'str'], ['sponsor', '대표발의 Bioguide', 'str'], ['sponsor_name', '대표발의자', 'str'], ['sponsor_party', '대표발의자 정당', 'str'],
      ['n_cosp', '공동발의 수(철회 제외)', 'long'], ['n_cosp_d', '민주 공동발의', 'long'], ['n_cosp_r', '공화 공동발의', 'long'], ['n_orig', '처음부터 공동발의', 'long'], ['n_withdrawn', '철회', 'long'],
      ['n_votes', '호명투표 수', 'long'], ['law', '법률 번호', 'str'], ['latest_date', '최근 처리일', 'date'], ['latest', '최근 처리', 'str'], ['basis', '분류 근거', 'str'], ['url', 'congress.gov', 'str']],
      rows: B.map(b => { const a = b.cs.filter(c => !c[3]); const p = x => a.filter(c => typeof c[0] === 'number' && (R[c[0]] || {}).pc === x).length; const sp = typeof b.sp === 'number' ? R[b.sp] : null;
        return [S.D.congress, b.id, b.bl, b.title, b.intro, tl(b.topics[0]), b.topics.map(tl).join('; '), b.scope, b.commem ? 1 : 0, b.dir, dl(b.topics[0], b.dir), b.pa,
          sp ? sp.b : b.sp, sp ? sp.n : '', sp ? sp.p : '', a.length, p('D'), p('R'), a.filter(c => c[2]).length, b.cs.length - a.length, b.votes.length, b.law, (b.latest || [])[0], (b.latest || [])[1], (b.basis || []).join(' | '), b.url]; }) }),
    cosponsors: () => ({ cols: [['congress', '회기', 'long'], ['bill_id', '법안 ID', 'str'], ['bill', '법안 번호', 'str'], ['topic', '세부 정책(주)', 'str'], ['dir', '방향', 'byte'], ['role', '역할(sponsor/cosponsor)', 'str'],
      ['date', '날짜', 'date'], ['original', '처음부터(1)', 'byte'], ['withdrawn', '철회(1)', 'byte']].concat(memberCols().slice(2)),
      rows: B.flatMap(b => { const out = []; const sp = typeof b.sp === 'number' ? R[b.sp] : null; if (sp) out.push([S.D.congress, b.id, b.bl, tl(b.topics[0]), b.dir, 'sponsor', b.intro, null, 0].concat(memberVals(sp).slice(2)));
        b.cs.forEach(c => { const m = typeof c[0] === 'number' ? R[c[0]] : null; if (m) out.push([S.D.congress, b.id, b.bl, tl(b.topics[0]), b.dir, 'cosponsor', c[1], c[2], c[3]].concat(memberVals(m).slice(2))); }); return out; }) }),
    votes: () => ({ cols: [['congress', '회기', 'long'], ['chamber', '원', 'str'], ['vote_id', '표결 ID', 'str'], ['date', '날짜', 'date'], ['roll', 'Voteview 번호', 'long'], ['clerk', '사무처 번호', 'long'],
      ['bill_id', '법안 ID', 'str'], ['bill', '법안', 'str'], ['amendment', '수정안', 'str'], ['question', '표결 질문', 'str'], ['result', '결과', 'str'], ['yea', '찬성', 'long'], ['nay', '반대', 'long'],
      ['vote_type', '표결 종류', 'str'], ['topic', '세부 정책(주)', 'str'], ['topics', '세부 정책(모두)', 'str'], ['yea_dir', '찬성의 방향(+1 확대, -1 제한)', 'byte'], ['measure_dir', '안건 방향', 'byte'],
      ['d_yea', '민주 찬성', 'long'], ['d_nay', '민주 반대', 'long'], ['r_yea', '공화 찬성', 'long'], ['r_nay', '공화 반대', 'long'], ['f_yea', '여성 의원 찬성', 'long'], ['f_nay', '여성 의원 반대', 'long'],
      ['desc', '설명', 'str'], ['basis', '분류 근거', 'str']],
      rows: V.map(v => { const c = { dy: 0, dn: 0, ry: 0, rn: 0, fy: 0, fn: 0 }; for (let i = 0; i < v.cast.length; i++) { const m = R[i]; const k = v.cast[i]; if (!m || (k !== '1' && k !== '2')) continue; const y = k === '1'; if (m.pc === 'D') c[y ? 'dy' : 'dn']++; if (m.pc === 'R') c[y ? 'ry' : 'rn']++; if (m.g === 'F') c[y ? 'fy' : 'fn']++; }
        return [S.D.congress, v.ch, v.id, v.date, v.roll, v.clerk, v.bill, v.bl, v.amdt ? `${v.amdt.num || ''} ${v.amdt.text || ''}`.trim() : '', v.q, v.res, v.yea, v.nay, VT[v.vt] || v.vt, tl(v.topics[0]), v.topics.map(tl).join('; '),
          v.dir, v.mdir, c.dy, c.dn, c.ry, c.rn, c.fy, c.fn, v.desc, (v.basis || []).join(' | ')]; }) }),
    member_votes: () => ({ cols: [['vote_id', '표결 ID', 'str'], ['date', '날짜', 'date'], ['bill', '법안', 'str'], ['topic', '세부 정책(주)', 'str'], ['yea_dir', '찬성의 방향', 'byte'],
      ['cast', '표(1 찬성, 2 반대, 3 불참·출석)', 'byte'], ['toward_plus', '확대 쪽 표(1/0)', 'byte']].concat(memberCols().slice(2)),
      rows: V.flatMap(v => { const out = []; for (let i = 0; i < v.cast.length; i++) { const k = v.cast[i]; if (k === '0' || !R[i]) continue; const tp = v.dir && (k === '1' || k === '2') ? (((k === '1' && v.dir === 1) || (k === '2' && v.dir === -1)) ? 1 : 0) : null;
        out.push([v.id, v.date, v.bl, tl(v.topics[0]), v.dir, +k, tp].concat(memberVals(R[i]).slice(2))); } return out; }) }),
    members: () => ({ cols: memberCols().concat([['n_spons', '대표발의 수(조건 기준)', 'long'], ['n_cosp', '공동발의 수(조건 기준)', 'long'], ['n_dir_votes', '방향이 정해진 표결 참여', 'long'], ['plus_share', '확대 쪽 표 비율', 'double']]),
      rows: R.map((m, i) => memberVals(m).concat([st[i].sp, st[i].cs, st[i].n, st[i].n ? st[i].plus / st[i].n : null])) }),
  };
}
function csvText(cols, rows) {
  const q = v => { if (v === null || v === undefined) return ''; const s = String(v); return /[",\n\r]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s; };
  return '﻿' + [cols.map(c => c[0]).join(',')].concat(rows.map(r => r.map(q).join(','))).join('\r\n');
}
function download(name, kind) {
  const ds = datasets()[name]();
  const tag = `${S.ch}${S.D.congress}` + (S.topic !== 'all' ? '_' + S.topic.replace('g:', '') : '');
  let blob, fn;
  if (kind === 'csv') { blob = new Blob([csvText(ds.cols, ds.rows)], { type: 'text/csv;charset=utf-8' }); fn = `gp_${name}_${tag}.csv`; }
  else { const u8 = writeDta(ds.cols.map(c => ({ name: c[0], label: c[1], type: c[2] })), ds.rows, `여성정책 트래커 ${name} ${tag}`); blob = new Blob([u8], { type: 'application/x-stata-dta' }); fn = `gp_${name}_${tag}.dta`; }
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = fn; document.body.appendChild(a); a.click();
  setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
}
function viewDownload() {
  const items = [['bills', '법안 목록', '한 줄 = 법안 하나'], ['cosponsors', '공동발의', '한 줄 = 법안 × 대표·공동발의 의원'], ['votes', '표결 목록', '한 줄 = 호명투표 하나(정당·여성 의원 찬반 수 포함)'],
    ['member_votes', '의원별 표', '한 줄 = 표결 × 의원'], ['members', '의원 명단', '한 줄 = 의원(특징 + 조건 기준 공동발의·표 요약)']];
  return `<p class="muted">${filterNote()} 기준으로 지금 화면의 조건이 그대로 적용됩니다.</p>
  ${items.map(([k, l, d]) => `<h3>${l}</h3><p class="muted">${d}</p><div class="btns"><button class="btn" data-dl="${k}:csv">CSV</button><button class="btn" data-dl="${k}:dta">Stata (.dta)</button></div>`).join('')}
  <p class="note">CSV는 UTF-8(BOM)이라 엑셀에서 한글이 그대로 보입니다. Stata에서 CSV는 <code>import delimited using "파일.csv", encoding(utf-8) clear</code>로 엽니다. .dta는 Stata 14 이상에서 열리며 변수 설명이 한글로 붙어 있습니다.</p>`;
}

function viewAbout() {
  const gen = S.idx.generated ? S.idx.generated.replace('T', ' ').replace('Z', ' UTC') : '';
  return `<div class="about">
  <h2>무엇을 보여 주나</h2>
  <p>미국 상·하원(111대, 2009년 ~ 현재)의 여성정책 법안과 호명투표를 세부 정책으로 나누고, 의원이 어떤 법안을 공동발의했고 어떻게 표결했는지를 의원 특징(성별, 인종, 지역구 농촌 비율, 당파 지수, 나이, 선수, 지역, 이념 위치, 지역구 인구 구성, 주 임신중지 법 등)에 따라 비교합니다. 기본은 정당 안에서 비교입니다(성별·인종이 정당과 많이 겹치기 때문).</p>
  <h2>자료</h2>
  <ul>
    <li>법안·공동발의·주제어: GovInfo BILLSTATUS(미 의회도서관·정부출판국)</li>
    <li>호명투표·DW-NOMINATE: Voteview (Lewis, Poole, Rosenthal, Boche, Rudkin, Sonnet)</li>
    <li>의원 성별·생일·임기: congress-legislators (unitedstates 프로젝트)</li>
    <li>인종: 하원 역사국(History, Art & Archives)과 CRS의 이름 명단을 바탕으로, 그 뒤 당선 의원은 공식 소개·보도로 의원마다 출처를 적어 정리했습니다. CRS 회기별 의원 구성 보고서의 인원수와 대조해 72칸 중 62칸이 일치하고 나머지도 이유를 확인했습니다(집계 시점 차이 등). 여러 집단에 속하는 의원은 각 집단에 모두 셉니다. 포르투갈계 의원은 CRS·하원 역사국처럼 히스패닉 코커스·콘퍼런스 회원이면 히스패닉으로 셌습니다(Pew는 빼므로 Pew 숫자와 다를 수 있음). 판단이 갈리는 의원과 근거는 저장소의 config/race_README.md에 있습니다.</li>
    <li>농촌 인구 비율: 미국 인구조사국 원본 파일. 118~119대 선거구는 2020년 인구조사, 113~117대는 2010년 인구조사(선거구별 도시·농촌 인구 파일). 111~112대는 공식 선거구별 파일이 없어 2010년 인구조사의 우편번호 구역(ZCTA) 단위 자료로 추정했습니다. 2020년 인구조사부터 '도시' 기준이 바뀌어(2,500명 → 5,000명 또는 2,000가구) 117대와 118대 사이 변화에는 기준 변경이 섞여 있습니다. 117대 노스캐롤라이나는 선거구가 바뀌었지만 2010년 기준 파일이 없어 116대 값을 썼습니다(표시됨). 상원은 주 전체 값입니다.</li>
    <li>당파 지수: Cook PVI와 같은 공식(2022년부터 쓰는 방식: 가장 최근 대선 75% + 그 전 대선 25%, 전국 양당 득표율과의 차이)으로 직접 계산했습니다. 지역구 대선 결과는 The Downballot, 주 결과와 전국 득표는 FEC 공식 집계입니다. 118대는 2016년 대선 결과가 그 선거구 기준으로 없어 2020년 결과만 썼습니다. Cook이 낸 값과 1점 안팎 다를 수 있습니다. 양수가 민주 쪽입니다.</li>
    <li>지역구 인구 구성(인종 구성·대졸 비율·가구 소득): 인구조사국 ACS 1년 추정치(원본 요약 파일). 회기마다 그 선거구 경계로 집계된 해를 씁니다(111대 2009년, 112대 2011년, 113대 2013년, 114대 2015년, 115대 2017년, 116대 2019년, 117대 2021년, 118대 2023년, 119대 2024년). 소득은 그해 달러 기준이라 회기끼리 비교할 때 물가를 감안해야 합니다.</li>
    <li>주 임신중지 법: 2021-09-01(텍사스 SB 8) 이후 주마다 실제로 시행된 임신 주수 제한을 날짜별로 정리(KFF, Guttmacher 등 여러 추적 자료와 법원 판결 보도로 대조). 그 전은 'Roe 시기'로 둡니다.</li>
  </ul>
  <h2>여성정책 분류(자동)</h2>
  <p>사람이 하나씩 확인하지 않고 규칙으로 자동 분류합니다. 법안 이름에 여성정책 낱말(임신중지, 피임, 모성 건강, 가정폭력, 성폭력, 동일임금, 임신 노동자, 여성 창업, 남녀평등 헌법 수정안, Title IX, 여성 참전군인 등)이 있거나, 주제어가 적은 법안에 여성 관련 CRS 주제어가 붙어 있으면 넣습니다. 수정안은 법안과 상관없이 수정안 내용으로 다시 판단합니다(예: 국방수권법의 임신중지 수정안). 다른 정책 영역과 겹쳐도 넣고, 겹치는 영역(CRS 정책 분야)을 함께 보여 줍니다.</p>
  <ul><li>빼는 것: 성소수자 차별 금지(여성을 직접 내세우지 않는 법안), 운동부 축하 결의안, '소수자·여성 소유 기업' 같은 구절만 있는 법안, 환경 법안의 '임신부' 낱말 등</li>
  <li>넓은 범위(처음엔 꺼 둠): 아이 돌봄·유급 가족휴가·WIC 영양 지원, 인신매매</li>
  <li>기념 결의안(처음엔 꺼 둠): 여성사의 달, 특정 여성 기리기 등</li>
  <li>방향: 세부 정책마다 내용만 적은 이름(예: 임신중지 '접근 확대/접근 제한')을 붙입니다. 법안 이름·수정안 설명의 낱말로 정하고, 정하기 어려우면 '방향 없음'으로 둡니다. 표결에서는 안건의 방향에 표결 종류를 곱해 '찬성의 뜻'을 정합니다(예: 수정안 보류 동의에 찬성 = 수정안 반대). 의사규칙·재회부 동의 등은 방향을 매기지 않습니다.</li></ul>
  <h2>DW-NOMINATE 그림</h2>
  <p>표결 창과 법안 창에서 의원들의 이념 위치(Voteview의 DW-NOMINATE 1·2차원)에 찬성(O)·반대(X)·불참(점) 또는 발의·공동발의(채운 점)·하지 않음(빈 점)을 찍어 보여 줍니다. 컬러(정당 색)와 흑백 O·X 두 방식이 있고, 위에서 고른 비교 기준의 한 집단(예: 여성)을 강조할 수 있습니다. PNG(3배 해상도)·SVG로 저장됩니다. 분할선(cutting line)은 그리지 않았습니다.</p>
  <h2>세부 정책</h2><ul>${(S.idx.groups || []).map(g => `<li><b>${esc(g.label)}</b>: ${(S.idx.topics || []).filter(t => t.group === g.code).map(t => esc(t.label)).join(', ')}</li>`).join('')}</ul>
  <h2>주의</h2>
  <ul><li>자동 분류라 잘못 들어가거나 빠진 법안이 있을 수 있습니다. 법안 창의 '분류 근거'를 함께 보세요.</li>
  <li>공동발의 비율은 법안 발의일에 재임 중이던 의원을 분모로 셉니다.</li>
  <li>대의원(워싱턴 DC·푸에르토리코 등)은 공동발의에는 들어가지만 본회의 표결권이 없고, 당파 지수는 DC만 있습니다.</li>
  <li>여성정책 관련 코커스는 공개된 전체 명단을 구할 수 있는 경우만 넣었습니다(119대: 하원 Reproductive Freedom Caucus(옛 Pro-Choice Caucus), 하원 민주당 여성 코커스, 상원 Pro-Life Caucus). 명단은 한 시점의 것이라 회기 중에 떠난 의원은 빠져 있을 수 있습니다.</li></ul>
  <p class="muted">마지막 갱신: ${esc(gen)} · 매일 한 번 GitHub Actions가 자료를 다시 받아 만듭니다. 코드와 자료: <a href="https://github.com/jongkonlee/genderpolitics">github.com/jongkonlee/genderpolitics</a></p></div>`;
}

/* ---------- events & state ---------- */
function bindTables(root) {
  root = root || $('#main');
  root.querySelectorAll('[data-open]').forEach(el => el.addEventListener('click', e => { e.preventDefault(); openPanel(el.dataset.open); }));
  root.querySelectorAll('[data-topic]').forEach(el => el.addEventListener('click', () => { S.topic = el.dataset.topic; $('#topicSel').value = S.topic; S.page = 0; render(); }));
  root.querySelectorAll('[data-sort]').forEach(el => el.addEventListener('click', () => { const k = el.dataset.sort; S.sort = S.sort && S.sort.k === k ? { k, d: -S.sort.d } : { k, d: k === 'cs' || k === 'votes' || k === 'plus' || k === 'margin' ? -1 : 1 }; render(); }));
  root.querySelectorAll('[data-page]').forEach(el => el.addEventListener('click', () => { S.page = +el.dataset.page; render(); window.scrollTo(0, $('#tabs').offsetTop); }));
  root.querySelectorAll('[data-dl]').forEach(el => el.addEventListener('click', () => { const [n, k] = el.dataset.dl.split(':'); download(n, k); }));
  root.querySelectorAll('[data-sumy]').forEach(el => el.addEventListener('click', () => { S.sumY = el.dataset.sumy; render(); }));
  root.querySelectorAll('[data-sumgroup]').forEach(el => el.addEventListener('change', () => { S.plotGroup = el.value; render(); }));
}

function writeHash() {
  const p = new URLSearchParams();
  p.set('c', S.c); p.set('ch', S.ch); if (S.tab !== 'summary') p.set('tab', S.tab); if (S.topic !== 'all') p.set('topic', S.topic);
  if (S.cmp !== 'gender') p.set('cmp', S.cmp); if (!S.within) p.set('within', '0'); if (S.commem) p.set('commem', '1'); if (S.broad) p.set('broad', '1');
  if (S.vtype !== 'all') p.set('vt', S.vtype); if (S.dir !== 'all') p.set('dir', S.dir); if (S.q) p.set('q', S.q); if (S.open) p.set('open', S.open);
  history.replaceState(null, '', '#' + p.toString());
}
function readHash() {
  const p = new URLSearchParams(location.hash.slice(1));
  if (p.get('c')) S.c = +p.get('c'); if (p.get('ch')) S.ch = p.get('ch') === 'S' ? 'S' : 'H'; if (p.get('tab')) S.tab = p.get('tab');
  if (p.get('topic')) S.topic = p.get('topic'); if (p.get('cmp') && CMP[p.get('cmp')]) S.cmp = p.get('cmp'); S.within = p.get('within') !== '0';
  S.commem = p.get('commem') === '1'; S.broad = p.get('broad') === '1'; if (p.get('vt')) S.vtype = p.get('vt'); if (p.get('dir')) S.dir = p.get('dir');
  S.q = p.get('q') || ''; S.open = p.get('open');
}

function fillControls() {
  const cs = S.idx.congresses.map(x => x.c).sort((a, b) => b - a);
  $('#congressSel').innerHTML = cs.map(c => `<option value="${c}">${c}대 (${1789 + 2 * (c - 1)}–${1789 + 2 * (c - 1) + 2})</option>`).join('');
  let t = '<option value="all">전체</option>';
  for (const g of S.idx.groups) {
    t += `<optgroup label="${esc(g.label)}"><option value="g:${g.code}">${esc(g.label)} 전체</option>`;
    t += S.idx.topics.filter(x => x.group === g.code).map(x => `<option value="${x.code}">${esc(x.label)}</option>`).join('') + '</optgroup>';
  }
  $('#topicSel').innerHTML = t;
  fillCmp();
}
function fillCmp() {
  const R = S.D ? [...S.D.members.H, ...S.D.members.S] : [];
  const has = { rel: R.some(m => m.rel), cau: R.some(m => m.cau), fac: R.some(m => m.fac), law: (S.idx.abortion_law || []).length > 0, race: S.raceLoaded };
  const opts = Object.entries(CMP).filter(([k, v]) => !v.needs || has[v.needs]);
  if (!opts.some(([k]) => k === S.cmp)) S.cmp = 'gender';
  $('#cmpSel').innerHTML = opts.map(([k, v]) => `<option value="${k}">${esc(v.label)}</option>`).join('');
  $('#cmpSel').value = S.cmp;
}
function syncControls() {
  $('#congressSel').value = S.c; $('#topicSel').value = S.topic; $('#cmpSel').value = S.cmp; $('#withinChk').checked = S.within;
  $('#commemChk').checked = S.commem; $('#broadChk').checked = S.broad; $('#vtypeSel').value = S.vtype; $('#dirSel').value = S.dir; $('#searchBox').value = S.q;
}

async function init() {
  try {
    S.idx = await getJSON('data/index.json');
  } catch (e) {
    $('#main').innerHTML = '<p>자료를 아직 만들고 있습니다. 잠시 뒤 다시 열어 주세요.</p>'; return;
  }
  TOPIC = Object.fromEntries(S.idx.topics.map(t => [t.code, t]));
  try { const pj = await getJSON('data/people.json'); S.people = pj.people || {}; S.raceLoaded = !!pj.race_loaded; } catch (e) { S.people = {}; S.raceLoaded = false; }
  S.c = S.idx.congresses.length ? Math.max(...S.idx.congresses.map(x => x.c)) : null;
  readHash();
  if (!S.idx.congresses.some(x => x.c === S.c)) S.c = Math.max(...S.idx.congresses.map(x => x.c));
  fillControls();
  await loadCongress(S.c);
  fillCmp(); syncControls();
  const on = (sel, ev, fn) => $(sel).addEventListener(ev, fn);
  document.querySelectorAll('#chamberSeg button').forEach(b => b.addEventListener('click', async () => { S.ch = b.dataset.ch; S.page = 0; S.sort = null; await loadCongress(S.c); render(); }));
  on('#congressSel', 'change', async e => { S.c = +e.target.value; S.page = 0; $('#main').innerHTML = '<p class="muted">불러오는 중…</p>'; await loadCongress(S.c); fillCmp(); render(); });
  on('#topicSel', 'change', e => { S.topic = e.target.value; S.page = 0; render(); });
  on('#cmpSel', 'change', e => { S.cmp = e.target.value; S.plotGroup = ''; render(); });
  on('#withinChk', 'change', e => { S.within = e.target.checked; render(); });
  on('#commemChk', 'change', e => { S.commem = e.target.checked; S.page = 0; render(); });
  on('#broadChk', 'change', e => { S.broad = e.target.checked; S.page = 0; render(); });
  on('#vtypeSel', 'change', e => { S.vtype = e.target.value; S.page = 0; render(); });
  on('#dirSel', 'change', e => { S.dir = e.target.value; S.page = 0; render(); });
  let tmr; on('#searchBox', 'input', e => { clearTimeout(tmr); tmr = setTimeout(() => { S.q = e.target.value.trim(); S.page = 0; render(); }, 250); });
  document.querySelectorAll('#tabs button').forEach(b => b.addEventListener('click', () => { S.tab = b.dataset.tab; S.page = 0; S.sort = null; render(); }));
  on('#panelClose', 'click', closePanel);
  on('#panel', 'click', e => { if (e.target.id === 'panel') closePanel(); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && !$('#panel').hidden) closePanel(); });
  $('#foot').innerHTML = `마지막 갱신 ${esc((S.idx.generated || '').replace('T', ' ').replace('Z', ' UTC'))} · 자료: GovInfo, Voteview, congress-legislators, 미국 인구조사국, The Downballot, FEC · <a href="https://github.com/jongkonlee/genderpolitics">GitHub</a>`;
  render();
  if (S.open) openPanel(S.open);
}
init();
