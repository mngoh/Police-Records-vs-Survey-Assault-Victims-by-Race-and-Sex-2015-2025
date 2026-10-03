# Racial bias review

Focus: Black women. This screen finds candidates; read every flag in context before acting.

## Data

- **FLAG: race coding.** Officers record race by sight; the denominator is Black alone. Alone or in combination is 20% larger. Worst-case ratios: Hispanic 1.17x (from 1.41x), White 4.09x (from 4.92x), Asian 3.19x (from 3.84x). The writeup must state this bound.
- **note: overlapping denominators.** Share of each race-alone group that is also Hispanic: {'Black': 7.0, 'Asian': 0.7}. These residents count in two denominators; small shares are tolerable, large ones need non-Hispanic tables.
- **note: race outside the groups.** 6.5% of victims map to no group. Largest raw codes: `U` 12,777, `I` 1,237. Check none of them should belong to a group.
- **note: unknown race by sex.** Women 5.7%, men 7.4%.
- **note: enforcement and reporting.** Police data reflects where police patrol and who calls them. Heavier policing or more reporting in some neighborhoods raises recorded rates there. The writeup must say the data cannot separate this from real differences.
- **note: controls are not neutral.** Neighborhood, income and housing are shaped by segregation and discrimination. A gap that shrinks after these controls has been located, not explained away; say so.

## Writeup

Files: `README.md`

### README.md
- **review: Offender implication** (`offender`): "By the victim's relationship to the offender (`out/by_relationship.md`, `scripts/by_relationship.py`), women 18 and older:"  
  Victim data says nothing about who offended. Remove, or state that offenders are not in the data.
- **review: Offender implication** (`offender`): "- Not the cause, tested in DC's records (the largest gap, 10.5x for women 18 and older): one assault producing several victim records. Counting one record per incident, leaving out mutual fights ("victim was offender"), ..."  
  Victim data says nothing about who offended. Remove, or state that offenders are not in the data.

### Required statements

- present: says it does not explain why
- present: names reporting differences
- present: names the race-coding limit
- present: separates reports from people

## Reviewer questions (answer in prose, not by regex)

- Does any sentence invite the reader to infer who the offenders are?
- Would the framing read the same if the groups were swapped?
- Is the comparison group chosen to make the gap look larger (for example, headlining the most extreme pair)?
- Are structural explanations (segregation, policing intensity, access to services) acknowledged as unmeasured, without being asserted?
- Does the headline survive the race-coding worst case and the least favorable comparison?
- Is the focus group described with agency and dignity, as people harmed, not as a problem?