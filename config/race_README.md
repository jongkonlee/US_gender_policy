# Race/ethnicity coding of members of Congress, 111th–119th Congresses (2009–2026)

Prepared 4 November 2026. Covers the 1,267 people in `members_111_119.csv` (House members, Delegates, Resident Commissioners and Senators).

## Files

| File | Contents |
|---|---|
| `race_coding.csv` | One row per coded person: `bioguide, name, black, hispanic, asian_pi, native_american, sources, note, confidence`. Contains every member with at least one flag (272 people) plus 23 flagged edge cases with all flags 0 (295 rows). Anyone in the member list who is not in this file is coded 0 on all four groups. |
| `counts_check.csv` | For each Congress (111–119), chamber and group: this coding's counts at the CRS as-of date, at the start of the Congress, and for anyone who served at any time, next to the CRS profile count. Each row has the report number, version date, as-of statement, URL, the difference, an explanation and, where available, a Pew cross-check. |
| `README.md` | This file. |

Scripts used to build both CSVs (kept outside this folder): `/tmp/claude-0/-home-claude/60f21bfa-7dca-5544-8bba-6a24e661457b/scratchpad/scripts/coding_data.py` (all coding decisions and source keys), `/tmp/claude-0/-home-claude/60f21bfa-7dca-5544-8bba-6a24e661457b/scratchpad/scripts/build.py` and `/tmp/claude-0/-home-claude/60f21bfa-7dca-5544-8bba-6a24e661457b/scratchpad/scripts/counts_check.py`.

## Result in brief

| Group | People coded 1 | Backed by a House History publication or a CRS name list | Coded from other sources (entered after the latest accessible House History list) |
|---|---|---|---|
| Black/African American | 120 | 93 | 27 (118th–119th entrants) |
| Hispanic/Latino | 113 | 38 | 75 (113th–119th entrants) |
| Asian American/Pacific Islander | 43 | 28 | 15 (116th–119th entrants) |
| American Indian/Alaska Native | 7 | 0 (no House History list found) | 7 |

11 people carry two flags: Bobby Scott, Hansen Clarke, Kamala Harris, Marilyn Strickland (Black + Asian/PI); Antonio Delgado, Ritchie Torres, Maxwell Frost, Analilia Mejia (Black + Hispanic); Gregorio Sablan, Michael San Nicolas, James Moylan (Hispanic + Asian/PI).

At the CRS as-of dates, this coding reproduces the CRS counts in 62 of 72 Congress × chamber × group cells. All 10 differences have a stated cause; 9 are explained, and 1 (115th House Hispanic, +1 in CRS) is unresolved. Where Pew gives counts (Senate 116th–119th, House 118th), this coding reproduces them exactly once Pew's own rules are applied (voting members only, Portuguese-ancestry members excluded).

## Coding rules

- Four 0/1 flags: `black`, `hispanic`, `asian_pi`, `native_american`. White or other is not coded.
- A member in several groups gets a flag in each.
- Coding is a person attribute: the same in every Congress.
- Reference standard (set by the project owner): CRS "Membership of the Nth Congress: A Profile" reports for counts; House History, Art & Archives lists for names; Pew as a cross-check.
- `confidence`: **high** = listed in a House History publication or a CRS name list and consistent with CRS counts; **medium** = entered after the accessible House History lists and coded from caucus, official, advocacy or news sources, consistent with CRS counts, or an edge case where the coding follows the reference standard but sources disagree; **low** = rests on one secondary source or an inference, or sources conflict.
- `note` starts with tags so decisions can be filtered or reversed:
  - `EDGE:PORTUGUESE` (8), `EDGE:BRAZILIAN` (1), `EDGE:MENA` (20, includes notes on two Hispanic-coded members with Lebanese ancestry), `EDGE:MULTI` (11), `EDGE:SOURCES_DIFFER` (7), `EDGE:PI_DELEGATE` (4), `EDGE:NATIVE_HAWAIIAN` (2)
  - `EDGE:MIDCONGRESS` (69): joined or left mid-Congress. For coded members whose notes did not already say so, the dates were added automatically from congress-legislators term data.

## Sources

### 1. CRS profile reports (counts)

All read through EveryCRSReport, which serves the CRS text. The latest version of each report was used.

| Congress | Report | Version used | As-of statement |
|---|---|---|---|
| 111th | R40086 | 27 Dec 2010 | none stated; counts fit membership between 22 May and 29 Nov 2010 — https://www.everycrsreport.com/reports/R40086.html |
| 112th | R41647 | 26 Nov 2012 | none stated — https://www.everycrsreport.com/reports/R41647.html |
| 113th | R42964 | 24 Nov 2014 | as of 24 Nov 2014 — https://www.everycrsreport.com/reports/R42964.html |
| 114th | R43869 | 5 Dec 2016 | as of 5 Dec 2016 — https://www.everycrsreport.com/reports/R43869.html |
| 115th | R44762 | 20 Dec 2018 | as of 20 Dec 2018 — https://www.everycrsreport.com/reports/R44762.html |
| 116th | R45583 | 17 Dec 2020 (v.27) | as of 17 Dec 2020 — https://www.everycrsreport.com/reports/R45583.html |
| 117th | R46705 | 14 Dec 2022 (v.30) | as of 13 Dec 2022 — https://www.everycrsreport.com/reports/R46705.html |
| 118th | R47470 | 12 Dec 2024 (v.25) | as of 12 Dec 2024 — https://www.everycrsreport.com/reports/R47470.html |
| 119th | R48535 | 4 Aug 2025 | as of 4 Aug 2025 — https://www.everycrsreport.com/reports/R48535.html (the 21 May 2025 version 2 PDF, https://www.congress.gov/crs_external_products/R/PDF/R48535/R48535.2.pdf, gives the same group totals) |

CRS counts Delegates and the Resident Commissioner as House members. Its American Indian count includes "only Members who are enrolled members of federally recognized tribes" (it cites an unpublished CRS memo). From the 111th through the 119th, its Hispanic footnote says the total includes House Members (and in the 113th–117th "one Senator") "of Portuguese ancestry" who "belong, or have belonged, to the Congressional Hispanic Caucus or the Congressional Hispanic Conference". The profiles name almost no individuals.

### 2. House History, Art & Archives (names)

`history.house.gov` blocks automated retrieval (robots.txt), and archived copies could not be read either (see "Access problems"). So the online "by Congress" lists, which run to the present, were **not** checked directly. The same office's printed volumes, hosted by GPO, were used instead:

- **Black Americans in Congress** (H. Doc. 118-16), Appendix A "Black-American Members by Congress, 1870–2022", closing date 1 June 2022, with footnotes on mid-Congress changes: https://www.govinfo.gov/content/pkg/GPO-CDOC-118hdoc16/pdf/GPO-CDOC-118hdoc16-4.pdf. Source for all Black members of the 111th–117th Congresses.
- **Hispanic Americans in Congress, 1822–2012** (H. Doc. 108-225), Appendix B (by state and territory; closing date 1 Sep 2012): https://www.govinfo.gov/content/pkg/GPO-CDOC-108hdoc225/pdf/GPO-CDOC-108hdoc225-4-2.pdf. The closing date is stated in Part Two: https://www.govinfo.gov/content/pkg/GPO-CDOC-108hdoc225/pdf/GPO-CDOC-108hdoc225-3-1.pdf. Source for the 111th–112th Hispanic members. It **includes** the Portuguese-ancestry members Dennis Cardoza, Devin Nunes and Jim Costa, and Delegate Gregorio Sablan. It does **not** include John Garamendi, Charles Rangel or Pat Toomey.
- **Asian and Pacific Islander Americans in Congress** (2017 edition): the index, where profiled members are printed in capitals, https://www.govinfo.gov/content/pkg/GPO-CDOC-108hdoc226/pdf/GPO-CDOC-108hdoc226-5.pdf; Part Two "Current Members" for the 115th Congress, https://www.govinfo.gov/content/pkg/GPO-CDOC-108hdoc226/pdf/GPO-CDOC-108hdoc226-3.pdf; and the Akaka profile, https://www.govinfo.gov/content/pkg/GPO-CDOC-108hdoc226/pdf/GPO-CDOC-108hdoc226-2-4-9.pdf. Covers members through the start of the 115th. Native Hawaiians (Akaka) and Pacific Islanders (Samoan and Chamorro delegates) are included. Madeleine Bordallo (Delegate, Guam) is not profiled.
- **Native American list:** none was found on House History.

### 3. CRS reports that name members

- CRS 97-398, *Asian Pacific Americans in the United States Congress* (Lorraine H. Tong, 12 June 2013), tables by Congress for the 111th–113th, with ancestry for some members: https://www.everycrsreport.com/files/20130612_97-398_ec0b4de5a2c51e4f18e80870dd46891bb5db1c1f.html. Its definition covers East and Southeast Asia, the Indian subcontinent and "the original peoples of Hawaii, Guam, Samoa, or other Pacific Islands" by self-identification.
- CRS RL30378, *African American Members of the U.S. Congress: 1870–2020* (15 Dec 2020), https://www.everycrsreport.com/reports/RL30378.html. It says its inclusion follows House History's *Black Americans in Congress*. Only part of the text could be retrieved (entries A–F and L–M), so it was used as corroboration, not as a per-member source.

### 4. Senate Historical Office

African American senators: https://www.senate.gov/senators/african-american-senators.htm

### 5. Pew Research Center (cross-check)

- 2017 (115th): https://www.pewresearch.org/short-reads/2017/01/24/115th-congress-sets-new-high-for-racial-ethnic-diversity/
- 2019 (116th): https://www.pewresearch.org/short-reads/2019/02/08/for-the-fifth-time-in-a-row-the-new-congress-is-the-most-racially-and-ethnically-diverse-ever/
- 2021 (117th): https://www.pewresearch.org/short-reads/2021/01/28/racial-ethnic-diversity-increases-yet-again-with-the-117th-congress/
- 2023 (118th): https://www.pewresearch.org/short-reads/2023/01/09/u-s-congress-continues-to-grow-in-racial-ethnic-diversity/
- 2025 (119th): https://www.pewresearch.org/short-reads/2025/01/21/119th-congress-brings-new-growth-in-racial-ethnic-diversity-to-capitol-hill/

Pew counts voting members only, excludes Portuguese Americans from the Hispanic count, uses CRS and CQ Roll Call data, and counts multiracial members in each group.

Pew 2017 gives only combined House + Senate totals for the 115th: 39 Hispanic and 15 Asian/PI. On the same basis (voting members at the start of the Congress, before Becerra resigned on 24 Jan 2017, Portuguese-ancestry members excluded), this coding gives 39 Hispanic and 16 Asian/PI. The 2017 piece does not say how multiracial members such as Bobby Scott and Kamala Harris were counted. Pew 2021 counted Kai Kahele with Native Americans. Pew 2019 and 2025 count Adriano Espaillat as Black and Hispanic; Pew 2023 does not list him among multiracial members.

### 6. Sources for members who entered after the House History volumes

These are all in the `sources` column:

- **Congressional Black Caucus documents:**
  - 118th member list: https://cbc.house.gov/uploadedfiles/118th_congress_cbc_first_100_days-2.pdf
  - 118th end-of-session list: https://cbc.house.gov/UploadedFiles/2024_CBC_Q4_Report.pdf
  - 119th committee letter: https://cbc.house.gov/uploadedfiles/1.3.25_sp_final4.pdf
  - Report on new 119th members: https://bmorenews.com/congressional-black-caucus-swears-in-new-members-for-119th-congress
- **Black Republicans:** Washington Times, 9 Nov 2022, and theGrio, 30 Apr 2026.
- **Hispanic lists:**
  - CHCI list of Hispanic members of the 117th Congress
  - Congressional Hispanic Conference 118th roster
  - CHC BOLD PAC list of new 2023 members
  - UnidosUS "Latino Members of the 119th Congress": https://unidosus.org/wp-content/uploads/2025/01/unidosus_latinomembersofthe119thcongress_listing-1.pdf
  - Fox News Latino (2013, 2014), NewsTaco (2012), NBC News (2018)
- **Asian/PI lists:**
  - CAPAC releases (2012, 2016)
  - NBC News (2018)
  - AsAmNews (2020, 2023, 2024)
  - Asia Matters for America (2021)
  - Official and PAC releases for Dave Min and Derek Tran
  - Pew repost on Kimberlyn King-Hinds' House site
- **Native American:** Fox29 (5 Nov 2020) and Native News Online (6 Feb 2023), which give tribal affiliations; Pew for Markwayne Mullin.
- **Wikipedia:** list pages were used to generate candidates and to document edge cases (Garamendi, Perry, Donalds, Rangel, Toomey, the MENA list, Native list scope). A Wikipedia page is the main basis for a flag of 1 only for Greg Lopez ("third-generation Mexican American", citing Denverite). That flag is also supported by the CRS 118th footnote on a Hispanic member sworn in July 2024. Before publication, replace the Wikipedia citations with primary sources where possible.

### 7. Term dates

The `unitedstates/congress-legislators` YAML files (raw.githubusercontent.com, retrieved 4 Nov 2026) supplied service start and end dates for the as-of counts.

## Decisions on edge cases (flagged, not silent)

1. **Portuguese ancestry.** House History's 2012 Hispanic list includes Cardoza, Nunes and Costa. CRS counts Portuguese-ancestry members of the Hispanic Caucus or Conference in every profile. Pew excludes them.
   - Coded `hispanic=1`, confidence medium/low:
     - Cardoza, Nunes, Costa: in House History's list
     - David Valadao, Lori Trahan, John Duarte: CRS totals reconcile only with them included; all three appear on Hispanic caucus, conference or advocacy lists
   - Coded 0:
     - **Pat Toomey**: House History's 2012 list omits him even though he served in the Senate from 2011. CRS 113th–117th count "one Senator" of Portuguese ancestry, which by inference is Toomey.
     - **Eric Swalwell**: no source counts him as Hispanic.
   - To follow Pew instead, set all `EDGE:PORTUGUESE` rows to 0. To follow CRS fully, set Toomey to 1.
2. **George Santos (Brazilian-American).** Coded 1, low confidence. CRS's 118th count included him (its footnote calls him "of Portuguese ancestry"), Wikipedia lists him as Brazilian, and Pew appears to exclude him.
3. **Delegates from Guam and the Northern Mariana Islands.** Sablan, San Nicolas and Moylan are coded Hispanic and Asian/PI:
   - House History lists Sablan in both books, and CRS 97-398 calls him "Chamorro with Hispanic and English ancestry".
   - CRS profiles count these delegates in both groups.
   - Pew 2025 counts one delegate (Moylan) in both groups.
   - Kimberlyn King-Hinds is coded Asian/PI only, as CRS and Pew treat her.
   - Madeleine Bordallo is coded 0: neither CRS 97-398 nor House History lists her as APA.
4. **Native Hawaiians are coded `asian_pi`**, following House History and CRS 97-398. The CRS 117th profile defined Native Americans as "American Indians, Alaska Natives, or Native Hawaiians" and counted Kai Kahele in both groups; Pew 2021 counted him with Native Americans. CRS 118th–119th define the group as American Indians or Alaska Natives. Kahele is coded `native_american=0` (flagged). This is the cause of the 117th Native American difference.
5. **Black + Hispanic.** Coded per House History's BAIC list (Delgado and Torres are on it). Frost and Mejia, who entered after it, are coded from CBC membership, self-identification and CRS/Pew dual counts.
   - **Adriano Espaillat** is coded Hispanic only. He self-identifies as a Latino of African descent, Pew 2019/2025 count him as Black, and the CRS 115th Black total appears to include him. But BAIC (through June 2022) and CRS 116th–119th do not count him.
   - **Charles Rangel** is coded Black only (not in House History's Hispanic list).
   - **Byron Donalds** is coded Black only (only Wikipedia gives Panamanian heritage).
6. **MENA ancestry** (Issa, Boustany, Rahall, Amash, Hanna, Abraham, Gwen Graham, Graves, LaHood, Crist, Eshoo, Shalala, Tlaib, Bice, Ansari, Hamadeh, Helmy): all 0. None of the reference sources places MENA in the four groups. AsAmNews 2024 grouped Tlaib, Bice and Ansari with AAPI members, but the CRS 119th Asian/PI count excludes them. **Aisha Wahab** (first Afghan American, sworn in 2 Sep 2026) is coded 0, low confidence, pending a decision; Afghanistan is not clearly inside House History's APA definition, and no CRS profile covers her yet.
7. **John Garamendi** (Basque grandparents): coded 0. He says he does not consider himself Hispanic, House History omits him and CRS counts reconcile without him, although Wikipedia reports that the House Press Gallery lists him. **Scott Perry**: coded 0, low confidence; Wikipedia's "Colombian" entry is not supported by any other list.

## How counts_check.csv was computed

- **House** includes Delegates and the Resident Commissioner, as CRS counts them.
- **`my_count_at_crs_date`**: coded members serving on the CRS as-of date, using congress-legislators term dates. For the 111th, where CRS gives no as-of date, 28 Nov 2010 was used.
- **`my_count_start_of_congress`**: members serving on 10 January of the Congress's first year.
- **`my_count_served_any_time`**: members who served at any point in the Congress. This is larger whenever there was turnover.

Differences against CRS, all explained in the file:

| Cell | Difference | Cause |
|---|---|---|
| 112th House Hispanic | −1 | CRS keeps Cardoza after his August 2012 resignation |
| 113th–117th Senate Hispanic | −1 each | Toomey, coded 0 here (see decision 1) |
| 115th House Black | −1 | CRS appears to count Espaillat |
| 115th House Hispanic | −1 | **Unresolved.** CRS has one more Democrat. Becerra and Gomez may both have been kept, or Garamendi may have been counted |
| 117th House Black | +1 | Karen Bass: CRS says she resigned in December 2022; the member-list term data runs her term to 3 Jan 2023 |
| 117th House Native American | −1 | Kahele (see decision 4) |

CRS internal inconsistencies noted along the way:

- 117th: the Summary gives 46 Hispanic House members, the body 45. The body matches the 52 total and this coding.
- 119th: the Hispanic text mentions two Delegates, but only Moylan fits. The total of 50 matches this coding.
- 112th: the African American party split adds up to 44, against a total of 43.
- 111th: Asian/PI is given as "3%" of 541 members; 13 is about 2.4%.

## Unresolved issues

1. **House History's current online lists were not read.** 27 Black, 75 Hispanic and 15 Asian/PI codings rest on caucus, advocacy, official and news sources instead. CRS count reconciliation supports them as a group but cannot confirm individuals. Before publication, check `race_coding.csv` against the live House History lists, which can be opened in an ordinary browser.
2. **Portuguese-ancestry policy.** CRS and the 2012 House History list include these members; Pew excludes them. Pat Toomey is the one person the two reference sources treat differently.
3. **115th CRS Hispanic House count** is one higher than can be reproduced.
4. **Identification differs between sources:** Espaillat (Black?), Kahele (Native American?), Santos (Hispanic?), Brian Mast (Hispanic identification rests on Conference membership, UnidosUS and Wikipedia), Garamendi, Perry, Donalds, Rangel.
5. **Entrants after the CRS 119th profile** (Adelita Grijalva, Menefee, Mejia, Blair, Wahab; 2025–2026) have no CRS cross-check. Everton Blair Jr. rests on a single news article (low confidence).
6. **Native American:** no House History list exists, and the CRS memo that names enrolled members is not public. The 7 coded members are described with tribal affiliations by news sources and match CRS counts in every Congress except the 117th (Kahele).
7. **Term-data caveat.** The congress-legislators data appears to omit Karen Bass's December 2022 resignation. Any other such gaps would affect the as-of counts, though not the coding.

## Access problems (URLs that could not be read)

- `history.house.gov` (all pages): robots.txt disallows automated fetching
- `webharvest.gov` archive copies of House History pages: repeated rate-limit errors
- `web.archive.org`: blocked
- `webarchive.loc.gov`: error
- `webarchive.library.unt.edu` (End of Term archive): robots.txt
- `archive.ph`, `congress.gov` HTML pages for CRS products, `denverite.com` (Greg Lopez), a Yahoo News article on 2022 Latino freshmen: permission not granted in this session
- NBC News article on the 119th CBC (2024): robots.txt
- Florida Phoenix and Pennsylvania Capital-Star 2022 CHC articles: errors
