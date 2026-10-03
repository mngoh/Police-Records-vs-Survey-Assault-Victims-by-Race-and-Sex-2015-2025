"""The calls test in Los Angeles: LAPD violence-related 911 calls against recorded assault victims, by reporting district,
2022 to 2023 (the last two full years before LAPD's move to NIBRS).

  calls      LAPD Calls for Service 2022 and 2023 (data.lacity.org u6ri-98iw, uq7m-rynj), call types naming domestic
             violence, fights, battery, cutting, ADW, assault, shooting, stabbing or a violent person, grouped by
             reporting district (data/la/calls_<year>.csv). About a third of all calls carry no reporting district
             and are left out.
  victims    the Los-Angeles-CA-Assault-Victim-Rates-by-Race-and-Sex-2020-2023 project's simple and aggravated assault victims (codes 624, 626, 230, 236), all ages and
             both sexes for the per-call figures; women 18 and older by descent (B, W) for the within-band ratio.
  residents  the Los-Angeles-CA-Assault-Victim-Rates-by-Race-and-Sex-2020-2023 project's ACS tract tables, tracts assigned to the 1,135 reporting-district polygons
             (data/la/reporting_districts.geojson) by centroid.
Reporting districts with 500+ residents, in five population-weighted bands by Black share.

  python scripts/la_calls.py      ->  out/la_calls.json, out/la_calls.md
"""
import json
import pathlib

import numpy as np
import pandas as pd
import statsmodels.api as sm
from shapely.geometry import shape
from shapely.strtree import STRtree

ROOT = pathlib.Path(__file__).resolve().parent.parent
LA = ROOT.parent / "Los-Angeles-CA-Assault-Victim-Rates-by-Race-and-Sex-2020-2023"
D = ROOT / "data/la"
TABLES = {"Black": "B01001B", "White": "B01001H", "Hispanic": "B01001I", "Asian": "B01001D"}
YEARS = [2022, 2023]


def rd_population():
    acs = json.loads((LA / "data/external/acs_la_tracts.json").read_text())["data"]
    geo = json.loads((LA / "data/external/la_tracts_geometry.json").read_text())["features"]
    feats = [f for f in json.loads((D / "reporting_districts.geojson").read_text())["features"] if f.get("geometry")]
    polys = [shape(f["geometry"]) for f in feats]
    names = [int(f["properties"]["REPDIST"]) for f in feats]
    tree = STRtree(polys)
    rows = []
    for f in geo:
        gid = f["properties"]["geoid"]
        if gid not in acs:
            continue
        c = shape(f["geometry"]).centroid
        hit = [i for i in tree.query(c) if polys[i].contains(c)]
        rd = names[hit[0]] if hit else None
        row = {"rd": rd, "total": sum(float(acs[gid][t]["estimate"][f"{t}001"] or 0) for t in TABLES.values())}
        for g, t in TABLES.items():
            est = acs[gid][t]["estimate"]
            row[g] = float(est[f"{t}001"] or 0)
            row[f"{g}_F18"] = sum(float(est[f"{t}{i:03d}"] or 0) for i in range(22, 32))
        rows.append(row)
    d = pd.DataFrame(rows)
    un = d[d["rd"].isna()]
    return d.dropna(subset=["rd"]).astype({"rd": int}).groupby("rd").sum(numeric_only=True), int(len(un)), float(un["total"].sum())


def main():
    pop, n_un, pop_un = rd_population()
    pop["black_share"] = pop["Black"] / pop["total"]
    calls = pd.concat([pd.read_csv(D / f"calls_{y}.csv", dtype={"rpt_dist": str}) for y in YEARS]).dropna(subset=["rpt_dist"])
    calls["rd"] = pd.to_numeric(calls["rpt_dist"], errors="coerce")
    calls = calls.dropna(subset=["rd"]).astype({"rd": int})
    c = calls.groupby("rd")["n"].sum().rename("calls")
    v = pd.concat([pd.read_csv(LA / f"data/{f}", dtype=str) for f in ("eda_data.csv", "eda_data_deadly.csv")]).drop_duplicates("div_record")
    v = v[v["year_incident_date"].astype(int).isin(YEARS)]
    v["rd"] = pd.to_numeric(v["rpt"], errors="coerce")
    v = v.dropna(subset=["rd"]).astype({"rd": int})
    v["age"] = pd.to_numeric(v["vict_age"], errors="coerce")
    vict = v.groupby("rd").size().rename("victims")
    w = v[(v["vict_sex"] == "F") & (v["age"] >= 18)]
    bw = w[w["vict_race"] == "B"].groupby("rd").size().rename("black_women")
    ww = w[w["vict_race"] == "W"].groupby("rd").size().rename("white_women")
    d = pop.join([c, vict, bw, ww], how="inner").fillna(0)
    d = d[(d["total"] >= 500) & (d["calls"] > 0)]
    yrs = len(YEARS)
    d["victims_per_call"] = d["victims"] / d["calls"]
    d = d.sort_values("black_share")
    d["band"] = np.minimum(((d["total"].cumsum() / d["total"].sum()) * 5).astype(int), 4)
    bands = []
    for b, x in d.groupby("band"):
        tot = x["total"].sum()
        rb = x["black_women"].sum() / x["Black_F18"].sum() / yrs * 1e5 if x["Black_F18"].sum() else None
        rw = x["white_women"].sum() / x["White_F18"].sum() / yrs * 1e5 if x["White_F18"].sum() else None
        bands.append({"band": int(b), "districts": int(len(x)), "black_share": [round(x["black_share"].min() * 100), round(x["black_share"].max() * 100)], "residents": int(tot),
                      "calls_per_1k": round(x["calls"].sum() / tot / yrs * 1000, 1), "victims_per_1k": round(x["victims"].sum() / tot / yrs * 1000, 1),
                      "victims_per_call": round(x["victims"].sum() / x["calls"].sum(), 3), "black_women_rate": round(rb) if rb else None, "white_women_rate": round(rw) if rw else None,
                      "ratio_black_white_women": round(rb / rw, 2) if rb and rw else None, "black_women_victims": int(x["black_women"].sum()), "white_women_victims": int(x["white_women"].sum())})
    X = sm.add_constant(pd.DataFrame({"log_calls": np.log(d["calls"]), "black_share": d["black_share"], "log_pop": np.log(d["total"])}))
    fit = sm.OLS(np.log(d["victims"].clip(lower=0.5)), X).fit(cov_type="HC1")
    corr = float(np.corrcoef(d["black_share"], d["victims_per_call"])[0, 1])
    city = {"black_women_rate": round(d["black_women"].sum() / d["Black_F18"].sum() / yrs * 1e5), "white_women_rate": round(d["white_women"].sum() / d["White_F18"].sum() / yrs * 1e5)}
    city["ratio"] = round(city["black_women_rate"] / city["white_women_rate"], 2)
    lo, hi = bands[0], bands[-1]
    res = {"years": YEARS, "districts": int(len(d)), "tracts_unassigned": n_un, "residents_unassigned": int(pop_un),
           "totals": {"calls": int(d["calls"].sum()), "victims": int(d["victims"].sum())}, "bands": bands, "citywide_women_18plus": city,
           "top_over_bottom": {"calls_per_1k": round(hi["calls_per_1k"] / lo["calls_per_1k"], 2), "victims_per_1k": round(hi["victims_per_1k"] / lo["victims_per_1k"], 2), "victims_per_call": round(hi["victims_per_call"] / lo["victims_per_call"], 2)},
           "regression": {"black_share_coef": round(float(fit.params["black_share"]), 3), "black_share_se": round(float(fit.bse["black_share"]), 3), "log_calls_coef": round(float(fit.params["log_calls"]), 3), "r2": round(float(fit.rsquared), 3)},
           "corr_black_share_victims_per_call": round(corr, 3)}
    (ROOT / "out/la_calls.json").write_text(json.dumps(res, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)) + "\n")
    L = [f"# Los Angeles: violence-related 911 calls against recorded assault victims, by reporting district, {YEARS[0]} to {YEARS[-1]}", "",
         f"{len(d)} reporting districts of 500+ residents, {res['totals']['calls']:,} calls, {res['totals']['victims']:,} recorded assault victims (all ages, both sexes). "
         f"Women's rates 18 and older. Citywide, Black women {city['black_women_rate']:,}, White women {city['white_women_rate']:,}, ratio {city['ratio']}. Generated by `scripts/la_calls.py`.", "",
         "| Black share of residents | Districts | Residents | Calls per 1,000 a year | Recorded victims per 1,000 | Victims per call | Black women's rate | White women's rate | Ratio |", "|---|---|---|---|---|---|---|---|---|"]
    for b in bands:
        L.append(f"| {b['black_share'][0]}% to {b['black_share'][1]}% | {b['districts']} | {b['residents']:,} | {b['calls_per_1k']} | {b['victims_per_1k']} | {b['victims_per_call']} | "
                 f"{b['black_women_rate']:,} | {b['white_women_rate']:,} | {b['ratio_black_white_women']} |")
    t, r = res["top_over_bottom"], res["regression"]
    L += ["", f"Highest band over lowest: calls per resident {t['calls_per_1k']}x, recorded victims per resident {t['victims_per_1k']}x, victims per call {t['victims_per_call']}x.",
          f"Regression (log victims on log calls, Black share, log residents): Black share {r['black_share_coef']} (SE {r['black_share_se']}), exp = {np.exp(r['black_share_coef']):.2f}. Correlation of Black share with victims per call: {corr:.2f}.",
          f"Tracts not assigned to a reporting district: {n_un} ({int(pop_un):,} residents)."]
    (ROOT / "out/la_calls.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
