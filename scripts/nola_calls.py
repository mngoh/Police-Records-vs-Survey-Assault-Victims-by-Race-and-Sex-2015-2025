"""The calls test in New Orleans, at the level of the call: each 911 assault call joined to the police report it produced.

New Orleans publishes calls for service (data.nola.gov, by year) and electronic police reports with victim race, sex
and age, and the two share an item number (the call's nopd_item is the report's item_number without its dashes). So
for every assault-type call this asks directly: did it produce a report with a victim, and of what race. Place is the
call's ZIP code, with residents by group from ACS ZCTAs (Census Reporter, fetched once into data/nola/acs_zcta.json).
  calls      2022 and 2023, types naming simple or aggravated assault or battery, shooting, cutting, a fight or a
             domestic disturbance, dispute or violence (data/nola/calls_<year>.csv); self-initiated calls left out
  reports    assault and battery reports, rows with persontype VICTIM (data/nola/epr_<year>.csv)
ZIP codes with 2,000+ residents, in five population-weighted bands by Black share.

  python scripts/nola_calls.py      ->  out/nola_calls.json, out/nola_calls.md
"""
import json
import pathlib
import time
import urllib.request

import numpy as np
import pandas as pd
import statsmodels.api as sm

ROOT = pathlib.Path(__file__).resolve().parent.parent
D = ROOT / "data/nola"
CR = "https://api.censusreporter.org/1.0/data/show/acs2024_5yr"
TABLES = {"Black": "B01001B", "White": "B01001H", "Hispanic": "B01001I", "Asian": "B01001D"}
YEARS = [2022, 2023]


def zcta_population(zips):
    path = D / "acs_zcta.json"
    if not path.exists():
        geos = ",".join(f"86000US{z}" for z in zips)
        url = f"{CR}?table_ids=B01003,{','.join(TABLES.values())}&geo_ids={geos}"
        for attempt in range(6):
            try:
                path.write_bytes(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "disparity-kit"}), timeout=300).read())
                break
            except urllib.error.HTTPError as e:
                if e.code != 429:
                    raise
                time.sleep(int(e.headers.get("Retry-After") or 300) + 5)
    data = json.loads(path.read_text())["data"]
    rows = []
    for z in zips:
        g = data.get(f"86000US{z}")
        if not g:
            continue
        row = {"zip": z, "total": float(g["B01003"]["estimate"]["B01003001"] or 0)}
        for name, t in TABLES.items():
            est = g[t]["estimate"]
            row[name] = float(est[f"{t}001"] or 0)
            row[f"{name}_F18"] = sum(float(est[f"{t}{i:03d}"] or 0) for i in range(22, 32))
        rows.append(row)
    return pd.DataFrame(rows).set_index("zip")


def main():
    c = pd.concat([pd.read_csv(D / f"calls_{y}.csv", dtype=str) for y in YEARS])
    c = c[(c["selfinitiated"] != "Y") & c["zip"].notna()]
    e = pd.concat([pd.read_csv(D / f"epr_{y}.csv", dtype=str) for y in YEARS])
    e = e[e["persontype"] == "VICTIM"].copy()
    e["key"] = e["item_number"].str.replace("-", "", regex=False)
    e["age"] = pd.to_numeric(e["victim_age"], errors="coerce")
    victims = e.groupby("key").size().rename("victims")
    w = e[(e["victim_gender"] == "FEMALE") & (e["age"] >= 18)]
    bw = w[w["victim_race"] == "BLACK"].groupby("key").size().rename("black_women")
    ww = w[w["victim_race"] == "WHITE"].groupby("key").size().rename("white_women")
    c = c.set_index("nopd_item").join([victims, bw, ww]).fillna({"victims": 0, "black_women": 0, "white_women": 0}).reset_index()
    c["report"] = c["victims"] > 0
    by_zip = c.groupby("zip").agg(calls=("nopd_item", "size"), with_report=("report", "sum"), victims=("victims", "sum"), black_women=("black_women", "sum"), white_women=("white_women", "sum"))
    pop = zcta_population(sorted(by_zip.index))
    d = pop.join(by_zip, how="inner")
    d = d[(d["total"] >= 2000) & (d["calls"] > 0)]
    d["black_share"] = d["Black"] / d["total"]
    yrs = len(YEARS)
    d["victims_per_call"] = d["victims"] / d["calls"]
    d["report_share"] = d["with_report"] / d["calls"]
    d = d.sort_values("black_share")
    d["band"] = np.minimum(((d["total"].cumsum() / d["total"].sum()) * 5).astype(int), 4)
    bands = []
    for b, x in d.groupby("band"):
        tot = x["total"].sum()
        rb = x["black_women"].sum() / x["Black_F18"].sum() / yrs * 1e5 if x["Black_F18"].sum() else None
        rw = x["white_women"].sum() / x["White_F18"].sum() / yrs * 1e5 if x["White_F18"].sum() else None
        bands.append({"band": int(b), "zips": int(len(x)), "black_share": [round(x["black_share"].min() * 100), round(x["black_share"].max() * 100)], "residents": int(tot),
                      "calls_per_1k": round(x["calls"].sum() / tot / yrs * 1000, 1), "victims_per_1k": round(x["victims"].sum() / tot / yrs * 1000, 1),
                      "calls_with_report_pct": round(x["with_report"].sum() / x["calls"].sum() * 100, 1), "victims_per_call": round(x["victims"].sum() / x["calls"].sum(), 3),
                      "black_women_rate": round(rb) if rb else None, "white_women_rate": round(rw) if rw else None, "ratio_black_white_women": round(rb / rw, 2) if rb and rw else None,
                      "black_women_victims": int(x["black_women"].sum()), "white_women_victims": int(x["white_women"].sum())})
    X = sm.add_constant(pd.DataFrame({"log_calls": np.log(d["calls"]), "black_share": d["black_share"], "log_pop": np.log(d["total"])}))
    fit = sm.OLS(np.log(d["victims"].clip(lower=0.5)), X).fit(cov_type="HC1")
    corr = float(np.corrcoef(d["black_share"], d["victims_per_call"])[0, 1])
    city = {"black_women_rate": round(d["black_women"].sum() / d["Black_F18"].sum() / yrs * 1e5), "white_women_rate": round(d["white_women"].sum() / d["White_F18"].sum() / yrs * 1e5)}
    city["ratio"] = round(city["black_women_rate"] / city["white_women_rate"], 2)
    lo, hi = bands[0], bands[-1]
    res = {"years": YEARS, "zips": int(len(d)), "totals": {"calls": int(d["calls"].sum()), "calls_with_report": int(d["with_report"].sum()), "victims": int(d["victims"].sum())}, "bands": bands,
           "citywide_women_18plus": city, "top_over_bottom": {"calls_per_1k": round(hi["calls_per_1k"] / lo["calls_per_1k"], 2), "victims_per_1k": round(hi["victims_per_1k"] / lo["victims_per_1k"], 2), "victims_per_call": round(hi["victims_per_call"] / lo["victims_per_call"], 2)},
           "regression": {"black_share_coef": round(float(fit.params["black_share"]), 3), "black_share_se": round(float(fit.bse["black_share"]), 3), "r2": round(float(fit.rsquared), 3)},
           "corr_black_share_victims_per_call": round(corr, 3)}
    (ROOT / "out/nola_calls.json").write_text(json.dumps(res, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)) + "\n")
    L = [f"# New Orleans: 911 assault calls joined to the reports they produced, by ZIP code, {YEARS[0]} to {YEARS[-1]}", "",
         f"{len(d)} ZIP codes of 2,000+ residents, {res['totals']['calls']:,} assault-type calls, {res['totals']['calls_with_report']:,} with a victim report, {res['totals']['victims']:,} victims (all ages, both sexes). "
         f"Women's rates 18 and older. Citywide, Black women {city['black_women_rate']:,}, White women {city['white_women_rate']:,}, ratio {city['ratio']}. Generated by `scripts/nola_calls.py`.", "",
         "| Black share of residents | ZIPs | Residents | Calls per 1,000 a year | Calls with a victim report | Victims per call | Recorded victims per 1,000 | Black women's rate | White women's rate | Ratio |", "|---|---|---|---|---|---|---|---|---|---|"]
    for b in bands:
        L.append(f"| {b['black_share'][0]}% to {b['black_share'][1]}% | {b['zips']} | {b['residents']:,} | {b['calls_per_1k']} | {b['calls_with_report_pct']}% | {b['victims_per_call']} | {b['victims_per_1k']} | "
                 f"{b['black_women_rate']:,} | {b['white_women_rate']:,} | {b['ratio_black_white_women']} |")
    t, r = res["top_over_bottom"], res["regression"]
    L += ["", f"Highest band over lowest: calls per resident {t['calls_per_1k']}x, recorded victims per resident {t['victims_per_1k']}x, victims per call {t['victims_per_call']}x.",
          f"Regression (log victims on log calls, Black share, log residents): Black share {r['black_share_coef']} (SE {r['black_share_se']}), exp = {np.exp(r['black_share_coef']):.2f}. Correlation of Black share with victims per call: {corr:.2f}."]
    (ROOT / "out/nola_calls.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
