# 연구용 보조 자료 (config/)

자동으로 받는 자료(Voteview, GovInfo, congress-legislators, 인구조사국, The Downballot, FEC) 말고, 사람이 출처를 확인해 정리한 파일들입니다. 파이프라인(`pipeline/build.py`)이 매 실행 때 읽습니다.

| 파일 | 내용 | 출처 |
|---|---|---|
| `abortion_law_timeline.csv` | 주별 임신중지 법 상태(실제로 시행된 임신 주수 제한), 2021-09-01 ~ 현재. 한 줄 = 한 주의 한 기간 | KFF, Guttmacher Institute, Center for Reproductive Rights, Ballotpedia, 법원 판결·보도. 줄마다 `sources` 칸에 URL. 불확실한 날짜는 `abortion_law_README.md` |
| `caucus_members.csv` | 여성정책 관련 코커스 명단(공개된 전체 명단이 있는 경우만): 119대 하원 Reproductive Freedom Caucus(옛 Pro-Choice Caucus), 119대 하원 민주당 여성 코커스, 119대 상원 Pro-Life Caucus | 각 코커스·의원 누리집(`source_url`, `snapshot_date`) |
| `caucus_availability.csv` | 코커스·회기별로 명단을 구할 수 있었는지 | 같음 |
| `factions_groups.json`, `factions_house.csv`, `factions_senate.csv` | 계파 명단. 외교안보 표결 트래커(Google Drive)의 `config/groups.json`·`factions_house.csv`·`factions_senate.csv`를 그대로 복사한 것(2026-11-02 판, 2026-11-04 복사). 하원은 회기 × 의원 한 줄(1 = 소속, 0 = 아님, 빈칸 = 그 회기 명단 없음, `until` = 회기 중 탈퇴 날짜 `열이름:YYYY-MM-DD`), 상원은 한 번 정한 명단을 모든 회기에 씀(`basis` = 고른 이유). `factions_groups.json`의 `from`·`to`가 각 계파를 쓰는 회기 | 하원: 강우창, 미국 의회 정당 계파(us_party_faction, https://woochangkang.github.io/us_party_faction/) — 115대까지 Clarke, Andrew J. 2020. "Party Sub-Brands and American Party Factions." *AJPS* 64(3): 452–470, 116대부터 각 코커스 공식 명단, 프리덤 코커스는 Matthew Green 명단(저자 제공, 출처를 밝히는 조건으로 사용 허락), 119대 프리덤 코커스는 Wikipedia 현재 회원 + Green 명단. 상원: 외교안보 트래커 기준(Common Sense Coalition 113·115대 명단, 이스라엘 무기판매 불승인·이란 전쟁권한 결의안 표결, 메디케어 포 올·공공주택 그린뉴딜 발의) |
| `race.csv` | 의원 인종(흑인·히스패닉·아시아·태평양계·원주민, 여러 집단이면 각각 1). 여기 없는 의원은 네 집단 모두 0 | 하원 역사국(History, Art & Archives) 명단과 CRS 이름 명단, 그 뒤 의원은 공식 소개·보도. 줄마다 `sources`. CRS 회기별 의원 구성 보고서 숫자와의 대조는 `race_counts_check.csv`(72칸 중 62칸 일치, 차이는 모두 이유 적음), 방법·판단이 갈린 의원은 `race_README.md` |

열 설명
- `abortion_law_timeline.csv`: `status` = `ban`(전면 금지) / `ban_6wk`(6주 전후) / `limit_12_18` / `limit_20_24`(20~24주 또는 생존 가능 시점) / `no_limit`, `weeks` = 주수 또는 `viability`
- 2021-09-01 이전 날짜는 페이지에서 'Roe 시기'로 표시합니다.
- 계파: 외교안보 트래커에서 명단을 고치면(예: 120대 하원 명단 추가) 세 파일을 같은 이름으로 여기에 다시 복사하면 됩니다. 매 실행 때 모든 회기의 계파가 `docs/data/people.json`으로 다시 만들어지므로 지난 회기를 다시 만들 필요는 없습니다.

종교: Pew Research Center "Faith on the Hill"(111~119대)의 의원별 목록을 정리할 수 있지만, Pew 이용 조건상 내용 대부분을 다시 싣는 것은 서면 허락이 필요해 공개 페이지에는 넣지 않았습니다.
