# Police records against the survey: assault victims by race and sex, 2015 to 2025

**In four cities, police write up about the same share of victims per 911 assault call whatever a neighborhood's racial makeup: the same in New York, Los Angeles and New Orleans, about a fifth more in Baltimore's Blackest neighborhoods. The 4x gap in police-recorded assaults on Black women is already there when the phone rings, and hospital emergency departments see a gap of the same size. Only the national victimization survey, in which women describe their own assaults, puts it at 1 to 2 times.**

The national run ([US-Large-Cities-Assault-Victim-Rates-by-Race-and-Sex-2022-2025](https://github.com/mngoh/US-Large-Cities-Assault-Victim-Rates-by-Race-and-Sex-2022-2025)) found the police gap. This asks what it measures, with four tests: the National Crime Victimization Survey, which counts assaults whether or not police learned of them; DC's records, for one assault becoming several; Los Angeles's, for the same women counted repeatedly; and New York's 911 calls against its recorded victims, by precinct, for the recording stage. The scripts read the national run's outputs and the [LA-Crime](https://github.com/mngoh/LA-Crime) project from sibling folders.

## New York: the gap is in the calls, not in the recording

New York publishes 911 calls by type and precinct, recorded complaints with victim race and sex, and precinct boundaries, so the recording stage can be tested (`out/nyc_calls.md`, `scripts/nyc_calls.py`; 77 precincts, 2022 to 2025, 525,000 assault calls, 294,000 recorded assault victims).

| Precincts by Black share of residents | Assault calls per 1,000 residents a year | Recorded victims per 1,000 | Victims recorded per call | Black women's rate | White women's rate | Ratio |
|---|---|---|---|---|---|---|
| 1% to 3% | 7.4 | 4.6 | 0.62 | 1,880 | 248 | 7.6x |
| 3% to 7% | 13.4 | 7.5 | 0.56 | 2,328 | 292 | 8.0x |
| 7% to 23% | 15.6 | 8.8 | 0.56 | 1,963 | 328 | 6.0x |
| 24% to 38% | 22.5 | 12.7 | 0.57 | 1,782 | 493 | 3.6x |
| 41% to 81% | 20.5 | 10.9 | 0.54 | 1,246 | 437 | 2.9x |

- Police record about 0.55 to 0.62 victims per assault call everywhere. At the same number of calls and residents, a wholly Black precinct records 1.07 times the victims of one with no Black residents (regression coefficient 0.06, standard error 0.07). The gap does not come from what police write down after a call; it is in the calls.
- Calls per resident are 2.8 times higher in the Blackest precincts than the whitest. That is a difference between places, not a measurement of any group.
- Black women's rate is highest in the whitest precincts (Manhattan's), where few Black women live: assaults are recorded where they happen, residents are counted where they live. Within the Blackest precincts, where Black and White women are neighbors, the gap is 2.9x, not the citywide 5.2x.
- By place (`out/nyc_premises.md`): public housing holds 17% of the recorded assaults on Black women and 3% of those on White women, with a 29x ratio there; outside public housing the ratio is 4.5x. On the street it is 4.0x, in apartment buildings 5.2x, in shelters 8.2x. No single kind of place carries the gap.

## Baltimore: the same test, with a small recording effect

Baltimore publishes the same three pieces (`out/bmore_calls.md`, `scripts/bmore_calls.py`; 133 neighborhoods of 1,000+ residents, 2022 to 2023, 55,000 assault calls, 21,500 recorded assault victims).

| Neighborhoods by Black share of residents | Assault calls per 1,000 residents a year | Recorded victims per 1,000 | Victims recorded per call | Black women's rate (18+) | White women's rate (18+) | Ratio |
|---|---|---|---|---|---|---|
| 3% to 21% | 29.1 | 10.8 | 0.37 | 3,823 | 648 | 5.9x |
| 21% to 57% | 60.9 | 22.7 | 0.37 | 4,104 | 1,324 | 3.1x |
| 58% to 79% | 50.0 | 18.6 | 0.37 | 2,567 | 1,592 | 1.6x |
| 79% to 89% | 61.4 | 25.5 | 0.42 | 2,984 | 4,074 | 0.7x |
| 89% to 100% | 67.6 | 27.3 | 0.40 | 3,256 | 6,122 | 0.5x |

- Victims per call rise from 0.37 to 0.40 across the bands; at the same calls and residents, a wholly Black neighborhood records 1.22 times the victims of one with no Black residents (coefficient 0.20, standard error 0.07). A recording effect exists in Baltimore, and it is small beside the gap.
- Calls per resident are 2.3 times higher in the Blackest neighborhoods, as in New York (2.8).
- Residence is a poor denominator for place: in the Blackest neighborhoods, White women's recorded rate is higher than Black women's: the few White women living there are not the White women assaulted there. Citywide, women 18 and older, the ratio is 2.5x.
- Cincinnati, the other city with published calls, records no victim race since 2022, so it could not be used.

## Los Angeles and New Orleans: the same test, two more cities

Los Angeles (`out/la_calls.md`, `scripts/la_calls.py`): 680 LAPD reporting districts, 2022 to 2023, 82,000 violence-related calls, 70,000 recorded assault victims. Victims per call run 0.84 to 0.89 across the five bands of Black share (coefficient 0.08, standard error 0.11); calls per resident are 2.1 times higher in the Blackest districts than the whitest.

New Orleans (`out/nola_calls.md`, `scripts/nola_calls.py`), where each call can be joined to the report it produced by its item number: 17 ZIP codes, 2022 to 2023, 40,000 assault-type calls, 22% of them producing a victim report. Victims per call run 0.94 to 1.08 across the bands with no trend (coefficient 0.00, standard error 0.12); calls per resident are 1.8 times higher in the Blackest ZIPs.

| City | Unit | Victims per call, whitest to Blackest band | Recording effect (regression) | Calls per resident, Blackest over whitest |
|---|---|---|---|---|
| New York | 77 precincts | 0.62 to 0.54 | 1.07 (SE 0.07) | 2.8x |
| Los Angeles | 680 reporting districts | 0.89 to 0.84 | 1.09 (SE 0.11) | 2.1x |
| New Orleans | 17 ZIP codes | 0.99 to 1.07 | 1.00 (SE 0.12) | 1.8x |
| Baltimore | 133 neighborhoods | 0.37 to 0.40 | 1.22 (SE 0.07) | 2.3x |

In every city the within-band ratio of Black to White women's recorded rates is largest in the whitest areas and smallest in the Blackest: assaults are recorded where they happen, residents are counted where they live. Citywide, women 18 and older: New York 5.2x, Los Angeles 5.2x, New Orleans 3.5x, Baltimore 2.5x.

## Emergency departments see the police gap, not the survey's

Hospital records do not depend on anyone calling the police. The National Hospital Ambulatory Medical Care Survey samples emergency department visits nationally; a visit counts as an assault when any listed cause or diagnosis carries ICD-10 code X92 to Y09 (the definition in NCHS Data Brief 481, which reports 13.8 visits per 1,000 for Black non-Hispanic people against 3.1 for White over 2019 to 2021). From the 2022 public-use file (`out/nhamcs_ed.md`, `scripts/nhamcs_ed.py`), adults 18 and older, per 100,000 a year:

| | Black | White | Ratio (95% interval) |
|---|---|---|---|
| Women | 1,872 | 380 | 4.9x (3.0 to 8.2) |
| Men | 2,361 | 438 | 5.4x (3.3 to 8.9) |
| All ages, both sexes | 1,792 | 390 | 4.6x (3.3 to 6.3) |

The cells are small (34 Black women's visits and 27 White women's sampled) and the intervals ignore the survey design, so the figures are rough. But the emergency-room gap for women is about 5x: the same size as the police gap, not the survey's 1 to 2x. The cell for Hispanic women is too small to use (6 visits).

That moves the weight of the evidence. Two independent systems, police and hospitals, agree on 4 to 5x; the one source that puts it near 1 to 2x is the household survey, whose coverage of Black women is the weakest of the three.

## The survey

Women 18 and older, aggravated and simple assault, ratio of Black women's rate to the other group's. Intervals: 95% bootstrap over persons, widened for a design effect of 2.

| Source | vs White | vs Hispanic |
|---|---|---|
| Police records, 51 cities that record ethnicity (2022 to 2025) | 4.19 | 2.10 |
| NCVS, every assault, US (2015 to 2024) | 0.98 (0.80 to 1.20) | 1.15 (0.89 to 1.45) |
| NCVS, every assault, places of 250,000+ | 0.96 (0.65 to 1.33) | 1.36 (0.92 to 1.99) |
| NCVS, assaults reported to police, US | 1.13 (0.86 to 1.49) | 1.11 (0.81 to 1.53) |
| NCVS, assaults reported to police, places of 250,000+ | 1.37 (0.78 to 2.14) | 1.45 (0.82 to 2.44) |

- In the survey, Black women's assault rate is about the same as White women's and a little above Hispanic women's. The 4x police gap does not appear.
- Black women report more often: 54% of their assaults reached police, against 47% for White women (39% in large places) and 55% for Hispanic women. That lifts the reported-only ratio to about 1.1 to 1.4, still far below 4.
- The difference sits on Black women's side. Police records hold about 4,400 assaults on Black women per 100,000 a year; the survey's estimate of assaults on Black women that reached police in large places is about 1,200. For White women the two are close (about 1,050 and 900).
- It holds for aggravated assault only, for assaults with an injury, and without repeat ("series") victimizations: the survey ratio against White women stays between 1.0 and 1.8; the police ratio for aggravated assault alone is 4.9. See `out/ncvs.md`.

## Where the two sources part ways

By the victim's relationship to the offender (`out/by_relationship.md`, `scripts/by_relationship.py`), women 18 and older:

| | Survey, all assaults, large places | Survey, with injury, large places | Police, 51 cities | Police, with injury |
|---|---|---|---|---|
| Intimate partner | 2.37x | 2.81x | 4.47x | 4.10x |
| Other relative | 2.45x | 1.52x | 5.60x | 5.06x |
| Known | 1.19x | 1.52x | 4.33x | 3.92x |
| Stranger | 0.45x | 1.02x | 3.11x | 2.75x |
| All known relationships | 0.91x | 1.75x | 4.39x | 4.03x |

- The survey's low stranger ratio is mostly verbal threats against White women, which police would code as intimidation or not record: with an injury required, it is 1.0x.
- Like for like (assaults with an injury), police records show about 4x and the survey 1.0x nationally, 1.75x in large places. The difference holds in every relationship category.
- It sits on Black women's side. Police record about 2,000 assaults with an injury on Black women per 100,000 a year; the survey estimates about 500 in large places, reported or not. For White women the figures are about 500 and 290.
- Not the cause, tested in DC's records (the largest gap, 10.5x for women 18 and older): one assault producing several victim records. Counting one record per incident, leaving out mutual fights ("victim was offender"), or keeping only single-victim incidents moves the ratio between 10.4x and 10.7x.
- Not the cause, tested in Los Angeles (`out/la_repeat_victims.md`): the same women reported again and again. Matching reports by block address, descent and birth year (net of chance matches, measured with a placebo of birth years 5 to 7 apart), Black and White women both average about 1.1 reports each over 2020 to 2023, and counting women instead of reports moves the ratio against White women from 5.7x to 5.65x. The matching misses women who moved or whose address is missing, but there is no sign it misses them more in one group.
- Possible, not proven: the survey under-reaching Black women. Each Black woman who answers stands in for 1.25 times as many women as each White woman who answers (1.15 in 2015, 1.32 in 2024). Weighting restores the count, but not whether those who answer were assaulted as often as those who do not. Hispanic and Asian women are weighted up about as much, so this alone does not single out Black women.
- Not testable with DC's public data: calls against recorded incidents (DC publishes no incident-level 911 data) and repeat victimization of the same women (no person or address link to victims).

## What this does and does not say

The gap in police records is much larger than the gap in what women tell the survey. Each explanation tested here, and what it did:

| Explanation | Tested where | Result |
|---|---|---|
| Black women report assaults to police more often | NCVS | A little (54% against 47%); lifts the survey ratio to about 1.1 to 1.4, not 4 |
| Survey "simple assault" includes threats police do not record | NCVS, injury only | No: with an injury required the survey ratio is 1.0 nationally, 1.75 in large places |
| One assault becomes several police records | DC | No: 10.4x to 10.7x however records are counted |
| The same women are reported again and again | Los Angeles | No: about 1.1 reports per woman in both groups; the ratio moves from 5.7x to 5.65x |
| Police write up more victims per call in Black neighborhoods | New York, Los Angeles, New Orleans, Baltimore | Not in three cities (victims per call flat across bands); a little in Baltimore (up to 1.2x) |
| The excess is public housing or shelters | New York | Partly: 17% of the recorded assaults on Black women are in public housing against 3% of those on White women; outside it the ratio is 4.5x, not 5.2x |
| Assaults are recorded where they happen, residents counted where they live | New York | Large: within the Blackest precincts the gap is 2.9x, against 5.2x citywide and 7.6x in the whitest |

What remains is a gap of roughly 2 to 3 between the calls that reach police from the places Black women live and what Black women tell the survey. Two explanations are left. The emergency-room figures, which agree with the police and not the survey, point to the first; neither can be settled with public data:

- The survey misses assaults on Black women: through non-response (each Black woman who answers stands in for 25% more women than each White woman who answers), women outside households, or partner violence not described at home.
- More assaults on Black women come to police attention through other people: neighbors and bystanders calling 911, building and housing staff, hospitals, in places where that is the norm.

## What would close the gap in what is known

Two explanations are left, and each needs a dataset this project cannot reach. In order of what each would settle:

| Open question | What would answer it | Where it is | Who can do it |
|---|---|---|---|
| Does the survey undercount assaults on Black women? | The restricted NCVS files, which carry the sample design and the non-respondents' Census characteristics, so victimization can be estimated by who did not answer and where they live | Federal Statistical Research Data Centers (Census Bureau), by approved proposal | A researcher with RDC access; about a year from proposal to result |
| Who makes the call? | 911 records that say whether the caller was the victim, a bystander, a neighbor, a building or housing employee, or an alarm, joined to the recorded victim | Dispatch systems hold a caller type; few cities publish it. Ask the departments in New York, Baltimore, Chicago and Philadelphia for a one-year extract by call type and caller relationship, with no names | A records request to each department; weeks to months |
| Is the emergency-room gap for women precise? | The 2022 figure rests on 34 and 27 sampled visits. Pooling NHAMCS 2019 to 2023 would triple the sample; HCUP state databases hold every visit | ftp.cdc.gov NHAMCS files (the FTP stalls; the Internet Archive holds copies); HCUP by purchase | Anyone, a day; HCUP for a fee |
| Are Black women in shelters and institutions counted anywhere? | Shelter intake counts by race and sex and reason, and hospital records from places the survey does not reach | HUD Homeless Management Information Systems (local continuums of care); hospital data as above | A records request to each city's continuum of care |
| Does the recording effect vary by city? | The New York and Baltimore test in every city that publishes calls with a type and a location and victims with race: Seattle, Detroit, Nashville, Minneapolis, Denver and Philadelphia look possible | Each city's open-data portal | This pipeline, about a day a city |

Next steps, in the order they pay off:

1. Done: the calls test in Los Angeles and New Orleans (flat) and Baltimore (a small effect). The recording effect is local where it exists; Baltimore is the city to ask about.
2. Done: the emergency-room gap is 4.9x for women (NHAMCS 2022), so the survey is the outlier.
3. Write the one-page question for the restricted NCVS and offer it to a researcher with Research Data Center access. The question: among women who did not answer the survey, estimated from their block's characteristics, how much higher would the assault rate of Black women be?
4. Ask one department for a caller-type extract. Baltimore, whose dispatch data is already published in detail, is the natural first ask.

What none of these would change: police records show about 4 times as many assaults on Black women as on White women in every large city, the difference is already in the 911 calls, and emergency departments see a gap of the same size.

## Limits

- This shows what, not why: it says what each source counts and where they part ways. It does not say why Black women are assaulted, or why anyone calls the police.
- Reported crimes only, on the police side: willingness to report, and who else reports, differ by group, place and time. The survey side counts assaults not reported to police, but only among people it reaches.
- Race is recorded by officers in police data and by respondents in the survey; the two need not agree. Police denominators count residents who are Black alone, so the race-coding bound from the national run applies.
- Reports, not people: police records count reports (someone assaulted twice counts twice); the survey caps one person's repeated victimizations at 10.
- Small samples: 919 Black women victims over 2015 to 2024 (248 for 2022 to 2024). Intervals are wide for any one window or place size.
- The public NCVS Select files carry no survey strata or clusters; the intervals assume a design effect of 2, a rough correction.
- Definitions differ: survey simple assault includes verbal threats, which police code as intimidation (left out of the police side). The injury-only check addresses this.
- Ages 18 and older on both sides, the first age at which the survey's and the Census's bands align.
- Police-side ratios pool the 51 cities whose departments record ethnicity.

## Data and rebuild

Bureau of Justice Statistics, NCVS Select person-level files, through the BJS open-data API (victimization `gcuy-rt5g`, population `r4j4-fdwx`). Codebook in `docs/`. Weights follow BJS: series-adjusted victimization weights over person weights. Checked against BJS published violent victimization rates: 21.0 per 1,000 in 2019, 23.5 in 2022, 22.5 in 2023, all matched.

```bash
python scripts/fetch_ncvs.py      # data/raw/, as received, with .source.json
python scripts/analyze_ncvs.py    # out/ncvs_results.json, out/ncvs.md
python scripts/by_relationship.py  # out/by_relationship.json, out/by_relationship.md
python scripts/la_repeat_victims.py  # out/la_repeat_victims.json, out/la_repeat_victims.md (reads ../LA-Crime/data)
python scripts/nyc_calls.py          # out/nyc_calls.json, out/nyc_calls.md (NYPD calls, complaints and precincts in data/nyc/, downloaded by curl; see the script)
python scripts/nyc_premises.py       # out/nyc_premises.json, out/nyc_premises.md
python scripts/bmore_calls.py        # out/bmore_calls.json, out/bmore_calls.md (Baltimore calls and polygons in data/baltimore/; victims from ../Baltimore-Assault-Victims)
python scripts/la_calls.py           # out/la_calls.json, out/la_calls.md (LAPD calls and reporting districts in data/la/; victims and tracts from ../LA-Crime)
python scripts/nola_calls.py         # out/nola_calls.json, out/nola_calls.md (New Orleans calls and reports in data/nola/)
python scripts/nhamcs_ed.py          # out/nhamcs_ed.json, out/nhamcs_ed.md (data/nhamcs/ed2022-stata.dta, from CDC's FTP via the Internet Archive)
```
