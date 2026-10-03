"""Is the police-recorded gap a reporting gap? Black women's assault rate against White and Hispanic women's in the NCVS,
with and without the assaults never reported to police, beside the same ratio in police records.

NCVS (scripts/fetch_ncvs.py): women 18 and older; aggravated (newoff 3) and simple (newoff 4) assault, matching NIBRS
13A and 13B. Groups from race_ethnicity: non-Hispanic Black (2), non-Hispanic White (1), Hispanic (6), non-Hispanic
Asian or Pacific Islander (4), the same Hispanic-first rule as the police analysis. Rates follow BJS: series-adjusted
victimization weights (newwgt) over person weights (wgtpercy), per 100,000 a year. For each group:
  all          every assault, reported or not
  reported     assaults the victim says police learned of (notify 1)
  not reported (notify 2); "do not know" and residue are in "all" only
  share reported = reported / (reported + not reported)
Windows 2022 to 2024 (closest to the police data) and 2015 to 2024 (pooled, steadier); the whole country and places of
250,000 or more (popsize 3 to 5), the size of the cities in the police analysis.

Intervals: 95%, from a Poisson bootstrap over persons (idper), 400 replicates. The public files carry no survey strata
or clusters, so these understate the true uncertainty; a second set widens each on the log scale by sqrt(2), a design
effect of 2, as a rough correction. Unweighted case counts are reported so thin cells are visible.

Police side: the national run's victim files and ACS populations, pooled over its 59 cities, women 18 and older, for
the cities whose departments record ethnicity (the White comparison is biased where they do not).

Robustness (2015 to 2024): the same NCVS comparison for aggravated assault only, for assaults with an injury (NCVS
simple assault includes verbal threats, which police would code as intimidation, left out of the police side), and with
series victimizations left out; and the police side for aggravated assault only.

  python scripts/analyze_ncvs.py      ->  out/ncvs_results.json, out/ncvs.md
"""
import json
import pathlib

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
RUN = ROOT.parent / "US-Large-Cities-Assault-Victim-Rates-by-Race-and-Sex-2022-2025"
GROUPS = {"2": "Black", "1": "White", "6": "Hispanic", "4": "Asian"}
WINDOWS = {"2022 to 2024": (2022, 2024), "2015 to 2024": (2015, 2024)}
PLACES = {"US": None, "Places of 250,000+": {"3", "4", "5"}}
B = 400
rng = np.random.default_rng(20261003)


def load():
    v = pd.read_csv(ROOT / "data/raw/personal_victimization.csv", dtype=str)
    v = v[(v["sex"] == "2") & (v["ager"] != "1") & v["newoff"].isin(["3", "4"]) & v["race_ethnicity"].isin(GROUPS)].copy()
    v["w"] = pd.to_numeric(v["newwgt"])
    v["rep"] = v["w"] * (v["notify"] == "1")
    v["unrep"] = v["w"] * (v["notify"] == "2")
    p = pd.read_csv(ROOT / "data/raw/personal_population.csv", dtype=str)
    p = p[(p["sex"] == "2") & (p["ager"] != "1") & p["race_ethnicity"].isin(GROUPS)].copy()
    p["w"] = pd.to_numeric(p["wgtpercy"])
    for d in (v, p):
        d["year"] = d["year"].astype(int)
        d["group"] = d["race_ethnicity"].map(GROUPS)
    return v, p


def estimate(v, p):
    """Rates per 100,000 a year by group, ratios to Black women, share reported; point and bootstrap."""
    # one unit per person and group: their population weight and victimization weights
    pu = p.groupby(["idper", "group"])["w"].sum().rename("pop")
    vu = v.groupby(["idper", "group"])[["w", "rep", "unrep"]].sum()
    u = pd.concat([pu, vu], axis=1).fillna(0).reset_index()
    g = pd.Categorical(u["group"], categories=list(GROUPS.values())).codes
    cols = {k: u[k].to_numpy() for k in ("pop", "w", "rep", "unrep")}

    def stats(mult=None):
        s = {k: np.bincount(g, weights=a if mult is None else a * mult, minlength=4) for k, a in cols.items()}
        rate = {k: s[k] / s["pop"] * 1e5 for k in ("w", "rep", "unrep")}
        share = s["rep"] / (s["rep"] + s["unrep"]) * 100
        return rate, share

    rate, share = stats()
    reps = [stats(rng.poisson(1.0, len(u))) for _ in range(B)]
    names = list(GROUPS.values())
    out = {"cases": {n: int((v["group"] == n).sum()) for n in names},
           "cases_reported": {n: int(((v["group"] == n) & (v["notify"] == "1")).sum()) for n in names}}

    def ci(point, draws, log=True, deff=1.0):
        d = np.array(draws)
        if log:
            lo, hi = np.percentile(np.log(d), [2.5, 97.5])
            mid = np.log(point)
            return [round(float(np.exp(mid - (mid - lo) * np.sqrt(deff))), 2), round(float(np.exp(mid + (hi - mid) * np.sqrt(deff))), 2)]
        lo, hi = np.percentile(d, [2.5, 97.5])
        return [round(float(max(0.0, point - (point - lo) * np.sqrt(deff))), 1), round(float(min(100.0, point + (hi - point) * np.sqrt(deff))), 1)]

    for kind, label in (("w", "all"), ("rep", "reported"), ("unrep", "not_reported")):
        out[f"rate_{label}"] = {n: round(float(rate[kind][i])) for i, n in enumerate(names)}
        out[f"ratio_{label}"] = {}
        for i, n in enumerate(names[1:], 1):
            point = rate[kind][0] / rate[kind][i]
            draws = [r[kind][0] / r[kind][i] for r, _ in reps]
            out[f"ratio_{label}"][n] = {"ratio": round(float(point), 2), "ci95": ci(point, draws), "ci95_deff2": ci(point, draws, deff=2.0)}
    out["share_reported"] = {n: {"pct": round(float(share[i]), 1), "ci95": ci(share[i], [s[i] for _, s in reps], log=False),
                                 "ci95_deff2": ci(share[i], [s[i] for _, s in reps], log=False, deff=2.0)} for i, n in enumerate(names)}
    return out


def police_side(kinds=("simple", "aggravated")):
    """Pooled police-recorded rates for women 18 and older over the national run's cities that record ethnicity."""
    comp = json.loads((RUN / "out/comparison.json").read_text())
    vict = {g: 0 for g in ("Black", "Hispanic", "White", "Asian")}
    pop = dict(vict)
    cities = []
    for r in comp["rows"]:
        if r["ethnicity_recording"] != "recorded":
            continue
        d = RUN / "cities" / r["slug"]
        cfg = json.loads((d / "analysis.json").read_text())
        yrs = int(cfg["window"]["end"][:4]) - int(cfg["window"]["start"][:4]) + 1
        P = json.loads((d / "out/population.json").read_text())["city_age"]
        x = pd.concat([pd.read_csv(d / s["path"], dtype=str, usecols=["sex", "age", "race_group"]) for s in cfg["incidents"] if s["kind"] in kinds])
        x = x[(x["sex"] == "F") & (pd.to_numeric(x["age"], errors="coerce") >= 18)]
        for g, code in (("Black", "B"), ("Hispanic", "H"), ("White", "W"), ("Asian", "A")):
            vict[g] += int((x["race_group"] == code).sum())
            pop[g] += sum(P[g]["F"][4:]) * yrs  # ACS bands from 18-19 on, times years
        cities.append(r["city"])
    rate = {g: vict[g] / pop[g] * 1e5 for g in vict}
    return {"cities": len(cities), "victims": vict, "rate": {g: round(v) for g, v in rate.items()},
            "ratio": {g: round(rate["Black"] / rate[g], 2) for g in ("White", "Hispanic", "Asian")}}


def main():
    v, p = load()
    res = {"windows": {}}
    for wname, (a, b) in WINDOWS.items():
        for pname, sizes in PLACES.items():
            vv = v[(v["year"] >= a) & (v["year"] <= b)]
            pp = p[(p["year"] >= a) & (p["year"] <= b)]
            if sizes:
                vv, pp = vv[vv["popsize"].isin(sizes)], pp[pp["popsize"].isin(sizes)]
            key = f"{wname}, {pname}"
            res["windows"][key] = estimate(vv, pp)
            print("done", key, flush=True)
    rob = {"aggravated only": lambda d: d[d["newoff"] == "3"], "injured only": lambda d: d[d["injury"] == "1"],
           "series victimizations left out": lambda d: d[d["series"] == "1"]}
    res["robustness"] = {}
    for wname, (a, b) in (("2015 to 2024", WINDOWS["2015 to 2024"]),):
        for pname, sizes in PLACES.items():
            vv = v[(v["year"] >= a) & (v["year"] <= b)]
            pp = p[(p["year"] >= a) & (p["year"] <= b)]
            if sizes:
                vv, pp = vv[vv["popsize"].isin(sizes)], pp[pp["popsize"].isin(sizes)]
            for rname, f in rob.items():
                res["robustness"][f"{wname}, {pname}, {rname}"] = estimate(f(vv), pp)
                print("done", rname, pname, flush=True)
    res["police"] = police_side()
    res["police_aggravated"] = police_side(kinds=("aggravated",))
    (ROOT / "out").mkdir(exist_ok=True)
    (ROOT / "out/ncvs_results.json").write_text(json.dumps(res, indent=1) + "\n")

    L = ["# NCVS: is the police-recorded gap a reporting gap?", "",
         "Women 18 and older, aggravated and simple assault, per 100,000 a year. Ratio = Black women's rate over the other group's. "
         "Intervals: 95% bootstrap over persons; the second assumes a design effect of 2. Generated by `scripts/analyze_ncvs.py`.", ""]
    pol = res["police"]
    L += [f"Police records (59-city run, the {pol['cities']} cities that record ethnicity, women 18+): Black women {pol['rate']['Black']:,}; "
          f"ratio {pol['ratio']['White']} vs White, {pol['ratio']['Hispanic']} vs Hispanic, {pol['ratio']['Asian']} vs Asian.", ""]
    for key, r in res["windows"].items():
        L += [f"## {key}", "", "| | Black | White | Hispanic | Asian |", "|---|---|---|---|---|"]
        L.append("| Cases (unweighted) | " + " | ".join(f"{r['cases'][g]:,}" for g in GROUPS.values()) + " |")
        for lab in ("all", "reported", "not_reported"):
            L.append(f"| Rate, {lab.replace('_', ' ')} | " + " | ".join(f"{r['rate_' + lab][g]:,}" for g in GROUPS.values()) + " |")
        L.append("| Share reported, % | " + " | ".join(f"{r['share_reported'][g]['pct']} ({r['share_reported'][g]['ci95_deff2'][0]} to {r['share_reported'][g]['ci95_deff2'][1]})" for g in GROUPS.values()) + " |")
        L += ["", "| Black women's ratio | vs White | vs Hispanic | vs Asian |", "|---|---|---|---|"]
        for lab in ("all", "reported", "not_reported"):
            L.append(f"| {lab.replace('_', ' ')} | " + " | ".join(
                f"{r['ratio_' + lab][g]['ratio']} ({r['ratio_' + lab][g]['ci95_deff2'][0]} to {r['ratio_' + lab][g]['ci95_deff2'][1]})" for g in ("White", "Hispanic", "Asian")) + " |")
        L.append("")
    pa = res["police_aggravated"]
    L += ["## Robustness, 2015 to 2024", "", f"Police records, aggravated only (women 18+): ratio {pa['ratio']['White']} vs White, {pa['ratio']['Hispanic']} vs Hispanic.", "",
          "| Subset | Cases, Black women | All: vs White | All: vs Hispanic | Reported: vs White | Reported: vs Hispanic | Share reported, Black / White / Hispanic |",
          "|---|---|---|---|---|---|---|"]
    for key, r in res["robustness"].items():
        f = lambda lab, g: f"{r['ratio_' + lab][g]['ratio']} ({r['ratio_' + lab][g]['ci95_deff2'][0]} to {r['ratio_' + lab][g]['ci95_deff2'][1]})"
        L.append(f"| {key.split(', ', 1)[1]} | {r['cases']['Black']} | {f('all', 'White')} | {f('all', 'Hispanic')} | {f('reported', 'White')} | {f('reported', 'Hispanic')} | "
                 f"{r['share_reported']['Black']['pct']} / {r['share_reported']['White']['pct']} / {r['share_reported']['Hispanic']['pct']} |")
    (ROOT / "out/ncvs.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
