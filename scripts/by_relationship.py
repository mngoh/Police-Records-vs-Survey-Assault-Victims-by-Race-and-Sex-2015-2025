"""Where do police records and the survey part ways? Black women's assault rate against White women's, by the victim's
relationship to the offender, in the NCVS and in police records.

Categories, both sides: intimate partner; other relative; known (acquaintance, friend, neighbor, coworker and the
like); stranger. NCVS from direl (1 intimates, 2 other relatives, 3 well known or casual acquaintance, 4 strangers;
5 and 6, unknown, left out). Police from the NIBRS relationship codes on each victim, taking the closest relationship
when a victim has several (intimate, then relative, then known, then stranger); RU and none, unknown, left out.
Women 18 and older, aggravated and simple assault. NCVS 2015 to 2024 in places of 250,000+ and the whole US; police
records from the 51 cities of the national run whose departments record ethnicity, and DC alone. The survey side is
also shown for assaults with an injury only, since survey simple assault includes verbal threats.

  python scripts/by_relationship.py      ->  out/by_relationship.json, out/by_relationship.md
"""
import json
import pathlib

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
RUN = ROOT.parent / "US-Large-Cities-Assault-Victim-Rates-by-Race-and-Sex-2022-2025"
CATS = ["intimate", "relative", "known", "stranger"]
NIBRS = {"intimate": {"SE", "CS", "BG", "HR", "XS", "XR"}, "relative": {"PA", "CH", "SB", "GP", "GC", "IL", "SP", "SC", "SS", "OF"},
         "known": {"AQ", "FR", "NE", "BE", "EE", "ER", "OK", "CF", "VO"}, "stranger": {"ST"}}
DIREL = {"1": "intimate", "2": "relative", "3": "known", "4": "stranger"}


def nibrs_cat(codes):
    s = set(str(codes).split(";")) if isinstance(codes, str) else set()
    for c in CATS:
        if s & NIBRS[c]:
            return c
    return None


def survey(sizes, injured=False):
    v = pd.read_csv(ROOT / "data/raw/personal_victimization.csv", dtype=str)
    v = v[(v["sex"] == "2") & (v["ager"] != "1") & v["newoff"].isin(["3", "4"]) & (v["year"].astype(int) >= 2015)]
    p = pd.read_csv(ROOT / "data/raw/personal_population.csv", dtype=str, usecols=["sex", "ager", "race_ethnicity", "popsize", "wgtpercy", "year"])
    p = p[(p["sex"] == "2") & (p["ager"] != "1") & (p["year"].astype(int) >= 2015)]
    if sizes:
        v, p = v[v["popsize"].isin(sizes)], p[p["popsize"].isin(sizes)]
    if injured:  # survey simple assault includes verbal threats; an injury means an attack
        v = v[v["injury"] == "1"]
    pop = p.groupby("race_ethnicity")["wgtpercy"].apply(lambda s: pd.to_numeric(s).sum())
    v = v.assign(w=pd.to_numeric(v["newwgt"]), cat=v["direl"].map(DIREL))
    out = {}
    for c in CATS + ["all known relationships"]:
        x = v[v["cat"] == c] if c in CATS else v[v["cat"].notna()]
        rate = {g: x.loc[x["race_ethnicity"] == code, "w"].sum() / pop[code] * 1e5 for g, code in (("Black", "2"), ("White", "1"))}
        out[c] = {"black_rate": round(rate["Black"]), "white_rate": round(rate["White"]), "ratio": round(rate["Black"] / rate["White"], 2),
                  "cases_black": int(((x["race_ethnicity"] == "2")).sum()), "cases_white": int(((x["race_ethnicity"] == "1")).sum())}
    return out


def police(slugs=None):
    comp = json.loads((RUN / "out/comparison.json").read_text())
    vict = {(g, c): 0 for g in ("Black", "White") for c in CATS}
    pop = {"Black": 0, "White": 0}
    for r in comp["rows"]:
        if r["ethnicity_recording"] != "recorded" or (slugs and r["slug"] not in slugs):
            continue
        d = RUN / "cities" / r["slug"]
        cfg = json.loads((d / "analysis.json").read_text())
        yrs = int(cfg["window"]["end"][:4]) - int(cfg["window"]["start"][:4]) + 1
        P = json.loads((d / "out/population.json").read_text())["city_age"]
        x = pd.concat([pd.read_csv(d / s["path"], dtype=str, usecols=["sex", "age", "race_group", "relationship"]) for s in cfg["incidents"]])
        x = x[(x["sex"] == "F") & (pd.to_numeric(x["age"], errors="coerce") >= 18)]
        x["cat"] = x["relationship"].map(nibrs_cat)
        for g, code in (("Black", "B"), ("White", "W")):
            pop[g] += sum(P[g]["F"][4:]) * yrs
            for c in CATS:
                vict[(g, c)] += int(((x["race_group"] == code) & (x["cat"] == c)).sum())
    out = {}
    for c in CATS + ["all known relationships"]:
        cs = CATS if c not in CATS else [c]
        rate = {g: sum(vict[(g, k)] for k in cs) / pop[g] * 1e5 for g in ("Black", "White")}
        out[c] = {"black_rate": round(rate["Black"]), "white_rate": round(rate["White"]), "ratio": round(rate["Black"] / rate["White"], 2)}
    return out


def main():
    res = {"survey, places of 250,000+": survey({"3", "4", "5"}), "survey, US": survey(None),
           "survey, US, injured only": survey(None, injured=True), "survey, places of 250,000+, injured only": survey({"3", "4", "5"}, injured=True),
           "police, 51 cities": police(), "police, DC": police({"dc"})}
    (ROOT / "out/by_relationship.json").write_text(json.dumps(res, indent=1) + "\n")
    L = ["# Black women's assault rate against White women's, by relationship to the offender", "",
         "Women 18 and older, aggravated and simple assault, per 100,000 a year. Survey: NCVS 2015 to 2024. Police: the national run, 2022 to 2025. "
         "Unknown relationships are left out on both sides. Generated by `scripts/by_relationship.py`.", "",
         "| Relationship | " + " | ".join(res) + " |", "|---|" + "---|" * len(res)]
    for c in CATS + ["all known relationships"]:
        L.append(f"| {c} | " + " | ".join(f"{r[c]['ratio']}x ({r[c]['black_rate']:,} vs {r[c]['white_rate']:,})" for r in res.values()) + " |")
    s = res["survey, places of 250,000+"]
    si = res["survey, US, injured only"]
    L += ["", "Survey cases, Black women / White women, injured only, US: " + "; ".join(f"{c} {si[c]['cases_black']} / {si[c]['cases_white']}" for c in CATS) + "."]
    L += ["", "Survey cases, Black women / White women: " + "; ".join(f"{c} {s[c]['cases_black']} / {s[c]['cases_white']}" for c in CATS) + " (places of 250,000+)."]
    (ROOT / "out/by_relationship.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
