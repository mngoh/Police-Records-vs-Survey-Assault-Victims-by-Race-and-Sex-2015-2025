"""The New York test in a second city: Baltimore's 911 assault calls against its recorded assault victims, by neighborhood.

Baltimore publishes 911 calls with a description and the neighborhood (ArcGIS services CallsForService_2022,
911_CallsForService_2023, 911_CallsForService_PreviousYear_Present, grouped server-side into data/baltimore/calls_<year>.json),
victim-based crime records with race, sex, age and neighborhood (the Baltimore-MD-Assault-Victim-Rates-by-Race-and-Sex-2022-2024 project's copy of
Part1_Crime_Beta, cut to assaults in data/baltimore/victims_assault_2022_2024.csv), and neighborhood polygons
(data/baltimore/neighborhoods.geojson). Residents by group come from the national run's ACS tract cache, tracts
assigned to neighborhoods by centroid.
  calls      COMMON ASSAULT, AGGRAV ASSAULT, CUTTING, SHOOTING; a sensitivity adds FAMILY DISTURB
  victims    COMMON ASSAULT and AGG. ASSAULT, all ages and both sexes for the per-call figures; women 18 and older by
             race for the within-band ratio (Race BLACK_OR_AFRICAN_AMERICAN and WHITE; Hispanic ethnicity is mostly
             blank in this file, so White victims are White of any ethnicity while the denominator is non-Hispanic
             White women, which runs White women's rate a little high; about 6% of Baltimore is Hispanic)
Neighborhoods with 1,000+ residents, in five population-weighted bands by Black share, as for New York.

  python scripts/bmore_calls.py      ->  out/bmore_calls.json, out/bmore_calls.md
"""
import json
import pathlib

import numpy as np
import pandas as pd
import statsmodels.api as sm
from shapely.geometry import shape

ROOT = pathlib.Path(__file__).resolve().parent.parent
BM = ROOT / "data/baltimore"
CACHE = ROOT.parent / "US-Large-Cities-Assault-Victim-Rates-by-Race-and-Sex-2022-2025/cities/baltimore/out/cache"
TABLES = {"Black": "B01001B", "White": "B01001A", "Hispanic": "B01001I", "Asian": "B01001D"}
CALLS = ["COMMON ASSAULT", "AGGRAV ASSAULT", "CUTTING", "SHOOTING"]
YEARS = [2022, 2023]


def norm(s):
    return s.astype(str).str.upper().str.replace(r"[^A-Z0-9]+", " ", regex=True).str.strip()


def neighborhood_population():
    acs = json.loads((CACHE / "acs_tracts.json").read_text())["data"]
    ses = json.loads((CACHE / "acs_tracts_ses.json").read_text())["data"]
    geo = json.loads((CACHE / "tracts_geometry.json").read_text())["features"]
    polys = [(shape(f["geometry"]), f["properties"]["Name"]) for f in json.loads((BM / "neighborhoods.geojson").read_text())["features"] if f.get("geometry")]
    rows = []
    for f in geo:
        gid = f["properties"]["geoid"]
        if gid not in acs:
            continue
        c = shape(f["geometry"]).centroid
        name = next((n for poly, n in polys if poly.contains(c)), None)
        row = {"geoid": gid, "nb": name, "total": float(ses[gid]["B01003"]["estimate"]["B01003001"] or 0)}
        for g, t in TABLES.items():
            est = acs[gid].get(t, {}).get("estimate") if t in acs[gid] else None
            if est is None:  # White of any ethnicity is not in the kit's cache; fall back to non-Hispanic White
                est = acs[gid]["B01001H"]["estimate"]; t = "B01001H"
            row[g] = float(est[f"{t}001"] or 0)
            row[f"{g}_F18"] = sum(float(est[f"{t}{i:03d}"] or 0) for i in range(22, 32))
        rows.append(row)
    d = pd.DataFrame(rows)
    un = d[d["nb"].isna()]
    d = d.dropna(subset=["nb"])
    d["nb"] = norm(d["nb"])
    return d.groupby("nb").sum(numeric_only=True), int(len(un)), float(un["total"].sum())


def main():
    pop, n_un, pop_un = neighborhood_population()
    pop["black_share"] = pop["Black"] / pop["total"]
    calls = pd.concat([pd.DataFrame([f["attributes"] for f in json.loads((BM / f"calls_{y}.json").read_text())["features"]]).assign(year=y) for y in YEARS])
    calls = calls.dropna(subset=["Neighborhood"])
    calls["nb"] = norm(calls["Neighborhood"])
    core = calls[calls["description"].isin(CALLS)].groupby("nb")["n"].sum().rename("calls")
    wide = calls.groupby("nb")["n"].sum().rename("calls_with_family")
    v = pd.read_csv(BM / "victims_assault_2022_2024.csv", dtype=str)
    v = v[v["yr"].astype(int).isin(YEARS)].dropna(subset=["Neighborhood"])
    v["nb"] = norm(v["Neighborhood"])
    v["age"] = pd.to_numeric(v["Age"], errors="coerce")
    vict = v.groupby("nb").size().rename("victims")
    w = v[(v["Gender"] == "F") & (v["age"] >= 18)]
    bw = w[w["Race"] == "BLACK_OR_AFRICAN_AMERICAN"].groupby("nb").size().rename("black_women")
    ww = w[w["Race"] == "WHITE"].groupby("nb").size().rename("white_women")
    d = pop.join([core, wide, vict, bw, ww], how="inner").fillna(0)
    d = d[(d["total"] >= 1000) & (d["calls"] > 0)]
    yrs = len(YEARS)
    d["victims_per_call"] = d["victims"] / d["calls"]
    d = d.sort_values("black_share")
    d["band"] = np.minimum(((d["total"].cumsum() / d["total"].sum()) * 5).astype(int), 4)
    bands = []
    for b, x in d.groupby("band"):
        tot = x["total"].sum()
        rb = x["black_women"].sum() / x["Black_F18"].sum() / yrs * 1e5 if x["Black_F18"].sum() else None
        rw = x["white_women"].sum() / x["White_F18"].sum() / yrs * 1e5 if x["White_F18"].sum() else None
        bands.append({"band": int(b), "neighborhoods": int(len(x)), "black_share": [round(x["black_share"].min() * 100), round(x["black_share"].max() * 100)],
                      "residents": int(tot), "calls_per_1k": round(x["calls"].sum() / tot / yrs * 1000, 1), "victims_per_1k": round(x["victims"].sum() / tot / yrs * 1000, 1),
                      "victims_per_call": round(x["victims"].sum() / x["calls"].sum(), 3), "victims_per_call_with_family": round(x["victims"].sum() / x["calls_with_family"].sum(), 3),
                      "black_women_rate": round(rb) if rb else None, "white_women_rate": round(rw) if rw else None,
                      "ratio_black_white_women": round(rb / rw, 2) if rb and rw else None, "black_women_victims": int(x["black_women"].sum()), "white_women_victims": int(x["white_women"].sum())})
    X = sm.add_constant(pd.DataFrame({"log_calls": np.log(d["calls"]), "black_share": d["black_share"], "log_pop": np.log(d["total"])}))
    fit = sm.OLS(np.log(d["victims"].clip(lower=0.5)), X).fit(cov_type="HC1")
    corr = float(np.corrcoef(d["black_share"], d["victims_per_call"])[0, 1])
    city = {"black_women_rate": round(d["black_women"].sum() / d["Black_F18"].sum() / yrs * 1e5), "white_women_rate": round(d["white_women"].sum() / d["White_F18"].sum() / yrs * 1e5)}
    city["ratio"] = round(city["black_women_rate"] / city["white_women_rate"], 2)
    lo, hi = bands[0], bands[-1]
    res = {"years": YEARS, "neighborhoods": int(len(d)), "tracts_unassigned": n_un, "residents_unassigned": int(pop_un),
           "totals": {"calls": int(d["calls"].sum()), "calls_with_family": int(d["calls_with_family"].sum()), "victims": int(d["victims"].sum())}, "bands": bands, "citywide_women_18plus": city,
           "top_over_bottom": {"calls_per_1k": round(hi["calls_per_1k"] / lo["calls_per_1k"], 2), "victims_per_1k": round(hi["victims_per_1k"] / lo["victims_per_1k"], 2), "victims_per_call": round(hi["victims_per_call"] / lo["victims_per_call"], 2)},
           "regression": {"black_share_coef": round(float(fit.params["black_share"]), 3), "black_share_se": round(float(fit.bse["black_share"]), 3), "log_calls_coef": round(float(fit.params["log_calls"]), 3), "r2": round(float(fit.rsquared), 3)},
           "corr_black_share_victims_per_call": round(corr, 3)}
    (ROOT / "out/bmore_calls.json").write_text(json.dumps(res, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)) + "\n")
    L = [f"# Baltimore: 911 assault calls against recorded assault victims, by neighborhood, {YEARS[0]} to {YEARS[-1]}", "",
         f"{len(d)} neighborhoods of 1,000+ residents, {res['totals']['calls']:,} assault calls, {res['totals']['victims']:,} recorded assault victims (all ages, both sexes). "
         f"Women's rates are 18 and older; White victims are White of any ethnicity over non-Hispanic White residents (ethnicity is mostly blank in the file). Citywide, Black women {city['black_women_rate']:,}, White women {city['white_women_rate']:,}, ratio {city['ratio']}. Generated by `scripts/bmore_calls.py`.", "",
         "| Black share of residents | Neighborhoods | Residents | Assault calls per 1,000 a year | Recorded victims per 1,000 | Victims per call | With family-disturbance calls | Black women's rate | White women's rate | Ratio |", "|---|---|---|---|---|---|---|---|---|---|"]
    for b in bands:
        L.append(f"| {b['black_share'][0]}% to {b['black_share'][1]}% | {b['neighborhoods']} | {b['residents']:,} | {b['calls_per_1k']} | {b['victims_per_1k']} | {b['victims_per_call']} | {b['victims_per_call_with_family']} | "
                 f"{b['black_women_rate']:,} | {b['white_women_rate']:,} | {b['ratio_black_white_women']} |")
    t, r = res["top_over_bottom"], res["regression"]
    L += ["", f"Highest band over lowest: calls per resident {t['calls_per_1k']}x, recorded victims per resident {t['victims_per_1k']}x, victims per call {t['victims_per_call']}x.",
          f"Regression (log victims on log calls, Black share, log residents): Black share {r['black_share_coef']} (SE {r['black_share_se']}), exp = {np.exp(r['black_share_coef']):.2f}. Correlation of Black share with victims per call: {corr:.2f}.",
          f"Tracts not assigned to a neighborhood: {n_un} ({int(pop_un):,} residents)."]
    (ROOT / "out/bmore_calls.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
