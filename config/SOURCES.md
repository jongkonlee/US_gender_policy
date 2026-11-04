# 연구용 보조 자료 (config/)

자동으로 받는 자료(Voteview, GovInfo, congress-legislators, 인구조사국, The Downballot, FEC) 말고, 사람이 출처를 확인해 정리한 파일들입니다. 파이프라인(`pipeline/build.py`)이 매 실행 때 읽습니다.

| 파일 | 내용 | 출처 |
|---|---|---|
| `abortion_law_timeline.csv` | 주별 임신중지 법 상태(실제로 시행된 임신 주수 제한), 2021-09-01 ~ 현재. 한 줄 = 한 주의 한 기간 | KFF, Guttmacher Institute, Center for Reproductive Rights, Ballotpedia, 법원 판결·보도. 줄마다 `sources` 칸에 URL. 불확실한 날짜는 `abortion_law_README.md` |
| `caucus_members.csv` | 여성정책 관련 코커스 명단(공개된 전체 명단이 있는 경우만): 119대 하원 Reproductive Freedom Caucus(옛 Pro-Choice Caucus), 119대 하원 민주당 여성 코커스, 119대 상원 Pro-Life Caucus | 각 코커스·의원 누리집(`source_url`, `snapshot_date`) |
| `caucus_availability.csv` | 코커스·회기별로 명단을 구할 수 있었는지 | 같음 |
| `race.csv` | 의원 인종(흑인·히스패닉·아시아·태평양계·원주민, 여러 집단이면 각각 1) | 하원 역사국(History, Art & Archives) 명단, CRS 회기별 의원 구성 보고서로 합계 대조 |

열 설명
- `abortion_law_timeline.csv`: `status` = `ban`(전면 금지) / `ban_6wk`(6주 전후) / `limit_12_18` / `limit_20_24`(20~24주 또는 생존 가능 시점) / `no_limit`, `weeks` = 주수 또는 `viability`
- 2021-09-01 이전 날짜는 페이지에서 'Roe 시기'로 표시합니다.

종교: Pew Research Center "Faith on the Hill"(111~119대)의 의원별 목록을 정리할 수 있지만, Pew 이용 조건상 내용 대부분을 다시 싣는 것은 서면 허락이 필요해 공개 페이지에는 넣지 않았습니다.
