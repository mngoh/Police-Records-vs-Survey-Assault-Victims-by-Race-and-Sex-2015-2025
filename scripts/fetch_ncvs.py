"""Download the BJS NCVS Select person-level files through the BJS open-data API, as received.

  Personal Victimization (gcuy-rt5g): every row, every column. One row per victimization; persons with none are absent.
  Personal Population (r4j4-fdwx): women and men from FIRST_YEAR on, only the columns the rates need. One row per
  person-interview; summing wgtpercy over a year gives the population 12 and older.

Each file goes to data/raw/<name>.csv with <name>.csv.source.json beside it (endpoint, query, time, rows, sha256).
Codebook: docs/NCVS_Select_person_level_codebook.pdf (https://bjs.ojp.gov/document/NCVS_Select_person_level_codebook.pdf).

  python scripts/fetch_ncvs.py
"""
import datetime as dt
import hashlib
import io
import json
import pathlib
import urllib.parse
import urllib.request

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
API = "https://api.ojp.gov/bjsdataset/v1"
FIRST_YEAR = "2015"
PAGE = 50000
FILES = {
    "personal_victimization": ("gcuy-rt5g", None, None),
    "personal_population": ("r4j4-fdwx", "idper,yearq,year,ager,sex,hispanic,race,race_ethnicity,msa,popsize,region,locality,wgtpercy", f"year >= '{FIRST_YEAR}'"),
}


def get(dataset, select, where, offset):
    q = {"$limit": PAGE, "$offset": offset, "$order": ":id"}
    if select:
        q["$select"] = select
    if where:
        q["$where"] = where
    url = f"{API}/{dataset}.csv?{urllib.parse.urlencode(q)}"
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "disparity-kit"}), timeout=300).read()


def main():
    raw = ROOT / "data/raw"
    raw.mkdir(parents=True, exist_ok=True)
    for name, (dataset, select, where) in FILES.items():
        parts, offset = [], 0
        while True:
            df = pd.read_csv(io.BytesIO(get(dataset, select, where, offset)), dtype=str)
            parts.append(df)
            offset += len(df)
            print(f"{name}: {offset:,} rows", flush=True)
            if len(df) < PAGE:
                break
        d = pd.concat(parts, ignore_index=True)
        dest = raw / f"{name}.csv"
        d.to_csv(dest, index=False)
        side = {"api": f"{API}/{dataset}", "select": select or "all columns", "where": where or "all rows", "rows": len(d),
                "fetched_at": dt.datetime.now().isoformat(timespec="seconds"), "sha256": hashlib.sha256(dest.read_bytes()).hexdigest(),
                "source": "Bureau of Justice Statistics, National Crime Victimization Survey, NCVS Select person-level files, as received"}
        (raw / f"{name}.csv.source.json").write_text(json.dumps(side, indent=1) + "\n")
        print(f"wrote {dest} ({len(d):,} rows)", flush=True)


if __name__ == "__main__":
    main()
