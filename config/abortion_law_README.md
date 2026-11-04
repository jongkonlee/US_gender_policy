# State abortion-law status timeline, 2021-09-01 to 2026-11-04

Dated timeline of the gestational limit that was **in effect and enforceable** in each of the 50 states and DC. Built to be joined to congressional votes by date ("what was the law in this member's state on the day of the vote?"). Compiled 2026-11-04.

## Files

| File | Contents |
|---|---|
| `timeline.csv` | 124 rows for 51 jurisdictions: 51 starting rows (all dated 2021-09-01) plus 73 change rows, across 28 states. Columns: `state, start_date, end_date, status, weeks, measure, note, sources`. |
| `current_check.csv` | Each state's status on 2026-11-04 compared with KFF (dashboard map and State Health Facts table), Guttmacher and Ballotpedia, with `agreement` yes/no. |
| `work/rows_raw.tsv` | Working input, before end dates were computed. |

## Coding rules

**Dates**
- `start_date` is the day a change took legal effect: the date of the court order, or the law's effective date. The new status covers that whole day, even when an order came late in the day; the `note` says so where it matters.
- `end_date` is the day before the next row's `start_date`, so ranges are inclusive and do not overlap. A blank `end_date` means the row was still in effect on 2026-11-04.
- To join: `start_date <= vote_date <= end_date`, or `start_date <= vote_date` when `end_date` is blank.
- A script checked that each state has no gaps, no overlaps, a first row dated 2021-09-01, and no two consecutive rows with the same status and weeks.

**When a new row starts**
- A new row starts only when the status category or the weeks value changes.
- Other dated events go in `note` instead. These include an overlapping ban taking effect (for example the Texas trigger law on 2022-08-25), ballot measures that left the operative limit unchanged, and appeals rulings that kept the status the same.
- Changes that were undone within the same day get no row of their own; they are described in `note`. Examples: FL 2022-07-05, MI 2022-08-01, WY 2022-07-27.

**Weeks**
- Weeks are counted from the last menstrual period (LMP), as KFF does.
- A post-fertilization limit is converted by adding 2 weeks: 20 weeks post-fertilization is coded 22. The original wording is kept in `note` and `measure`.
- `viability` is used where the statute is keyed to viability.
- Weeks are left blank for "third trimester" limits (Virginia, and Idaho before Dobbs), which are coded `limit_20_24`, and for `ban` and `no_limit`.

**Starting rows (2021-09-01)**
- Each starting row records the limit actually in effect on that date. For Texas, that is SB 8.
- For states with 20-week laws, whether the law was in effect or enjoined comes from the Lozier Institute's survey dated 2021-09-10. That source is anti-abortion, but this use is a factual list of statutes and their litigation status.
- Other states' starting limits come from statutes, KFF, Guttmacher and news reports. No starting row records a law that was enjoined at the time.

**Pre-Roe statutes that were contested but not enjoined**
- Three cases are coded `ban`: TX 2022-06-24 to 06-27, WV 2022-06-24 to 07-17, and WI 2022-06-24 to 2023-07-06.
- In each, no court had blocked the statute, the attorney general or prosecutors treated it as enforceable (or would not rule enforcement out), and providers stopped.
- The notes flag that enforceability was disputed.

## Main sources

**Trackers**
- KFF Abortion in the U.S. Dashboard (map as of 2026-08-10; page modified 2026-10-28).
- KFF State Health Facts "Gestational Limits and Exceptions" (as of 2026-01-06).
- Guttmacher, "State Bans on Abortion Throughout Pregnancy," Table 1 (as of 2026-09-17).
- Ballotpedia, "Abortion regulations by state" (as of 2026-08-10, with timeline entries to 2026-08-25).
- CRS R47595, "State Laws Restricting or Prohibiting Abortion" (2026-09-01, via EveryCRSReport).
- Center for Reproductive Rights state and case pages.

**Dates**
- Exact dates come from contemporaneous news reports and court or legislative documents cited row by row.
- These include States Newsroom outlets, AP reports carried by member stations, local TV, Texas Tribune, Cowboy State Daily, KCUR, STLPR, Spokesman-Review, wyoleg.gov, and the Wisconsin DOJ.

**Cross-check**
- Every state's current status was compared against at least two trackers, KFF and Guttmacher. Ballotpedia is a third for every state.

## Dates that are uncertain or depend on a coding choice

- **AZ, 15 weeks to viability.** Coded 2025-03-05, the date of the court's permanent injunction.
  - Proposition 139 took effect 2024-11-25.
  - In December 2024 the attorney general agreed not to enforce the 15-week law while litigation continued. The exact date was not found.
  - Some doctors resumed later abortions before 2025-03-05; Planned Parenthood waited for the ruling.
- **ID, 6-week ban.** Coded 2022-08-19, when the criminal heartbeat law took effect. The Idaho Supreme Court vacated its stay of SB 1309's civil provisions on 2022-08-12, and those provisions could be argued to apply from then.
- **KY, reinstatement of the ban.** Coded 2022-08-01: the Court of Appeals order was reported that evening. Ballotpedia gives 2022-08-08, which conflicts with contemporaneous reports.
- **LA.**
  - The second TRO is dated 2022-07-11 but was released 2022-07-12; it is coded 2022-07-12.
  - The limit that applied while the trigger bans were blocked (2022-06-27 to 07-07 and 2022-07-12 to 07-28) is not stated in any source. It is coded as the 20-week post-fertilization law (22 LMP). A contingent 2018 15-week law may instead have been operative.
- **MN, viability to no limit.** SF 2995 (2023, chapter 70) repealed the viability statute and was signed 2023-05-24. The repealer's own effective date was not found. The change is coded 2023-07-01, the default for appropriation acts under Minn. Stat. 645.02. This date is an inference.
- **MO.**
  - Amendment 3 took effect 2024-12-05 according to CRS, or 2024-12-06 according to STLPR. Status did not change until the 2024-12-20 injunction.
  - For 2025-05-27 to 07-02, STLPR reported the near-total ban back in effect. Some outlets described only clinic rules as reinstated.
- **ND.** The court ruling striking the ban was 2024-09-12; the date judgment was entered was not confirmed. No clinic operated in the state during that period.
- **UT.** The 18-week ban is coded from 2022-06-27, when the federal injunction was dismissed. Some reports give 2022-06-28.
- **WI, ban to 20 weeks post-fertilization.** Coded 2023-07-07, the date of the non-final ruling that the 1849 statute does not ban consensual abortions. Providers resumed 2023-09-18; final judgment came 2023-12-05; the Wisconsin Supreme Court affirmed 2025-07-02. Choose another date if your analysis needs it.
- **WY.**
  - HB 152 became law "overnight Saturday," 2023-03-18; some reports say 03-17 or 03-19.
  - The backup viability ban in HB 126 (Article 5) took effect after the governor certified it on 2026-05-01 and the Secretary of State published notice, which was due within 5 days. The exact date was not found.
  - See also the legal question under Unresolved issues.
- **MI.** This is a coding choice rather than a date question.
  - Viability (the 1931 ban as limited by Roe) is coded through 2022-06-23. No limit is coded from 2022-06-24, because the 1931 ban, the only gestational restriction, was enjoined.
  - Trackers today list Michigan as having no limit. Earlier editions may have said "viability."
  - The few-hour enforcement window on 2022-08-01 is in the note only.
- **TX.** The injunction against SB 8 was issued on the evening of 2021-10-06, and the stay came late on 2021-10-08. The two-day window is coded 2021-10-06 to 10-07.

## Unresolved issues

1. **Tracker disagreements on the current status (2026-11-04).**
   - **WY:** The KFF dashboard map (as of 2026-08-10) and Ballotpedia show the 6-week ban. Guttmacher (2026-09-17), CRR and CRS show viability. Viability is coded here because the 6-week ban was blocked on 2026-04-24.
   - **MA:** Ballotpedia shows no restriction. The law removing the 24-week limit was signed 2026-08-10 but takes effect 90 days after signing, on 2026-11-08 by my count. The 24-week limit is coded as still in effect.
   - **OH:** KFF and Guttmacher agree the 20-week post-fertilization ban still applies. CRS strikes it through after Issue 1.
2. **Wyoming, 2023-03-22 to 2026-03-08.** HB 152 section 5 repealed the old viability statute, W.S. 35-6-102. Whether that statute survived after HB 152 was enjoined and later struck down is legally unclear. KFF, Guttmacher and CRR list viability, so this period is coded viability. The period from 2026-04-24 until Article 5 took effect has the same caveat.
3. **2026-11-03 ballot measures.** Idaho Proposition 1, Missouri Amendment 3, Nevada Question 6 and Virginia Question 1 had no final results in the sources checked; Idaho had partial results only. None could take effect by 2026-11-04. Idaho's would take effect 2027-01-01 if approved, and Missouri's 30 days after the election.
4. **Possible gap at the end of the period.** The latest tracker data is from 2026-09-17. News searches for changes between then and 2026-11-04 found none, but a change in that window could have been missed.
5. **Changes to exceptions are not coded.** Examples are Idaho's EMTALA and St. Luke's injunctions and the 2026 federal order, Indiana's religious-exemption injunction, and medical-exception clarifications in TX, TN and SC.
6. **Indiana, 2022-09-22 to 2023-08-20.** The injunction formally bound prosecutors only in the defendant counties, where the clinics were. It is coded as statewide.

## Pages that could not be accessed

- en.wikipedia.org "Abortion_in_Texas" and "Abortion_in_Missouri": refused because no permission was given for these URLs.
- web.archive.org: blocked, so archived pre-Dobbs tracker tables could not be read.
- ncsl.org: site error.
- Some news article pages (idahocapitalsun.com, wisconsinexaminer.com, one lailluminator.com page): site error. Other outlets were used for the same facts.
- KFF's litigation tracker: its interactive table could not be read.
- The New York Times tracker: not used, because of its paywall.
