"""Does the gap exist before police record anything? New York's 911 assault calls against its recorded assault victims,
by precinct, 2022 to 2025.

A 911 call carries no victim race, so the test runs through place. For each of the 77 precincts:
  residents by group (ACS 2020 to 2024 tracts, assigned to precincts by centroid; the national run's cache)
  assault calls (NYPD calls for service, typ_desc starting ASSAULT; child abuse and school calls kept, flagged)
  recorded assault victims (NYPD complaints, felony assault and assault 3 and related, less menacing and assaults on
  officers and public employees, to match NIBRS 13A and 13B), by victim race and sex, Hispanic first
Precincts are grouped into five population-weighted bands by their Black share of residents. In each band: calls per
1,000 residents, recorded victims per 1,000, and victims recorded per call. If calls per resident climb with the Black
share as steeply as recorded victims do, the gap is already there when the phone rings; if victims per call climb, the
recording stage adds to it. A regression of log victims on log calls and the Black share puts a number on the second.
Alongside: Black women's recorded rate against White women's within each band, which is the national gap seen inside
precincts of like composition.

  python scripts/nyc_calls.py      ->  out/nyc_calls.json, out/nyc_calls.md   (after the data/nyc downloads)
"""
import glob
import json
import pathlib

import numpy as np
import pandas as pd
import statsmodels.api as sm
from shapely.geometry import shape

ROOT = pathlib.Path(__file__).resolve().parent.parent
NYC = ROOT / "data/nyc"
CACHE = ROOT.parent / "US-Large-Cities-Assault-Victim-Rates-by-Race-and-Sex-2022-2025/cities/new_york/out/cache"
TABLES = {"Black": "B01001B", "White": "B01001H", "Hispanic": "B01001I", "Asian": "B01001D"}
RACE = {"BLACK": "Black", "WHITE": "White", "WHITE HISPANIC": "Hispanic", "BLACK HISPANIC": "Hispanic", "ASIAN / PACIFIC ISLANDER": "Asian"}
NOT_ASSAULT = ("MENACING", "POLICE/PEACE OFFICER", "PUBLIC SERVICE", "TRAFFIC AGENT", "SCHOOL SAFETY")
YEARS = [2022, 2023, 2024, 2025]


def precinct_population():
    acs = json.loads((CACHE / "acs_tracts.json").read_text())["data"]
    ses = json.loads((CACHE / "acs_tracts_ses.json").read_text())["data"]
    geo = json.loads((CACHE / "tracts_geometry.json").read_text())["features"]
    pcts = [(shape(f["geometry"]), int(f["properties"]["precinct"])) for f in json.loads((NYC / "precincts.geojson").read_text())["features"]]
    rows = []
    for f in geo:
        gid = f["properties"]["geoid"]
        if gid not in acs:
            continue
        c = shape(f["geometry"]).centroid
        pct = next((p for poly, p in pcts if poly.contains(c)), None)
        est = {g: acs[gid][t]["estimate"] for g, t in TABLES.items()}
        row = {"geoid": gid, "precinct": pct, "total": float(ses[gid]["B01003"]["estimate"]["B01003001"] or 0)}
        for g, t in TABLES.items():
            row[g] = float(est[g][f"{t}001"] or 0)
            row[f"{g}_F"] = float(est[g][f"{t}017"] or 0)
        rows.append(row)
    d = pd.DataFrame(rows)
    unassigned = d[d["precinct"].isna()]
    return d.dropna(subset=["precinct"]).groupby("precinct").sum(numeric_only=True), int(len(unassigned)), float(unassigned["total"].sum())


def main():
    pop, n_un, pop_un = precinct_population()
    pop.index = pop.index.astype(int)
    pop["black_share"] = pop["Black"] / pop["total"]

    calls = pd.concat([pd.read_csv(f, dtype={"nypd_pct_cd": str}).assign(year=int(pathlib.Path(f).stem[-4:])) for f in sorted(glob.glob(str(NYC / "calls_assault_20*.csv")))])
    calls = calls[calls["nypd_pct_cd"].notna()]
    calls["precinct"] = pd.to_numeric(calls["nypd_pct_cd"], errors="coerce")
    calls = calls.dropna(subset=["precinct"]).astype({"precinct": int})
    calls["other"] = calls["typ_desc"].str.contains("CHILD ABUSE|SCHOOL", regex=True)
    years = sorted(calls["year"].unique())
    c = calls.groupby("precinct")["n"].sum().rename("calls")
    c_adult = calls[~calls["other"]].groupby("precinct")["n"].sum().rename("calls_no_child_school")

    comp = pd.read_csv(NYC / "complaints_assault_by_pct.csv", dtype={"addr_pct_cd": str})
    comp = comp[comp["yr"].isin(years) & ~comp["pd_desc"].str.contains("|".join(NOT_ASSAULT), regex=True)]
    comp["precinct"] = pd.to_numeric(comp["addr_pct_cd"], errors="coerce")
    comp = comp.dropna(subset=["precinct"]).astype({"precinct": int})
    comp["group"] = comp["vic_race"].map(RACE)
    v = comp.groupby("precinct")["n"].sum().rename("victims")
    vw = comp[comp["vic_sex"] == "F"].pivot_table(index="precinct", columns="group", values="n", aggfunc="sum", fill_value=0)

    d = pop.join([c, c_adult, v, vw.add_suffix("_women_victims")], how="inner").fillna(0)
    d = d[d["total"] > 5000]
    yrs = len(years)
    d["calls_per_1k"] = d["calls"] / d["total"] / yrs * 1000
    d["victims_per_1k"] = d["victims"] / d["total"] / yrs * 1000
    d["victims_per_call"] = d["victims"] / d["calls"]
    d = d.sort_values("black_share")
    cum = d["total"].cumsum() / d["total"].sum()
    d["band"] = np.minimum((cum * 5).astype(int), 4)

    bands = []
    for b, x in d.groupby("band"):
        tot = x["total"].sum()
        rb = x["Black_women_victims"].sum() / x["Black_F"].sum() / yrs * 1e5 if x["Black_F"].sum() else None
        rw = x["White_women_victims"].sum() / x["White_F"].sum() / yrs * 1e5 if x["White_F"].sum() else None
        bands.append({"band": int(b), "precincts": int(len(x)), "black_share": [round(x["black_share"].min() * 100), round(x["black_share"].max() * 100)],
                      "residents": int(tot), "calls_per_1k": round(x["calls"].sum() / tot / yrs * 1000, 1),
                      "victims_per_1k": round(x["victims"].sum() / tot / yrs * 1000, 1), "victims_per_call": round(x["victims"].sum() / x["calls"].sum(), 3),
                      "black_women_rate": round(rb) if rb else None, "white_women_rate": round(rw) if rw else None,
                      "ratio_black_white_women": round(rb / rw, 2) if rb and rw else None})
    lo, hi = bands[0], bands[-1]
    X = sm.add_constant(pd.DataFrame({"log_calls": np.log(d["calls"]), "black_share": d["black_share"], "log_pop": np.log(d["total"])}))
    fit = sm.OLS(np.log(d["victims"]), X).fit(cov_type="HC1")
    corr = float(np.corrcoef(d["black_share"], d["victims_per_call"])[0, 1])
    res = {"years": years, "precincts": int(len(d)), "tracts_unassigned": n_un, "residents_unassigned": int(pop_un),
           "totals": {"calls": int(d["calls"].sum()), "calls_no_child_school": int(d["calls_no_child_school"].sum()), "victims": int(d["victims"].sum())},
           "bands": bands,
           "top_over_bottom": {"calls_per_1k": round(hi["calls_per_1k"] / lo["calls_per_1k"], 2), "victims_per_1k": round(hi["victims_per_1k"] / lo["victims_per_1k"], 2),
                               "victims_per_call": round(hi["victims_per_call"] / lo["victims_per_call"], 2)},
           "regression": {"black_share_coef": round(float(fit.params["black_share"]), 3), "black_share_se": round(float(fit.bse["black_share"]), 3),
                          "log_calls_coef": round(float(fit.params["log_calls"]), 3), "r2": round(float(fit.rsquared), 3),
                          "reading": "exp(coef) is the multiplier on recorded victims, at the same number of calls and residents, going from a precinct with no Black residents to one entirely Black"},
           "corr_black_share_victims_per_call": round(corr, 3),
           "precincts_table": json.loads(d.reset_index()[["precinct", "total", "black_share", "calls", "victims", "calls_per_1k", "victims_per_1k", "victims_per_call", "band"]].round(3).to_json(orient="records"))}
    (ROOT / "out/nyc_calls.json").write_text(json.dumps(res, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)) + "\n")

    L = [f"# New York: 911 assault calls against recorded assault victims, by precinct, {years[0]} to {years[-1]}", "",
         f"{len(d)} precincts, {res['totals']['calls']:,} assault calls, {res['totals']['victims']:,} recorded assault victims (all ages, both sexes). "
         "Precincts in five population-weighted bands by Black share of residents. Generated by `scripts/nyc_calls.py`.", "",
         "| Black share of residents | Precincts | Residents | Assault calls per 1,000 a year | Recorded victims per 1,000 | Victims per call | Black women's rate | White women's rate | Ratio |",
         "|---|---|---|---|---|---|---|---|---|"]
    for b in bands:
        L.append(f"| {b['black_share'][0]}% to {b['black_share'][1]}% | {b['precincts']} | {b['residents']:,} | {b['calls_per_1k']} | {b['victims_per_1k']} | {b['victims_per_call']} | "
                 f"{b['black_women_rate']:,} | {b['white_women_rate']:,} | {b['ratio_black_white_women']} |")
    t = res["top_over_bottom"]
    L += ["", f"Highest band over lowest: calls per resident {t['calls_per_1k']}x, recorded victims per resident {t['victims_per_1k']}x, victims per call {t['victims_per_call']}x.",
          f"Regression (log victims on log calls, Black share, log residents): Black share {res['regression']['black_share_coef']} (SE {res['regression']['black_share_se']}), "
          f"so at the same calls a wholly Black precinct records exp({res['regression']['black_share_coef']}) = {np.exp(res['regression']['black_share_coef']):.2f} times the victims of a precinct with no Black residents. "
          f"Correlation of Black share with victims per call: {corr:.2f}.",
          f"Tracts not assigned to a precinct: {n_un} ({int(pop_un):,} residents)."]
    (ROOT / "out/nyc_calls.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
