# 여성정책 관련 의회 코커스 명단 확인 (111~119대)

확인한 날: 2026-11-04. 빠른 확인 작업이라 한 코커스에 오래 매달리지 않았습니다.

## 한눈에 보기

| 코커스 | 명단을 모은 의회 | 명단이 있지만 못 모은 의회 | 못 찾은 의회 |
|---|---|---|---|
| 하원 Pro-Choice Caucus (119대부터 이름이 Reproductive Freedom Caucus) | 119대 (전체 161명), 117대 (일부 123명) | 111대 (학술자료), 115·116대 (웹 보관본) | 112~114대, 118대 |
| 하원 Pro-Life Caucus (Chris Smith) | 없음 | 111대 (학술자료) | 112~119대 |
| 상원 Pro-Life Caucus (2019년에 생김) | 119대 (21명) | 없음 | 116~118대 (111~115대에는 아직 없던 코커스) |
| Congressional Caucus for Women's Issues (CCWI) | 없음 | 111대 (학술자료) | 112~119대 |
| Democratic Women's Caucus (DWC) | 119대 (97명) | 116~118대 (아래 '규칙으로 만들 수 있는 명단' 참고) | 111~115대 |

## 모은 명단 (`caucus_members.csv`, 402행)

네 명단은 모두 bioguide ID와 짝을 맞췄습니다(402행 모두 매칭됨). 각 명단은 같은 페이지를 서로 다른 질문으로 두 번 읽어서 이름이 하나도 다르지 않은 것을 확인했습니다.

1. **Pro-Choice Caucus, 119대: 161명.** 출처는 코커스 공식 사이트 <https://reproductivefreedom.house.gov/about-the-rfc/members> 입니다. 페이지 정보상 마지막 수정일은 2026-05-04입니다.
2. **Pro-Choice Caucus, 117대: 123명이지만 일부만 있음.** 출처는 Brad Sherman 의원 사이트 <https://sherman.house.gov/prochoicecaucus> 입니다(2022-08-16 게시, 2023-06-07 수정). 이름은 알파벳 순서인데 Kathleen Rice에서 끝나서, 성이 S~Z인 의원은 하나도 없습니다. 페이지 자체가 잘린 것입니다. 117대 도중이나 117대를 끝으로 떠난 의원(예: 2022년 9월에 사임한 Ted Deutch, Karen Bass)은 들어 있고 118대 초선은 없습니다. 그래서 117대 2022년 8월 무렵의 명단으로 봅니다(추정).
3. **상원 Pro-Life Caucus, 119대: 21명.** 출처는 의장 Cindy Hyde-Smith 의원 사이트 <https://www.hydesmith.senate.gov/pro-life-caucus> 이고, 제목이 "Senate Pro-Life Caucus Members (119th Congress)"입니다. 원문에는 "Darline Graham (S.C.)"이라고 오타가 나 있는데, Lindsey Graham(G000359)으로 맞췄습니다.
4. **DWC, 119대: 97명.** 출처는 코커스 공식 사이트 <https://democraticwomenscaucus.house.gov/members> 입니다. 페이지에 날짜는 없습니다. 하지만 119대 도중에 들어온 의원(Analilia Mejia, Aisha Wahab, Adelita Grijalva)이 들어 있고, 2025년 11월에 사임한 Mikie Sherrill은 없습니다. 그래서 2026년 무렵의 명단으로 봅니다(추정).

열 설명: `bioguide, name, caucus, congress, source_url, snapshot_date` 는 요청한 그대로입니다. 확인을 돕도록 뒤에 두 열을 덧붙였습니다. `name_on_source`는 출처에 적힌 그대로의 이름이고, `role_on_source`는 출처에 적힌 직책(공동의장 등)입니다. `name`은 회원 파일에 있는 이름입니다.

## 명단이 있지만 이번에 못 모은 것

- **111대 학술자료 (Ringe & Victor).** 하원만 들어 있고, 의원 번호는 ICPSR입니다. 다음 코커스가 있습니다.
  - 231 Bipartisan Congressional Pro-Choice Caucus
  - 232 Bipartisan Congressional Pro-Life Caucus
  - 233 Congressional Pro-Life Women's Caucus
  - 397 Congressional Caucus for Women's Issues
  - 147 Congressional Iraqi Women's Caucus

  파일 주소:
  - 회원 여부 표: <https://jvictor.schar.gmu.edu/wp-content/uploads/2017/04/membership_111.csv>
  - 코커스 이름: `Caucuses_111.csv` (같은 폴더)
  - 설명 페이지: <https://jvictor.schar.gmu.edu/index.php/data-download/>

  이 작업 환경에서는 파일을 내려받을 수 없어서 명단을 만들지 못했습니다. 이용 조건은 비상업 연구용이고 인용이 필요합니다. 공개 트래커에 쓰려면 출처를 밝히면 될 것으로 보이지만, 조건을 한 번 더 확인하세요. 설명 페이지에는 103~113대 전체 자료가 bridgeinfogap.org에 있다고 나오지만, 실제 내려받기 주소는 찾지 못했습니다.
- **Pro-Choice Caucus 115·116대.** 국립기록관리청(NARA)이 의회 사이트를 저장한 webharvest.gov에 코커스 사이트가 보관되어 있습니다.
  - 116대 회원 페이지(2020-11-23 저장): <https://www.webharvest.gov/congress116th/20201123173752/https://houseprochoicecaucus-degette.house.gov/members>
  - 115대 소개 페이지(2018-12-21 저장): <https://www.webharvest.gov/congress115th/20181221220624/https://houseprochoicecaucus-degette.house.gov/about>

  여기서는 계속 요청 제한에 걸려 열지 못했습니다. 그래서 내용과 인원은 확인하지 못했습니다. 브라우저로는 열릴 가능성이 큽니다.

## 규칙으로 만들 수 있는 명단 (DWC 116~118대)

DWC는 하원 민주당 여성 의원 모두가 회원이라고 스스로 밝힙니다. 118대 보도자료(2023-03-22)에는 "94명 모두 회원"이라고 나와 있고, 지금 'About' 페이지에는 "97명 모두"라고 나와 있습니다. 그래서 회원 파일에서 하원·민주당·여성을 골라내면 명단을 만들 수 있습니다. 다만 출처에 실린 명단이 아니어서 이번에는 만들지 않았습니다. 주의할 점도 있습니다. 119대 명단에는 Sheila Cherfilus-McCormick(FL-20)이 없습니다. 이유는 페이지에 나오지 않습니다. 이처럼 규칙과 실제 명단이 어긋날 수 있습니다.

## 못 찾은 것

- **하원 Pro-Life Caucus 112~119대:** 회원 명단을 공개한 곳을 찾지 못했습니다. Chris Smith 의원 사이트에는 본인이 맡은 직책만 나옵니다.
- **CCWI 112~119대:** 공개된 것은 의장단(공동의장·부의장)뿐입니다. 112대 명단이 하나 있기는 합니다. NAWJ(여성판사협회)가 올린 PDF로, 68명이 들어 있습니다. 하지만 출처와 날짜가 적혀 있지 않고, 요청한 출처 종류에도 들지 않아서 넣지 않았습니다. 이 PDF에는 당시 재직하던 여성 의원 몇 명(Ellmers, E.B. Johnson, McCarthy, Richardson, Schwartz)이 빠져 있습니다. 그래서 "여성 의원은 모두 회원"이라는 규칙(위키백과 설명, 공식 확인 안 됨)으로 명단을 만드는 것은 믿기 어렵습니다.
- **상원 Pro-Life Caucus 116~118대, Pro-Choice Caucus 112~114·118대:** 명단을 찾지 못했습니다. 예전 페이지가 웹 보관소에 남아 있을 수는 있습니다.

## 주의할 점

- **본인 신고 명단입니다.** 코커스 가입은 의원이 스스로 하는 것이고, 공식 기록으로 관리되지 않습니다. 페이지가 늦게 고쳐지거나 빠뜨린 이름이 있을 수 있습니다.
- **한 시점의 명단입니다.** 어느 명단도 그 의회 2년 전체를 담지 않습니다. 예를 들어 119대 명단에는 2025년에 세상을 떠나거나 물러난 의원(Raúl Grijalva, Gerry Connolly, Mikie Sherrill 등)이 없습니다.
- **`snapshot_date`의 뜻:** 지금 열려 있는 페이지는 2026-11-04(읽은 날)로 적었습니다. 페이지가 고쳐진 날짜는 `availability.csv`의 note에 적었습니다.
- **웹 보관소를 쓰지 못했습니다.** 이 환경에서는 Wayback Machine(web.archive.org)과 archive.ph가 막혀 있었습니다. webharvest.gov는 요청 제한에 걸렸고, 의회도서관 보관소(webarchive.loc.gov)는 오류가 났습니다. 그래서 116~118대 명단이 보관본으로 남아 있는지는 거의 확인하지 못했습니다. 브라우저로 다시 확인할 만합니다.
- **유료 자료(LegiStorm, CQ)는 쓰지 않았습니다.**

## `availability.csv`의 `list_available` 값

- `yes`: 받아들일 수 있는 출처에 전체 명단이 있음.
- `partial`: 명단이 잘려 있음. 또는 특정 출처에 명단이 있는 것은 확인했지만 여기서 열거나 내려받지 못함(note에 어느 쪽인지 적음). DWC 116~118대는 규칙으로 만들 수 있다는 뜻입니다.
- `no`: 받아들일 수 있는 명단을 찾지 못함.

맨 아래의 "(other)" 행들은 다른 여성정책 코커스입니다. 목록에만 올리고 명단은 만들지 않았습니다.
- Black Maternal Health Caucus: 118대 회원 페이지에 122명(의장 2, 하원 113, 상원 7)
- Congressional Caucus on Black Women & Girls: 공동의장 3명만 공개
- Pro-Life Women's Caucus, Iraqi Women's Caucus: 111대 학술자료에 있음

## 다음에 할 수 있는 일

1. 브라우저로 Victor의 `membership_111.csv`를 내려받습니다. 첫 행은 코커스 번호, 첫 열은 ICPSR입니다. 231·232·397(필요하면 233) 열에서 값이 1인 의원을 고른 뒤, 회원 파일의 `icpsr` 열로 bioguide와 맞춥니다.
2. 위의 webharvest 주소들을 브라우저로 열어 Pro-Choice 115·116대 명단을 확인합니다.
3. DWC 116~118대를 규칙으로 만들지 정합니다. 만든다면 '출처 명단'과 구분되는 표시를 붙여야 합니다.
